"""Turns a real bowling clip into a painted/animated-look demo (local OpenCV, no AI credits).
Run: python scripts/animate_demo.py <input.mp4> /app/frontend/public/demo/bowling-side-on.mp4"""
import sys, subprocess, cv2, numpy as np, imageio_ffmpeg

src, dst = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(src)
fps = cap.get(cv2.CAP_PROP_FPS) or 30
step = 2 if fps > 40 else 1
tmp = dst + ".raw.mp4"
w, h = int(cap.get(3)) // 2 * 2, int(cap.get(4)) // 2 * 2
vw = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*"mp4v"), fps / step, (w, h))
i = 0
while True:
    ok, f = cap.read()
    if not ok:
        break
    if i % step == 0:
        f = cv2.resize(f, (w, h))
        a = cv2.stylization(f, sigma_s=60, sigma_r=0.45)
        hsv = cv2.cvtColor(a, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * 1.35, 0, 255)
        hsv[..., 2] = np.clip(hsv[..., 2] * 1.12 + 8, 0, 255)
        vw.write(cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR))
    i += 1
vw.release()
logo = "/app/frontend/public/logo.png"
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", tmp, "-i", logo, "-filter_complex",
                "[0:v]scale=1280:-2[v];[1:v]scale=200:-1,format=rgba,colorkey=0xFFFFFF:0.25:0.1,colorchannelmixer=aa=0.75[l];[v][l]overlay=W-w-24:H-h-20",
                "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], check=True)
import os
os.remove(tmp)
print("ok", dst)
