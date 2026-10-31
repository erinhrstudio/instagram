"""Reel speciale Halloween: Danny Elfman. Video muto 1080x1920: la canzone si aggiunge dall'app.

Fatti verificati (fonti in posts/danny-elfman/fonti.md):
- Oingo Boingo, Tim Burton e il primo film (Pee-wee's Big Adventure, 1985): MasterClass.
- Sigla dei Simpson (Grammy), 4 nomination all'Oscar e nessuna vinta: Wikipedia.
- Nightmare Before Christmas (1993): canta lui le canzoni di Jack in originale, Renato Zero in italiano: Movieplayer.
- Sigla di Mercoledì (Netflix, 2022): BroadwayWorld, Remezcla.

Uso: python -m tools.reel_elfman   ->  media/tiktok/danny-elfman.mp4
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import ImageDraw

from reels import style
from reels.style import Canvas, font, MUTED, TEXT

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
POST = ROOT / "posts" / "danny-elfman"
FPS, W, H = 30, 1080, 1920
WHITE = (255, 255, 255)
INK = (31, 31, 31)

# (inizio, scena)
SCENE = [(0.0, "hook"), (3.4, "lista"), (7.2, "chi"), (11.6, "jack"), (16.4, "oscar"),
         (20.4, "ricetta"), (25.4, "cta")]
END = 29.5


def fade(rgb, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(v * k + b * (1 - k)) for v, b in zip(rgb, INK))


def t_in(t, t0, d=0.35):
    return max(0.0, min(1.0, (t - t0) / d))


def centro(c, y, s, size, fill, k=1.0, kind="display", weight=400, tracking=0):
    """Testo centrato che entra salendo di 24 px e schiarendo."""
    c.text((W / 2, y + (1 - k) * 24), s, font(kind, size, weight), fill=fade(fill, k), anchor="ma", tracking=tracking)


def corpo(c, y, righe, t, t0, size=40, passo=62):
    for i, r in enumerate(righe):
        centro(c, y + i * passo, r, size, TEXT, t_in(t, t0 + 0.18 * i), "sans")


def kicker(c, s, k):
    centro(c, 300, s, 24, style.PINK_SOFT, k, "sans", 700, 5)


def frame(c, t, scena, t0):
    r = t - t0
    if scena == "hook":
        kicker(c, "SPECIALE HALLOWEEN", t_in(r, 0.0))
        centro(c, 1080, "HAI SENTITO", 150, WHITE, t_in(r, 0.0, 0.25))
        centro(c, 1230, "LA SUA MUSICA.", 150, WHITE, t_in(r, 0.25, 0.25))
        centro(c, 1400, "NON SAI CHI SIA.", 110, style.PINK, t_in(r, 1.3, 0.3))
        return
    if scena == "lista":
        voci = ["I SIMPSON.", "BATMAN.", "SPIDER-MAN.", "MERCOLEDÌ."]
        for i, v in enumerate(voci):
            centro(c, 420 + i * 175, v, 160, WHITE, t_in(r, 0.15 + 0.5 * i, 0.2))
        centro(c, 1200, "LE HA SCRITTE", 90, style.PINK_SOFT, t_in(r, 2.4))
        centro(c, 1310, "LO STESSO UOMO.", 120, style.PINK, t_in(r, 2.6))
        return
    if scena == "chi":
        kicker(c, "CHI È", t_in(r, 0))
        centro(c, 400, "DANNY ELFMAN", 170, WHITE, t_in(r, 0.1))
        corpo(c, 640, ["Prima del cinema cantava in una band",
                       "new wave di Los Angeles: gli Oingo Boingo.",
                       "Un giovane Tim Burton lo nota",
                       "e gli affida il suo primo film."], r, 0.6)
        centro(c, 980, "PEE-WEE'S BIG ADVENTURE · 1985", 28, MUTED, t_in(r, 1.6), "sans", 600, 4)
        return
    if scena == "jack":
        kicker(c, "NIGHTMARE BEFORE CHRISTMAS · 1993", t_in(r, 0))
        centro(c, 400, "JACK CANTA", 160, WHITE, t_in(r, 0.1))
        centro(c, 560, "CON LA SUA VOCE.", 130, style.PINK, t_in(r, 0.4))
        corpo(c, 800, ["Elfman scrive tutte le canzoni",
                       "e nella versione originale",
                       "canta lui le parti di Jack."], r, 1.0)
        centro(c, 1060, "IN ITALIANO?", 70, WHITE, t_in(r, 2.4))
        centro(c, 1150, "RENATO ZERO.", 120, style.PINK, t_in(r, 2.9, 0.25))
        return
    if scena == "oscar":
        centro(c, 400, "4 NOMINATION", 160, WHITE, t_in(r, 0.0))
        centro(c, 560, "ALL'OSCAR.", 160, WHITE, t_in(r, 0.2))
        centro(c, 760, "ZERO STATUETTE.", 130, style.PINK, t_in(r, 1.0, 0.25))
        centro(c, 980, "MEN IN BLACK · GOOD WILL HUNTING · BIG FISH · MILK", 26, MUTED,
               t_in(r, 1.8), "sans", 600, 3)
        return
    if scena == "ricetta":
        kicker(c, "PER CHI FA MUSICA", t_in(r, 0))
        centro(c, 380, "IL SUONO ELFMAN", 150, WHITE, t_in(r, 0.1))
        voci = [("CORO", "voci senza parole, riverbero lungo"),
                ("CELESTA", "o carillon, sopra la melodia"),
                ("ARCHI", "pizzicati corti, quasi a passi"),
                ("MELODIA", "in minore, ma che si canta")]
        for i, (a, b) in enumerate(voci):
            k = t_in(r, 0.8 + 0.5 * i)
            y = 620 + i * 170
            centro(c, y, a, 30, style.PINK_SOFT, k, "sans", 700, 5)
            centro(c, y + 50, b, 44, TEXT, k, "sans")
        centro(c, 1330, "PROVALO NELLA TUA DAW", 26, MUTED, t_in(r, 2.8), "sans", 600, 4)
        return
    centro(c, 520, "MANDALO A CHI", 130, WHITE, t_in(r, 0.0))
    centro(c, 660, "GUARDA NIGHTMARE", 120, style.PINK, t_in(r, 0.2))
    centro(c, 790, "BEFORE CHRISTMAS", 120, style.PINK, t_in(r, 0.35))
    centro(c, 930, "OGNI HALLOWEEN.", 120, WHITE, t_in(r, 0.6))
    c.line([(W / 2 - 80, 1110), (W / 2 + 80, 1110)], fill=style.PINK, width=2)
    centro(c, 1160, "ERIN · VOCI E SUONI DA CONOSCERE", 26, MUTED, t_in(r, 1.2), "sans", 600, 4)


def basi():
    style.set_accent("zucca")
    out = {}
    piena = Canvas(W, H, seed=31, bg="pieno")
    piena.header("ERIN · HOME RECORDING STUDIO", "HALLOWEEN")
    out["base"] = piena.img.copy()
    foto = POST / "foto.jpg"
    ritratto = Canvas(W, H, seed=31)
    if foto.exists():
        ritratto.portrait(foto, focus=FOCUS, zoom=1.0, fade_from=0.35, darken=0.25)
    ritratto.header("ERIN · HOME RECORDING STUDIO", "HALLOWEEN")
    out["foto"] = ritratto.img.copy()
    return out


FOCUS = (0.5, 0.35)


def zoom_img(img, k, amount=0.05):
    z = 1 + amount * k
    w, h = int(img.width / z), int(img.height / z)
    box = ((img.width - w) // 2, (img.height - h) // 3, (img.width - w) // 2 + w, (img.height - h) // 3 + h)
    return img.crop(box).resize(img.size)


def render(out):
    b = basi()
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for f in range(int(END * FPS)):
        t = f / FPS
        i = max(j for j, (s, _) in enumerate(SCENE) if s <= t)
        t0, scena = SCENE[i]
        fine = SCENE[i + 1][0] if i + 1 < len(SCENE) else END
        c = Canvas.__new__(Canvas)
        c.w, c.h = W, H
        sfondo = b["foto"] if scena == "hook" else b["base"]
        c.img = zoom_img(sfondo, t / 3.4) if scena == "hook" else sfondo.copy()
        c.d = ImageDraw.Draw(c.img)
        frame(c, t, scena, t0)
        a = np.asarray(c.final().convert("RGB"), np.float32)
        u = (fine - t) / 0.25  # breve dissolvenza al nero tra le scene
        if u < 1:
            a = a * max(u, 0) + np.array(INK, np.float32) * (1 - max(u, 0))
        p.stdin.write(a.astype(np.uint8).tobytes())
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg non ha completato il video")


style.ACCENTS["zucca"] = style._ruota(26)

if __name__ == "__main__":
    out = ROOT / "media" / "tiktok" / "danny-elfman.mp4"
    render(out)
    print("scritto", out)
