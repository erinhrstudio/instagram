"""Reel "fin dove senti ancora?" (test dell'udito sugli acuti).

Toni puri che salgono da 8.000 a 19.000 Hz: chi guarda scrive nei commenti l'ultimo che sente.
Onesto sui limiti: telefono, auricolari e compressione dell'app possono tagliare gli acuti.
Nessuna tabella "età dell'udito": si dice solo che gli acuti si perdono per primi.

Uso: python -m tools.reel_udito media/tiktok/test-udito.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
FREQ = [8000, 10000, 12000, 14000, 15000, 16000, 17000, 18000, 19000]
T0, DUR, PASSO = 1.2, 1.3, 1.7
FINE_TONI = T0 + PASSO * len(FREQ)
SPIEGA, CTA, END = FINE_TONI + 0.4, FINE_TONI + 8.4, FINE_TONI + 15.4


def tono(f):
    n = int(DUR * SR)
    t = np.arange(n) / SR
    env = np.clip(np.minimum(t, DUR - t) / 0.04, 0, 1)   # rampe lente: niente click
    return np.sin(2 * np.pi * f * t) * env


def build():
    a = np.zeros(int(END * SR) + SR)
    for i, f in enumerate(FREQ):
        x = tono(f)
        j = int((T0 + i * PASSO) * SR)
        a[j:j + len(x)] += x
    return a[:int(END * SR)]


def attuale(t):
    i = int((t - T0) // PASSO)
    if 0 <= i < len(FREQ):
        return i, (t - T0 - i * PASSO) < DUR
    return (len(FREQ) - 1 if t >= FINE_TONI else -1), False


def scala(c, y, t, k=1.0):
    i, on = attuale(t)
    x0, x1 = 150, W - 150
    for j, f in enumerate(FREQ):
        x = x0 + (x1 - x0) * j / (len(FREQ) - 1)
        h = 40 + 26 * j
        col = WHITE if (j == i and on) else (style.PINK if j <= i else (70, 66, 78))
        c.rect((x - 26, y - h, x + 26, y), fill=fade(col, k), radius=6)
        c.text((x, y + 30), f"{f // 1000}K", style.font("sans", 24, 700), fill=fade(MUTED, k),
               anchor="ma", tracking=2)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "HEADPHONES ON · START AT LOW VOLUME", center=True)
        centered(c, 360, "HOW HIGH CAN", 150, WHITE)
        centered(c, 510, "YOU STILL HEAR?", 150, style.PINK)
        i, on = attuale(t)
        if i >= 0:
            centered(c, 760, f"{FREQ[i]:,} HZ", 170, WHITE if on else fade(WHITE, 0.5))
        scala(c, 1180, t)
        centered(c, 1290, "COMMENT THE LAST ONE YOU HEAR", 30, MUTED, "sans", 700, 4)
        return
    if t < CTA:
        c.kicker(0, 300, "WHY THE TOP GOES FIRST", center=True)
        centered(c, 360, "THE HIGHEST", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "GO FIRST.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["The cells that hear the highest pitches",
                           "sit at the entrance of the cochlea",
                           "and wear out first: with age,",
                           "and faster with loud music.",
                           "",
                           "Phones, cheap earbuds and app compression",
                           "can cut the top too. Try good headphones.",
                           "",
                           "· Presbycusis · high frequencies first"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "SEND IT TO A FRIEND.", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "WHO HEARS", 120, fade(WHITE, k(CTA + 0.2)))
    centered(c, 680, "HIGHER?", 120, fade(style.PINK, k(CTA + 0.4)))
    scala(c, 1080, FINE_TONI, k=k(CTA + 0.3, 0.4))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "test-udito.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=72, picco=0.25)
    print("scritto", out)
