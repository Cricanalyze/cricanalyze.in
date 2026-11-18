# Iteration 7: coach/academy approval gate removed (no ID upload, no admin approval)
import pytest
from conftest import C, login, signup_verified, mdb

QA_COACH = ("qa.coach+qa@cricanalyze.in", "QaCoach#2026")
QA_PCOACH = ("qa.pendingcoach+qa@cricanalyze.in", "QaCoach#2026")
QA_ADMIN = ("qa.admin+qa@cricanalyze.in", "QaAdmin#2026")
QA_PLAYER = ("qa.player+qa@cricanalyze.in", "QaPlayer#2026")

created = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    for e in created:
        mdb.users.delete_one({"email": e})


# Signup coach/academy -> approval_status None, no 403 gate
@pytest.mark.parametrize("role", ["coach", "academy_admin"])
def test_signup_coach_no_gate(role):
    c = signup_verified(role=role, name=f"TEST {role}")
    created.append(c.email)
    doc = mdb.users.find_one({"email": c.email})
    assert doc["role"] == role
    assert doc.get("approval_status") is None
    me = c.get("/auth/me")
    assert me.status_code == 200, me.text
    r = c.get("/academies/mine")
    assert r.status_code == 200, r.text
    assert "approval" not in r.text.lower()
    if role == "academy_admin":
        r = c.post("/academies", json={"name": "TEST Academy NoGate", "city": "Pune"})
        assert r.status_code in (200, 201), r.text
        aid = r.json().get("id") or r.json().get("academy", {}).get("id")
        if aid:
            mdb.academies.delete_one({"id": aid})


# Existing QA coach accounts
@pytest.mark.parametrize("cred", [QA_COACH, QA_PCOACH])
def test_existing_coaches(cred):
    c = login(*cred)
    assert c.get("/auth/me").status_code == 200
    r = c.get("/academies/mine")
    assert r.status_code == 200, r.text
    assert "coach_approval_pending" not in r.text


# Removed endpoints
def test_removed_endpoints():
    a = login(*QA_ADMIN)
    assert a.get("/admin/approvals").status_code in (404, 405)
    assert a.post("/admin/approvals/xyz", json={"action": "approve"}).status_code in (404, 405)
    c = login(*QA_COACH)
    assert c.post("/account/verification-doc", files={"file": ("a.png", b"x", "image/png")}).status_code in (404, 405)


def test_admin_other_endpoints():
    a = login(*QA_ADMIN)
    for p in ["/admin/users", "/admin/settings", "/admin/academies", "/admin/commissions", "/admin/api-keys"]:
        r = a.get(p)
        assert r.status_code == 200, (p, r.status_code, r.text[:200])


def test_player_regression():
    p = login(*QA_PLAYER)
    assert p.get("/auth/me").status_code == 200
