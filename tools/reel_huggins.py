"""Reel "melodia nascosta nel rumore" (Huggins pitch, Cramer e Huggins 1958): solo in cuffia.

Lo stesso rumore bianco arriva ai due orecchi. A destra, solo una fettina stretta di frequenze
è invertita di fase: in ogni orecchio da solo c'è soltanto rumore, ma il cervello confronta
i due lati e ci sente una nota. Spostando la fettina nota per nota, nel rumore compare "Fra Martino".

Uso: python -m tools.reel_huggins media/tiktok/melodia-nascosta.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
# Fra Martino in sol maggiore: (frequenza, durata)
G4, A4, B4, C5, D5 = 392.0, 440.0, 493.9, 523.3, 587.3
Q = 0.42
MELODY = [(G4, Q), (A4, Q), (B4, Q), (G4, Q)] * 2 + [(B4, Q), (C5, Q), (D5, 2 * Q)] * 2
MEL = sum(d for _, d in MELODY)                      # 6.72 s
ENTRAMBI, SINISTRO, ANCORA, SPIEGA, FINE = 0.0, MEL, 2 * MEL, 3 * MEL, 3 * MEL + 5.6
END = FINE + MEL + 0.6
BW = 0.04                                            # fettina invertita: ±4% intorno alla nota


def huggins(dur, rng):
    """(n, 2): rumore identico nei due orecchi, con la banda della nota invertita a destra."""
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    spec = np.fft.rfft(noise)
    f = np.fft.rfftfreq(n, 1 / SR)
    t = np.arange(n) / SR
    right = noise.copy()
    t0 = 0.0
    for fr in sorted({fr for fr, _ in MELODY}):
        band = np.fft.irfft(spec * ((f > fr * (1 - BW)) & (f < fr * (1 + BW))), n)
        env = np.zeros(n)
        t0 = 0.0
        for fk, d in MELODY:
            if fk == fr:
                # gate morbido (15 ms) e una piccola pausa tra le note uguali
                a = np.clip(np.minimum((t - t0) / 0.015, (t0 + d - 0.05 - t) / 0.015), 0, 1)
                env = np.maximum(env, a)
            t0 += d
        right -= 2 * env * band
    return np.stack([noise, right], 1)


def build():
    rng = np.random.default_rng(11)
    a = np.zeros((int(END * SR), 2))
    for t0, mono in [(ENTRAMBI, False), (SINISTRO, True), (ANCORA, False), (FINE, False)]:
        s = huggins(MEL, rng)
        if mono:
            s[:, 1] = 0                               # solo l'orecchio sinistro
        i = int(t0 * SR)
        a[i:i + len(s)] = s
    # dissolvenze brevi a ogni cambio, così non ci sono click
    for t0 in [ENTRAMBI, SINISTRO, ANCORA, SPIEGA, FINE]:
        i = int(t0 * SR); r = int(0.02 * SR)
        a[max(0, i - r):i] *= np.linspace(1, 0, min(r, i))[:, None] if i else 1
        a[i:i + r] *= np.linspace(0, 1, r)[:, None]
    return a * 0.25


def note_at(t):
    t0 = 0.0
    for k, (fr, d) in enumerate(MELODY):
        if t0 <= t < t0 + d:
            return k, fr
        t0 += d
    return None, None


def lanes(c, y, t, left=True, right=True, k=1.0):
    """Due tracce di rumore, sinistra e destra: sembrano uguali."""
    rng = np.random.default_rng(int(t * 30))
    for i, (lab, on) in enumerate([("SINISTRO", left), ("DESTRO", right)]):
        yy = y + i * 190
        c.text((W / 2, yy - 70), lab, font("sans", 24, 700), fill=fade(MUTED, k), anchor="mm", tracking=4)
        x0, x1, n = 150, W - 150, 60
        bw = (x1 - x0) / n
        for j in range(n):
            h = (10 + 34 * rng.random()) * k if on else 2
            c.rect((x0 + j * bw + 2, yy - h, x0 + (j + 1) * bw - 2, yy + h), fill=fade((120, 116, 128), 0.8 if on else 0.4))


def staff(c, y, t, k=1.0, show=True):
    """La melodia che il cervello ricostruisce: un pallino per nota, in alto le acute."""
    x0, x1 = 170, W - 170
    span = x1 - x0
    lo, hi = np.log(G4), np.log(D5)
    t0 = 0.0
    cur, _ = note_at(t % MEL)
    for idx, (fr, d) in enumerate(MELODY):
        x = x0 + (t0 + d / 2) / MEL * span
        yy = y + 60 - (np.log(fr) - lo) / (hi - lo) * 120
        on = show and idx == cur
        r = 22 if on else 12
        col = style.PINK if on else (90, 88, 98)
        if show and t0 <= (t % MEL):
            col = style.PINK if on else fade(style.PINK, 0.45)
        c.ellipse((x - r, yy - r, x + r, yy + r), fill=fade(col, k))
        t0 += d


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SINISTRO:
        c.kicker(0, 300, "SOLO IN CUFFIA", center=True)
        centered(c, 360, "È SOLO RUMORE.", 130, WHITE)
        centered(c, 490, "O NO?", 150, style.PINK)
        lanes(c, 800, t)
        staff(c, 1140, t, show=t > 2.2, k=k(2.2, 0.6))
        centered(c, 1240, "SENTI UNA MELODIA?", 30, MUTED, "sans", 700, 4)
        return
    if t < ANCORA:
        c.kicker(0, 300, "ORA SOLO L'ORECCHIO SINISTRO", center=True)
        centered(c, 360, "STESSO RUMORE.", 130, fade(WHITE, k(SINISTRO)))
        centered(c, 490, "LA MELODIA?", 150, fade(style.PINK, k(SINISTRO + 0.2)))
        lanes(c, 800, t, right=False)
        staff(c, 1140, t, show=False)
        centered(c, 1240, "SPARITA", 30, fade(MUTED, k(SINISTRO + 1.5)), "sans", 700, 4)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "E ORA TUTTI E DUE", center=True)
        centered(c, 360, "ECCOLA", 150, fade(WHITE, k(ANCORA)))
        centered(c, 510, "DI NUOVO.", 150, fade(style.PINK, k(ANCORA + 0.2)))
        lanes(c, 800, t)
        staff(c, 1140, t, k=k(ANCORA + 0.3))
        centered(c, 1240, "FRA MARTINO, NEL RUMORE", 30, fade(MUTED, k(ANCORA + 1.2)), "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "MELODIA DI HUGGINS", center=True)
        centered(c, 360, "NON È IN NESSUN", 120, fade(WHITE, k(SPIEGA)))
        centered(c, 480, "DEI DUE ORECCHI.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 690, ["Ai due orecchi arriva lo stesso rumore.",
                           "A destra ho solo invertito una fettina",
                           "di frequenze, nota per nota.",
                           "Il cervello confronta i due lati",
                           "e la differenza diventa una melodia.",
                           "",
                           "· Cramer e Huggins · 1958"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "TOGLI UNA CUFFIA.", 140, fade(WHITE, k(FINE)))
    centered(c, 560, "DOV'È FINITA?", 140, fade(style.PINK, k(FINE + 0.3)))
    lanes(c, 840, t, k=k(FINE + 0.6, 0.5))
    staff(c, 1180, t - FINE, k=k(FINE + 0.6, 0.5))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "melodia-nascosta.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=56)
    print("scritto", out)
