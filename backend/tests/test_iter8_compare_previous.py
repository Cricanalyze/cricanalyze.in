# Iteration 8: "Compare with my last report?" — compare_previous on analysis jobs drives report.view.progress / compare_note
import sys
import pytest
sys.path.insert(0, "/app/backend")
from conftest import login, mdb

QA_PLAYER = ("qa.player+qa@cricanalyze.in", "QaPlayer#2026")
FIRST, LAST = "f7c71b4026fc43faa753477bdeb7647c", "18864366759e4e2c8da2978c8757105c"


@pytest.fixture(scope="module", autouse=True)
def restore():
    orig = {j: mdb.analysis_jobs.find_one({"id": j}) for j in (FIRST, LAST)}
    if not all(orig.values()):
        pytest.skip("qa.player completed batting jobs not found")
    yield
    for j, d in orig.items():
        mdb.analysis_jobs.update_one({"id": j}, {"$set": {"report_level": d.get("report_level", "basic")}})
        if "compare_previous" in d:
            mdb.analysis_jobs.update_one({"id": j}, {"$set": {"compare_previous": d["compare_previous"]}})
        else:
            mdb.analysis_jobs.update_one({"id": j}, {"$unset": {"compare_previous": ""}})


_C = {}


def _c():
    if "c" not in _C:
        _C["c"] = login(*QA_PLAYER)
    return _C["c"]


def _view(c, jid, cp, level=None):
    if level:
        mdb.analysis_jobs.update_one({"id": jid}, {"$set": {"report_level": level}})
    if cp is None:
        mdb.analysis_jobs.update_one({"id": jid}, {"$unset": {"compare_previous": ""}})
    else:
        mdb.analysis_jobs.update_one({"id": jid}, {"$set": {"compare_previous": cp}})
    r = c.get(f"/analyses/{jid}")
    assert r.status_code == 200, r.text
    return r.json()["report"]["view"]


def test_entitlement_has_comparisons():
    c = _c()
    r = c.get("/me/entitlements") if c.get("/me/entitlements").status_code == 200 else None
    print("entitlements", r.json() if r is not None else "n/a")


def test_compare_true_with_previous_has_progress():
    v = _view(_c(), LAST, True, level="advanced")
    print("progress", str(v.get("progress"))[:300])
    assert v.get("progress"), "expected progress history"
    assert not v.get("compare_note")


def test_compare_true_basic_level_with_previous_has_progress():
    # BUG (iter8): basic report_level nulls metric values before history_for -> no rows -> misleading 'no earlier report' note
    v = _view(_c(), LAST, True, level="basic")
    assert v.get("progress") or "no earlier" not in (v.get("compare_note") or ""), v.get("compare_note")


def test_compare_true_without_previous_has_note():
    v = _view(_c(), FIRST, True)
    assert not v.get("progress")
    assert v.get("compare_note") and "baseline" in v["compare_note"]


def test_compare_false_neither():
    c = _c()
    for j in (FIRST, LAST):
        v = _view(c, j, False)
        assert not v.get("progress") and not v.get("compare_note"), j


def test_legacy_job_without_field():
    # legacy basic-level jobs: old behaviour = no comparison
    c = _c()
    v = _view(c, LAST, None)
    print("legacy last: progress", bool(v.get("progress")), "note", v.get("compare_note"))
    assert not v.get("compare_note")
