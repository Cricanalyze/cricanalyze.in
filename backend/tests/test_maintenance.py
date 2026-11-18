# Maintenance mode regression: schedule via admin, gate anon/player/admin, end-now. Always leaves maintenance disabled.
import os
from datetime import datetime, timedelta, timezone
import pytest
import requests
from dotenv import dotenv_values

BASE = (os.environ.get("REACT_APP_BACKEND_URL") or dotenv_values("/app/frontend/.env")["REACT_APP_BACKEND_URL"]).rstrip("/") + "/api"
ADMIN = ("qa.admin+qa@cricanalyze.in", "QaAdmin#2026")
PLAYER = ("qa.player+qa@cricanalyze.in", "QaPlayer#2026")
IST = timezone(timedelta(hours=5, minutes=30))


def login(email, pw):
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"email": email, "password": pw}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"login failed {email}: {r.status_code} {r.text[:200]}")
    s.headers["x-csrf-token"] = s.cookies.get("ca_csrf") or ""
    return s


def ist(dt):
    return dt.astimezone(IST).strftime("%Y-%m-%dT%H:%M")


@pytest.fixture(scope="module")
def admin():
    return login(*ADMIN)


@pytest.fixture(scope="module")
def player():
    return login(*PLAYER)


@pytest.fixture(scope="module", autouse=True)
def always_disable(admin):
    yield
    admin.put(f"{BASE}/admin/maintenance", json={"enabled": False, "start_at": None, "end_at": None, "message": None}, timeout=30)


class TestMaintenance:
    def test_public_status_off(self):
        r = requests.get(f"{BASE}/maintenance", timeout=30)
        assert r.status_code == 200
        assert set(r.json()) >= {"active", "enabled", "start_at", "end_at", "message"}

    def test_player_cannot_set(self, player):
        r = player.put(f"{BASE}/admin/maintenance", json={"enabled": False}, timeout=30)
        assert r.status_code in (401, 403)

    def test_anon_cannot_set(self):
        r = requests.put(f"{BASE}/admin/maintenance", json={"enabled": False}, timeout=30)
        assert r.status_code in (401, 403)

    def test_validation_end_before_start(self, admin):
        n = datetime.now(timezone.utc)
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": True, "start_at": ist(n), "end_at": ist(n - timedelta(hours=1))}, timeout=30)
        assert r.status_code == 422

    def test_validation_missing_times(self, admin):
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": True}, timeout=30)
        assert r.status_code == 422

    def test_scheduled_future_not_active(self, admin):
        n = datetime.now(timezone.utc)
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": True, "start_at": ist(n + timedelta(hours=2)), "end_at": ist(n + timedelta(hours=3)), "message": "TEST_future"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["enabled"] is True and d["active"] is False
        assert requests.get(f"{BASE}/plans", timeout=30).status_code == 200

    def test_live_gate(self, admin, player):
        n = datetime.now(timezone.utc)
        start, end = n - timedelta(minutes=3), n + timedelta(minutes=30)
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": True, "start_at": ist(start), "end_at": ist(end), "message": "TEST_ maintenance msg"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["active"] is True and d["message"] == "TEST_ maintenance msg"
        # IST naive input -> correct UTC instant (minute precision)
        got_end = datetime.fromisoformat(d["end_at"])
        assert abs((got_end - end).total_seconds()) < 61
        # anon blocked
        rp = requests.get(f"{BASE}/plans", timeout=30)
        assert rp.status_code == 503
        assert rp.json()["detail"] == "maintenance" and rp.json()["end_at"]
        # open endpoints
        assert requests.get(f"{BASE}/maintenance", timeout=30).json()["active"] is True
        # player blocked
        assert player.get(f"{BASE}/account/status", timeout=30).status_code == 503
        assert player.get(f"{BASE}/auth/me", timeout=30).status_code == 200
        # admin passes
        assert admin.get(f"{BASE}/account/status", timeout=30).status_code == 200
        assert admin.get(f"{BASE}/plans", timeout=30).status_code == 200
        # fresh admin login works during maintenance
        s = login(*ADMIN)
        assert s.get(f"{BASE}/auth/me", timeout=30).status_code == 200

    def test_end_now_restores(self, admin, player):
        r = admin.put(f"{BASE}/admin/maintenance", json={"enabled": False, "start_at": None, "end_at": None, "message": None}, timeout=30)
        assert r.status_code == 200 and r.json()["active"] is False
        assert requests.get(f"{BASE}/plans", timeout=30).status_code == 200
        assert player.get(f"{BASE}/account/status", timeout=30).status_code == 200
