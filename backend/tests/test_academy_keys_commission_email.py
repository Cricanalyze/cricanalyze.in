# Regression tests: multi-key pool, coach approvals, commissions, academy code/join/leaderboard/nickname, report email, plans
import datetime
import pytest
from conftest import login, mdb, C

PW_P, PW_C, PW_A = "QaPlayer#2026", "QaCoach#2026", "QaAdmin#2026"
ACADEMY = "QA Lions Academy"


@pytest.fixture(scope="module")
def admin():
    return login("qa.admin+qa@cricanalyze.in", PW_A)


@pytest.fixture(scope="module")
def coach():
    return login("qa.coach+qa@cricanalyze.in", PW_C)


@pytest.fixture(scope="module")
def player():
    return login("qa.player+qa@cricanalyze.in", PW_P)


@pytest.fixture(scope="module")
def newplayer():
    return login("qa.newplayer+qa@cricanalyze.in", PW_P)


@pytest.fixture(scope="module")
def aid():
    return mdb.academies.find_one({"name": ACADEMY})["id"]


# ---------- plans ----------
def test_plans_12_active():
    r = C().get("/plans")
    assert r.status_code == 200
    ps = r.json()
    assert len(ps) == 12
    prods = {}
    for p in ps:
        prods.setdefault(p["product"], set()).add(p["tier"])
    assert set(prods) == {"batting", "bowling", "combined", "academy"}
    assert all(len(v) == 3 for v in prods.values())


# ---------- api key pool ----------
def test_api_keys_list_and_crud(admin):
    r = admin.get("/admin/api-keys")
    assert r.status_code == 200, r.text
    d = r.json()
    envs = {k["provider"] for k in d["keys"] if k.get("env")}
    assert envs == {"anthropic", "ultralytics"}
    assert "anthropic_mode" in d["modes"] and "ultralytics_mode" in d["modes"]
    r = admin.post("/admin/api-keys", json={"provider": "anthropic", "label": "TEST_dummy", "key": "sk-ant-dummy-12345678", "priority": 99})
    assert r.status_code == 200, r.text
    kid = r.json()["id"]
    try:
        # immediately deactivate so rotate mode never uses it
        assert admin.patch(f"/admin/api-keys/{kid}", json={"active": False}).status_code == 200
        row = next(k for k in admin.get("/admin/api-keys").json()["keys"] if k["id"] == kid)
        assert row["masked"] == "sk-ant…5678" and row["active"] is False
        assert "key_enc" not in row and "key" not in row
    finally:
        assert admin.delete(f"/admin/api-keys/{kid}").status_code == 200
    assert not any(k["id"] == kid for k in admin.get("/admin/api-keys").json()["keys"])
    assert mdb.api_keys.count_documents({"id": kid}) == 0


def test_api_keys_bad_provider_and_rbac(admin, player):
    assert admin.post("/admin/api-keys", json={"provider": "openai", "label": "x", "key": "12345678xx"}).status_code == 422
    assert player.get("/admin/api-keys").status_code in (403, 404)


def test_key_mode_save(admin):
    cur = admin.get("/admin/api-keys").json()["modes"]
    r = admin.put("/admin/settings", json={"keys": {"anthropic_mode": "failover"}, "confirm": True})
    assert r.status_code == 200, r.text
    m = admin.get("/admin/api-keys").json()["modes"]
    assert m["anthropic_mode"] == "failover"
    assert m["ultralytics_mode"] == cur["ultralytics_mode"]  # other provider's mode not clobbered
    admin.put("/admin/settings", json={"keys": {"anthropic_mode": cur["anthropic_mode"]}, "confirm": True})


# ---------- approval gate ----------
def test_pending_coach_gate():
    u = mdb.users.find_one({"email": "qa.pendingcoach+qa@cricanalyze.in"})
    if u.get("approval_status") != "pending":
        pytest.skip("pending coach already approved")
    c = login("qa.pendingcoach+qa@cricanalyze.in", PW_C)
    r = c.get("/analyses")
    assert r.status_code == 403 and "coach_approval_pending" in r.text
    me = c.get("/auth/me")
    assert me.status_code == 200
    # player can't upload verification doc
    p = login("qa.newplayer+qa@cricanalyze.in", PW_P)
    r = p.post("/account/verification-doc", files={"file": ("a.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")}, data={"doc_type": "certificate"})
    assert r.status_code == 403


