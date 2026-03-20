"""
Module: test_api.py
Description: Automated API smoke tests for NSAP Classification System.
             Tests all endpoints in correct order with real HTTP requests.
             Run with: python test_api.py (server must be running)
"""

import json
import requests

BASE_URL = "http://localhost:8000/api/v1"

# ─── Colors for terminal output ───────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ─── Test State ───────────────────────────────────────────────
# Shared across tests
state = {
    "citizen_token":     None,
    "officer_token":     None,
    "admin_token":       None,
    "application_id":    None,
    "citizen_email":     "test.citizen@nsap.com",
    "officer_email":     "test.officer@nsap.com",
    "admin_email":       "test.admin@nsap.com",
    "password":          "test1234",
}

# ─── Helpers ──────────────────────────────────────────────────
def print_header(title: str):
    print(f"\n{BOLD}{BLUE}{'─'*55}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'─'*55}{RESET}")


def print_result(name: str, passed: bool, detail: str = ""):
    icon   = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  {icon} {name:<45} {status}")
    if detail and not passed:
        print(f"     {YELLOW}→ {detail}{RESET}")


def post(endpoint, data, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(
            f"{BASE_URL}{endpoint}",
            json    = data,
            headers = headers,
            timeout = 10,
        )
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}


def get(endpoint, token=None, params=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(
            f"{BASE_URL}{endpoint}",
            headers = headers,
            params  = params,
            timeout = 10,
        )
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"error": str(e)}


# ─── Test Suites ──────────────────────────────────────────────

def test_health():
    print_header("1. HEALTH CHECK")
    code, body = get("/health")
    print_result(
        "GET /health",
        code == 200 and body.get("status") == "ok",
        str(body)
    )
    print_result(
        "Model loaded",
        body.get("model", {}).get("status") == "loaded",
        str(body.get("model"))
    )
    print_result(
        "Database connected",
        body.get("database") == "connected",
        str(body.get("database"))
    )


def test_auth():
    print_header("2. AUTHENTICATION")

    # ── Register Citizen ──────────────────────────────────────
    code, body = post("/auth/register", {
        "name":     "Test Citizen",
        "email":    state["citizen_email"],
        "password": state["password"],
        "role":     "citizen",
        "state":    "Bihar",
    })
    # 201 = registered, 400 = already exists (both ok for smoke test)
    print_result(
        "POST /auth/register (citizen)",
        code in [201, 400],
        str(body)
    )

    # ── Register Officer ──────────────────────────────────────
    code, body = post("/auth/register", {
        "name":     "Test Officer",
        "email":    state["officer_email"],
        "password": state["password"],
        "role":     "officer",
        "state":    "Bihar",
    })
    print_result(
        "POST /auth/register (officer)",
        code in [201, 400],
        str(body)
    )

    # ── Register Admin ────────────────────────────────────────
    code, body = post("/auth/register", {
        "name":     "Test Admin",
        "email":    state["admin_email"],
        "password": state["password"],
        "role":     "admin",
        "state":    "Bihar",
    })
    print_result(
        "POST /auth/register (admin)",
        code in [201, 400],
        str(body)
    )

    # ── Login Citizen ─────────────────────────────────────────
    code, body = post("/auth/login", {
        "email":    state["citizen_email"],
        "password": state["password"],
    })
    passed = code == 200 and "access_token" in body
    print_result("POST /auth/login (citizen)", passed, str(body))
    if passed:
        state["citizen_token"] = body["access_token"]

    # ── Login Officer ─────────────────────────────────────────
    code, body = post("/auth/login", {
        "email":    state["officer_email"],
        "password": state["password"],
    })
    passed = code == 200 and "access_token" in body
    print_result("POST /auth/login (officer)", passed, str(body))
    if passed:
        state["officer_token"] = body["access_token"]

    # ── Login Admin ───────────────────────────────────────────
    code, body = post("/auth/login", {
        "email":    state["admin_email"],
        "password": state["password"],
    })
    passed = code == 200 and "access_token" in body
    print_result("POST /auth/login (admin)", passed, str(body))
    if passed:
        state["admin_token"] = body["access_token"]

    # ── Get Current User ──────────────────────────────────────
    code, body = get("/auth/me", token=state["citizen_token"])
    print_result(
        "GET /auth/me",
        code == 200 and body.get("role") == "citizen",
        str(body)
    )

    # ── Wrong Password ────────────────────────────────────────
    code, body = post("/auth/login", {
        "email":    state["citizen_email"],
        "password": "wrongpassword",
    })
    print_result(
        "POST /auth/login (wrong password → 401)",
        code == 401,
        str(body)
    )

    # ── No Token ──────────────────────────────────────────────
    code, body = get("/auth/me")
    print_result(
        "GET /auth/me (no token → 401)",
        code == 401,
        str(body)
    )


