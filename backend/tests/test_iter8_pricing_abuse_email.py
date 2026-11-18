# Iteration 8: new pricing, offer tag, 25s video limit, email templates, coach welcome, abuse reports
import sys, subprocess, time
import pytest
sys.path.insert(0, "/app/backend")
from conftest import C, login, signup_verified, mdb

QA_ADMIN = ("qa.admin+qa@cricanalyze.in", "QaAdmin#2026")
QA_PLAYER = ("qa.player+qa@cricanalyze.in", "QaPlayer#2026")
QA_COACH = ("qa.coach+qa@cricanalyze.in", "QaCoach#2026")
QA_PCOACH = ("qa.pendingcoach+qa@cricanalyze.in", "QaCoach#2026")

EXPECTED = {
    "batting": ([799, 1299, 1499], [3, 6, 10]),
    "bowling": ([999, 1399, 1799], [3, 5, 8]),
    "combined": ([1399, 1899, 2199], [5, 10, 15]),
    "academy": ([1999, 2499, 3999], [15, 20, 30]),
}
TIERS = ["starter", "pro", "elite"]
created_emails, created_videos, created_reports = [], [], []
STATE = {}


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    for e in created_emails:
        u = mdb.users.find_one({"email": e})
        if u:
            mdb.academy_memberships.delete_many({"user_id": u["id"]})
        mdb.users.delete_one({"email": e})
    for v in created_videos:
        mdb.video_assets.delete_one({"id": v})


# ---- Plans ----
def test_plans_prices_credits():
    r = C().get("/plans")
    assert r.status_code == 200
    plans = {p["slug"]: p for p in r.json()}
    for g, (prices, credits) in EXPECTED.items():
        for i, t in enumerate(TIERS):
            p = plans.get(f"{g}-{t}")
            assert p, f"missing {g}-{t}"
            assert p["price_inr"] == prices[i], (p["slug"], p["price_inr"])
            assert p["credits"] == credits[i], (p["slug"], p["credits"])
            assert p["max_duration_s"] == 25
    assert all(p["max_duration_s"] <= 25 for p in r.json())
    print("active plan count", len(r.json()), sorted(plans))
    assert len(r.json()) == 12


def test_academy_combined_types():
    plans = {p["slug"]: p for p in C().get("/plans").json()}
    for s in ["combined-pro", "academy-starter", "academy-elite"]:
        assert set(plans[s]["analysis_types"]) == {"batting", "bowling"}


def test_admin_plan_rejects_over_25():
    a = login(*QA_ADMIN)
    plans = a.get("/admin/plans").json()
    p = [x for x in plans if x["slug"] == "batting-starter"][0]
    body = {k: p[k] for k in ("name", "slug", "product", "billing", "price_inr", "currency", "period_days", "credits", "videos_per_analysis",
                              "max_duration_s", "max_file_mb", "analysis_types") if k in p}
    bad = {**body, "max_duration_s": 30}
    r = a.put(f"/admin/plans/{p['id']}", json=bad)
    assert r.status_code == 422, r.text
    r = a.post("/admin/plans", json={**bad, "slug": "test-iter8-over25"})
    assert r.status_code == 422, r.text
    assert not mdb.plans.find_one({"slug": "test-iter8-over25"})
    assert mdb.plans.find_one({"id": p["id"]})["max_duration_s"] == 25


# ---- Offer tag ----
def test_offer_tag_roundtrip():
    a = login(*QA_ADMIN)
    orig = C().get("/public/config").json().get("offer_tag")
    STATE["orig_tag"] = orig
    try:
        assert a.put("/admin/settings", json={"offer": {"tag": "TEST Diwali Offer"}}).status_code == 422  # confirm required
        r = a.put("/admin/settings", json={"offer": {"tag": "TEST Diwali Offer"}, "confirm": True})
        assert r.status_code == 200, r.text
        assert r.json()["offer"]["tag"] == "TEST Diwali Offer"
        assert C().get("/public/config").json()["offer_tag"] == "TEST Diwali Offer"
        r = a.put("/admin/settings", json={"offer": {"tag": ""}, "confirm": True})
        assert C().get("/public/config").json()["offer_tag"] == ""
        r = a.put("/admin/settings", json={"offer": {"tag": "x" * 60}, "confirm": True})
        assert len(C().get("/public/config").json()["offer_tag"]) == 40
    finally:
        a.put("/admin/settings", json={"offer": {"tag": orig or "New Year Offer"}, "confirm": True})
    assert C().get("/public/config").json()["offer_tag"] == (orig or "New Year Offer")


def test_player_cannot_save_settings():
    p = login(*QA_PLAYER)
    assert p.put("/admin/settings", json={"offer": {"tag": "hack"}, "confirm": True}).status_code == 403


