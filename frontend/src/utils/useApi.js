import React, { useEffect, useRef } from "react";

/**
 * useApi — generic hook for one-shot API calls with loading/error/data states.
 *
 * Usage:
 *   const { data, loading, error, refetch } = useApi(() => citizenApi.getApplications(), []);
 *
 * @param {Function} apiFn   — returns a Promise (axios response)
 * @param {Array}    deps    — refetch when these values change (like useEffect deps)
 * @param {*}        initial — initial value for `data`
 */
export function useApi(apiFn, deps = [], initial = null) {
  const [data, setData]     = useState(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const mountedRef           = useRef(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFn();
      if (mountedRef.current) setData(res.data);
    } catch (err) {
      if (mountedRef.current)
        setError(err.response?.data?.detail || err.message || 'Something went wrong.');
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mountedRef.current = true;
    fetch();
    return () => { mountedRef.current = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

/**
 * useMutation — for POST/PUT/DELETE calls triggered by user action.
 *
 * Usage:
 *   const { mutate, loading, error } = useMutation((data) => authApi.login(data));
 *   await mutate({ email, password });
 */
export function useMutation(apiFn) {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const mutate = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFn(...args);
      return res.data;
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Request failed.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  }, [apiFn]);

  return { mutate, loading, error, clearError: () => setError(null) };
}