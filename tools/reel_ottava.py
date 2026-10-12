"""Reel "illusione dell'ottava" (Diana Deutsch, 1974): da ascoltare in cuffia.

Due note a un'ottava di distanza (400 e 800 Hz) si alternano ogni 250 ms, sempre in orecchi opposti:
quando a sinistra c'è l'acuta, a destra c'è la grave, e viceversa. Quasi nessuno lo sente così:
di solito si sente l'acuta in un orecchio e la grave nell'altro, che si alternano.

Uso: python -m tools.reel_ottava media/tiktok/ottava.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
LO, HI, STEP = 400.0, 800.0, 0.25
TEST, VOTA, RIVELA, SPIEGA, FINE, END = 0.0, 8.0, 10.4, 15.4, 20.4, 25.0


def stimulus(dur):
    """Restituisce (n, 2): a sinistra acuta-grave-acuta…, a destra grave-acuta-grave…"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = (t // STEP).astype(int)
    ph = t % STEP
    env = np.clip(np.minimum(ph / 0.005, (STEP - ph) / 0.005), 0, 1)
    left_hi = k % 2 == 0
    fl = np.where(left_hi, HI, LO)
    fr = np.where(left_hi, LO, HI)
    # fase continua per ciascun orecchio, così niente click tra una nota e l'altra
    l = np.sin(2 * np.pi * np.cumsum(fl) / SR) * env
    r = np.sin(2 * np.pi * np.cumsum(fr) / SR) * env
    return np.stack([l, r], 1)


def build():
    a = np.zeros((int(END * SR), 2))
    for t0, t1 in [(TEST, VOTA), (RIVELA, SPIEGA), (FINE + 1.0, END)]:
        s = stimulus(t1 - t0)
        a[int(t0 * SR):int(t0 * SR) + len(s)] = s
    return a * 0.7


def head(c, cy, show=None, t=0.0, k=1.0):
    """Testa vista da sopra. show=None: nessun indizio; altrimenti mostra cosa suona in ogni orecchio."""
    r = 150
    c.ellipse((W / 2 - r, cy - r, W / 2 + r, cy + r), outline=fade(LINE, k), width=3)
    for side, x in [(-1, W / 2 - r - 22), (1, W / 2 + r + 22)]:
        c.ellipse((x - 22, cy - 50, x + 22, cy + 50), outline=fade((120, 116, 128), k), width=3)
        lab = "SINISTRA" if side < 0 else "DESTRA"
        c.text((W / 2 + side * 330, cy + 205), lab, font("sans", 26, 700), fill=fade(MUTED, k),
               anchor="mm", tracking=4)
    if show is None:
        p = 0.5 + 0.5 * np.sin(t * 2 * np.pi * 2)
        rr = 30 + 14 * p
        c.ellipse((W / 2 - rr, cy - rr, W / 2 + rr, cy + rr), fill=fade(style.PINK, k * (0.5 + 0.5 * p)))
        return
    left_hi = int(show // STEP) % 2 == 0
    for side, hi in [(-1, left_hi), (1, not left_hi)]:
        x = W / 2 + side * 330
        y = cy - 70 if hi else cy + 70
        col = style.PINK if hi else (150, 146, 160)
        c.ellipse((x - 34, y - 34, x + 34, y + 34), fill=fade(col, k))
        c.text((x, y + (-62 if hi else 62)), "ACUTA" if hi else "GRAVE", font("sans", 24, 700),
               fill=fade(TEXT, k), anchor="mm", tracking=3)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < VOTA:
        c.kicker(0, 300, "SOLO IN CUFFIA", center=True)
        centered(c, 360, "DOVE SENTI", 150, WHITE)
        centered(c, 510, "LA NOTA ACUTA?", 150, style.PINK)
        head(c, 900, None, t)
        centered(c, 1232, "SINISTRA O DESTRA?", 30, MUTED, "sans", 700, 4)
        return
    if t < RIVELA:
        centered(c, 520, "SCRIVILO:", 180, fade(WHITE, k(VOTA)))
        centered(c, 700, "SINISTRA", 150, fade(style.PINK, k(VOTA + 0.3)))
        centered(c, 850, "O DESTRA?", 150, fade(style.PINK, k(VOTA + 0.3)))
        return
    if t < SPIEGA:
        c.kicker(0, 300, "COSA SUONA DAVVERO", center=True)
        centered(c, 360, "L'ACUTA SALTA", 140, fade(WHITE, k(RIVELA)))
        centered(c, 500, "DA UN LATO ALL'ALTRO.", 110, fade(style.PINK, k(RIVELA + 0.2)))
        head(c, 900, t - RIVELA, k=k(RIVELA + 0.3))
        centered(c, 1232, "OGNI QUARTO DI SECONDO", 30, fade(MUTED, k(RIVELA + 0.6)), "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "ILLUSIONE DELL'OTTAVA", center=True)
        centered(c, 360, "IL CERVELLO", 140, fade(WHITE, k(SPIEGA)))
        centered(c, 500, "SI INVENTA UNA NOTA.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Ogni orecchio riceve acuta e grave a turno.",
                           "Il cervello prende l'altezza da un orecchio",
                           "e la posizione dall'altro: senti un suono",
                           "che, così, non esiste.",
                           "",
                           "· Diana Deutsch · 1974"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "GIRA LE CUFFIE", 150, fade(WHITE, k(FINE)))
    centered(c, 550, "AL CONTRARIO.", 150, fade(WHITE, k(FINE + 0.2)))
    centered(c, 720, "L'ACUTA RESTA DOV'ERA?", 100, fade(style.PINK, k(FINE + 0.4)))
    head(c, 990, None, t, k=k(FINE + 0.8, 0.5))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "ottava.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=54)
    print("scritto", out)