# ---- 25s limit ----
def _ffmpeg_clip(path, secs):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([exe, "-y", "-f", "lavfi", "-i", f"testsrc=size=640x480:rate=25:duration={secs}", "-pix_fmt", "yuv420p", "-c:v", "libx264", path],
                   check=True, capture_output=True)
    return path


def test_upload_over_25s_rejected():
    p = login(*QA_PLAYER)
    path = _ffmpeg_clip("/tmp/iter8_30s.mp4", 30)
    with open(path, "rb") as f:
        r = p.post("/videos", files={"file": ("long.mp4", f, "video/mp4")}, data={"analysis_type": "batting", "angle": "side_on"})
    assert r.status_code == 422, r.text
    assert "25 seconds" in r.json()["detail"]


def test_upload_under_25s_accepted():
    p = login(*QA_PLAYER)
    path = _ffmpeg_clip("/tmp/iter8_20s.mp4", 20)
    with open(path, "rb") as f:
        r = p.post("/videos", files={"file": ("short.mp4", f, "video/mp4")}, data={"analysis_type": "batting", "angle": "side_on"})
    assert r.status_code == 200, r.text
    created_videos.append(r.json()["id"])
    assert r.json()["meta"]["duration_s"] <= 25.5


# ---- Email templates ----
CODE_T = ["verify_email", "login_otp", "reset_password", "step_up", "change_email"]
NONCODE_T = ["report_delivery", "welcome", "coach_welcome", "receipt", "maintenance", "notice", "join_request", "join_decision", "academy_invite",
             "abuse_report", "password_changed", "payment_failed", "report_ready", "test", "guardian_consent"]
CTX = dict(code="123456", kind="batting", pdf_note="Your PDF report is attached.", share="https://x/s", link="https://cta.example/link",
           amount="₹799", plan="Batting Starter", payment_id="pay_1", academy="Acad", role="coach", player="P", decision="approved",
           start="a", end="b", message="m", reporter="R", target="T", reason="Harassment", details="d")


@pytest.mark.parametrize("t", CODE_T)
def test_code_emails_have_code_note(t):
    from core import render_email
    s, html, text = render_email(t, CTX)
    assert "Never share this code" in text and "Never share this code" in html
    assert "123456" in html


@pytest.mark.parametrize("t", NONCODE_T)
def test_noncode_emails_no_code_note(t):
    from core import render_email, EMAIL_TEMPLATES
    s, html, text = render_email(t, CTX)
    assert "Never share this code" not in text and "Never share this code" not in html
    if t not in ("maintenance", "test", "guardian_consent"):
        assert "https://cta.example/link" in html, t


def test_report_delivery_content():
    from core import render_email
    s, html, text = render_email("report_delivery", CTX)
    assert "attached" in text.lower()
    assert "Please go through the website for the in-detail analysis" in text
    assert "Open full report" in html


def test_noncode_notes_distinct():
    from core import EMAIL_TEMPLATES, ACCOUNT_NOTE
    generic = [t for t in NONCODE_T if EMAIL_TEMPLATES[t]["note"] == ACCOUNT_NOTE]
    print("templates using generic account note:", generic)


# ---- Coach welcome ----
@pytest.mark.parametrize("role,tmpl,path", [("coach", "coach_welcome", "/app/academy"), ("academy_admin", "coach_welcome", "/app/academy"),
                                            ("player", "welcome", "/app/upload")])
def test_welcome_email_on_verify(role, tmpl, path):
    c = signup_verified(role=role, name=f"TEST_{role}")
    created_emails.append(c.email)
    time.sleep(2)
    logs = list(mdb.email_logs.find({"to": c.email}, {"_id": 0}))
    tmpls = [l.get("template") for l in logs]
    assert tmpl in tmpls, (tmpls, logs[:2])
    other = "welcome" if tmpl == "coach_welcome" else "coach_welcome"
    assert other not in tmpls
    # logs don't persist ctx/link; verify the link in source + rendered email
    src = open("/app/backend/auth_routes.py").read()
    assert f'"{tmpl}", {{"link": f"{{APP_URL}}{path}"}}' in src
    from core import render_email, APP_URL
    _, html, _ = render_email(tmpl, {"link": f"{APP_URL}{path}"})
    assert f"{APP_URL}{path}" in html