def test_citizen():
    print_header("3. CITIZEN ENDPOINTS")

    if not state["citizen_token"]:
        print(f"  {YELLOW}⚠️  Skipping — no citizen token{RESET}")
        return

    # ── Submit Application ────────────────────────────────────
    code, body = post("/citizen/apply", {
        "age":                   68,
        "gender":                "Female",
        "marital_status":        "Widowed",
        "annual_income":         35000,
        "bpl_card":              "Yes",
        "area_type":             "Rural",
        "state":                 "Uttar Pradesh",
        "social_category":       "SC",
        "employment_status":     "Unemployed",
        "has_disability":        "No",
        "disability_percentage": 0,
        "disability_type":       "None",
        "aadhaar_linked":        "Yes",
        "bank_account":          "Yes",
    }, token=state["citizen_token"])

    passed = code == 201 and "application_id" in body
    print_result("POST /citizen/apply (WP expected)", passed, str(body))
    if passed:
        state["application_id"] = body["application_id"]
        print(f"     {YELLOW}→ Predicted: {body.get('predicted_scheme')} "
              f"({body.get('confidence_score', 0)*100:.1f}%){RESET}")

    # ── Submit OAP Application ────────────────────────────────
    code, body = post("/citizen/apply", {
        "age":                   72,
        "gender":                "Male",
        "marital_status":        "Married",
        "annual_income":         28000,
        "bpl_card":              "Yes",
        "area_type":             "Rural",
        "state":                 "Bihar",
        "social_category":       "OBC",
        "employment_status":     "Unemployed",
        "has_disability":        "No",
        "disability_percentage": 0,
        "disability_type":       "None",
        "aadhaar_linked":        "Yes",
        "bank_account":          "Yes",
    }, token=state["citizen_token"])
    passed = code == 201
    print_result("POST /citizen/apply (OAP expected)", passed, str(body))
    if passed:
        print(f"     {YELLOW}→ Predicted: {body.get('predicted_scheme')} "
              f"({body.get('confidence_score', 0)*100:.1f}%){RESET}")

    # ── Submit DP Application ─────────────────────────────────
    code, body = post("/citizen/apply", {
        "age":                   35,
        "gender":                "Male",
        "marital_status":        "Single",
        "annual_income":         28000,
        "bpl_card":              "Yes",
        "area_type":             "Rural",
        "state":                 "Bihar",
        "social_category":       "ST",
        "employment_status":     "Unemployed",
        "has_disability":        "Yes",
        "disability_percentage": 65,
        "disability_type":       "Locomotor",
        "aadhaar_linked":        "Yes",
        "bank_account":          "Yes",
    }, token=state["citizen_token"])
    passed = code == 201
    print_result("POST /citizen/apply (DP expected)", passed, str(body))
    if passed:
        print(f"     {YELLOW}→ Predicted: {body.get('predicted_scheme')} "
              f"({body.get('confidence_score', 0)*100:.1f}%){RESET}")

    # ── NOT ELIGIBLE Application ──────────────────────────────
    code, body = post("/citizen/apply", {
        "age":                   45,
        "gender":                "Male",
        "marital_status":        "Married",
        "annual_income":         250000,
        "bpl_card":              "No",
        "area_type":             "Urban",
        "state":                 "Maharashtra",
        "social_category":       "General",
        "employment_status":     "Salaried",
        "has_disability":        "No",
        "disability_percentage": 0,
        "disability_type":       "None",
        "aadhaar_linked":        "Yes",
        "bank_account":          "Yes",
    }, token=state["citizen_token"])
    passed = code == 201
    print_result("POST /citizen/apply (NOT_ELIGIBLE expected)", passed, str(body))
    if passed:
        print(f"     {YELLOW}→ Predicted: {body.get('predicted_scheme')} "
              f"({body.get('confidence_score', 0)*100:.1f}%){RESET}")

    # ── List Applications ─────────────────────────────────────
    code, body = get(
        "/citizen/applications",
        token=state["citizen_token"]
    )
    print_result(
        "GET /citizen/applications",
        code == 200 and "data" in body,
        str(body)
    )
    if code == 200:
        print(f"     {YELLOW}→ Total applications: {body.get('total')}{RESET}")

    # ── Single Application ────────────────────────────────────
    if state["application_id"]:
        code, body = get(
            f"/citizen/applications/{state['application_id']}",
            token=state["citizen_token"]
        )
        print_result(
            "GET /citizen/applications/{id}",
            code == 200 and body.get("id") == state["application_id"],
            str(body)
        )

    # ── Notifications ─────────────────────────────────────────
    code, body = get(
        "/citizen/notifications",
        token=state["citizen_token"]
    )
    print_result(
        "GET /citizen/notifications",
        code == 200 and "notifications" in body,
        str(body)
    )
    if code == 200:
        print(f"     {YELLOW}→ Unread: {body.get('unread_count')}{RESET}")

    # ── Wrong Role Access ─────────────────────────────────────
    code, body = get(
        "/officer/queue",
        token=state["citizen_token"]
    )
    print_result(
        "GET /officer/queue (citizen token → 403)",
        code == 403,
        str(body)
    )


