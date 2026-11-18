"""Batting biomechanics from 2D pose: weight transfer, head balance, base width and stride. Not part of the technique score."""
import math
import pose_pipeline as pp
from bowling_assess import Pk, _mid, _at, _mark, render

METHOD = {
    "bat_weight_transfer": "Hip centre position between the two ankles at setup, impact and follow-through (0% = over the back foot, 100% = over the front foot). "
                           "Front foot = the ankle that moved most horizontally between setup and impact (the stride foot). 2D, side-on camera.",
    "bat_head_balance": "Horizontal distance from the head (nose) to the middle of the two ankles at impact, in torso lengths. Smaller means the head is over the base.",
    "bat_base_stride": "Ankle-to-ankle distance in torso lengths at setup and at impact; stride = change in the stride foot's position between setup and impact.",
}
NAMES = {"bat_weight_transfer": "Weight transfer (back → front foot)", "bat_head_balance": "Head balance over the base at impact",
         "bat_base_stride": "Base width and stride"}


def _base(key, phase=None):
    return {"key": key, "name": NAMES[key], "status": "unavailable", "phase": phase, "summary": "", "details": [], "reason": "", "method": METHOD[key], "marks": []}


def _frame(ph, k):
    return (ph.get(k) or {}).get("frame")


def _feet(setup, imp):
    a = {s: (Pk(setup, f"{s}_ank"), Pk(imp, f"{s}_ank")) for s in ("l", "r")}
    if not all(x and y for x, y in a.values()):
        return None
    move = {s: abs(a[s][1][0] - a[s][0][0]) for s in a}
    front = max(move, key=move.get)
    return front, ("r" if front == "l" else "l"), move[front]


def _share(f, front, back):
    fa, ba, hm = Pk(f, f"{front}_ank"), Pk(f, f"{back}_ank"), _mid(f, "l_hip", "r_hip")
    if not (fa and ba and hm) or abs(fa[0] - ba[0]) < 1:
        return None, None
    return max(0, min(100, round(100 * (hm[0] - ba[0]) / (fa[0] - ba[0])))), (fa, ba, hm)


def weight_transfer(ph, angle, feet):
    d = _base("bat_weight_transfer", "impact")
    if angle != "side_on":
        d["reason"] = "Weight transfer needs a side-on camera."
        return d
    if not feet:
        d["reason"] = "Both ankles weren't clearly visible at setup and impact."
        return d
    front, back, _ = feet
    rows, best = [], None
    for k, label in (("setup", "Setup"), ("impact", "Impact (approx.)"), ("follow_through", "Follow-through")):
        f = _frame(ph, k)
        v, pts = _share(f, front, back) if f else (None, None)
        rows.append({"label": label, "value": f"{v}% towards the front foot · {f['t']:.3f} s" if v is not None else "Not available"})
        if v is not None:
            if k == "impact" or best is None:
                best = (f, v, pts)
            d.setdefault("_vals", {})[k] = v
    if not best:
        d["reason"] = "Hips or ankles weren't clear at the key moments."
        return d
    f, v, (fa, ba, hm) = best
    vals = d.pop("_vals")
    _at(d, f)
    d["status"] = "measured"
    shift = vals.get("impact", v) - vals["setup"] if "setup" in vals and "impact" in vals else None
    lean = "mostly on the front foot" if v >= 65 else "mostly on the back foot" if v <= 35 else "fairly central"
    d["summary"] = f"At impact the weight was {lean} ({v}% towards the front foot)" + (f", a shift of {shift:+d} points from setup." if shift is not None else ".")
    d["details"] = rows + [{"label": "Front (stride) foot", "value": "left" if front == "l" else "right"}]
    lines = [(ba[:2], fa[:2], (220, 220, 220)), ((hm[0], hm[1]), (hm[0], max(fa[1], ba[1])), (11, 158, 245))]
    d["marks"].append(_mark(f, f"Weight {v}% front", [(ba[:2], fa[:2], "#E2E8F0"), ((hm[0], hm[1]), (hm[0], max(fa[1], ba[1])), "#F59E0B")]))
    d["_draw"] = (f, lines)
    return d


