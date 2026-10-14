"""Reel "il galoppo che si spezza" (segregazione in flussi, van Noorden 1975).

Due note, A e B, in sequenza A-B-A pausa: lentamente è un galoppo. Accelerando, a un certo punto
il galoppo si rompe e senti due ritmi separati, uno acuto e uno grave. Le note non cambiano.

Uso: python -m tools.reel_galoppo media/tiktok/galoppo.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
FA, FB = 500.0, 840.0                    # nove semitoni circa
ACCEL, SPIEGA, FINE, END = 15.0, 15.4, 21.0, 26.0
D0, D1 = 0.16, 0.06                      # durata di ogni nota: da lenta a veloce


def durata(t):
    """Durata di una nota al tempo t: scende piano da D0 a D1 durante l'accelerazione."""
    x = min(1, max(0, (t - 1.5) / (ACCEL - 3.5)))
    return D0 * (D1 / D0) ** x


def eventi(t0, t1, fissa=None):
    """Lista di (tempo, nota, durata) della sequenza A B A pausa."""
    ev, t, i = [], t0, 0
    while t < t1:
        d = fissa or durata(t)
        nota = [FA, FB, FA, None][i % 4]
        if nota:
            ev.append((t, nota, d))
        t += d
        i += 1
    return ev


def tono(f, d):
    n = int(d * SR)
    t = np.arange(n) / SR
    env = np.clip(np.minimum(t / 0.005, (d * 0.85 - t) / 0.01), 0, 1)
    return np.sin(2 * np.pi * f * t) * env


EV = eventi(0.2, ACCEL) + eventi(FINE + 0.4, END - 0.2, fissa=D1)


def build():
    a = np.zeros(int(END * SR) + SR)
    for t, f, d in EV:
        x = tono(f, d)
        i = int(t * SR)
        a[i:i + len(x)] += x
    return a[:int(END * SR)] * 0.5


def trama(c, y, t, k=1.0, separati=None):
    """Ultime note suonate: in alto le B, in basso le A, unite come le senti."""
    win = 2.0
    vis = [(tt, f, d) for tt, f, d in EV if t - win <= tt <= t]
    x0, x1 = 140, W - 140
    if separati is None:
        separati = durata(t) < 0.08
    pts = []
    for tt, f, d in vis:
        x = x1 - (t - tt) / win * (x1 - x0)
        yy = y - 110 if f == FB else y + 110
        pts.append((x, yy, f))
    if separati:
        for f in (FA, FB):
            line = [(x, yy) for x, yy, ff in pts if ff == f]
            if len(line) > 1:
                c.line(line, fill=fade(style.PINK if f == FB else (170, 166, 180), k), width=4)
    else:
        for i in range(len(pts) - 1):
            if pts[i + 1][0] - pts[i][0] < 2.5 * durata(t) / win * (x1 - x0):
                c.line([pts[i][:2], pts[i + 1][:2]], fill=fade(LINE, k), width=3)
    for x, yy, f in pts:
        c.rect((x - 14, yy - 9, x + 14, yy + 9), fill=fade(style.PINK if f == FB else (170, 166, 180), k))


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        rotto = durata(t) < 0.08
        c.kicker(0, 300, "ACCELERO", center=True)
        centered(c, 360, "UN GALOPPO" if not rotto else "ORA SONO", 150, WHITE)
        centered(c, 510, "O DUE RITMI?" if not rotto else "DUE RITMI?", 150, style.PINK)
        trama(c, 900, t)
        centered(c, 1240, f"{60 / (durata(t) * 4):.0f} GALOPPI AL MINUTO", 30, MUTED, "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "SEGREGAZIONE IN FLUSSI", center=True)
        centered(c, 360, "LE NOTE", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "SONO LE STESSE.", 130, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Quando le note acute e gravi si alternano",
                           "troppo in fretta, il cervello smette",
                           "di seguirle come una melodia sola",
                           "e le separa in due flussi.",
                           "Bach lo usava per far sentire due voci",
                           "a un solo violino.",
                           "",
                           "· Leon van Noorden · 1975"], SPIEGA + 0.5, k)
        return
    centered(c, 420, "IN CHE SECONDO", 140, fade(WHITE, k(FINE)))
    centered(c, 570, "SI È SPEZZATO?", 140, fade(style.PINK, k(FINE + 0.3)))
    centered(c, 730, "SCRIVILO NEI COMMENTI", 50, fade(TEXT, k(FINE + 0.6)), "sans", 700, 3)
    trama(c, 1010, t, k=k(FINE + 0.4, 0.4), separati=True)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "galoppo.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=65)
    print("scritto", out)
