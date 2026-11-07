"""Reel "davanti o dietro?" (bande direzionali, Jens Blauert 1969).

Tre rumori a banda stretta (terzo d'ottava), identici nelle due orecchie: cambia solo la banda.
Molti li sentono in posti diversi: 4 kHz davanti, 1 kHz dietro, 8 kHz sopra (Blauert 1969,
replicato in parte da Aalto ICA 2022: sopra e dietro sì, davanti più sfumato). Non tutti
sentono lo stesso, ed è il gancio per confrontare.

Uso: python -m tools.reel_direzione media/tiktok/davanti-dietro.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
SUONI = [("A", 4000, 0.55), ("B", 1000, 1.0), ("C", 8000, 0.8)]   # lettera, centro banda, guadagno
TIPICO = {"A": "FRONT", "B": "BEHIND", "C": "ABOVE"}
COLPO, PAUSA_COLPO, GRUPPO = 0.35, 0.15, 3.0
GIRO1, GIRO2 = 1.0, 10.4
VOTA, RIVELA, SPIEGA, CTA, END = 19.4, 22.0, 25.0, 32.0, 38.5
CY = 1060
POS = {"FRONT": (W / 2 + 270, CY), "BEHIND": (W / 2 - 270, CY), "ABOVE": (W / 2, CY - 270)}


def banda(fc, d, seed):
    n = int(d * SR)
    x = np.random.default_rng(seed).standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X[(f < fc * 2 ** (-1 / 6)) | (f > fc * 2 ** (1 / 6))] = 0     # terzo d'ottava
    y = np.fft.irfft(X, n)
    t = np.arange(n) / SR
    y *= np.clip(np.minimum(t, d - t) / 0.02, 0, 1)
    return y / np.sqrt(np.mean(y ** 2))


def colpi(t0):
    """(inizio, lettera) di ogni gruppo di tre colpi."""
    return [(t0 + i * GRUPPO, s) for i, s in enumerate(SUONI)]


GRUPPI = colpi(GIRO1) + colpi(GIRO2)


def build():
    a = np.zeros(int(END * SR) + SR)
    for g, (t0, (_, fc, gain)) in enumerate(GRUPPI):
        for j in range(3):
            x = banda(fc, COLPO, seed=g * 10 + j) * gain
            i = int((t0 + j * (COLPO + PAUSA_COLPO)) * SR)
            a[i:i + len(x)] += x
    return a[:int(END * SR)]


def suona(t):
    for t0, s in GRUPPI:
        if t0 <= t < t0 + 3 * (COLPO + PAUSA_COLPO):
            on = ((t - t0) % (COLPO + PAUSA_COLPO)) < COLPO
            return s[0], on
    return None, False


def testa(c, t, k=1.0, accese=()):
    cx, cy = W / 2, CY
    c.ellipse((cx - 130, cy - 150, cx + 130, cy + 150), outline=fade(LINE, k), width=3)
    c.d.polygon([(x * style.S, y * style.S) for x, y in [(cx + 128, cy - 30), (cx + 165, cy + 10), (cx + 128, cy + 30)]],
                fill=fade(LINE, k))  # naso: davanti
    c.ellipse((cx - 22, cy - 34, cx + 22, cy + 34), outline=fade(MUTED, k), width=3)              # orecchio
    for nome, (x, y) in POS.items():
        on = nome in accese
        r = 30 if on else 16
        c.ellipse((x - r, y - r, x + r, y + r), fill=fade(style.PINK if on else (70, 66, 78), k))
        if nome == "ABOVE":
            c.text((x + 50, y - 14), nome, style.font("sans", 26, 700), fill=fade(TEXT if on else MUTED, k),
                   tracking=4)
        else:
            c.text((x, y + 50), nome, style.font("sans", 26, 700), fill=fade(TEXT if on else MUTED, k),
                   anchor="ma", tracking=4)
    lettera, on = suona(t)
    if lettera:
        c.text((cx, cy), lettera, style.font("display", 120), fill=WHITE if on else fade(WHITE, 0.6), anchor="mm")


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < VOTA:
        c.kicker(0, 300, "HEADPHONES ON · EYES CLOSED", center=True)
        centered(c, 360, "IN FRONT", 160, WHITE)
        centered(c, 520, "OR BEHIND?", 160, style.PINK)
        testa(c, t)
        centered(c, 1300, "WHERE IS A? WHERE IS B? WHERE IS C?" if t < GIRO2 else "ONE MORE TIME",
                 30, MUTED, "sans", 700, 4)
        return
    if t < RIVELA:
        centered(c, 500, "COMMENT", 170, fade(WHITE, k(VOTA)))
        centered(c, 680, "A, B AND C.", 170, fade(style.PINK, k(VOTA + 0.2)))
        centered(c, 920, "FRONT · BEHIND · ABOVE", 40, fade(TEXT, k(VOTA + 0.5)), "sans", 700, 4)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "THE TRICK", center=True)
        centered(c, 360, "SAME SPOT.", 160, fade(WHITE, k(RIVELA)))
        centered(c, 520, "ALL THREE.", 160, fade(style.PINK, k(RIVELA + 0.2)))
        centered(c, 1300, "Same sound in both ears. Only the pitch changed.", 38, fade(TEXT, k(RIVELA + 0.6)), "sans")
        testa(c, t, k(RIVELA + 0.3))
        return
    if t < CTA:
        c.kicker(0, 300, "DIRECTIONAL BANDS", center=True)
        centered(c, 360, "YOUR EAR", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "GUESSED.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Your outer ear colours sound differently",
                           "from every direction. With no real clue,",
                           "your brain reads the pitch band as one:",
                           "A (4 kHz) front, B (1 kHz) behind,",
                           "C (8 kHz) above, for most people.",
                           "",
                           "· Jens Blauert · 1969"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "SEND IT TO A FRIEND.", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "SAME PLACES", 120, fade(WHITE, k(CTA + 0.2)))
    centered(c, 680, "FOR BOTH OF YOU?", 120, fade(style.PINK, k(CTA + 0.4)))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "davanti-dietro.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=73, picco=0.5)
    print("scritto", out)
