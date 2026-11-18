# Helper: python maint_toggle.py on|off  -> toggles live maintenance window via admin API (ISO Z)
import sys, requests
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values
B = dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
s = requests.Session()
s.post(f"{B}/auth/login", json={"email": "qa.admin+qa@cricanalyze.in", "password": "QaAdmin#2026"}, timeout=30)
s.headers["x-csrf-token"] = s.cookies.get("ca_csrf")
n = datetime.now(timezone.utc)
f = lambda d: d.strftime("%Y-%m-%dT%H:%M:%SZ")
body = {"enabled": True, "start_at": f(n - timedelta(minutes=5)), "end_at": f(n + timedelta(minutes=30)), "message": "TEST_ We are upgrading the analysis engine"} \
    if sys.argv[1] == "on" else {"enabled": False, "start_at": None, "end_at": None, "message": None}
r = s.put(f"{B}/admin/maintenance", json=body, timeout=30)
print(r.status_code, r.json())
