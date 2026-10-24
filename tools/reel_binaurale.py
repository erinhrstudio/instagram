"""Reel "il battito che esiste solo nella tua testa" (battimenti binaurali, Dove 1839): SOLO in cuffia.

A sinistra una nota a 250 Hz, a destra una a 254 Hz. Nessuna delle due pulsa,
ma insieme, in cuffia, senti un battito 4 volte al secondo: lo crea il cervello confrontando i due orecchi.
Niente promesse su sonno o concentrazione: è solo un'illusione.

Uso: python -m tools.reel_binaurale media/tiktok/battito-binaurale.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
FL, FR = 250.0, 254.0
INSIEME, SOLO_S, SOLO_D, ANCORA, SPIEGA, FINE, END = 0.0, 6.0, 9.6, 13.2, 17.4, 23.0, 27.4


def build():
    n = int(END * SR)
    t = np.arange(n) / SR
    l = np.sin(2 * np.pi * FL * t); r = np.sin(2 * np.pi * FR * t)
    gl = np.zeros(n); gr = np.zeros(n)
    for t0, t1, a, b in [(INSIEME, SOLO_S, 1, 1), (SOLO_S, SOLO_D, 1, 0), (SOLO_D, ANCORA, 0, 1),
                         (ANCORA, SPIEGA, 1, 1), (FINE, END, 1, 1)]:
        m = (t >= t0) & (t < t1)
        gl[m] = a; gr[m] = b
    ramp = int(0.05 * SR)
    k = np.ones(ramp) / ramp
    gl = np.convolve(gl, k, "same"); gr = np.convolve(gr, k, "same")
    return np.stack([l * gl, r * gr], 1) * 0.5


def head(c, cy, left, right, t, k=1.0):
    r = 150
    c.ellipse((W / 2 - r, cy - r, W / 2 + r, cy + r), outline=fade(LINE, k), width=3)
    for side, on, f in [(-1, left, FL), (1, right, FR)]:
        x = W / 2 + side * (r + 22)
        col = style.PINK if on else (90, 88, 98)
        c.ellipse((x - 22, cy - 50, x + 22, cy + 50), outline=fade(col, k), width=4)
        c.text((W / 2 + side * 330, cy), f"{f:.0f} Hz" if on else "—", font("display", 64),
               fill=fade(TEXT if on else MUTED, k), anchor="mm")
        c.text((W / 2 + side * 330, cy + 70), "SINISTRA" if side < 0 else "DESTRA", font("sans", 24, 700),
               fill=fade(MUTED, k), anchor="mm", tracking=4)
    if left and right:
        p = 0.5 + 0.5 * np.cos(2 * np.pi * (FR - FL) * t)
        rr = 30 + 50 * p
        c.ellipse((W / 2 - rr, cy - rr, W / 2 + rr, cy + rr), fill=fade(style.PINK, k * (0.3 + 0.7 * p)))


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SOLO_S:
        c.kicker(0, 300, "SOLO IN CUFFIA", center=True)
        centered(c, 360, "SENTI", 160, WHITE)
        centered(c, 520, "IL BATTITO?", 160, style.PINK)
        head(c, 900, True, True, t)
        centered(c, 1240, "DUE NOTE FISSE, NIENTE RITMO", 30, MUTED, "sans", 700, 4)
        return
    if t < ANCORA:
        sx = t < SOLO_D
        c.kicker(0, 300, "ORA SOLO UN ORECCHIO", center=True)
        centered(c, 360, "SINISTRA:" if sx else "DESTRA:", 150, fade(WHITE, k(SOLO_S if sx else SOLO_D)))
        centered(c, 510, "NESSUN BATTITO.", 140, fade(style.PINK, k((SOLO_S if sx else SOLO_D) + 0.2)))
        head(c, 900, sx, not sx, t)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "TUTTI E DUE", center=True)
        centered(c, 360, "ECCOLO.", 160, fade(WHITE, k(ANCORA)))
        centered(c, 520, "4 VOLTE AL SECONDO.", 110, fade(style.PINK, k(ANCORA + 0.2)))
        head(c, 900, True, True, t)
        return
    if t < FINE:
        c.kicker(0, 300, "BATTIMENTI BINAURALI", center=True)
        centered(c, 360, "IL BATTITO", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "NON È NELL'AUDIO.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 710, ["Le due note differiscono di 4 Hz.",
                           "Il cervello confronta i due orecchi",
                           "e quella differenza la senti come un battito.",
                           "Nessuna prova che aiuti a dormire o studiare:",
                           "è solo un'illusione, e bellissima.",
                           "",
                           "· Heinrich Wilhelm Dove · 1839"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "TOGLI UNA CUFFIA.", 140, fade(WHITE, k(FINE)))
    centered(c, 560, "SPARISCE.", 150, fade(WHITE, k(FINE + 0.2)))
    centered(c, 720, "SPARISCE ANCHE A TE? SCRIVILO", 64, fade(style.PINK, k(FINE + 0.4)))
    head(c, 1020, True, True, t, k=k(FINE + 0.6, 0.5))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "battito-binaurale.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=63)
    print("scritto", out)
