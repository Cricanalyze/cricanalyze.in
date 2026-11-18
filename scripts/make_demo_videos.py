"""Generates the illustrative demo clips shown on the upload page (frontend/public/demo). Run: python scripts/make_demo_videos.py"""
import subprocess, numpy as np, cv2, imageio_ffmpeg

W, H, FPS, SEC = 640, 360, 30, 5
J = ["head", "ls", "rs", "le", "re", "lw", "rw", "lh", "rh", "lk", "rk", "la", "ra"]
BONES = [("ls", "rs"), ("ls", "le"), ("le", "lw"), ("rs", "re"), ("re", "rw"), ("ls", "lh"), ("rs", "rh"), ("lh", "rh"), ("lh", "lk"), ("lk", "la"), ("rh", "rk"), ("rk", "ra")]
BAT = [("Stance", {"head": (0, 1.62), "ls": (-0.2, 1.42), "rs": (0.2, 1.42), "le": (-0.22, 1.15), "re": (0.12, 1.12), "lw": (-0.05, 0.98), "rw": (0.0, 0.98), "lh": (-0.13, 0.95), "rh": (0.13, 0.95), "lk": (-0.2, 0.52), "rk": (0.2, 0.52), "la": (-0.25, 0.06), "ra": (0.25, 0.06), "tip": (-0.1, 0.12)}),
       ("Backlift", {"head": (0, 1.62), "ls": (-0.2, 1.42), "rs": (0.2, 1.42), "le": (-0.05, 1.3), "re": (0.3, 1.28), "lw": (0.25, 1.5), "rw": (0.3, 1.52), "lh": (-0.13, 0.95), "rh": (0.13, 0.95), "lk": (-0.2, 0.52), "rk": (0.2, 0.52), "la": (-0.25, 0.06), "ra": (0.25, 0.06), "tip": (0.55, 1.95)}),
       ("Stride", {"head": (-0.12, 1.55), "ls": (-0.3, 1.36), "rs": (0.12, 1.36), "le": (-0.3, 1.15), "re": (0.2, 1.15), "lw": (0.05, 1.25), "rw": (0.1, 1.27), "lh": (-0.2, 0.9), "rh": (0.1, 0.9), "lk": (-0.38, 0.5), "rk": (0.22, 0.48), "la": (-0.45, 0.06), "ra": (0.25, 0.06), "tip": (0.35, 1.6)}),
       ("Impact", {"head": (-0.25, 1.45), "ls": (-0.4, 1.28), "rs": (0.0, 1.28), "le": (-0.38, 1.02), "re": (-0.08, 1.0), "lw": (-0.25, 0.82), "rw": (-0.2, 0.84), "lh": (-0.3, 0.84), "rh": (0.02, 0.84), "lk": (-0.45, 0.46), "rk": (0.2, 0.4), "la": (-0.5, 0.06), "ra": (0.25, 0.07), "tip": (-0.35, 0.12)}),
       ("Follow-through", {"head": (-0.22, 1.47), "ls": (-0.38, 1.3), "rs": (0.02, 1.3), "le": (-0.45, 1.5), "re": (-0.1, 1.45), "lw": (-0.2, 1.7), "rw": (-0.15, 1.68), "lh": (-0.3, 0.86), "rh": (0.02, 0.86), "lk": (-0.45, 0.47), "rk": (0.18, 0.42), "la": (-0.5, 0.06), "ra": (0.22, 0.15), "tip": (0.25, 2.0)})]
BOWL = [("Gather", {"head": (0, 1.65), "ls": (0.05, 1.42), "rs": (-0.05, 1.42), "le": (0.12, 1.25), "re": (-0.1, 1.25), "lw": (0.05, 1.3), "rw": (0, 1.32), "lh": (0.03, 0.95), "rh": (-0.03, 0.95), "lk": (0.15, 0.6), "rk": (-0.05, 0.52), "la": (0.05, 0.3), "ra": (-0.1, 0.06)}),
        ("Back-foot contact", {"head": (0.35, 1.6), "ls": (0.5, 1.45), "rs": (0.25, 1.4), "le": (0.7, 1.6), "re": (0.05, 1.2), "lw": (0.8, 1.85), "rw": (-0.1, 1.0), "lh": (0.4, 0.95), "rh": (0.3, 0.95), "lk": (0.6, 0.6), "rk": (0.3, 0.5), "la": (0.75, 0.35), "ra": (0.3, 0.06)}),
        ("Front-foot contact", {"head": (0.85, 1.55), "ls": (0.95, 1.42), "rs": (0.7, 1.42), "le": (1.05, 1.3), "re": (0.5, 1.6), "lw": (1.0, 1.1), "rw": (0.45, 1.9), "lh": (0.8, 0.92), "rh": (0.68, 0.92), "lk": (1.05, 0.5), "rk": (0.5, 0.45), "la": (1.2, 0.06), "ra": (0.25, 0.08)}),
        ("Release", {"head": (1.05, 1.5), "ls": (1.05, 1.35), "rs": (0.95, 1.45), "le": (0.95, 1.05), "re": (1.05, 1.85), "lw": (0.75, 0.95), "rw": (1.15, 2.2), "lh": (0.95, 0.92), "rh": (0.85, 0.92), "lk": (1.15, 0.5), "rk": (0.7, 0.4), "la": (1.2, 0.06), "ra": (0.5, 0.2)}),
        ("Follow-through", {"head": (1.45, 1.3), "ls": (1.5, 1.2), "rs": (1.3, 1.25), "le": (1.6, 0.95), "re": (1.55, 1.0), "lw": (1.4, 0.8), "rw": (1.7, 0.7), "lh": (1.3, 0.85), "rh": (1.2, 0.85), "lk": (1.5, 0.45), "rk": (1.45, 0.5), "la": (1.4, 0.06), "ra": (1.7, 0.3)})]


