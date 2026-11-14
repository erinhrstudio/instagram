"""Reel "Sweet or bitter? Same toffee." (suono e gusto, Crisinel & Spence, Oxford 2012).

A: suoni acuti, morbidi, da carillon. B: suoni gravi, da ottoni.
Nello studio la stessa caramella mou sembrava più dolce con la colonna sonora acuta
e più amara con quella grave. Qui facciamo votare: "quale è più dolce?".

Uso: python -m tools.reel_dolce media/instagram/dolce-amaro.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
TA, TB, DUR = 0.8, 5.6, 4.4
VOTO = TB + DUR + 0.2
SPIEGA = VOTO + 3.0
CTA = SPIEGA + 8.0
END = CTA + 7.0


def nota(f, dur, kind):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "dolce":   # carillon: poche armoniche, attacco netto, coda lunga
        x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.1 * np.sin(2 * np.pi * 3 * f * t)
        env = np.exp(-t * 3.0) * np.clip(t / 0.005, 0, 1)
    else:                 # ottone grave: tante armoniche, attacco lento
        x = sum(np.sin(2 * np.pi * f * h * t) / h ** 0.7 for h in range(1, 14))
        env = np.clip(t / 0.12, 0, 1) * np.clip((dur - t) / 0.15, 0, 1)
    return x * env


def build():
    a = np.zeros(int(END * SR) + SR)
    dolce = [1046.5, 1318.5, 1568.0, 2093.0, 1568.0, 1318.5, 1568.0, 2093.0]   # do maggiore, in alto
    for i, f in enumerate(dolce):
        x = nota(f, 1.2, "dolce") * 0.5
        j = int((TA + i * 0.5) * SR)
        a[j:j + len(x)] += x
    amaro = [(65.4, 77.8), (61.7, 73.4), (65.4, 77.8)]                        # bicordi gravi e tesi
    for i, (f1, f2) in enumerate(amaro):
        x = (nota(f1, 1.45, "amaro") + nota(f2, 1.45, "amaro")) * 0.35
        j = int((TB + i * 1.45) * SR)
        a[j:j + len(x)] += x
    return a[:int(END * SR)]


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "IMAGINE YOU'RE EATING A TOFFEE", center=True)
        centered(c, 360, "WHICH ONE", 150, WHITE)
        centered(c, 510, "TASTES SWEETER?", 140, style.PINK)
        for x, lab, t0 in ((W / 2 - 200, "A", TA), (W / 2 + 200, "B", TB)):
            on = t0 <= t < t0 + DUR
            r = 120 if on else 95
            col = style.PINK if on else (70, 66, 78)
            c.ellipse((x - r, 950 - r, x + r, 950 + r), outline=fade(col, 1), width=6)
            c.text((x, 950), lab, style.font("display", 120), fill=WHITE if on or t > t0 else MUTED, anchor="mm")
        if t >= VOTO:
            centered(c, 1240, "COMMENT A OR B", 32, MUTED, "sans", 700, 4)
        return
    if t < CTA:
        c.kicker(0, 300, "SOUND CHANGES TASTE", center=True)
        centered(c, 360, "SAME TOFFEE.", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "SWEETER WITH A.", 140, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["In an Oxford study, people ate the same",
                           "toffee while listening to two soundtracks.",
                           "With high, soft notes it tasted sweeter.",
                           "With low, brassy notes, more bitter.",
                           "",
                           "Your brain mixes what you hear",
                           "into what you taste.",
                           "",
                           "· Crisinel & Spence, 2012 · sonic seasoning"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "TRY IT WITH", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "YOUR NEXT SNACK.", 120, fade(style.PINK, k(CTA + 0.2)))
    centered(c, 700, "TELL ME IF IT WORKED", 32, fade(MUTED, k(CTA + 0.4)), "sans", 700, 4)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "dolce-amaro.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=87, picco=0.8)
    print("scritto", out)