def test_officer():
    print_header("4. OFFICER ENDPOINTS")

    if not state["officer_token"]:
        print(f"  {YELLOW}⚠️  Skipping — no officer token{RESET}")
        return

    # ── Review Queue ──────────────────────────────────────────
    code, body = get(
        "/officer/queue",
        token=state["officer_token"]
    )
    print_result(
        "GET /officer/queue",
        code == 200 and "queue" in body,
        str(body)
    )
    if code == 200:
        print(f"     {YELLOW}→ Pending: {body.get('total')} "
              f"(needs_review: {body.get('needs_review_count')}){RESET}")

    # ── All Applications ──────────────────────────────────────
    code, body = get(
        "/officer/applications",
        token=state["officer_token"]
    )
    print_result(
        "GET /officer/applications",
        code == 200 and "data" in body,
        str(body)
    )

    # ── Application Detail ────────────────────────────────────
    if state["application_id"]:
        code, body = get(
            f"/officer/applications/{state['application_id']}",
            token=state["officer_token"]
        )
        print_result(
            "GET /officer/applications/{id}",
            code == 200,
            str(body)
        )
        if code == 200:
            shap = body.get("prediction", {}).get("shap_explanation", {})
            print(f"     {YELLOW}→ SHAP values: "
                  f"{'present' if shap else 'null'}{RESET}")

    # ── Make Decision ─────────────────────────────────────────
    if state["application_id"]:
        code, body = post(
            f"/officer/applications/{state['application_id']}/decide",
            {
                "application_id":  state["application_id"],
                "decision":        "approved",
                "remarks":         "Documents verified. Applicant qualifies.",
                "override_scheme": None,
            },
            token=state["officer_token"]
        )
        print_result(
            "POST /officer/applications/{id}/decide",
            code == 201,
            str(body)
        )

        # ── Duplicate Decision Should Fail ────────────────────
        code, body = post(
            f"/officer/applications/{state['application_id']}/decide",
            {
                "application_id": state["application_id"],
                "decision":       "approved",
                "remarks":        "Duplicate",
            },
            token=state["officer_token"]
        )
        print_result(
            "POST decide again (duplicate → 400)",
            code == 400,
            str(body)
        )

    # ── Officer Stats ─────────────────────────────────────────
    code, body = get(
        "/officer/stats",
        token=state["officer_token"]
    )
    print_result(
        "GET /officer/stats",
        code == 200 and "queue" in body,
        str(body)
    )

    # ── Wrong Role Access ─────────────────────────────────────
    code, body = get(
        "/admin/stats",
        token=state["officer_token"]
    )
    print_result(
        "GET /admin/stats (officer token → 403)",
        code == 403,
        str(body)
    )


