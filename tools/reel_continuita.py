"""Reel "il tono che non si ferma" (illusione di continuità / induzione uditiva,
Warren, Obusek & Ackroff 1972).

Un glissando a pezzi con buchi di silenzio suona spezzato. Riempi i buchi con un rumore più forte
e lo senti continuare sotto il rumore, anche se nei buchi il tono non c'è.

Uso: python -m tools.reel_continuita media/tiktok/continuita.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
LUNGO, ON, OFF = 4.0, 0.30, 0.17           # durata di un giro, pezzo di tono, buco
GIRO_A, GIRO_B = 1.0, 6.0
CHIEDI, RIVELA = 10.4, 13.0
GIRO_C = RIVELA + 0.8
SPIEGA = GIRO_C + LUNGO + 1.0
CTA, END = SPIEGA + 6.8, SPIEGA + 13.3


def freq(t):
    return 850 + 350 * np.sin(2 * np.pi * t / 2.0)        # sale e scende, un giro ogni 2 s


def buchi(t):
    """True dove il tono tace."""
    return (t % (ON + OFF)) >= ON


def giro(rumore):
    n = int(LUNGO * SR)
    t = np.arange(n) / SR
    fase = 2 * np.pi * np.cumsum(freq(t)) / SR
    gate = (~buchi(t)).astype(float)
    k = int(0.008 * SR)                                      # bordi morbidi, niente click
    gate = np.convolve(gate, np.ones(k) / k, mode="same")
    x = np.sin(fase) * gate * 0.35
    if rumore:
        X = np.fft.rfft(np.random.default_rng(3).standard_normal(n))
        f = np.fft.rfftfreq(n, 1 / SR)
        X[(f < 250) | (f > 4000)] = 0
        noise = np.fft.irfft(X, n)
        noise /= np.abs(noise).max()
        x += noise * (1 - gate) * 0.9
    return x


def build():
    a = np.zeros(int(END * SR) + SR)
    for t0, r in [(GIRO_A, False), (GIRO_B, True), (GIRO_C, True)]:
        x = giro(r); j = int(t0 * SR); a[j:j + len(x)] += x
    return a[:int(END * SR)]


def quale(t):
    for t0, nome in [(GIRO_A, "A"), (GIRO_B, "B"), (GIRO_C, "C")]:
        if t0 <= t < t0 + LUNGO:
            return nome, t - t0
    return None, 0


def linea(c, y, k=1.0, fino=LUNGO):
    """Il tono (rosa) a pezzi e i buchi (grigi, pieni di rumore), fino al punto ascoltato."""
    x0, x1 = 120, W - 120
    ts = np.linspace(0, LUNGO, 900)
    for a_, b_ in zip(ts[:-1], ts[1:]):
        if a_ > fino:
            break
        xa, xb = x0 + (x1 - x0) * a_ / LUNGO, x0 + (x1 - x0) * b_ / LUNGO
        if buchi(a_):
            c.rect((xa, y - 260, xb + 1, y + 20), fill=fade((62, 60, 70), k))
        else:
            ya, yb = y - 120 - (freq(a_) - 850) / 3, y - 120 - (freq(b_) - 850) / 3
            c.line([(xa, ya), (xb, yb)], fill=fade(style.PINK, k), width=8)
    c.text((x0, y + 50), "TONE", style.font("sans", 24, 700), fill=fade(style.PINK, k), tracking=4)
    c.text((x1, y + 50), "NOISE, NO TONE", style.font("sans", 24, 700), fill=fade(MUTED, k), anchor="ra",
           tracking=4)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    nome, dt = quale(t)
    if t < CHIEDI:
        c.kicker(0, 300, "HEADPHONES ON", center=True)
        centered(c, 360, "DOES IT", 160, WHITE)
        centered(c, 520, "EVER STOP?", 160, style.PINK)
        lab = {"A": "A · THE TONE WITH GAPS", "B": "B · THE SAME TONE, GAPS FILLED WITH NOISE"}.get(nome, "")
        if nome:
            r = 60 + 25 * np.sin(dt * 2 * np.pi * 2)
            c.ellipse((W / 2 - r, 900 - r, W / 2 + r, 900 + r), outline=style.PINK, width=6)
        centered(c, 1060, lab, 30, MUTED, "sans", 700, 4)
        return
    if t < RIVELA:
        centered(c, 460, "IN B, DID THE TONE", 120, fade(WHITE, k(CHIEDI)))
        centered(c, 600, "KEEP GOING?", 120, fade(style.PINK, k(CHIEDI + 0.2)))
        centered(c, 820, "COMMENT YES OR NO", 40, fade(TEXT, k(CHIEDI + 0.5)), "sans", 700, 4)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "B AGAIN, WITH THE PICTURE", center=True)
        centered(c, 360, "IT STOPPED", 150, fade(WHITE, k(RIVELA)))
        centered(c, 510, "EVERY TIME.", 150, fade(style.PINK, k(RIVELA + 0.2)))
        linea(c, 1080, k(RIVELA + 0.3), fino=dt if nome == "C" else (LUNGO if t > GIRO_C else 0))
        return
    if t < CTA:
        c.kicker(0, 300, "AUDITORY INDUCTION", center=True)
        centered(c, 360, "YOUR BRAIN", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "FILLED THE GAPS.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Under each burst of noise there was silence.",
                           "But a loud noise could have hidden the tone,",
                           "so your brain assumes it kept going",
                           "and plays you the missing pieces.",
                           "It's how you follow a voice in a noisy room.",
                           "",
                           "· Warren, Obusek & Ackroff · 1972"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "SEND IT TO A FRIEND.", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "DID THEY HEAR", 120, fade(WHITE, k(CTA + 0.2)))
    centered(c, 680, "THE GAPS?", 120, fade(style.PINK, k(CTA + 0.4)))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "continuita.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=75, picco=0.7)
    print("scritto", out)
