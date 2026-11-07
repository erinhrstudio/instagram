"""Reel "la canzone che conosci ma non riconosci" (melodia misteriosa, Diana Deutsch 1972).

Le note di Twinkle Twinkle Little Star, giuste come nome, ma ognuna in un'ottava a caso: quasi nessuno
riconosce la canzone. Poi la versione normale. Riascoltando quella sparpagliata, ora la senti.

Uso: python -m tools.reel_melodia media/tiktok/melodia-misteriosa.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
# Twinkle Twinkle Little Star (pubblico dominio): semitoni sopra il Do
MEL = [0, 0, 7, 7, 9, 9, 7, None, 5, 5, 4, 4, 2, 2, 0]
NOTA = 0.42
OTTAVE = [1, -1, 1, 0, -1, 1, 0, None, -1, 1, 0, -1, 1, -1, 0]   # sparpagliate a mano: mai due vicine uguali
C4 = 261.63

GIRO1, CHI, TITOLO, NORMALE, GIRO2, SPIEGA, FINE, END = 0.6, 7.2, 10.0, 12.4, 19.2, 25.8, 31.4, 38.8


def piano(f, d):
    n = int(d * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.6 for h in range(1, 6))
    env = np.minimum(1, t / 0.006) * np.exp(-t * 3.2) * np.clip((d - t) / 0.03, 0, 1)
    return x * env


def eventi(t0, sparse):
    ev = []
    for i, (s, o) in enumerate(zip(MEL, OTTAVE)):
        if s is not None:
            ev.append((t0 + i * NOTA, s + (12 * o if sparse else 0)))
    return ev


EV = [(GIRO1, eventi(GIRO1, True)), (NORMALE, eventi(NORMALE, False)), (GIRO2, eventi(GIRO2, True)),
      (FINE + 0.3, eventi(FINE + 0.3, True))]


def build():
    a = np.zeros(int(END * SR) + SR)
    for _, ev in EV:
        for t, s in ev:
            x = piano(C4 * 2 ** (s / 12), NOTA * 1.6)
            i = int(t * SR)
            a[i:i + len(x)] += x
    return a[:int(END * SR)] * 0.35


def rullo(c, y, t, k=1.0):
    """Le note come punti: altezza = nota reale (con l'ottava), quella che suona si accende."""
    giro = max((g for g in EV if g[0] - 0.3 <= t), key=lambda g: g[0], default=EV[0])
    ev = giro[1]
    x0, x1 = 120, W - 120
    for i, (tt, s) in enumerate(ev):
        x = x0 + (x1 - x0) * i / (len(ev) - 1)
        yy = y - s * 9
        on = tt <= t < tt + NOTA
        past = tt <= t
        col = WHITE if on else (style.PINK if past else (70, 66, 78))
        r = 18 if on else 12
        c.ellipse((x - r, yy - r, x + r, yy + r), fill=fade(col, k))
    c.line([(x0 - 20, y + 140), (x1 + 20, y + 140)], fill=fade(LINE, k), width=2)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < CHI:
        c.kicker(0, 300, "YOU KNOW THIS SONG", center=True)
        centered(c, 360, "CAN YOU", 160, WHITE)
        centered(c, 520, "NAME IT?", 160, style.PINK)
        rullo(c, 980, t)
        centered(c, 1240, "EVERYONE HAS HEARD IT", 30, MUTED, "sans", 700, 4)
        return
    if t < TITOLO:
        centered(c, 520, "NO IDEA?", 190, fade(WHITE, k(CHI)))
        centered(c, 720, "HERE IT IS.", 110, fade(style.PINK, k(CHI + 0.8)))
        return
    if t < GIRO2:
        c.kicker(0, 300, "THE SAME NOTES, IN ONE OCTAVE", center=True)
        centered(c, 360, "TWINKLE TWINKLE", 130, fade(WHITE, k(TITOLO)))
        centered(c, 490, "LITTLE STAR.", 130, fade(style.PINK, k(TITOLO + 0.2)))
        if t >= NORMALE - 0.3:
            rullo(c, 1000, t)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "THE FIRST VERSION AGAIN", center=True)
        centered(c, 360, "NOW YOU", 160, fade(WHITE, k(GIRO2)))
        centered(c, 520, "HEAR IT.", 160, fade(style.PINK, k(GIRO2 + 0.2)))
        rullo(c, 980, t)
        centered(c, 1240, "SAME RANDOM OCTAVES AS BEFORE", 30, MUTED, "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "MYSTERIOUS MELODY", center=True)
        centered(c, 360, "THE NOTES", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "WERE RIGHT.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Every note had the right name,",
                           "but in a random octave.",
                           "Without the ups and downs of the tune,",
                           "your brain can't find the song.",
                           "Once you know what it is, it fills it in.",
                           "",
                           "· Diana Deutsch · 1972"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "SEND IT TO A FRIEND.", 120, fade(WHITE, k(FINE)))
    centered(c, 540, "DON'T TELL THEM", 120, fade(WHITE, k(FINE + 0.2)))
    centered(c, 680, "THE TITLE.", 120, fade(style.PINK, k(FINE + 0.4)))
    rullo(c, 1040, t, k=k(FINE + 0.3, 0.4))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "melodia-misteriosa.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=71)
    print("scritto", out)