def test_admin():
    print_header("5. ADMIN ENDPOINTS")

    if not state["admin_token"]:
        print(f"  {YELLOW}⚠️  Skipping — no admin token{RESET}")
        return

    # ── Dashboard Stats ───────────────────────────────────────
    code, body = get(
        "/admin/stats",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/stats",
        code == 200 and "applications" in body,
        str(body)
    )
    if code == 200:
        apps = body.get("applications", {})
        print(f"     {YELLOW}→ Total applications: "
              f"{apps.get('total')}{RESET}")

    # ── All Applications ──────────────────────────────────────
    code, body = get(
        "/admin/applications",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/applications",
        code == 200 and "data" in body,
        str(body)
    )

    # ── Model Metrics ─────────────────────────────────────────
    code, body = get(
        "/admin/model/metrics",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/model/metrics",
        code in [200, 404],
        str(body) if code != 200 else
        f"Best model: {body.get('best_model', {}).get('model_name')}"
    )

    # ── Fairness Report ───────────────────────────────────────
    code, body = get(
        "/admin/model/fairness",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/model/fairness",
        code in [200, 404],
        str(body) if code != 200 else
        f"Groups: {body.get('total_groups')}, "
        f"Flagged: {body.get('flagged_count')}"
    )

    # ── Confusion Matrix ──────────────────────────────────────
    code, _ = get(
        "/admin/model/confusion",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/model/confusion",
        code in [200, 404],
        "Image endpoint"
    )

    # ── SHAP Image ────────────────────────────────────────────
    code, _ = get(
        "/admin/model/shap",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/model/shap",
        code in [200, 404],
        "Image endpoint"
    )

    # ── Officer Activity ──────────────────────────────────────
    code, body = get(
        "/admin/officers/activity",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/officers/activity",
        code == 200 and "officers" in body,
        str(body)
    )

    # ── All Users ─────────────────────────────────────────────
    code, body = get(
        "/admin/users",
        token=state["admin_token"]
    )
    print_result(
        "GET /admin/users",
        code == 200 and "data" in body,
        str(body)
    )

    # ── Wrong Role ────────────────────────────────────────────
    code, body = get(
        "/citizen/applications",
        token=state["admin_token"]
    )
    print_result(
        "GET /citizen/applications (admin token → 403)",
        code == 403,
        str(body)
    )


# ─── Summary ──────────────────────────────────────────────────
def print_summary(results: list):
    print(f"\n{BOLD}{'─'*55}{RESET}")
    print(f"{BOLD}  TEST SUMMARY{RESET}")
    print(f"{BOLD}{'─'*55}{RESET}")
    passed = sum(1 for r in results if r)
    total  = len(results)
    color  = GREEN if passed == total else YELLOW if passed > total//2 else RED
    print(f"  {color}{passed}/{total} tests passed{RESET}")
    print(f"{'─'*55}\n")


# ─── Main ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"{BOLD}   NSAP API — Automated Smoke Tests{RESET}")
    print(f"{BOLD}{'═'*55}{RESET}")
    print(f"  Base URL: {BASE_URL}")

    test_health()
    test_auth()
    test_citizen()
    test_officer()
    test_admin()

    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"{BOLD}   All tests complete!{RESET}")
    print(f"{BOLD}{'═'*55}{RESET}\n")