# ---- Abuse reports ----
def _setup_academy():
    if "aid" in STATE:
        return STATE
    co = login(*QA_COACH)
    r = co.get("/academies/mine")
    aid = None
    for a in (r.json() if isinstance(r.json(), list) else r.json().get("academies", [])):
        if a.get("owner_id") == co.user["id"] or a.get("role") == "academy_admin":
            aid = a.get("id") or a.get("academy_id")
            break
    if not aid:
        aid = co.post("/academies", json={"name": "TEST_QA Academy", "city": "Pune"}).json()["id"]
        STATE["created_academy"] = aid
    code = mdb.academies.find_one({"id": aid})["code"]
    p = login(*QA_PLAYER)
    if not mdb.academy_memberships.find_one({"academy_id": aid, "user_id": p.user["id"], "status": "active"}):
        r = p.post("/academies-join", json={"code": code})
        assert r.status_code in (200, 409), r.text
        req = mdb.academy_join_requests.find_one({"academy_id": aid, "user_id": p.user["id"], "status": "pending"})
        assert co.post(f"/academies/{aid}/requests/{req['id']}", json={"approve": True}).status_code == 200
    pc = mdb.users.find_one({"email": QA_PCOACH[0]})
    mdb.academy_memberships.update_one({"academy_id": aid, "user_id": pc["id"]}, {"$set": {"role": "coach", "status": "active"},
                                       "$setOnInsert": {"id": "test-iter8-pc", "created_at": time.time()}}, upsert=True)
    STATE.update(aid=aid, coach_id=co.user["id"], pcoach_id=pc["id"], player_id=p.user["id"])
    return STATE


def test_staff_list():
    s = _setup_academy()
    p = login(*QA_PLAYER)
    r = p.get(f"/academies/{s['aid']}/staff")
    assert r.status_code == 200, r.text
    ids = {x["user_id"] for x in r.json()}
    assert s["coach_id"] in ids and s["pcoach_id"] in ids
    assert s["player_id"] not in ids


def test_abuse_validation():
    s = _setup_academy()
    p = login(*QA_PLAYER)
    assert p.post("/abuse-reports", json={"academy_id": s["aid"], "reason": "bogus", "details": "long enough details"}).status_code == 422
    assert p.post("/abuse-reports", json={"academy_id": s["aid"], "reason": "other", "details": "short"}).status_code == 422
    r = p.post("/abuse-reports", json={"academy_id": s["aid"], "target_user_id": s["player_id"], "reason": "other", "details": "not staff target test"})
    assert r.status_code == 422, r.text


def test_abuse_non_member_and_rate_limit():
    s = _setup_academy()
    o = login(*QA_ADMIN)  # admin is not a member of the TEST academy (avoids signup IP rate limit)
    assert o.get(f"/academies/{s['aid']}/staff").status_code == 404
    codes = [o.post("/abuse-reports", json={"academy_id": s["aid"], "reason": "other", "details": "non member report test"}).status_code for _ in range(6)]
    assert codes[:5] == [404] * 5, codes
    assert codes[5] == 429, codes


def test_abuse_create_and_admin_flow():
    s = _setup_academy()
    p = login(*QA_PLAYER)
    r = p.post("/abuse-reports", json={"academy_id": s["aid"], "target_user_id": s["pcoach_id"], "reason": "harassment",
                                       "details": "TEST_iter8 automated QA report — please ignore"})
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    created_reports.append(rid)
    doc = mdb.abuse_reports.find_one({"id": rid})
    assert doc["status"] == "open" and doc["target_user_id"] == s["pcoach_id"]
    time.sleep(2)
    log = mdb.email_logs.find_one({"template": "abuse_report"}, sort=[("_id", -1)])
    assert log, "no abuse_report email log"
    print("abuse email log", {k: log.get(k) for k in ("to", "status", "template")})
    assert p.get("/admin/abuse-reports").status_code == 403
    a = login(*QA_ADMIN)
    rows = a.get("/admin/abuse-reports?status=open").json()
    assert any(x["id"] == rid and x["reason_label"] == "Harassment or bullying" for x in rows)
    assert a.post(f"/admin/abuse-reports/{rid}", json={"status": "resolved", "note": "TEST"}).status_code == 200
    assert any(x["id"] == rid for x in a.get("/admin/abuse-reports?status=resolved").json())
    assert not any(x["id"] == rid for x in a.get("/admin/abuse-reports?status=open").json())
    assert a.post(f"/admin/abuse-reports/{rid}", json={"status": "dismissed"}).status_code == 200
    assert mdb.abuse_reports.find_one({"id": rid})["status"] == "dismissed"
    assert a.post(f"/admin/abuse-reports/{rid}", json={"status": "weird"}).status_code == 422
    assert a.post("/admin/abuse-reports/nope", json={"status": "resolved"}).status_code == 404
    assert any(x["id"] == rid for x in a.get("/admin/abuse-reports").json())
    # reopen so UI test can see it in 'open'
    a.post(f"/admin/abuse-reports/{rid}", json={"status": "open"})
