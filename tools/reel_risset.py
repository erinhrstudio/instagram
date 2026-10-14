"""Reel "il beat che accelera per sempre" (ritmo di Risset): il gemello ritmico della scala infinita.

Più strati dello stesso battito, ognuno al doppio della velocità del precedente, accelerano insieme.
Il volume di ogni strato dipende dalla sua velocità: i più veloci svaniscono, i più lenti entrano
piano. Così il beat sembra accelerare senza mai arrivare da nessuna parte.

Uso: python -m tools.reel_risset media/tiktok/beat-infinito.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
P = 7.0                       # secondi per raddoppiare la velocità
B = 1.6                       # battiti al secondo dello strato di riferimento all'inizio (96 BPM)
CENTER, SIGMA = np.log2(3.2), 0.9
SPIEGA, FINE, END = 16.0, 22.0, 27.0


def click(rng):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (60 + 90 * np.exp(-t / 0.015)) * t) * np.exp(-t / 0.035)
    hat = rng.standard_normal(n) * np.exp(-t / 0.008) * 0.35
    return thump + hat


def build():
    rng = np.random.default_rng(5)
    k = click(rng)
    a = np.zeros(int(END * SR) + len(k))
    for j in range(-5, 4):
        rate0 = B * 2.0 ** j
        n_beats = int(rate0 * P / np.log(2) * (2 ** (END / P) - 1)) + 1
        for m in range(1, n_beats + 1):
            # tempo del battito m: rate0 * P/ln2 * (2^(t/P) - 1) = m
            t = P * np.log2(1 + m * np.log(2) / (rate0 * P))
            if t >= END:
                break
            rate = rate0 * 2 ** (t / P)
            g = np.exp(-((np.log2(rate) - CENTER) ** 2) / (2 * SIGMA ** 2))
            if g < 0.01:
                continue
            i = int(t * SR)
            a[i:i + len(k)] += g * k
    a = a[:int(END * SR)]
    a[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    a[-int(0.5 * SR):] *= np.linspace(1, 0, int(0.5 * SR))
    return a


def bpm_finto(t):
    """Il BPM che percepiamo: sale sempre."""
    return 96 * 2 ** (t / P)


def gauge(c, cy, t, k=1.0):
    """Contagiri: la lancetta gira e il numero sale."""
    r = 190
    c.ellipse((W / 2 - r, cy - r, W / 2 + r, cy + r), outline=fade(LINE, k), width=3)
    ang = 2 * np.pi * (t / P) - np.pi / 2
    x, y = W / 2 + np.cos(ang) * (r - 24), cy + np.sin(ang) * (r - 24)
    c.line([(W / 2, cy), (x, y)], fill=fade(style.PINK, k), width=8)
    c.ellipse((W / 2 - 14, cy - 14, W / 2 + 14, cy + 14), fill=fade(style.PINK, k))
    c.text((W / 2, cy + r + 70), f"{bpm_finto(t):.0f} BPM", font("display", 90), fill=fade(WHITE, k), anchor="mm")


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "ASCOLTA IL BEAT", center=True)
        centered(c, 360, "ACCELERA.", 160, WHITE)
        centered(c, 520, "PER SEMPRE.", 160, style.PINK)
        gauge(c, 870, t)
        centered(c, 1240, "QUANDO SI FERMA?", 30, MUTED, "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "RITMO DI RISSET", center=True)
        centered(c, 360, "NON ACCELERA.", 140, fade(WHITE, k(SPIEGA)))
        centered(c, 500, "GIRA IN TONDO.", 140, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 710, ["Sono tanti strati dello stesso beat,",
                           "ognuno veloce il doppio dell'altro.",
                           "I più veloci svaniscono, i più lenti entrano",
                           "piano: l'orecchio segue solo chi accelera.",
                           "È il gemello della scala infinita.",
                           "",
                           "· Jean-Claude Risset"], SPIEGA + 0.5, k)
        return
    centered(c, 400, f"{bpm_finto(SPIEGA):.0f} BPM?", 170, fade(WHITE, k(FINE)))
    centered(c, 580, "È SEMPRE LO STESSO GIRO.", 110, fade(style.PINK, k(FINE + 0.3)))
    centered(c, 760, "MANDALO AL TUO BATTERISTA", 50, fade(TEXT, k(FINE + 0.8)), "sans", 700, 3)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "beat-infinito.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=60)
    print("scritto", out)
