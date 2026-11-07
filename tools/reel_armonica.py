"""Reel "una nota o due?" (armonica stonata, Moore, Glasberg & Peters 1986).

Un tono di 10 armoniche da 200 Hz. A ogni passo la 3a armonica (600 Hz) si sposta: 0, 1, 2, 4, 8 %.
Da qualche punto in poi salta fuori come una seconda nota (nello studio: di solito tra 1 e 3 %,
diverso da persona a persona). Chi guarda scrive a che numero l'ha sentita: si confronta.

Uso: python -m tools.reel_armonica media/tiktok/armonica-stonata.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
F0, NH, H3 = 200.0, 10, 3
STONA = [0, 1, 2, 4, 8]               # % della 3a armonica, passo per passo
DUR, PASSO, T0 = 1.6, 2.1, 1.0
FASI = np.random.default_rng(5).uniform(0, 2 * np.pi, NH)
RIASCOLTA = T0 + PASSO * len(STONA) + 0.5          # passo 1 e passo 5 di nuovo
VOTA = RIASCOLTA + 2 * PASSO + 0.3
RIVELA = VOTA + 2.6
SOLO, ANCORA = RIVELA + 1.2, RIVELA + 3.4
SPIEGA = RIVELA + 6.0
CTA, END = SPIEGA + 6.8, SPIEGA + 13.3
EVENTI = ([(T0 + i * PASSO, i) for i in range(5)] + [(RIASCOLTA, 0), (RIASCOLTA + PASSO, 4)]
          + [(ANCORA, 4)])


def complesso(pct, solo=False):
    n = int(DUR * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for h in range(1, NH + 1):
        f = F0 * h * (1 + pct / 100 if h == H3 else 1)
        if solo and h != H3:
            continue
        x += np.sin(2 * np.pi * f * t + FASI[h - 1])
    env = np.clip(np.minimum(t, DUR - t) / 0.03, 0, 1)
    return x * env


def build():
    a = np.zeros(int(END * SR) + SR)
    for t0, i in EVENTI:
        x = complesso(STONA[i])
        j = int(t0 * SR); a[j:j + len(x)] += x
    x = complesso(8, solo=True) * 2.5          # la nota "in più", da sola
    j = int(SOLO * SR); a[j:j + len(x)] += x
    return a[:int(END * SR)]


def attivo(t):
    for t0, i in EVENTI:
        if t0 <= t < t0 + DUR:
            return i
    return None


def spettro(c, y, pct, k=1.0, evidenzia=False, solo=False):
    x0, x1 = 140, W - 140
    fmax = F0 * (NH + 0.6)
    c.line([(x0, y), (x1, y)], fill=fade(LINE, k), width=2)
    for h in range(1, NH + 1):
        f = F0 * h * (1 + pct / 100 if h == H3 else 1)
        x = x0 + (x1 - x0) * f / fmax
        hit = h == H3 and (evidenzia or pct > 0)
        if solo and h != H3:
            col = (70, 66, 78)
        else:
            col = style.PINK if hit else WHITE
        c.line([(x, y - 220), (x, y)], fill=fade(col, k), width=8 if hit else 6)
    c.text((W / 2, y + 26), "THE INGREDIENTS OF ONE NOTE", style.font("sans", 24, 700), fill=fade(MUTED, k),
           anchor="ma", tracking=4)


def passi(c, y, i, k=1.0):
    for j in range(5):
        x = W / 2 + (j - 2) * 130
        on = j == i
        c.ellipse((x - 44, y - 44, x + 44, y + 44), fill=fade(style.PINK if on else (60, 57, 68), k))
        c.text((x, y), str(j + 1), style.font("display", 60), fill=(31, 31, 31) if on else fade(TEXT, k),
               anchor="mm")


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    i = attivo(t)
    if t < VOTA:
        c.kicker(0, 300, "HEADPHONES ON · LISTEN TO THE NUMBERS", center=True)
        centered(c, 360, "ONE NOTE", 160, WHITE)
        centered(c, 520, "OR TWO?", 160, style.PINK)
        passi(c, 820, i if i is not None else -1)
        c.text((W / 2, 1000), "WHEN DO YOU HEAR A SECOND NOTE?" if t < RIASCOLTA else "AGAIN: 1, THEN 5",
               style.font("sans", 30, 700), fill=MUTED, anchor="ma", tracking=4)
        return
    if t < RIVELA:
        centered(c, 480, "COMMENT", 170, fade(WHITE, k(VOTA)))
        centered(c, 660, "THE NUMBER.", 170, fade(style.PINK, k(VOTA + 0.2)))
        centered(c, 900, "WHERE DID THE SECOND NOTE APPEAR?", 36, fade(TEXT, k(VOTA + 0.5)), "sans", 700, 3)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "THE TRICK", center=True)
        centered(c, 360, "ONE INGREDIENT", 140, fade(WHITE, k(RIVELA)))
        centered(c, 500, "WAS OFF.", 140, fade(style.PINK, k(RIVELA + 0.2)))
        solo = SOLO <= t < SOLO + DUR
        spettro(c, 1000, 8, k(RIVELA + 0.3), evidenzia=True, solo=solo)
        msg = ("THIS ONE, ALONE" if solo else
               ("AND BACK IN THE MIX: NOW YOU CAN'T UNHEAR IT" if t >= ANCORA else "1, 2, 4, 8 % OUT OF TUNE"))
        centered(c, 1120, msg, 30, fade(TEXT, k(RIVELA + 0.5)), "sans", 700, 3)
        return
    if t < CTA:
        c.kicker(0, 300, "HARMONIC GROUPING", center=True)
        centered(c, 360, "YOUR BRAIN", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "KICKED IT OUT.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["A note is many pitches that fit one pattern.",
                           "Push one off by just a few percent",
                           "and your brain stops counting it in:",
                           "you hear it as a second note.",
                           "It's how you tell instruments apart.",
                           "",
                           "· Moore, Glasberg & Peters · 1986"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "SEND IT TO A FRIEND.", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "SAME NUMBER", 120, fade(WHITE, k(CTA + 0.2)))
    centered(c, 680, "FOR BOTH OF YOU?", 120, fade(style.PINK, k(CTA + 0.4)))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "armonica-stonata.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=74, picco=0.6)
    print("scritto", out)
