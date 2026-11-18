# Report PDF v4.2: red "go through the website" note + app link on page 1, footer not overlapping body text
import fitz, pytest
from conftest import C

JOB = "18864366759e4e2c8da2978c8757105c"  # qa.player completed batting analysis


@pytest.fixture(scope="module")
def pdf():
    c = C()
    r = c.post("/auth/login", json={"email": "qa.player+qa@cricanalyze.in", "password": "QaPlayer#2026"})
    if r.status_code != 200:
        pytest.skip("login failed")
    r = c.get(f"/analyses/{JOB}/pdf")
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"].startswith("application/pdf")
    open("/tmp/iter6_report.pdf", "wb").write(r.content)
    return fitz.open(stream=r.content, filetype="pdf")


def test_red_note_page1(pdf):
    p = pdf[0]
    txt = p.get_text()
    assert "Please go through the website for the in-detail analysis" in txt
    assert f"/app/analyses/{JOB}" in txt
    reds = [s for b in p.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]
            if "Please go through" in s["text"]]
    assert reds and reds[0]["color"] == 0xDC2626, [hex(s["color"]) for s in reds]
    links = [l.get("uri", "") for l in p.get_links()]
    assert any(f"/app/analyses/{JOB}" in u for u in links), links


def test_footer_no_overlap(pdf):
    bad = []
    for i, p in enumerate(pdf):
        H = p.rect.height
        blocks = [b for b in p.get_text("blocks") if b[4].strip()]
        foot = [b for b in blocks if b[1] > H - 45]
        body = [b for b in blocks if b[1] <= H - 45]
        for f in foot:
            for b in body:
                if b[3] > f[1] + 1 and not (b[2] < f[0] or b[0] > f[2]):
                    bad.append((i + 1, b[4][:40], f[4][:40]))
    print("pages:", len(pdf), "overlaps:", bad)
    assert not bad