def test_approvals_list(admin):
    r = admin.get("/admin/approvals", params={"status": "pending"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    for row in r.json():
        assert row["role"] in ("coach", "academy_admin")


def test_approve_nonexistent(admin):
    assert admin.post("/admin/approvals/doesnotexist", json={"approve": True}).status_code == 404


# ---------- commissions ----------
def test_commissions_list(admin, aid):
    r = admin.get("/admin/commissions")
    assert r.status_code == 200
    d = r.json()
    rows = [x for x in d["rows"] if x["academy_id"] == aid]
    assert rows and rows[0]["academy_name"] == ACADEMY
    assert any(t["academy_id"] == aid for t in d["totals"])


def test_commission_default_save_string_value(admin):
    orig = admin.get("/admin/settings").json()["commission"]
    # frontend sends value as string from <input type=number>
    r = admin.put("/admin/settings", json={"commission": {"mode": "percent_first", "value": "12"}, "confirm": True})
    assert r.status_code == 200, r.text
    got = admin.get("/admin/settings").json()["commission"]
    admin.put("/admin/settings", json={"commission": orig, "confirm": True})
    assert got["mode"] == "percent_first" and float(got["value"]) == 12


def test_commission_override(admin, coach, aid):
    r = admin.put(f"/admin/academies/{aid}/commission", json={"mode": "fixed_per_student", "value": 150})
    assert r.status_code == 200
    e = coach.get(f"/academies/{aid}/earnings").json()
    assert e["commission"] == {"mode": "fixed_per_student", "value": 150}
    assert admin.put(f"/admin/academies/{aid}/commission", json={"mode": "bogus", "value": 1}).status_code == 422
    assert admin.put(f"/admin/academies/{aid}/commission", json={}).status_code == 200
    e = coach.get(f"/academies/{aid}/earnings").json()
    assert e["commission"]["mode"] == admin.get("/admin/settings").json()["commission"]["mode"]


def test_mark_paid_unknown_ids(admin):
    r = admin.post("/admin/commissions/mark-paid", json={"ids": ["nope"], "reference": "TEST"})
    assert r.status_code == 200 and r.json()["updated"] == 0


# ---------- academy code / earnings ----------
def test_earnings_code(coach, aid, player):
    r = coach.get(f"/academies/{aid}/earnings")
    assert r.status_code == 200
    d = r.json()
    assert len(d["code"]) == 6 and d["referral_link"].endswith(f"/signup?ref={d['code']}")
    assert d["pending_inr"] >= 0
    assert player.get(f"/academies/{aid}/earnings").status_code == 404


def test_lookup_and_join_rules(newplayer, coach, aid):
    code = mdb.academies.find_one({"id": aid})["code"]
    assert newplayer.get("/academies-lookup", params={"code": "ZZZZZZ"}).status_code == 404
    r = newplayer.get("/academies-lookup", params={"code": code.lower()})
    assert r.status_code == 200 and r.json()["name"] == ACADEMY
    assert coach.post("/academies-join", json={"code": code}).status_code == 403
    assert newplayer.post("/academies-join", json={"code": "ZZZZZZ"}).status_code == 404


def test_join_accept_flow(newplayer, coach, aid, player):
    code = mdb.academies.find_one({"id": aid})["code"]
    uid_ = newplayer.user["id"]
    if mdb.academy_memberships.find_one({"academy_id": aid, "user_id": uid_, "status": "active"}):
        pytest.skip("newplayer already a member")
    r = newplayer.post("/academies-join", json={"code": code})
    if r.status_code == 409:
        pass
    else:
        assert r.status_code == 200, r.text
    assert newplayer.post("/academies-join", json={"code": code}).status_code == 409
    reqs = coach.get(f"/academies/{aid}/requests").json()
    req = next(x for x in reqs if x["user_id"] == uid_)
    assert player.get(f"/academies/{aid}/requests").status_code == 404
    # store for later tests (UI test will do accept). Leave pending.
    assert req["status"] == "pending"


# ---------- leaderboard / nickname ----------
def test_leaderboard(coach, player, newplayer, aid):
    for t in ("batting", "bowling"):
        r = coach.get(f"/academies/{aid}/leaderboard", params={"type": t})
        assert r.status_code == 200
        rows = r.json()
        assert [x["rank"] for x in rows] == list(range(1, len(rows) + 1))
        assert all("job_id" in x for x in rows)
    assert coach.get(f"/academies/{aid}/leaderboard", params={"type": "x"}).status_code == 422
    rp = player.get(f"/academies/{aid}/leaderboard", params={"type": "batting"})
    assert rp.status_code == 200 and all("job_id" not in x for x in rp.json())
    if not mdb.academy_memberships.find_one({"academy_id": aid, "user_id": newplayer.user["id"], "status": "active"}):
        assert newplayer.get(f"/academies/{aid}/leaderboard").status_code == 404


def test_nickname(coach, player, aid):
    pid = player.user["id"]
    orig = (mdb.academy_memberships.find_one({"academy_id": aid, "user_id": pid}) or {}).get("nickname")
    r = coach.patch(f"/academies/{aid}/members/{pid}/nickname", json={"nickname": "TEST_Rocket"})
    assert r.status_code == 200
    assert mdb.academy_memberships.find_one({"academy_id": aid, "user_id": pid})["nickname"] == "TEST_Rocket"
    assert player.patch(f"/academies/{aid}/members/{pid}/nickname", json={"nickname": "hack"}).status_code in (403, 404)
    coach.patch(f"/academies/{aid}/members/{pid}/nickname", json={"nickname": orig or ""})


# ---------- report email ----------
def _job(player):
    j = mdb.analysis_jobs.find_one({"user_id": player.user["id"], "status": "completed"}, sort=[("created_at", -1)])
    if not j:
        pytest.skip("no completed job for qa.player")
    return j["id"]


def test_email_past_422(player):
    jid = _job(player)
    r = player.post(f"/analyses/{jid}/email", json={"send_at": "2020-01-01T10:00"})
    assert r.status_code == 422
    assert player.post(f"/analyses/{jid}/email", json={"send_at": "garbage"}).status_code == 422


def test_email_schedule_and_cancel(player, newplayer):
    jid = _job(player)
    t = (datetime.datetime.utcnow() + datetime.timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:00Z")
    r = player.post(f"/analyses/{jid}/email", json={"send_at": t})
    assert r.status_code == 200 and r.json()["scheduled"]
    sid = r.json()["id"]
    lst = player.get(f"/analyses/{jid}/email-schedules").json()["schedules"]
    assert any(s["id"] == sid and s["status"] == "pending" for s in lst)
    assert newplayer.delete(f"/report-schedules/{sid}").status_code == 404
    assert player.delete(f"/report-schedules/{sid}").status_code == 200
    assert player.delete(f"/report-schedules/{sid}").status_code == 404
    assert newplayer.post(f"/analyses/{jid}/email", json={}).status_code in (403, 404)
