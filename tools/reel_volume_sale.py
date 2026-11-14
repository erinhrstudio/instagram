"""Reel "Which one got louder?" (bias per i suoni che salgono, Neuhoff, Nature 1998).

A: un suono che scende di 15 dB in 2,5 secondi. B: lo stesso suono che SALE di 15 dB.
Stessa quantità di cambiamento, ma B sembra cambiare di più: il cervello tratta
quello che sale (che si avvicina) come più urgente.

Uso: python -m tools.reel_volume_sale media/instagram/volume-sale.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
DUR, DB = 2.5, 15.0
TA, TB = 1.0, 4.6
VOTO = TB + DUR + 0.3
SPIEGA = VOTO + 3.5
CTA = SPIEGA + 8.0
END = CTA + 7.0


def suono(sale):
    n = int(DUR * SR)
    t = np.arange(n) / SR
    f0 = 220.0
    x = sum(np.sin(2 * np.pi * f0 * h * t) / h for h in range(1, 9))   # timbro ricco, si sente anche sul telefono
    u = t / DUR
    db = (-DB + DB * u) if sale else (-DB * u)
    env = 10 ** (db / 20) * np.clip(np.minimum(t, DUR - t) / 0.03, 0, 1)
    return x * env


def build():
    a = np.zeros(int(END * SR) + SR)
    for t0, sale in ((TA, False), (TB, True)):
        x = suono(sale)
        j = int(t0 * SR)
        a[j:j + len(x)] += x
    return a[:int(END * SR)]


def barra(c, x, y0, y1, livello, k, lab, attivo):
    c.rect((x - 90, y0, x + 90, y1), outline=fade(LINE, k), width=2, radius=8)
    h = (y1 - y0) * livello
    if h > 2:
        c.rect((x - 84, y1 - h, x + 84, y1 - 6), fill=fade(WHITE if attivo else style.PINK, k), radius=6)
    c.text((x, y1 + 40), lab, style.font("display", 90), fill=fade(WHITE, k), anchor="ma")


def livello(t, t0, sale):
    u = min(1, max(0, (t - t0) / DUR))
    db = (-DB + DB * u) if sale else (-DB * u)
    return 0.15 + 0.8 * (1 + db / DB) if t >= t0 else 0.0


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "LISTEN TO BOTH", center=True)
        centered(c, 360, "WHICH ONE", 150, WHITE)
        centered(c, 510, "CHANGED MORE?", 150, style.PINK)
        mostra = t >= VOTO
        la = livello(t, TA, False) if (t < TA + DUR or mostra) else 0.0
        lb = livello(t, TB, True) if (t < TB + DUR or mostra) else 0.0
        barra(c, W / 2 - 200, 700, 1140, la if t >= TA else 0, 1, "A", TA <= t < TA + DUR)
        barra(c, W / 2 + 200, 700, 1140, lb if t >= TB else 0, 1, "B", TB <= t < TB + DUR)
        if mostra:
            centered(c, 1260, "COMMENT A OR B, THEN KEEP WATCHING", 30, MUTED, "sans", 700, 4)
        return
    if t < CTA:
        c.kicker(0, 300, "SAME CHANGE: 15 DB", center=True)
        centered(c, 360, "B FEELS", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "BIGGER.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["A went down by 15 dB. B went up by 15 dB.",
                           "Same sound, same amount of change.",
                           "Most people say B changed more.",
                           "",
                           "A sound getting louder may be coming",
                           "closer, so your brain gives it priority.",
                           "",
                           "· Neuhoff, Nature 1998 · bias for rising sounds"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "SEND IT TO SOMEONE.", 110, fade(WHITE, k(CTA)))
    centered(c, 530, "A OR B?", 140, fade(style.PINK, k(CTA + 0.2)))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "volume-sale.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=83, picco=0.85)
    print("scritto", out)
