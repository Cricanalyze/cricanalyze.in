import io, asyncio
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
from core import db, now, uid, get_object, put_object, BUCKET_PREFIX
import report_view

PDF_VERSION = "4.0"
HERO = 190
LOGO = Path(__file__).parent / "assets" / "logo_sm.png"
NAVY, TEAL, EMERALD, INK, MUTED, LINE, SOFT = (colors.HexColor(c) for c in ("#0B132B", "#00A6C4", "#10B981", "#1C2541", "#5B6477", "#D6DCE5", "#F2F6FA"))
W, H = A4
M = 36
CW = W - 2 * M
ST = {k: ParagraphStyle(k, fontName=f, fontSize=s, leading=s * 1.35, textColor=c, spaceAfter=a)
      for k, f, s, c, a in [("body", "Helvetica", 9.5, INK, 4), ("small", "Helvetica", 8, MUTED, 2), ("h2", "Helvetica-Bold", 13, NAVY, 6),
                            ("h3", "Helvetica-Bold", 10.5, NAVY, 3), ("cell", "Helvetica", 8.5, INK, 0), ("cellb", "Helvetica-Bold", 8.5, NAVY, 0),
                            ("th", "Helvetica-Bold", 8.5, colors.white, 0)]}


def t(s):
    return escape(str(s if s is not None else "")).replace("≥", "&gt;=").replace("≤", "&lt;=").replace("–", "-")


def P(s, st="body"):
    return Paragraph(t(s) if st != "raw" else s, ST[st if st != "raw" else "body"])


def grid_table(rows, widths, header=True):
    tb = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 4),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    style += [("BACKGROUND", (0, i), (-1, i), SOFT) for i in range(2 if header else 1, len(rows), 2)]
    tb.setStyle(TableStyle(style))
    return tb


def fit_image(blob, max_w, max_h):
    ir = ImageReader(io.BytesIO(blob))
    iw, ih = ir.getSize()
    s = min(max_w / iw, max_h / ih)
    return Image(io.BytesIO(blob), width=iw * s, height=ih * s)


def _arc(c, cx, cy, r, frac, col, width):
    c.setLineCap(1)
    c.setLineWidth(width)
    c.setStrokeColor(colors.Color(1, 1, 1, alpha=0.15))
    c.circle(cx, cy, r, stroke=1, fill=0)
    if frac > 0:
        c.setStrokeColor(col)
        pth = c.beginPath()
        pth.arc(cx - r, cy - r, cx + r, cy + r, 90, -360 * min(frac, 0.999))
        c.drawPath(pth, stroke=1, fill=0)