def pose(keys, u):
    n = len(keys)
    f = u * n
    i, t = int(f) % n, f - int(f)
    t = t * t * (3 - 2 * t)
    a, b = keys[i][1], keys[(i + 1) % n][1]
    return keys[i][0] if t < 0.5 else keys[(i + 1) % n][0], {k: (a[k][0] + (b[k][0] - a[k][0]) * t, a[k][1] + (b[k][1] - a[k][1]) * t) for k in a}


def render(keys, path, title, angle, ox, side):
    out = path + ".raw.mp4"
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    s = 120
    for fi in range(FPS * SEC):
        u = fi / (FPS * SEC)
        img = np.full((H, W, 3), (43, 19, 11), np.uint8)
        cv2.rectangle(img, (0, 300), (W, H), (61, 42, 20), -1)
        for x in range(0, W, 40):
            cv2.line(img, (x, 300), (W // 2 + (x - W // 2) * 2, H), (90, 70, 30), 1)
        name, p = pose(keys, u)
        P = lambda k: (int(ox + p[k][0] * s), int(300 - p[k][1] * s))
        if "tip" in p:
            g = ((P("lw")[0] + P("rw")[0]) // 2, (P("lw")[1] + P("rw")[1]) // 2)
            cv2.line(img, g, P("tip"), (130, 179, 217), 9, cv2.LINE_AA)
        for a, b in BONES:
            cv2.line(img, P(a), P(b), (129, 185, 16), 5, cv2.LINE_AA)
        for k in J:
            cv2.circle(img, P(k), 6, (239, 215, 95), -1, cv2.LINE_AA)
        cv2.circle(img, P("head"), 16, (216, 180, 0), 2, cv2.LINE_AA)
        cv2.rectangle(img, (14, 14), (330, 74), (65, 37, 28), -1)
        cv2.putText(img, title, (24, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, f"Recommended camera: {angle}", (24, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (129, 185, 16), 1, cv2.LINE_AA)
        cv2.putText(img, name, (24, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (11, 158, 245), 2, cv2.LINE_AA)
        # top-view camera diagram
        bx, by = W - 150, 18
        cv2.rectangle(img, (bx, by), (bx + 130, by + 90), (65, 37, 28), -1)
        cv2.rectangle(img, (bx + 55, by + 10), (bx + 75, by + 80), (120, 160, 90), -1)
        cam = (bx + 65, by + 86) if side == "front" else (bx + 115, by + 45)
        cv2.circle(img, cam, 7, (11, 158, 245), -1)
        cv2.putText(img, "camera", (cam[0] - 52 if side != "front" else cam[0] - 24, cam[1] - 10 if side == "front" else cam[1] + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (11, 158, 245), 1, cv2.LINE_AA)
        cv2.putText(img, "Phone steady at hip height - whole body in frame - good light", (24, H - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (226, 232, 240), 1, cv2.LINE_AA)
        cv2.putText(img, "Illustrative demo", (W - 150, H - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (140, 140, 140), 1, cv2.LINE_AA)
        vw.write(img)
    vw.release()
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", out, "-c:v", "libx264", "-preset", "slow", "-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], check=True)
    import os
    os.remove(out)


if __name__ == "__main__":
    d = "/app/frontend/public/demo/"
    import os
    os.makedirs(d, exist_ok=True)
    render(BAT, d + "batting-front-on.mp4", "Batting demo - front-on view", "FRONT-ON", W // 2, "front")
    render(BOWL, d + "bowling-side-on.mp4", "Bowling demo - side-on view", "SIDE-ON", 200, "side")
    print("ok")
