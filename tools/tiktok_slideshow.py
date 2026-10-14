"""Trasforma un carosello (posts/<nome>/NN.jpg) in un video verticale per TikTok.

Ogni slide 1080x1350 sta al centro di un fondo 1080x1920 con un lento zoom (movimento fin dal primo
fotogramma), per 2,4 s (la copertina 1,5 s), con una dissolvenza breve: circa 20 s per 9 slide.
Dal 14/10 i tempi sono più corti perché su TikTok la visione media del post Eva Korman era 4,4 s su 30,5.
Audio muto: il suono di tendenza si aggiunge dall'app.

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
        out.append((canvas, 1.5 if i == 0 else 2.4))
    return out


def zoom(img, x, amount=0.04):
    """Ingrandisce piano la slide (da 1 a 1+amount) tenendo il centro: dà movimento senza muovere il testo."""
    z = 1 + amount * x
    w, h = int(W / z), int(H / z)
    box = ((W - w) // 2, (H - h) // 2, (W - w) // 2 + w, (H - h) // 2 + h)
    return np.asarray(img.crop(box).resize((W, H), Image.BILINEAR))


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
            a = zoom(img, f / n)
            t = (f - (n - FADE * FPS)) / (FADE * FPS)
            if nxt is not None and t > 0:
                a = (a * (1 - t) + zoom(nxt, 0) * t).astype(np.uint8)
            p.stdin.write(a.tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg non ha completato il video")
    return out


if __name__ == "__main__":
    for n in sys.argv[1:]:
        print("scritto", render(n))
