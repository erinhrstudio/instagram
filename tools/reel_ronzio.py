"""Reel "This hum tells police when you recorded this." (analisi ENF).

Il ronzio di rete (50 Hz in Europa, con le armoniche) non è mai esattamente a 50 Hz:
oscilla di continuo. Le registrazioni vicine a apparecchi elettrici lo catturano e
confrontandolo con gli archivi si può datare una registrazione o trovare tagli.
Il Met Police di Londra archivia la frequenza dal 2005 (Wikipedia, ENF analysis).
L'oscillazione nel video è esagerata per vederla: lo diciamo a schermo.

Uso: python -m tools.reel_ronzio media/instagram/ronzio-rete.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
SPIEGA, CTA = 9.0, 18.5
END = CTA + 7.0
rng = np.random.default_rng(5)
DERIVA = np.cumsum(rng.normal(0, 1, 400))
DERIVA = (DERIVA - DERIVA.mean()) / np.abs(DERIVA - DERIVA.mean()).max()   # -1..1


def deriva(u):
    return np.interp(u * (len(DERIVA) - 1), np.arange(len(DERIVA)), DERIVA)


def build():
    n = int(END * SR)
    t = np.arange(n) / SR
    f = 50 + 0.05 * deriva(t / END)                    # ±0,05 Hz, come una rete vera
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(h * ph) * a for h, a in ((1, 1.0), (2, 0.6), (3, 0.8), (5, 0.35), (7, 0.2)))
    env = np.clip(np.minimum(t, END - t) / 0.5, 0, 1) * np.where(t < CTA, 1.0, 0.5)
    return x * env


def traccia(c, y0, y1, u, k=1.0, x0=150, x1=W - 150, col=None):
    c.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=fade(LINE, k), width=2)
    us = np.linspace(0, u, max(2, int(u * 200)))
    pts = [(x0 + (x1 - x0) * a, (y0 + y1) / 2 - deriva(a) * (y1 - y0) / 2) for a in us]
    c.line(pts, fill=fade(col or WHITE, k), width=5)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SPIEGA:
        c.kicker(0, 300, "LISTEN TO THE HUM", center=True)
        centered(c, 360, "THIS HUM CAN", 140, WHITE)
        centered(c, 500, "DATE A RECORDING.", 140, style.PINK)
        u = min(1, t / SPIEGA)
        c.text((150, 790), "50.05 HZ", style.font("sans", 22, 600), fill=MUTED)
        c.text((150, 1150), "49.95 HZ", style.font("sans", 22, 600), fill=MUTED)
        traccia(c, 830, 1130, u)
        centered(c, 1240, "THE GRID IS NEVER EXACTLY 50 HZ", 30, MUTED, "sans", 700, 4)
        return
    if t < CTA:
        c.kicker(0, 300, "A FINGERPRINT FROM THE POWER GRID", center=True)
        centered(c, 360, "IT DRIFTS", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "ALL DAY.", 150, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["The mains frequency moves up and down",
                           "a tiny bit, all the time. Recordings made",
                           "near electrical devices capture that hum.",
                           "",
                           "Experts compare its drift with grid logs",
                           "to find when a recording was made,",
                           "or spot where it was cut.",
                           "London's Met Police has kept logs since 2005.",
                           "",
                           "· ENF analysis · drift exaggerated on screen"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "DID YOU KNOW", 120, fade(WHITE, k(CTA)))
    centered(c, 540, "YOUR HUM TALKS?", 120, fade(style.PINK, k(CTA + 0.2)))
    centered(c, 700, "SEND IT TO A TRUE CRIME FAN", 32, fade(MUTED, k(CTA + 0.4)), "sans", 700, 4)
    traccia(c, 820, 1080, 1, k=k(CTA + 0.3, 0.4), col=style.PINK)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "ronzio-rete.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=85, picco=0.6)
    print("scritto", out)
