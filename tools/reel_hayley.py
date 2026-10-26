"""Reel cantante: Hayley Williams (Paramore). Foto in bianco e nero a tutto schermo, zoom lento, frasi brevi.

Audio muto: la canzone (Paramore) si aggiunge dall'app al momento della pubblicazione.
Uso: python -m tools.reel_hayley [instagram|youtube]  ->  media/tiktok/hayley-williams.mp4 (o media/youtube/)
"""
import subprocess, sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from reels.style import font, S, PINK, PINK_SOFT, TEXT, MUTED

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30

# (inizio, fine, righe grandi, riga piccola)
BATTUTE = [
    (0.0, 2.6, ["LA VOLEVANO POPSTAR.", "HA DETTO NO."], "Hayley Williams · Paramore"),
    (2.6, 5.0, ["A 14 ANNI FIRMA", "IL PRIMO CONTRATTO."], ""),
    (5.0, 7.4, ["L'ETICHETTA LA VUOLE", "SOLISTA E POP."], ""),
    (7.4, 9.8, ["LEI INSISTE:", "VUOLE UNA BAND."], ""),
    (9.8, 12.2, ["COSÌ NASCONO", "I PARAMORE."], ""),
    (12.2, 14.8, ["NEL 2015", "VINCONO UN GRAMMY."], "Best Rock Song con \"Ain't It Fun\""),
    (14.8, 18.5, ["E TU AVRESTI", "DETTO NO?"], "Alla fama da solista? Scrivilo nei commenti"),
]
FINE = 18.5


def foto():
    im = Image.open(ROOT / "posts" / "hayley-williams" / "foto.jpg").convert("L")
    im = ImageOps.autocontrast(im, cutoff=0.5)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    # riempie 1080x1920 tenendo il viso (in alto al centro della foto)
    k = max(W * 1.02 / im.width, H * 1.02 / im.height)
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    rng = np.random.default_rng(7)
    a = np.asarray(im, dtype=np.float32) + rng.normal(0, 5, (im.height, im.width))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGB")


def sfumatura():
    """Scurisce il basso per far leggere il testo."""
    y = np.linspace(0, 1, H)[:, None]
    a = np.clip((y - 0.55) / 0.32, 0, 1) ** 1.3 * 0.82 + 0.12
    return np.repeat(a, W, 1)[..., None]


def disegna_testo(t, piattaforma):
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (a, b, righe, piccola) in enumerate(BATTUTE):
        if not (a <= t < b):
            continue
        k = min(1, (t - a) / 0.18) if i else 1  # la prima frase c'è dal primo fotogramma
        y = 1350
        size = 132
        while max(font("display", size).getlength(r) for r in righe) > 960 * S:
            size -= 4  # le righe lunghe si stringono per stare dentro i margini
        f = font("display", size)
        for j, r in enumerate(righe):
            col = PINK if j == len(righe) - 1 else TEXT
            d.text((W * S / 2, (y + (1 - k) * 30) * S), r, font=f, fill=col + (int(255 * k),), anchor="ma")
            y += 128
        if piccola:
            d.text((W * S / 2, (y + 26) * S), piccola, font=font("sans", 40, 500),
                   fill=PINK_SOFT + (int(255 * k),), anchor="ma")
        if i == len(BATTUTE) - 1:
            invito = ("ISCRIVITI A @ERINHRSTUDIO PER LA PROSSIMA VOCE" if piattaforma == "youtube"
                      else "SEGUI @ERIN.RECORDINGSTUDIO PER LA PROSSIMA VOCE")
            d.text((W * S / 2, (y + 100) * S), invito, font=font("sans", 32, 600),
                   fill=MUTED + (int(255 * k),), anchor="ma")
    # kicker fisso in alto, sotto la zona dei pulsanti
    d.text((W * S / 2, 230 * S), "ANATOMIA DI UNA VOCE", font=font("sans", 30, 600),
           fill=PINK_SOFT + (220,), anchor="ma")
    return img.resize((W, H), Image.LANCZOS)


def render(piattaforma="instagram"):
    cartella = "youtube" if piattaforma == "youtube" else "tiktok"
    out = ROOT / "media" / cartella / "hayley-williams.mp4"
    base, sf = foto(), sfumatura()
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    n = int(FINE * FPS)
    cache = {}
    for f in range(n):
        t = f / FPS
        z = 1 + 0.09 * t / FINE
        h = int(base.height / z)
        w = int(h * W / H)  # ritaglio con le stesse proporzioni del video: niente foto schiacciata
        x0 = int((base.width - w) * 0.45)
        y0 = int((base.height - h) * 0.3)
        fr = base.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.BILINEAR)
        a = np.asarray(fr, dtype=np.float32) * (1 - sf)
        key = (int(t * 12),)
        if key not in cache:
            cache.clear()
            cache[key] = disegna_testo(t, piattaforma)
        txt = cache[key]
        frame = Image.fromarray(a.astype(np.uint8))
        frame.paste(txt, (0, 0), txt)
        p.stdin.write(np.asarray(frame).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg non ha completato il video")
    return out


if __name__ == "__main__":
    print(render(sys.argv[1] if len(sys.argv) > 1 else "instagram"))
