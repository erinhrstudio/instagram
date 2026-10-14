"""Reel "il rumore che diventa nota" (rumore ripetuto, Guttman e Julesz 1963).

Un pezzetto di rumore sempre uguale, ripetuto in loop sempre più corto: prima è un fruscio,
poi un ritmo, poi un ronzio e infine una nota. Il suono non cambia: cambia solo quanto è lungo il loop.

Uso: python -m tools.reel_rumore_nota media/tiktok/rumore-nota.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
# (lunghezza del loop in secondi, come lo senti)
FASI = [(1.0, "FRUSCIO"), (0.25, "RITMO"), (0.1, "RITMO VELOCE"), (0.04, "RONZIO"),
        (0.01, "NOTA · 100 Hz"), (0.005, "NOTA · 200 Hz"), (0.0025, "NOTA · 400 Hz")]
FASE = 2.2
SPIEGA = len(FASI) * FASE + 0.3
FINE, END = SPIEGA + 6.0, SPIEGA + 10.8


def build():
    rng = np.random.default_rng(21)
    master = rng.standard_normal(SR)                 # un secondo di rumore: tutti i loop ne prendono l'inizio
    a = np.zeros(int(END * SR))
    for i, (L, _) in enumerate(FASI):
        n = int(L * SR)
        seg = np.tile(master[:n], int(np.ceil(FASE * SR / n)))[:int(FASE * SR)]
        r = int(0.01 * SR)
        seg[:r] *= np.linspace(0, 1, r)
        seg[-r:] *= np.linspace(1, 0, r)
        a[int(i * FASE * SR):int(i * FASE * SR) + len(seg)] = seg
    # finale: di nuovo dal fruscio alla nota, più veloce
    t0 = FINE + 0.5
    for i, (L, _) in enumerate(FASI):
        n = int(L * SR)
        d = 0.6
        seg = np.tile(master[:n], int(np.ceil(d * SR / n)))[:int(d * SR)]
        i0 = int((t0 + i * d) * SR)
        if i0 + len(seg) <= len(a):
            a[i0:i0 + len(seg)] = seg
    return a / np.abs(a).max() * 0.5


def loopbar(c, y, L, t, k=1.0):
    """Il pezzetto di rumore (sempre lo stesso) e quante volte si ripete in un secondo."""
    x0, x1 = 140, W - 140
    rng = np.random.default_rng(21)
    shape = rng.random(80)
    reps = max(1, int(round(1 / L)))
    show = min(reps, 40)
    span = (x1 - x0) / show
    for r in range(show):
        xa = x0 + r * span
        col = style.PINK if r == 0 else (120, 116, 128)
        m = max(2, int(span // 6)) if show > 1 else 80
        m = min(m, 80)
        bw = span / m
        for j in range(m):
            h = (12 + 60 * shape[j % 80]) * k
            c.rect((xa + j * bw + 0.5, y - h, xa + (j + 1) * bw - 0.5, y + h), fill=fade(col, k))
        if show > 1:
            c.line([(xa, y - 90), (xa, y + 90)], fill=fade(LINE, k), width=2)
    lab = f"{L * 1000:.1f} ms" if L < 0.01 else f"{L * 1000:.0f} ms"
    c.text((W / 2, y + 140), f"LOOP DA {lab}  ·  {1 / L:.0f} VOLTE AL SECONDO".replace("·  1 VOLTE", "·  1 VOLTA"),
           font("sans", 28, 700), fill=fade(MUTED, k), anchor="mm", tracking=3)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        i = min(int(t // FASE), len(FASI) - 1)
        L, nome = FASI[i]
        c.kicker(0, 300, "SEMPRE LO STESSO RUMORE", center=True)
        centered(c, 360, "ACCORCIO", 150, WHITE)
        centered(c, 510, "IL LOOP.", 150, style.PINK)
        loopbar(c, 860, L, t)
        centered(c, 1140, nome, 90, fade(WHITE, k(i * FASE, 0.3)))
        return
    if t < FINE:
        c.kicker(0, 300, "RUMORE RIPETUTO", center=True)
        centered(c, 360, "UNA NOTA", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "È UNA RIPETIZIONE.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Se lo stesso suono si ripete più di",
                           "20-30 volte al secondo, il cervello",
                           "smette di sentire le ripetizioni",
                           "e sente un'altezza: una nota.",
                           "Anche se il suono è puro rumore.",
                           "",
                           "· Guttman e Julesz · 1963"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "PER CHI PRODUCE:", 120, fade(WHITE, k(FINE)))
    centered(c, 540, "UN LOOP CORTISSIMO", 110, fade(style.PINK, k(FINE + 0.2)))
    centered(c, 660, "È UN SYNTH.", 110, fade(style.PINK, k(FINE + 0.4)))
    centered(c, 800, "PROVALO COL TUO SAMPLER E SALVALO", 40, fade(TEXT, k(FINE + 0.8)), "sans", 700, 3)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "rumore-nota.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=61)
    print("scritto", out)
