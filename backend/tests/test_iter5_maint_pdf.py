# Iteration 5: maintenance mode with ISO-Z inputs (gate anon/player/admin) + bowling PDF v4.0. Always leaves maintenance OFF.
import os, io, time
from datetime import datetime, timedelta, timezone
import pytest, requests
from dotenv import dotenv_values

BASE = (os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"]).rstrip("/") + "/api"
ADMIN = ("qa.admin+qa@cricanalyze.in", "QaAdmin#2026")
PLAYER = ("qa.player+qa@cricanalyze.in", "QaPlayer#2026")
BOWL_JOB = "4b50454e0476462fb9977ea2402a175d"


def login(email, pw):
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"email": email, "password": pw}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"login failed {email}: {r.status_code}")
    s.headers["x-csrf-token"] = s.cookies.get("ca_csrf") or ""
    return s


def z(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


@pytest.fixture(scope="module")
def admin():
    return login(*ADMIN)


@pytest.fixture(scope="module")
def player():
    return login(*PLAYER)


@pytest.fixture(scope="module", autouse=True)
def always_off(admin):
    yield
    admin.put(f"{BASE}/admin/maintenance", json={"enabled": False, "start_at": None, "end_at": None, "message": None}, timeout=30)


def wait_status(url, code, sess=None, tries=8):
    r = None
    for _ in range(tries):
        r = (sess or requests).get(url, timeout=30)
        if r.status_code == code:
            return r
        time.sleep(2)
    return r


class TestMaintenanceZ:
    def test_csrf_required(self, admin):
        r = requests.put(f"{BASE}/admin/maintenance", json={"enabled": False}, cookies=admin.cookies, timeout=30)
        assert r.status_code == 403

    def test_live_window_iso_z(self, admin, player):
        n = datetime.now(timezone.utc)
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": True, "start_at": z(n - timedelta(minutes=5)),
                      "end_at": z(n + timedelta(minutes=30)), "message": "TEST_ upgrade in progress"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["active"] is True and d["enabled"] is True
        assert abs((datetime.fromisoformat(d["end_at"]) - (n + timedelta(minutes=30))).total_seconds()) < 2
        rp = wait_status(f"{BASE}/plans", 503)
        assert rp.status_code == 503 and rp.json()["detail"] == "maintenance"
        assert rp.json()["message"] == "TEST_ upgrade in progress"
        m = requests.get(f"{BASE}/maintenance", timeout=30).json()
        assert m["active"] is True
        assert wait_status(f"{BASE}/account/status", 503, player).status_code == 503
        assert admin.get(f"{BASE}/account/status", timeout=30).status_code == 200
        assert admin.get(f"{BASE}/plans", timeout=30).status_code == 200

    def test_off_restores(self, admin, player):
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": False, "start_at": None, "end_at": None, "message": None}, timeout=30)
        assert r.status_code == 200 and r.json()["active"] is False
        assert wait_status(f"{BASE}/plans", 200).status_code == 200
        assert wait_status(f"{BASE}/account/status", 200, player).status_code == 200


class TestPdfV4:
    def test_bowling_pdf_admin(self, admin):
        r = admin.get(f"{BASE}/analyses/{BOWL_JOB}/pdf", timeout=180)
        assert r.status_code == 200, r.text[:300]
        assert r.headers["content-type"].startswith("application/pdf")
        import pymupdf
        txt = "\n".join(pg.get_text() for pg in pymupdf.open(stream=r.content, filetype="pdf"))
        for s in ("Technique Report", "Three key takeaways", "v4.0"):
            assert s in txt, f"missing {s}"

    def test_pdf_player_forbidden_other_users(self, player):
        r = player.get(f"{BASE}/analyses/{BOWL_JOB}/pdf", timeout=60)
        assert r.status_code in (403, 404)
