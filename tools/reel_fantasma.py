"""Reel "che parola senti?" (trasformazioni verbali, Warren 1961; parole fantasma, Diana Deutsch).

Due sillabe, RO e MA, ripetute senza pause con intonazione piatta. Ascoltandole a lungo
il cervello cambia parola da solo: Roma, amor, mora, ramo... ognuno ne sente di diverse.

Uso: python -m tools.reel_fantasma media/tiktok/parole-fantasma.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4
from tools.voce import pho_audio

ROOT = Path(__file__).resolve().parent.parent
CICLO = [("r", 55), ("o", 175), ("m", 75), ("a", 175)]     # 0.48 s per "roma"
VOCE_VERA = ROOT / "posts" / "parole-fantasma" / "roma_giuseppe.wav"   # un solo "roma" detto da Giuseppe
if VOCE_VERA.exists():
    from scipy.io import wavfile
    _sr, _v = wavfile.read(VOCE_VERA)
    PAROLA = _v.astype(float) / 32768
    GIRO = (len(PAROLA) - int(0.01 * SR)) / SR
else:
    PAROLA = None
    GIRO = sum(d for _, d in CICLO) / 1000
LOOP1, SPIEGA, LOOP2, END = 0.0, 16.3, 21.6, 27.0
PAROLE = ["ROMA", "AMOR", "MORA", "RAMO", "ORA", "AROMA"]


def loop_vero(dur):
    """Lo stesso identico "roma" ripetuto, con 10 ms di dissolvenza tra una ripetizione e l'altra."""
    xf = int(0.01 * SR)
    passo = len(PAROLA) - xf
    n = int(dur * SR / passo) + 2
    x = np.zeros(passo * n + xf)
    w = np.ones(len(PAROLA))
    w[:xf] = np.linspace(0, 1, xf)
    w[-xf:] = np.linspace(1, 0, xf)
    for k in range(n):
        x[k * passo:k * passo + len(PAROLA)] += PAROLA * w
    x = x[:int(dur * SR)]
    r = int(0.03 * SR)
    x[:r] *= np.linspace(0, 1, r)
    x[-r:] *= np.linspace(1, 0, r)
    return x / np.abs(x).max() * 0.8


def loop(dur):
    if PAROLA is not None:
        return loop_vero(dur)
    n = int(dur / GIRO) + 2
    righe = ["_ 30"]
    for _ in range(n):
        for p, d in CICLO:
            righe.append(f"{p} {d} 0 118 100 118" if p in "oa" else f"{p} {d}")
    righe.append("_ 30")
    x = pho_audio("\n".join(righe) + "\n")
    x = x[int(0.03 * SR):int(0.03 * SR) + int(dur * SR)]
    r = int(0.03 * SR)
    x[:r] *= np.linspace(0, 1, r)
    x[-r:] *= np.linspace(1, 0, r)
    return x / np.abs(x).max() * 0.8


def build():
    a = np.zeros(int(END * SR))
    for t0, t1 in [(LOOP1, SPIEGA - 0.3), (LOOP2, END - 0.1)]:
        x = loop(t1 - t0)
        i = int(t0 * SR)
        a[i:i + len(x)] = x
    return a


def pulse(c, cy, t, k=1.0):
    p = 0.5 + 0.5 * np.cos(2 * np.pi * (t % GIRO) / GIRO)
    r = 70 + 26 * p
    c.ellipse((W / 2 - r, cy - r, W / 2 + r, cy + r), outline=fade(style.PINK, k), width=4)
    c.ellipse((W / 2 - 18, cy - 18, W / 2 + 18, cy + 18), fill=fade(style.PINK, k * (0.4 + 0.6 * p)))


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "ASCOLTA FINO ALLA FINE", center=True)
        centered(c, 360, "CHE PAROLA", 160, WHITE)
        centered(c, 520, "SENTI?", 160, style.PINK)
        pulse(c, 900, t)
        if t > 7.5:
            centered(c, 1120, "È ANCORA LA STESSA?", 70, fade(TEXT, k(7.5, 0.5)))
        centered(c, 1240, "TIENILA A MENTE", 30, MUTED, "sans", 700, 4)
        return
    if t < LOOP2:
        c.kicker(0, 300, "LA VERITÀ", center=True)
        centered(c, 360, "SOLO DUE SILLABE:", 120, fade(WHITE, k(SPIEGA)))
        centered(c, 490, "RO · MA", 170, fade(style.PINK, k(SPIEGA + 0.2)))
        for i, p in enumerate(PAROLE):
            x = W / 2 + (i % 3 - 1) * 290
            y = 790 + (i // 3) * 110
            c.text((x, y), p, font("display", 80), fill=fade(TEXT, k(SPIEGA + 0.6 + 0.25 * i)), anchor="mm")
        paragraph(c, 1020, ["Ripetute senza pause, il cervello",
                            "cerca un significato e cambia parola da solo.",
                            "",
                            "· Warren 1961 · Diana Deutsch, parole fantasma"], SPIEGA + 2.0, k)
        return
    centered(c, 400, "SCRIVI LA TUA", 160, fade(WHITE, k(LOOP2)))
    centered(c, 560, "NEI COMMENTI.", 160, fade(WHITE, k(LOOP2 + 0.2)))
    centered(c, 730, "QUANTE NE HAI SENTITE?", 100, fade(style.PINK, k(LOOP2 + 0.4)))
    pulse(c, 1030, t, k=k(LOOP2 + 0.6, 0.5))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "parole-fantasma.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=58)
    print("scritto", out)