def _chip(c, x, y, text, bg, fg=colors.white, size=7.5):
    w = c.stringWidth(text, "Helvetica-Bold", size) + 14
    c.setFillColor(bg)
    c.roundRect(x, y, w, size + 8, (size + 8) / 2, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", size)
    c.drawString(x + 7, y + 4.6, text)
    return x + w + 6


def _page(title, rep_id, generated, v):
    h = v["header"]
    sc = v["score"]

    def draw(c, doc):
        c.saveState()
        first = doc.page == 1
        hh = HERO if first else 34
        c.setFillColor(NAVY)
        c.rect(0, H - hh, W, hh, fill=1, stroke=0)
        if first:
            c.setFillColor(colors.Color(0, 0.65, 0.77, alpha=0.18))
            c.circle(W - 70, H - 40, 150, fill=1, stroke=0)
            c.setFillColor(colors.Color(0.06, 0.73, 0.5, alpha=0.12))
            c.circle(W - 210, H - hh + 10, 90, fill=1, stroke=0)
        if LOGO.exists():
            ir = ImageReader(str(LOGO))
            iw, ih = ir.getSize()
            lh = 34 if first else 24
            lw = iw * lh / ih
            ly = H - 14 - lh if first else H - hh / 2 - lh / 2
            c.setFillColor(colors.white)
            c.roundRect(M - 4, ly - 2, lw + 8, lh + 4, 5, fill=1, stroke=0)
            c.drawImage(ir, M, ly, width=lw, height=lh, mask="auto")
        if first:
            c.setFillColor(TEAL)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(M, H - 78, title.upper())
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 26)
            c.drawString(M, H - 108, (h["player"] or "Player")[:28])
            x = M
            for txt, bg in [(h["analysis_type"] + (f" - {h['shot_type']}" if h.get("shot_type") else ""), EMERALD), (", ".join(h["angles"]) or "-", colors.HexColor("#1F3A5F")),
                            ("Video: " + h["video_quality"], colors.HexColor("#1F3A5F")), (h["date"], colors.HexColor("#1F3A5F"))]:
                x = _chip(c, x, H - 136, t(txt), bg)
            c.setFillColor(colors.HexColor("#A9B4C7"))
            c.setFont("Helvetica", 8)
            c.drawString(M, H - 158, f"Report {rep_id[:8].upper()}  -  2D body tracking + AI coaching  -  cricanalyze.in")
            cx, cy, r = W - M - 58, H - hh / 2 - 4, 46
            val = sc.get("value")
            _arc(c, cx, cy, r, (val or 0) / 100, EMERALD if sc.get("status") == "complete" else colors.HexColor("#F59E0B"), 9)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 30 if val is not None else 12)
            c.drawCentredString(cx, cy - 4, str(val) if val is not None else "N/A")
            c.setFont("Helvetica", 7.5)
            c.setFillColor(colors.HexColor("#A9B4C7"))
            c.drawCentredString(cx, cy - 18, "/ 100")
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(cx, cy - r - 18, "TECHNIQUE SCORE")
        else:
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(W - M, H - hh / 2 - 3, f"{title}  -  {h['player'] or ''}")
        c.setFillColor(TEAL)
        c.rect(0, H - hh - 3, W * 0.62, 3, fill=1, stroke=0)
        c.setFillColor(EMERALD)
        c.rect(W * 0.62, H - hh - 3, W * 0.38, 3, fill=1, stroke=0)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.setLineCap(0)
        c.line(M, 30, W - M, 30)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(MUTED)
        c.drawString(M, 18, f"CricAnalyze - Buddy Innovations and Technologies Pvt Ltd - cricanalyze.in   |   Generated {generated}")
        c.drawRightString(W - M, 18, f"Report {rep_id[:8].upper()} - v{PDF_VERSION} - Page {doc.page}")
        c.restoreState()
    return draw


async def _blob(asset_id):
    a = await db.media_assets.find_one({"id": asset_id}) if asset_id else None
    if not a:
        return None
    data, _ = await asyncio.to_thread(get_object, a["storage_path"])
    return data


def crop_blob(blob, box):
    if not blob or not box:
        return blob
    import cv2, numpy as np
    im = cv2.imdecode(np.frombuffer(blob, np.uint8), cv2.IMREAD_COLOR)
    h, w = im.shape[:2]
    x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    if x1 - x0 < 20 or y1 - y0 < 20:
        return blob
    return cv2.imencode(".jpg", im[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 88])[1].tobytes()


def box(flow, bg=SOFT, bar=TEAL, width=CW):
    tb = Table([[flow]], colWidths=[width])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 4, bar), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return tb


def cards(cells, n, gap=8, pad=9, bgs=None, bars=None):
    w = (CW - gap * (n - 1)) / n
    rows = [cells[i:i + n] + [""] * (n - len(cells[i:i + n])) for i in range(0, len(cells), n)]
    data = [[x for c in r for x in (c, "")][:-1] for r in rows]
    widths = [x for _ in range(n) for x in (w, gap)][:-1]
    tb = Table(data, colWidths=widths)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
          ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad)]
    for ri, r in enumerate(rows):
        for ci, cell in enumerate(r):
            if cell == "":
                continue
            k = ri * n + ci
            st.append(("BACKGROUND", (ci * 2, ri), (ci * 2, ri), (bgs[k % len(bgs)] if bgs else SOFT)))
            st.append(("LINEABOVE", (ci * 2, ri), (ci * 2, ri), 3, (bars[k % len(bars)] if bars else TEAL)))
        for ci in range(n - 1):
            st.append(("LEFTPADDING", (ci * 2 + 1, ri), (ci * 2 + 1, ri), 0))
            st.append(("RIGHTPADDING", (ci * 2 + 1, ri), (ci * 2 + 1, ri), 0))
    tb.setStyle(TableStyle(st + [("ROWBACKGROUNDS", (0, 0), (-1, -1), [None])]))
    return tb


