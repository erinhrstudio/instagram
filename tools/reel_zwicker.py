"""Reel "il fischio nel silenzio" (tono di Zwicker, 1964): meglio in cuffia.

Dieci secondi di rumore con un buco di mezza ottava (2,8-4 kHz). Quando il rumore si ferma,
molte persone sentono per qualche secondo un fischio debole, vicino al bordo basso del buco.
Nel video, in quel momento, c'è silenzio digitale.

Uso: python -m tools.reel_zwicker media/tiktok/fischio-silenzio.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
NOTCH = (2800, 4000)
RUMORE, SILENZIO, SPIEGA, FINE, END = 0.3, 10.8, 16.4, 22.0, 27.0


def build():
    rng = np.random.default_rng(9)
    n = int((SILENZIO - RUMORE) * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = ((f > 60) & (f < 14000)).astype(float)
    g[(f > NOTCH[0]) & (f < NOTCH[1])] = 0
    x = np.fft.irfft(X * g, n)
    x /= np.abs(x).max()
    r = int(0.3 * SR)
    x[:r] *= np.linspace(0, 1, r)
    e = int(0.02 * SR)                      # fine netta: il fischio arriva quando il rumore sparisce
    x[-e:] *= np.linspace(1, 0, e)
    a = np.zeros(int(END * SR))
    a[int(RUMORE * SR):int(RUMORE * SR) + n] = x * 0.6
    return a


def spectrum(c, t, y0=760, y1=1100, x0=140, x1=W - 140, on=True, ghost=0.0, k=1.0):
    rng = np.random.default_rng(int(t * 12))
    n = 48
    c.line([(x0, y1 + 8), (x1, y1 + 8)], fill=LINE, width=2)
    c.text((x0, y1 + 24), "LOW", font("sans", 22, 700), fill=MUTED, anchor="la", tracking=3)
    c.text((x1, y1 + 24), "HIGH", font("sans", 22, 700), fill=MUTED, anchor="ra", tracking=3)
    fb = 60 * (14000 / 60) ** (np.arange(n) / (n - 1))
    bw = (x1 - x0) / n
    for i, fr in enumerate(fb):
        if NOTCH[0] < fr < NOTCH[1]:
            continue
        h = (y1 - y0) * (0.5 + 0.12 * rng.random()) * k if on else 3
        x = x0 + i * bw
        c.rect((x + 2, y1 - h, x + bw - 2, y1), fill=fade((120, 116, 128), 0.75))
    if ghost > 0:
        xb = x0 + (np.log(NOTCH[0] / 60) / np.log(14000 / 60)) * (x1 - x0)
        hb = (y1 - y0) * 0.35
        c.rect((xb - 4, y1 - hb, xb + 4, y1), fill=fade(style.PINK, ghost))
        c.ellipse((xb - 13, y1 - hb - 13, xb + 13, y1 - hb + 13), outline=fade(style.PINK, ghost), width=3)
        c.text((xb, y1 - hb - 50), "?", font("display", 60), fill=fade(style.PINK, ghost), anchor="mm")


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SILENZIO:
        c.kicker(0, 300, "BEST ON HEADPHONES · MEDIUM VOLUME", center=True)
        centered(c, 360, "LISTEN TO THE NOISE.", 120, WHITE)
        centered(c, 490, "THEN THE SILENCE.", 120, style.PINK)
        spectrum(c, t)
        left = max(0, int(np.ceil(SILENZIO - t)))
        centered(c, 1240, f"SILENCE IN {left} SECONDS" if left > 1 else "SILENCE IN 1 SECOND", 30, MUTED, "sans", 700, 4)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "NOTHING IS PLAYING NOW", center=True)
        centered(c, 360, "DO YOU HEAR", 150, fade(WHITE, k(SILENZIO)))
        centered(c, 510, "A WHISTLE?", 150, fade(style.PINK, k(SILENZIO + 0.2)))
        spectrum(c, t, on=False, ghost=0.35 + 0.35 * np.sin((t - SILENZIO) * 3) ** 2 if t > SILENZIO + 1 else 0)
        centered(c, 1240, "THE VIDEO IS SILENT, I SWEAR", 30, fade(MUTED, k(SILENZIO + 2.0)), "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "ZWICKER TONE", center=True)
        centered(c, 360, "THE WHISTLE", 140, fade(WHITE, k(SPIEGA)))
        centered(c, 500, "IS IN YOUR HEAD.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 710, ["The noise had a slice of frequencies missing.",
                           "When the noise stops, your hearing",
                           "fills that gap for a few seconds",
                           "with a note that doesn't exist.",
                           "Not everyone hears it: do you?",
                           "",
                           "· Eberhard Zwicker · 1964"], SPIEGA + 0.5, k)
        return
    centered(c, 420, "YES OR NO?", 190, fade(WHITE, k(FINE)))
    centered(c, 620, "TELL ME IN THE COMMENTS.", 110, fade(style.PINK, k(FINE + 0.3)))
    centered(c, 800, "THEN TRY AGAIN ON HEADPHONES, IN THE DARK", 34, fade(TEXT, k(FINE + 0.8)), "sans", 700, 3)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "fischio-silenzio.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=59)
    print("scritto", out)
