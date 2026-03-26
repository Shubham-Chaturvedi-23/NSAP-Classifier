import { ROLES } from './constants';

export const decodeToken = (token) => {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
};

export const isTokenExpired = (token) => {
  const decoded = decodeToken(token);
  if (!decoded?.exp) return true;
  return decoded.exp * 1000 < Date.now();
};

export const getStoredUser = () => {
  try {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  } catch { return null; }
};

export const getRoleHomePath = (role) => {
  if (role === ROLES.OFFICER) return '/officer/queue';
  if (role === ROLES.ADMIN) return '/admin/dashboard';
  return '/citizen/applications';
};