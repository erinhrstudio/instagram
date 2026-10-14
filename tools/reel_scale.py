"""Reel "due scale a zig-zag" (illusione della scala, Diana Deutsch 1975): in cuffia.

Una scala sale e una scende nello stesso momento, ma le note saltano da un orecchio all'altro.
Quasi nessuno lo sente così: di solito si sentono le note acute in un orecchio e le gravi nell'altro,
come due melodie a forma di valle e di collina.

Uso: python -m tools.reel_scale media/tiktok/scale-zigzag.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
NOTE = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]   # do maggiore, do4-do5
SU, GIU = NOTE, NOTE[::-1]
STEP = 0.28
GIRO = len(NOTE) * STEP
ASCOLTA, VOTA, RIVELA, SPIEGA, FINE, END = 0.0, 4 * GIRO, 4 * GIRO + 2.6, 4 * GIRO + 2.6 + 2 * GIRO + 0.4, 0, 0
FINE = SPIEGA + 5.6
END = FINE + 2 * GIRO + 0.6


def orecchi(i):
    """(nota a sinistra, nota a destra) al passo i: le due scale si scambiano orecchio a ogni nota."""
    return (SU[i], GIU[i]) if i % 2 == 0 else (GIU[i], SU[i])


def tono(f, n):
    t = np.arange(n) / SR
    env = np.minimum(1, np.minimum(t / 0.01, (n / SR - t) / 0.03))
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * np.clip(env, 0, 1)


def build():
    a = np.zeros((int(END * SR) + SR, 2))
    for t0, giri in [(ASCOLTA, 4), (RIVELA, 2), (FINE + 0.3, 2)]:
        for g in range(giri):
            for i in range(len(NOTE)):
                l, r = orecchi(i)
                s = int((t0 + (g * len(NOTE) + i) * STEP) * SR)
                n = int(STEP * SR)
                a[s:s + n, 0] += tono(l, n)
                a[s:s + n, 1] += tono(r, n)
    return a[:int(END * SR)] * 0.4


def grafico(c, y, t_rel, k=1.0, vero=True):
    """Note di sinistra (pallini) e di destra (quadrati) sul pentagramma semplificato."""
    x0, x1 = 160, W - 160
    lo, hi = np.log(NOTE[0]), np.log(NOTE[-1])
    cur = int(t_rel // STEP) % len(NOTE) if t_rel is not None else -1
    for side, yy in [(0, y), (1, y + 260)]:
        c.text((W / 2, yy - 130), "SINISTRA" if side == 0 else "DESTRA", font("sans", 24, 700),
               fill=fade(MUTED, k), anchor="mm", tracking=4)
        pts = []
        for i in range(len(NOTE)):
            f = orecchi(i)[side] if vero else (sorted(orecchi(i))[1 - side] if side == 0 else sorted(orecchi(i))[0])
            if not vero and side == 0:
                f = max(orecchi(i))
            if not vero and side == 1:
                f = min(orecchi(i))
            x = x0 + (i + 0.5) / len(NOTE) * (x1 - x0)
            py = yy + 70 - (np.log(f) - lo) / (hi - lo) * 140
            pts.append((x, py))
        c.line(pts, fill=fade(LINE, k), width=3)
        for i, (x, py) in enumerate(pts):
            r = 20 if i == cur else 12
            c.ellipse((x - r, py - r, x + r, py + r), fill=fade(style.PINK if i == cur else (170, 166, 180), k))


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < VOTA:
        c.kicker(0, 300, "IN CUFFIA", center=True)
        centered(c, 360, "COSA SENTI", 150, WHITE)
        centered(c, 510, "A SINISTRA?", 150, style.PINK)
        c.text((W / 2, 900), "?", font("display", 300), fill=fade(style.PINK, 0.5 + 0.5 * k(0, 0.5)), anchor="mm")
        centered(c, 1240, "ACUTE O GRAVI? SALE O SCENDE?", 30, MUTED, "sans", 700, 4)
        return
    if t < RIVELA:
        c.kicker(0, 300, "QUELLO CHE SENTI DI SOLITO", center=True)
        centered(c, 360, "ACUTE A UN LATO,", 120, fade(WHITE, k(VOTA)))
        centered(c, 490, "GRAVI ALL'ALTRO.", 120, fade(style.PINK, k(VOTA + 0.2)))
        grafico(c, 820, None, k=k(VOTA + 0.4), vero=False)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "QUELLO CHE SUONA DAVVERO", center=True)
        centered(c, 360, "ZIG-ZAG", 150, fade(WHITE, k(RIVELA)))
        centered(c, 510, "IN TUTTI E DUE.", 130, fade(style.PINK, k(RIVELA + 0.2)))
        grafico(c, 820, t - RIVELA, k=k(RIVELA + 0.3))
        return
    if t < FINE:
        c.kicker(0, 300, "ILLUSIONE DELLA SCALA", center=True)
        centered(c, 360, "IL CERVELLO", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "RIMETTE IN ORDINE.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Una scala sale e una scende insieme,",
                           "e ogni nota cambia orecchio.",
                           "Il cervello raggruppa le note per altezza,",
                           "non per orecchio: ti costruisce",
                           "due melodie che nessuno ha suonato.",
                           "",
                           "· Diana Deutsch · 1975"], SPIEGA + 0.5, k)
        return
    centered(c, 420, "GIRA LE CUFFIE.", 150, fade(WHITE, k(FINE)))
    centered(c, 580, "LE ACUTE", 130, fade(style.PINK, k(FINE + 0.3)))
    centered(c, 710, "SI SPOSTANO?", 130, fade(style.PINK, k(FINE + 0.3)))
    c.text((W / 2, 1010), "?", font("display", 240), fill=fade(style.PINK, 0.6 * k(FINE + 0.8)), anchor="mm")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "scale-zigzag.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=64)
    print("scritto", out)
