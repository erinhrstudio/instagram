"""Reel "Which one is Bouba?" (effetto bouba/kiki).

Due forme (una tonda, una a punte) e due parole dette dalla voce sintetica: "bouba" e "kiki".
Fatti: Ramachandran & Hubbard 2001, il 95% sceglie la forma tonda per "bouba";
uno studio del 2022 con 917 persone e 25 lingue conferma l'effetto sopra il caso.
Prima ancora Köhler (1929) con "takete" e "maluma" (Wikipedia, Bouba/kiki effect).

Uso: python -m tools.reel_bouba media/instagram/bouba-kiki.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, S
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4
from tools.voce import tts

ROOT = Path(__file__).resolve().parent.parent
T1, T2 = 1.2, 3.2
VOTO = 5.5
SPIEGA = VOTO + 3.5
CTA = SPIEGA + 8.0
END = CTA + 7.0


def build():
    a = np.zeros(int(END * SR) + SR)
    for t0, parola in ((T1, "buba"), (T2, "kiki"), (SPIEGA + 0.6, "buba"), (SPIEGA + 1.8, "kiki")):
        x, _ = tts(parola, speed=110)
        j = int(t0 * SR)
        a[j:j + len(x)] += x
    return a[:int(END * SR)]


def tonda(cx, cy, r):
    ang = np.linspace(0, 2 * np.pi, 200)
    rr = r * (1 + 0.16 * np.sin(5 * ang) + 0.05 * np.sin(3 * ang + 1))
    return [(cx + a * np.cos(b), cy + a * np.sin(b)) for a, b in zip(rr, ang)]


def punte(cx, cy, r):
    pts = []
    for i in range(18):
        b = 2 * np.pi * i / 18
        a = r * (1.1 if i % 2 == 0 else 0.45) * (1 + 0.12 * np.sin(i * 1.7))
        pts.append((cx + a * np.cos(b), cy + a * np.sin(b)))
    return pts


def forme(c, y, k=1.0, scelta=False):
    c.d.polygon([(a * S, b * S) for a, b in tonda(W / 2 - 220, y, 150)], fill=fade(style.PINK if scelta else WHITE, k))
    c.d.polygon([(a * S, b * S) for a, b in punte(W / 2 + 220, y, 170)], fill=fade(WHITE, k))
    c.text((W / 2 - 220, y + 210), "1", style.font("display", 80), fill=fade(MUTED, k), anchor="ma")
    c.text((W / 2 + 220, y + 210), "2", style.font("display", 80), fill=fade(MUTED, k), anchor="ma")


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "TRUST YOUR FIRST INSTINCT", center=True)
        centered(c, 360, "WHICH ONE", 150, WHITE)
        centered(c, 510, "IS BOUBA?", 150, style.PINK)
        forme(c, 920)
        if t >= VOTO:
            centered(c, 1240, "COMMENT 1 OR 2", 32, MUTED, "sans", 700, 4)
        return
    if t < CTA:
        c.kicker(0, 300, "THE BOUBA / KIKI EFFECT", center=True)
        centered(c, 360, "95% SAY", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "THE ROUND ONE.", 140, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Round sounds go with round shapes,",
                           "sharp sounds with sharp ones.",
                           "In 2001, 95% of people matched them this way.",
                           "A 2022 study across 25 languages",
                           "found it well above chance too.",
                           "",
                           "Sounds carry shape, before any meaning.",
                           "",
                           "· Ramachandran & Hubbard 2001 · Köhler 1929"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "ARE YOU IN", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "THE OTHER 5%?", 120, fade(style.PINK, k(CTA + 0.2)))
    forme(c, 880, k=k(CTA + 0.3, 0.4), scelta=True)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "bouba-kiki.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=89, picco=0.85)
    print("scritto", out)
