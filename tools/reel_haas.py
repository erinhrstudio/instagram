"""Reel "effetto Haas" (effetto della precedenza): da ascoltare in cuffia.

Lo stesso loop, allo stesso volume nei due orecchi: se la destra arriva pochi millisecondi dopo,
il suono sembra venire tutto da sinistra. Oltre una certa soglia diventa un'eco.

Uso: python -m tools.reel_haas media/tiktok/haas.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.render import make_loop
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
BAR = 2.4
HAAS_MS, ECO_MS = 8, 70
CENTRO, SPOSTA, VOTA, RIVELA, ECO, SPIEGA, FINE, END = 0.0, 4.8, 9.6, 11.2, 16.0, 20.8, 25.6, 29.0


def build():
    loop = make_loop(seed=4, bpm=100, bars=1)[:, 0][:int(BAR * SR)]
    loop = loop * np.minimum(1, np.arange(len(loop)) / (0.003 * SR))
    a = np.zeros((int(END * SR) + SR, 2))

    def put(t0, bars, delay_ms):
        d = int(delay_ms * SR / 1000)
        for b in range(bars):
            s = int((t0 + b * BAR) * SR)
            a[s:s + len(loop), 0] += loop
            a[s + d:s + d + len(loop), 1] += loop

    put(CENTRO, 2, 0)
    put(SPOSTA, 2, HAAS_MS)
    put(RIVELA, 2, HAAS_MS)
    put(ECO, 2, ECO_MS)
    put(FINE, 1, 0)
    return a[:int(END * SR)]


def head(c, cy, x_src=None, k=1.0, t=0.0):
    r = 140
    c.ellipse((W / 2 - r, cy - r, W / 2 + r, cy + r), outline=fade(LINE, k), width=3)
    for side in (-1, 1):
        x = W / 2 + side * (r + 22)
        c.ellipse((x - 22, cy - 50, x + 22, cy + 50), outline=fade((120, 116, 128), k), width=3)
        c.text((W / 2 + side * 330, cy + 205), "SINISTRA" if side < 0 else "DESTRA",
               font("sans", 26, 700), fill=fade(MUTED, k), anchor="mm", tracking=4)
    if x_src is not None:
        p = 0.5 + 0.5 * np.sin(t * 2 * np.pi * 100 / 60)
        rr = 28 + 12 * p
        x = W / 2 + x_src * 330
        c.ellipse((x - rr, cy - rr, x + rr, cy + rr), fill=fade(style.PINK, k))


def lanes(c, y, delay_ms, k):
    """Due tracce con la stessa forma d'onda; la destra spostata del ritardo (esagerato per vederlo)."""
    for i, (lab, off) in enumerate([("SINISTRA", 0), ("DESTRA", delay_ms)]):
        yy = y + i * 140
        c.text((150, yy - 75), lab, font("sans", 24, 700), fill=fade(MUTED, k), anchor="la", tracking=3)
        x0 = 150 + off * 12
        for j in range(3):
            xs = x0 + j * 200
            c.rect((xs, yy - 30, xs + 14, yy + 30), fill=fade(style.PINK, k))
            c.rect((xs + 20, yy - 14, xs + 120, yy + 14), fill=fade((120, 116, 128), k * 0.6))
        c.text((W - 150, yy - 75), "0 dB", font("sans", 24, 700), fill=fade(TEXT, k), anchor="ra", tracking=2)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPOSTA:
        c.kicker(0, 300, "SOLO IN CUFFIA", center=True)
        centered(c, 360, "DA DOVE", 150, WHITE)
        centered(c, 510, "ARRIVA?", 150, style.PINK)
        head(c, 900, 0, t=t)
        centered(c, 1232, "AL CENTRO, VERO?", 30, MUTED, "sans", 700, 4)
        return
    if t < VOTA:
        c.kicker(0, 300, "SOLO IN CUFFIA", center=True)
        centered(c, 360, "E ADESSO", 150, WHITE)
        centered(c, 510, "DA DOVE ARRIVA?", 130, style.PINK)
        head(c, 900, None)
        centered(c, 1232, "NON HO TOCCATO IL PAN", 30, MUTED, "sans", 700, 4)
        return
    if t < RIVELA:
        centered(c, 560, "A SINISTRA,", 170, fade(WHITE, k(VOTA)))
        centered(c, 740, "VERO?", 170, fade(style.PINK, k(VOTA + 0.3)))
        return
    if t < ECO:
        c.kicker(0, 300, "IL TRUCCO", center=True)
        centered(c, 360, "STESSO VOLUME.", 130, fade(WHITE, k(RIVELA)))
        centered(c, 490, f"DESTRA IN RITARDO DI {HAAS_MS} ms.", 90, fade(style.PINK, k(RIVELA + 0.3)))
        lanes(c, 780, HAAS_MS, k(RIVELA + 0.6))
        centered(c, 1232, "IL CERVELLO SEGUE CHI ARRIVA PRIMA", 30, fade(MUTED, k(RIVELA + 1.2)), "sans", 700, 3)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "E SE ESAGERO?", center=True)
        centered(c, 360, f"{ECO_MS} ms:", 150, fade(WHITE, k(ECO)))
        centered(c, 510, "DIVENTA UN'ECO.", 140, fade(style.PINK, k(ECO + 1.2)))
        lanes(c, 780, ECO_MS / 4, k(ECO + 0.3))
        return
    if t < FINE:
        c.kicker(0, 300, "EFFETTO HAAS", center=True)
        centered(c, 360, "PER ALLARGARE", 130, fade(WHITE, k(SPIEGA)))
        centered(c, 490, "UN MIX.", 130, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Doppia una chitarra e ritarda una copia",
                           "di 10-20 ms: diventa larghissima.",
                           "Ma controlla in mono: sommate, le due",
                           "copie si cancellano a certe frequenze.",
                           "",
                           "· Helmut Haas · 1951"], SPIEGA + 0.5, k)
        return
    centered(c, 470, "SALVALO", 190, fade(WHITE, k(FINE)))
    centered(c, 680, "PER IL PROSSIMO MIX.", 120, fade(style.PINK, k(FINE + 0.3)))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "haas.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=55)
    print("scritto", out)