def bullets(items, st="body", mark="•", col="#00A6C4"):
    return [Paragraph(f"<font color='{col}'><b>{mark}</b></font>&nbsp; {t(x)}", ST[st]) for x in items if x]


def ring(val, size=56, col=EMERALD, label=None, out_of=100):
    from reportlab.graphics.shapes import Drawing, Wedge, Circle, String
    d = Drawing(size, size)
    r = size / 2
    d.add(Circle(r, r, r, fillColor=LINE, strokeColor=None))
    if val:
        d.add(Wedge(r, r, r, 90 - 360 * min(val / out_of, 0.999), 90, fillColor=col, strokeColor=None))
    d.add(Circle(r, r, r - 6, fillColor=colors.white, strokeColor=None))
    d.add(String(r, r - 3 if not label else r - 1, str(val if val is not None else "-"), fontName="Helvetica-Bold", fontSize=size / 3.6, fillColor=NAVY, textAnchor="middle"))
    if label:
        d.add(String(r, r - size / 5, label, fontName="Helvetica", fontSize=size / 9, fillColor=MUTED, textAnchor="middle"))
    return d


def heading(title, kicker=None):
    k = f"<font size=7.5 color='#00A6C4'><b>{t(kicker.upper())}</b></font><br/>" if kicker else ""
    return Paragraph(k + t(title), ParagraphStyle("hx", parent=ST["h2"], fontSize=14, leading=17, spaceBefore=4, spaceAfter=6))


def section(title, *flow, kicker=None):
    return KeepTogether([Spacer(1, 10), heading(title, kicker), *flow[:1]]), *flow[1:]


