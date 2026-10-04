"""Trasforma un carosello (posts/<nome>/NN.jpg) in un video verticale per TikTok.

Ogni slide 1080x1350 sta al centro di un fondo 1080x1920, per 3,5 s (la copertina 2,5 s), con una
dissolvenza breve. Audio muto: il suono di tendenza si aggiunge dall'app.

Uso: python -m tools.tiktok_slideshow billie-eilish   ->  media/tiktok/billie-eilish.mp4
"""
import subprocess, sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
W, H, FPS, FADE = 1080, 1920, 30, 0.3
BG = (31, 31, 31)


def frames(name):
    slides = sorted((ROOT / "posts" / name).glob("[0-9][0-9]*.jpg"))
    out = []
    for i, p in enumerate(slides):
        im = Image.open(p).convert("RGB").resize((W, int(W * 1350 / 1080)))
        canvas = Image.new("RGB", (W, H), BG)
        canvas.paste(im, (0, (H - im.height) // 2 - 60))
        out.append((np.asarray(canvas), 2.5 if i == 0 else 3.5))
    return out


def render(name):
    out = ROOT / "media" / "tiktok" / f"{name}.mp4"
    fr = frames(name)
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for k, (img, dur) in enumerate(fr):
        n = int(dur * FPS)
        nxt = fr[k + 1][0] if k + 1 < len(fr) else None
        for f in range(n):
            t = (f - (n - FADE * FPS)) / (FADE * FPS)
            if nxt is not None and t > 0:
                p.stdin.write((img * (1 - t) + nxt * t).astype(np.uint8).tobytes())
            else:
                p.stdin.write(img.tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg non ha completato il video")
    return out


if __name__ == "__main__":
    for n in sys.argv[1:]:
        print("scritto", render(n))
