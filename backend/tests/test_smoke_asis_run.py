# Smoke test for as-is run: health, public data, signup->OTP(dev_outbox)->verify->login->me, credential-gated endpoints
import os, time, uuid, random
import pytest, requests
from pymongo import MongoClient
from dotenv import dotenv_values

_fe = dotenv_values("/app/frontend/.env")
BASE = (os.environ.get("REACT_APP_BACKEND_URL") or _fe["REACT_APP_BACKEND_URL"]).rstrip("/")
API = BASE + "/api"
_be = dotenv_values("/app/backend/.env")
mdb = MongoClient(_be["MONGO_URL"])[_be["DB_NAME"]]
EMAIL = f"test_smoke_{uuid.uuid4().hex[:8]}@example.com"
PW = "Passw0rd1"
IP = f"10.{random.randint(1,250)}.{random.randint(1,250)}.{random.randint(1,250)}"
S = requests.Session()


def h():
    d = {"X-Forwarded-For": IP}
    if S.cookies.get("ca_csrf"):
        d["X-CSRF-Token"] = S.cookies.get("ca_csrf")
    return d


def outbox_code(template):
    for _ in range(10):
        r = mdb.dev_outbox.find_one({"to": EMAIL, "template": template}, sort=[("created_at", -1)])
        if r and r.get("code"):
            return r["code"]
        time.sleep(0.5)
    return None


# Health
def test_health():
    r = requests.get(f"{API}/health")
    print(r.text)
    assert r.status_code == 200
    d = r.json()
    assert d.get("ok") is True or d.get("status") == "ok"


# Public data
def test_plans_public():
    r = requests.get(f"{API}/plans")
    assert r.status_code == 200
    assert isinstance(r.json(), (list, dict))


def test_blog_public():
    r = requests.get(f"{API}/blog/posts")
    print(r.status_code, r.text[:200])
    assert r.status_code == 200


# Auth flow
class TestAuthFlow:
    def test_1_signup(self):
        r = S.post(f"{API}/auth/signup", headers=h(), json={"full_name": "TEST Smoke", "email": EMAIL, "password": PW,
                                                            "role": "player", "accept_terms": True})
        print(r.text)
        assert r.status_code == 200 and r.json()["ok"] is True

    def test_2_login_unverified_403(self):
        r = S.post(f"{API}/auth/login", headers=h(), json={"email": EMAIL, "password": PW})
        # either 403 email_unverified or 429 OTP cooldown (login re-issues OTP)
        print(r.status_code, r.text)
        assert r.status_code in (403, 429)

    def test_3_verify_email(self):
        code = outbox_code("verify_email")
        assert code and len(code) == 6
        r = S.post(f"{API}/auth/verify-email", headers=h(), json={"email": EMAIL, "code": code})
        print(r.text)
        assert r.status_code == 200
        assert r.json()["user"]["email"] == EMAIL
        assert S.cookies.get("ca_session")

    def test_4_logout_login(self):
        r = S.post(f"{API}/auth/logout", headers=h())
        assert r.status_code == 200
        S.cookies.clear()
        r = S.post(f"{API}/auth/login", headers=h(), json={"email": EMAIL, "password": PW})
        print(r.text)
        assert r.status_code == 200
        assert r.json()["user"]["email"] == EMAIL

    def test_5_me(self):
        r = S.get(f"{API}/auth/me", headers=h())
        assert r.status_code == 200
        assert r.json()["user"]["email"] == EMAIL

    def test_6_bad_password(self):
        r = requests.post(f"{API}/auth/login", headers={"X-Forwarded-For": IP}, json={"email": EMAIL, "password": "wrong1234"})
        assert r.status_code == 401

    # Credential-gated endpoints (expected to fail gracefully)
    def test_7_billing_order_without_razorpay(self):
        plans = requests.get(f"{API}/plans").json()
        lst = plans if isinstance(plans, list) else plans.get("plans", [])
        paid = [p for p in lst if (p.get("price_inr") or 0) >= 1]
        if not paid:
            pytest.skip("no paid plan")
        r = S.post(f"{API}/billing/order", headers=h(), json={"plan_id": paid[0]["id"]})
        print("billing/order", r.status_code, r.text)
        assert r.status_code == 503

    def test_8_entitlements(self):
        r = S.get(f"{API}/entitlements", headers=h())
        print("entitlements", r.status_code, r.text[:300])
        assert r.status_code == 200

    def test_9_coach_chat_llm(self):
        r = S.post(f"{API}/coach/chat", headers=h(), json={"message": "Give me one batting tip"}, timeout=90)
        print("coach/chat", r.status_code, r.text[:300])
        assert r.status_code in (200, 402, 403, 422, 503)


def test_contact_form():
    r = requests.post(f"{API}/contact", headers={"X-Forwarded-For": IP},
                      json={"name": "TEST Smoke", "email": EMAIL, "subject": "TEST", "message": "TEST smoke message from QA"})
    print("contact", r.status_code, r.text)
    assert r.status_code in (200, 503)