def timeline_grid(a, blobs):
    tl = a["timeline"]
    n = max(1, len(tl))
    cw = CW / n - 6
    cells = []
    for i, p in enumerate(tl):
        blob = blobs.get(p.get("ball_overlay_asset_id")) or blobs.get(p.get("overlay_asset_id")) or blobs.get(p.get("frame_asset_id"))
        if blob and p["status"] != "unavailable":
            img = fit_image(crop_blob(blob, p.get("crop")), cw - 6, 118)
        else:
            img = Table([[P("Not assessed reliably" if p["status"] == "unavailable" else "Frame not available", "small")]], colWidths=[cw - 8], rowHeights=[70],
                        style=[("BACKGROUND", (0, 0), (-1, -1), LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")])
        meta = p["status_label"] + (f" - {p['t']}s" if p.get("t") is not None else "")
        col = "#10B981" if p["status"] == "detected" else "#B45309" if p["status"] == "estimated" else "#5B6477"
        cell = [Paragraph(f"<font color='#00A6C4'><b>{i + 1:02d}</b></font>  <b>{t(p['name'])}</b>", ST["cellb"]), Spacer(1, 4), img, Spacer(1, 4),
                Paragraph(f"<font color='{col}'><b>{t(meta)}</b></font>", ST["small"]), P(p["note"], "small")]
        cell += [P(m, "small") for m in p["metrics"]]
        if p.get("overlay_note"):
            cell.append(P(p["overlay_note"], "small"))
        cells.append(cell)
    return cards(cells, n, gap=6, pad=5, bars=[TEAL, EMERALD])


def metric_bar(m, w=150):
    from reportlab.graphics.shapes import Drawing, Rect, Circle
    d = Drawing(w, 14)
    d.add(Rect(0, 5, w, 5, rx=2.5, ry=2.5, fillColor=LINE, strokeColor=None))
    d.add(Rect(0, 5, max(5, w * m["position"]), 5, rx=2.5, ry=2.5, fillColor=TEAL, strokeColor=None))
    d.add(Circle(w * m["position"], 7.5, 5, fillColor=EMERALD, strokeColor=colors.white, strokeWidth=1.5))
    return d


def kpis(v):
    sc, vq = v["score"], v["video_quality"]
    measured = sum(len(a["metrics"]) for a in v["angles"])
    bio = [x for a in v["angles"] for x in (a.get("assessments") or []) if x["status"] == "measured"]
    big = lambda val, lab, note, col="#0B132B": [Paragraph(f"<font size=7 color='#5B6477'><b>{t(lab)}</b></font>", ST["small"]),
                                                  Paragraph(f"<font size=17 color='{col}'><b>{t(val)}</b></font>", ParagraphStyle("k", parent=ST["body"], leading=21)), P(note, "small")]
    return cards([big(f"{sc['value']}/100" if sc.get("value") is not None else "N/A", "TECHNIQUE SCORE", sc["label"], "#10B981"),
                  big(vq["rating"], "VIDEO QUALITY", "Footage only, not technique", "#00A6C4"),
                  big(str(measured), "MEASUREMENTS", f"{len(bio)} biomechanics checks"),
                  big(str(sum(1 for a in v["angles"] for p in a["timeline"] if p["status"] != "unavailable")), "KEY MOMENTS", "Frames analysed in the timeline")],
                 4, bars=[EMERALD, TEAL, NAVY, colors.HexColor("#F59E0B")])


def score_breakdown(sc):
    left = [Paragraph(f"<b>{t(sc['label'])}</b>", ST["h3"]), P(sc["text"], "small")]
    if sc.get("evidence"):
        left.append(P(f"Evidence: {sc['evidence']}", "small"))
    if sc.get("tip"):
        left.append(P(f"Filming tip: {sc['tip']}", "small"))
    comps = sc.get("components") or []
    rows = [[P(c["name"], "cell"), metric_bar({"position": c["score"] / 100}, 120), Paragraph(f"<b>{c['score']}</b>", ST["cellb"])] for c in comps]
    right = Table(rows, colWidths=[110, 128, 30], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]) if rows else P("", "small")
    return box(Table([[left, right]], colWidths=[CW - 290, 272], style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))


def assessment_card(x, blobs):
    img = fit_image(blobs[x["overlay_asset_id"]], 120, 92) if blobs.get(x.get("overlay_asset_id")) else P("No reference frame", "small")
    col = "#10B981" if x["status"] == "measured" else "#B45309" if x["status"] == "inconclusive" else "#5B6477"
    head = [Paragraph(f"<b>{t(x['name'])}</b>  <font size=7.5 color='{col}'><b>{t(x['status_label'].upper())}</b></font>", ST["h3"]), P(x["summary"] or x["reason"], "body")]
    det = [Paragraph(f"<font color='#5B6477'>{t(d['label'])}:</font> <b>{t(d['value'])}</b>", ST["small"]) for d in x["details"]]
    if x.get("ai_note"):
        det.append(P(f"AI visual note (foot direction): {x['ai_note']}", "small"))
    mid = head + det
    cols = [[img, mid]]
    widths = [128, CW - 128 - 20]
    if x.get("score") is not None:
        cols[0].append(ring(x["score"], 58, EMERALD if x["score"] >= 6.5 else colors.HexColor("#F59E0B"), "/10", 10))
        widths = [128, CW - 128 - 20 - 70, 70]
    tb = Table(cols, colWidths=widths)
    tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), SOFT), ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor(col)),
                            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
    return KeepTogether([tb, Spacer(1, 6)])


