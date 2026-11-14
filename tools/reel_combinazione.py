"""Reel "There are 2 notes. You hear 3." (toni di combinazione).

Nel file ci sono solo due toni puri: 1000 Hz fisso e uno che sale da 1100 a 1600 Hz.
L'orecchio interno non è lineare e ne crea un terzo, 2·f1 − f2, che SCENDE da 900 a 400 Hz.
I due toni sono in entrambi i canali (nello stesso orecchio), così funziona anche in cuffia.
Onesto: non tutti lo sentono, aiuta il volume un po' più alto.

Uso: python -m tools.reel_combinazione media/instagram/nota-fantasma.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
F1, F2A, F2B = 1000.0, 1100.0, 1600.0
T0, SWEEP = 0.3, 8.0
SPIEGA = T0 + SWEEP + 0.4
RIPETI = SPIEGA + 0.6          # i toni ripartono mentre leggi la spiegazione
CTA = RIPETI + SWEEP + 0.2
END = CTA + 7.0


def f2(t):
    u = np.clip((t - T0) / SWEEP, 0, 1)
    return F2A + (F2B - F2A) * u


def sweep():
    n = int(SWEEP * SR)
    t = np.arange(n) / SR
    fb = F2A + (F2B - F2A) * t / SWEEP
    ph = 2 * np.pi * np.cumsum(fb) / SR
    env = np.clip(np.minimum(t, SWEEP - t) / 0.08, 0, 1)
    return (np.sin(2 * np.pi * F1 * t) + np.sin(ph)) * 0.5 * env


def build():
    a = np.zeros(int(END * SR) + SR)
    x = sweep()
    for t0 in (T0, RIPETI):
        j = int(t0 * SR)
        a[j:j + len(x)] += x
    return a[:int(END * SR)]


def grafico(c, y0, y1, tnow, t0, k=1.0, fantasma=True):
    """Frequenza (verticale, 300-1700 Hz) nel tempo: due linee vere e una tratteggiata."""
    x0, x1 = 150, W - 150
    fy = lambda f: y1 - (f - 300) / 1400 * (y1 - y0)
    tx = lambda u: x0 + (x1 - x0) * u
    c.line([(x0, y1), (x1, y1)], fill=fade(LINE, k), width=2)
    for f in (400, 1000, 1600):
        c.text((x0 - 16, fy(f)), f"{f}", style.font("sans", 22, 600), fill=fade(MUTED, k), anchor="rm")
    u = float(np.clip((tnow - t0) / SWEEP, 0, 1))
    steps = max(2, int(u * 120))
    us = np.linspace(0, u, steps)
    f2s = F2A + (F2B - F2A) * us
    c.line([(tx(0), fy(F1)), (tx(u), fy(F1))], fill=fade(WHITE, k), width=6)
    c.line([(tx(a), fy(b)) for a, b in zip(us, f2s)], fill=fade(WHITE, k), width=6)
    c.text((x1 + 10, fy(F1)), "A", style.font("sans", 26, 700), fill=fade(WHITE, k), anchor="lm")
    c.text((x1 + 10, fy(F2B)), "B", style.font("sans", 26, 700), fill=fade(WHITE, k), anchor="lm")
    if fantasma and u > 0.15:
        kk = k * min(1, (u - 0.15) / 0.2)
        ph = 2 * F1 - f2s
        for i in range(0, steps - 1, 3):   # tratteggio
            c.line([(tx(us[i]), fy(ph[i])), (tx(us[i + 1]), fy(ph[i + 1]))],
                   fill=fade(style.PINK, kk), width=6)
        c.text((x1 + 10, fy(400)), "?", style.font("sans", 30, 700), fill=fade(style.PINK, kk), anchor="lm")


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "VOLUME UP · HEADPHONES OR SPEAKERS", center=True)
        centered(c, 360, "THERE ARE 2 NOTES.", 128, WHITE)
        centered(c, 500, "YOU HEAR 3.", 150, style.PINK)
        grafico(c, 760, 1180, t, T0, fantasma=t > T0 + 3.0)
        txt = "ONE STAYS. ONE RISES." if t < T0 + 3.0 else "HEAR THE ONE FALLING?"
        centered(c, 1240, txt, 34, MUTED, "sans", 700, 4)
        return
    if t < CTA:
        c.kicker(0, 300, "THE THIRD NOTE ISN'T IN THE FILE", center=True)
        centered(c, 360, "YOUR EAR", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "MAKES IT.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["The file has only two pure tones: A and B.",
                           "Your inner ear isn't perfectly linear,",
                           "so together they create new tones.",
                           "The loudest one is 2 x A minus B:",
                           "when B goes up, it comes down.",
                           "",
                           "Not everyone hears it. Listen again now.",
                           "",
                           "· Combination tones, or Tartini tones"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "DID YOU HEAR", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "THE THIRD ONE?", 120, fade(style.PINK, k(CTA + 0.2)))
    centered(c, 700, "YES OR NO IN THE COMMENTS", 34, fade(MUTED, k(CTA + 0.4)), "sans", 700, 4)
    grafico(c, 820, 1120, CTA, T0 - SWEEP, k=k(CTA + 0.3, 0.4))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "nota-fantasma.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=81, picco=0.5)
    print("scritto", out)