def head_balance(ph, angle):
    d = _base("bat_head_balance", "impact")
    f = _frame(ph, "impact")
    if angle not in ("side_on", "front_on"):
        d["reason"] = "Needs a side-on or front-on camera."
        return d
    if not f:
        d["reason"] = "The impact moment wasn't identified."
        return d
    n, am, t = Pk(f, "nose"), _mid(f, "l_ank", "r_ank"), pp.torso(f)
    if not (n and am and t):
        d["reason"] = "Head or feet weren't clearly visible at impact."
        return d
    _at(d, f)
    off = abs(n[0] - am[0]) / t
    d["status"] = "measured"
    d["summary"] = "Head well over the base at impact." if off < 0.25 else "Head slightly outside the base at impact." if off < 0.5 else "Head clearly outside the base at impact — balance may be affected."
    d["details"] = [{"label": "Head offset from base centre", "value": f"{off:.2f} torso lengths"}, {"label": "Measured at", "value": f"impact (approx.), {f['t']:.3f} s"}]
    d["marks"].append(_mark(f, f"Head offset {off:.2f}", [((n[0], n[1]), (n[0], am[1]), "#F59E0B"), ((n[0], am[1]), (am[0], am[1]), "#E2E8F0")]))
    d["_draw"] = (f, [((n[0], n[1]), (n[0], am[1]), (11, 158, 245)), ((n[0], am[1]), (am[0], am[1]), (220, 220, 220))])
    return d


def base_stride(ph, feet):
    d = _base("bat_base_stride", "impact")
    s, f = _frame(ph, "setup"), _frame(ph, "impact")
    if not (s and f and feet):
        d["reason"] = "Both ankles weren't clearly visible at setup and impact."
        return d
    widths = []
    for g in (s, f):
        la, ra, t = Pk(g, "l_ank"), Pk(g, "r_ank"), pp.torso(g)
        widths.append(math.dist(la[:2], ra[:2]) / t if la and ra and t else None)
    if None in widths:
        d["reason"] = "Feet or torso unclear."
        return d
    _at(d, f)
    t = pp.torso(f)
    d["status"] = "measured"
    d["summary"] = f"Base {widths[0]:.2f} → {widths[1]:.2f} torso lengths from setup to impact; stride foot moved {feet[2] / t:.2f} torso lengths."
    d["details"] = [{"label": "Base at setup", "value": f"{widths[0]:.2f} torso lengths"}, {"label": "Base at impact", "value": f"{widths[1]:.2f} torso lengths"},
                    {"label": "Stride length", "value": f"{feet[2] / t:.2f} torso lengths"}]
    la, ra = Pk(f, "l_ank"), Pk(f, "r_ank")
    d["marks"].append(_mark(f, "Base", [(la[:2], ra[:2], "#F59E0B")]))
    d["_draw"] = (f, [(la[:2], ra[:2], (11, 158, 245))])
    return d


def assess(ph, angle):
    s, f = _frame(ph, "setup"), _frame(ph, "impact")
    feet = _feet(s, f) if s and f else None
    out = [weight_transfer(ph, angle, feet), head_balance(ph, angle), base_stride(ph, feet)]
    imgs = []
    import cv2
    for d in out:
        dr = d.pop("_draw", None)
        d.pop("_vals", None)
        if dr and d["status"] == "measured":
            g, lines = dr
            raw = cv2.imencode(".jpg", g["img"], [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
            ann = cv2.imencode(".jpg", render(g, lines, d["name"]), [cv2.IMWRITE_JPEG_QUALITY, 85])[1].tobytes()
            imgs.append((f"assess:{d['key']}", raw, ann))
    return out, imgs