def build(rep, job, owner, blobs):
    v = rep["view"]
    buf = io.BytesIO()
    title = f"{v['header']['analysis_type']} Technique Report"
    generated = report_view.ist(now())
    doc = BaseDocTemplate(buf, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=HERO + 16, bottomMargin=44, title=title, author="CricAnalyze")
    draw = _page(title, rep["id"], generated, v)
    doc.addPageTemplates([PageTemplate(id="first", frames=[Frame(M, 44, CW, H - HERO - 16 - 44, id="f1")], onPage=draw, autoNextPageTemplate="later"),
                          PageTemplate(id="later", frames=[Frame(M, 44, CW, H - 50 - 44, id="f2")], onPage=draw)])
    s = [kpis(v), Spacer(1, 10)]
    tk = [[Paragraph(f"<font size=16 color='#00A6C4'><b>{i + 1}</b></font>", ST["body"]), P(x)] for i, x in enumerate(v["takeaways"])]
    s += section("Three key takeaways", cards([[Table([r], colWidths=[18, (CW - 16) / 3 - 40], style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)])] for r in tk], 3,
                                              bars=[TEAL, EMERALD, colors.HexColor("#F59E0B")]), kicker="At a glance")
    s += section("How your score is built", score_breakdown(v["score"]), P(f"Video quality: {v['video_quality']['rating']} - {v['video_quality']['text']} Video quality describes the footage, not the player's technique.", "small"), kicker="Score")
    c = v["coaching"]
    good = bullets(v["whats_working"], mark="+", col="#10B981") or [P("Nothing stood out clearly in this clip.", "small")]
    fix = [P(c["priority"])] if c.get("priority") else [P("No single priority identified.", "small")]
    s += section("Strengths and priority", cards([[Paragraph("<font color='#10B981'><b>WHAT'S WORKING</b></font>", ST["small"]), *good],
                                                    [Paragraph("<font color='#B45309'><b>PRIORITY TO IMPROVE</b></font>", ST["small"]), *fix]], 2,
                                                   bgs=[colors.HexColor("#ECFDF5"), colors.HexColor("#FFF7ED")], bars=[EMERALD, colors.HexColor("#F59E0B")]), kicker="Summary")
    for a in v["angles"]:
        if a["metrics"]:
            rows = [[Paragraph(x, ST["th"]) for x in ("Measurement", "Value", "Scale", "What it means")]]
            rows += [[P(m["name"] + (f" ({m['t']}s)" if m.get("t") is not None else ""), "cell"), Paragraph(f"<font size=10 color='#0B132B'><b>{t(m['display'])}</b></font>", ST["cell"]),
                      metric_bar(m, 110), P(m["interpretation"], "cell")] for m in a["metrics"]]
            tb = grid_table(rows, [130, 62, 122, CW - 314])
            tb.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0, colors.white), ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            s += section(f"Measurements - {a['angle']} camera", tb,
                         P("Values are measured from the video. Target ranges are not shown until coach-approved references are available.", "small"), kicker="Body tracking")
        if a["timeline"]:
            if a.get("analysed_window"):
                s.append(P(a["analysed_window"], "small"))
            s += section(f"Technique timeline - {a['angle']} camera", timeline_grid(a, blobs),
                         P("Frames are cropped around the player from the original video at the times shown. 'Approximate timing' frames are best estimates, not exact events.", "small"), kicker="Frame by frame")
        if a.get("ball"):
            s.append(box([P("Ball: " + a["ball"]["text"] + " " + " ".join(a["ball"]["notes"]), "small")], bar=colors.HexColor("#C1121F")))
        if a.get("assessments"):
            items = [assessment_card(x, blobs) for x in a["assessments"]]
            s += section(f"Biomechanics - {a['angle']} camera", *items,
                         P("Measured from the original video frames at their original timestamps (2D body tracking). These assessments are not part of the technique score. "
                           "Trunk lean is whole-trunk lean; lower-back bending and spinal curvature are not measured.", "small"), kicker="Deep dive")
        if not a["pose_available"]:
            s += section(f"{a['angle'].title()} camera", P("Body tracking wasn't available for this clip, so only the coach's visual notes are shown."))
    coach = [[Paragraph(f"<font color='{col}'><b>{lab}</b></font>", ST["small"]), P(c[k])] for k, lab, col in
             (("priority", "PRIORITY", "#B45309"), ("why", "WHY IT MATTERS", "#00A6C4"), ("how", "HOW TO PRACTISE", "#10B981")) if c.get(k)]
    if coach:
        s += section("Coaching feedback", cards(coach, len(coach), bars=[colors.HexColor("#F59E0B"), TEAL, EMERALD]), kicker="Your coach says")
        if c.get("measured_basis"):
            s.append(P("Based on measurements: " + "; ".join(c["measured_basis"]) + ". Coaching text is an AI interpretation of the video and these measurements.", "small"))
    if v["drills"]:
        dc = [[Paragraph(f"<font color='#00A6C4'><b>DRILL {i + 1}</b></font>" + (f"<font color='#5B6477'>  -  {t(d['area'])}</font>" if d.get("area") else ""), ST["small"]),
               Paragraph(f"<b>{t(d['name'])}</b>", ST["h3"]), P(d.get("objective") or "", "small"), P(d.get("instructions") or ""),
               Paragraph(f"<font color='#10B981'><b>Dose: {t(d.get('dosage') or '-')}</b></font>", ST["small"])] + ([P(f"Avoid: {d['mistakes']}", "small")] if d.get("mistakes") else [])
              for i, d in enumerate(v["drills"])]
        s += section("Personalised drills", cards(dc, 2, bars=[EMERALD, TEAL]), kicker="Practise this")
    if v.get("practice_plan"):
        pc = [[Paragraph(f"<font color='#00A6C4'><b>{t((p.get('day') or '')[:3].upper())}</b></font>", ST["small"]), P(p.get("focus"), "small"),
               Paragraph(f"<b>{t(p.get('duration_min'))} min</b>", ST["small"])] for p in v["practice_plan"]]
        s += section("Weekly practice plan", cards(pc, min(7, len(pc)), gap=4, pad=5), kicker="Your week")
    pr = v.get("progress")
    if pr:
        rows = [[Paragraph(x, ST["th"]) for x in ("Measurement", f"Previous ({pr['previous_date']})", "Latest", "Change")]]
        rows += [[P(m["name"], "cell"), P(m["before_display"], "cell"), P(m["after_display"], "cell"), P(m["change_display"], "cell")] for m in pr["metrics"]]
        sb, sa = pr["score_before"], pr["score_after"]
        rows.append([P("Overall score", "cell"), P(f"{sb['value'] if sb['value'] is not None else '-'} ({sb['status']})", "cell"),
                     P(f"{sa['value'] if sa['value'] is not None else '-'} ({sa['status']})", "cell"), P("", "cell")])
        s += section("Progress comparison", grid_table(rows, [150, 130, 130, CW - 410]), P(pr["explanation"], "small"), kicker="Then vs now")
    s += section("Your action plan", box([Paragraph(f"<font color='#10B981'><b>[ ]</b></font>&nbsp; {t(x)}", ST["body"]) for x in v["action_plan"]], bg=colors.HexColor("#ECFDF5"), bar=EMERALD), kicker="Next steps")
    s += section("Filming tips for your next clip", *bullets(v["filming_tips"]), kicker="Better video, better report")
    s += section("About this report", P(v["score_method"], "small"), P(v["video_quality"]["method"], "small"), P(v["limitations"], "small"),
                 P("AI-assisted coaching report. Not a medical assessment, does not guarantee injury prevention or performance, and is not an official selection credential.", "small"))
    doc.build(s)
    return buf.getvalue()


async def get_or_build(rep, job, owner):
    cached = await db.analysis_reports.find_one({"id": rep["id"]}, {"pdf": 1})
    pc = (cached or {}).get("pdf") or {}
    if pc.get("version") == PDF_VERSION and pc.get("level") == job.get("report_level"):
        a = await db.media_assets.find_one({"id": pc["asset_id"]})
        if a:
            return (await asyncio.to_thread(get_object, a["storage_path"]))[0]
    blobs = {}
    for a in rep["view"]["angles"]:
        for p in a["timeline"] + (a.get("assessments") or []):
            for k in ("overlay_asset_id", "frame_asset_id", "ball_overlay_asset_id"):
                if p.get(k):
                    blobs[p[k]] = await _blob(p[k])
    pdf = await asyncio.to_thread(build, rep, job, owner, blobs)
    if pc.get("asset_id"):
        await db.media_assets.update_one({"id": pc["asset_id"]}, {"$set": {"is_deleted": True}})
    aid = uid()
    res = await asyncio.to_thread(put_object, f"{BUCKET_PREFIX}/reports/{rep['user_id']}/{aid}.pdf", pdf, "application/pdf")
    await db.media_assets.insert_one({"id": aid, "user_id": rep["user_id"], "kind": "report_pdf", "storage_path": res["path"], "content_type": "application/pdf",
                                      "is_deleted": False, "created_at": now()})
    await db.analysis_reports.update_one({"id": rep["id"]}, {"$set": {"pdf": {"asset_id": aid, "version": PDF_VERSION, "level": job.get("report_level"), "at": now()}}})
    return pdf
