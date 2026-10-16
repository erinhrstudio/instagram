"""Reel "mascheramento", versione B per TikTok (13,5 s): il test parte dal primo istante.

Cinque bip a 1 kHz dentro un rumore rosa. Tre sono sopra la soglia di mascheramento, due sotto:
quasi tutti ne contano tre. Nella rivelazione tolgo il rumore intorno a 1 kHz (stesso livello
dei bip) e li conto a schermo uno per uno: erano cinque.

Uso: python -m tools.reel_maschera_b media/tiktok/mascheramento-b.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, write_mp4
from tools.reel_maschera import noise, F0

ROOT = Path(__file__).resolve().parent.parent
TEST, SCEGLI, RIVELA, CHIUDI, END = 0.0, 4.5, 7.5, 11.6, 13.5
BEEP = 0.22
T_TEST = [0.15, 0.95, 1.75, 2.55, 3.35]          # inizio di ogni bip nel test
T_RIV = [RIVELA + 0.35 + 0.75 * i for i in range(5)]
LIVELLI_DB = [6, -12, 6, -12, 4]                   # rispetto alla potenza del rumore in ~1 ERB intorno a 1 kHz


def bip(n, amp):
    t = np.arange(n) / SR
    env = np.clip(np.minimum(t / 0.01, (BEEP - t) / 0.01), 0, 1)
    return amp * env * np.sin(2 * np.pi * F0 * t)


def build():
    rng = np.random.default_rng(11)
    a = np.zeros(int(END * SR))
    n_test = int(RIVELA * SR)
    full = noise(n_test, False, rng)
    ref = np.sqrt(np.mean(full ** 2))
    full /= ref
    spec = np.abs(np.fft.rfft(full)) ** 2
    f = np.fft.rfftfreq(len(full), 1 / SR)
    band = spec[(f > 935) & (f < 1065)].sum() / spec.sum()
    base = np.sqrt(2 * band)
    a[:n_test] = full * 0.9
    nb = int(BEEP * SR)
    for t0, db in zip(T_TEST, LIVELLI_DB):
        i = int(t0 * SR)
        a[i:i + nb] += bip(nb, base * 10 ** (db / 20) * 0.9)
    # dal secondo 4,5 il rumore scende piano: si sceglie in silenzio
    i0, i1 = int(SCEGLI * SR), int((SCEGLI + 0.6) * SR)
    a[i0:i1] *= np.linspace(1, 0, i1 - i0)
    a[i1:n_test] = 0
    # rivelazione: rumore con il buco intorno a 1 kHz, stessi cinque livelli
    n_riv = int((CHIUDI - RIVELA) * SR)
    hole = noise(n_riv, True, rng) / ref * 0.9
    seg = a[n_test:n_test + n_riv]
    seg += hole
    for t0, db in zip(T_RIV, LIVELLI_DB):
        i = int((t0 - RIVELA) * SR)
        seg[i:i + nb] += bip(nb, base * 10 ** (db / 20) * 0.9)
    e = np.minimum(1, np.minimum(np.arange(n_riv), n_riv - np.arange(n_riv)) / (0.03 * SR))
    seg *= e
    a[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    return a


def onde(c, t, y=1000, k=1.0, buco=False):
    """Barre di rumore che si muovono: niente indizi sul numero dei bip."""
    rng = np.random.default_rng(int(t * 15))
    n, x0, x1 = 40, 140, W - 140
    bw = (x1 - x0) / n
    c.line([(x0, y + 8), (x1, y + 8)], fill=LINE, width=2)
    for i in range(n):
        if buco and 15 <= i <= 19:
            continue
        h = 190 * (0.35 + 0.65 * rng.random()) * k
        c.rect((x0 + i * bw + 3, y - h, x0 + (i + 1) * bw - 3, y), fill=fade((120, 116, 128), 0.75))


def draw(c, t):
    k = lambda t0, d=0.2: min(1, max(0, (t - t0) / d))
    if t < SCEGLI:
        c.kicker(0, 330, "ERIN · EAR TEST", center=True)
        centered(c, 390, "QUANTI BIP", 150, WHITE)
        centered(c, 540, "RIESCI A CONTARE?", 110, style.PINK)
        onde(c, t)
        centered(c, 1120, "CONTA CON ME", 30, MUTED, "sans", 700, 4)
        return
    if t < RIVELA:
        centered(c, 400, "QUANTI NE", 140, fade(WHITE, k(SCEGLI)))
        centered(c, 540, "HAI SENTITI?", 140, fade(WHITE, k(SCEGLI + 0.1)))
        for i, n in enumerate("345"):
            x = W / 2 + (i - 1) * 260
            kk = k(SCEGLI + 0.3 + 0.15 * i)
            c.rect((x - 105, 720, x + 105, 930), fill=fade((60, 58, 66), kk))
            centered_x(c, x, 745, n, 170, fade(WHITE, kk))
        p = min(1, (t - SCEGLI) / (RIVELA - SCEGLI))
        c.rect((240, 1030, 240 + (W - 480) * p, 1040), fill=style.PINK)
        c.rect((240 + (W - 480) * p, 1030, W - 240, 1040), fill=(60, 58, 66))
        return
    if t < CHIUDI:
        heard = sum(t >= x for x in T_RIV)
        centered(c, 330, "TOLGO IL RUMORE", 110, fade(WHITE, k(RIVELA)))
        centered(c, 450, "SOLO INTORNO AI BIP", 110, fade(style.PINK, k(RIVELA + 0.1)))
        centered(c, 600, str(heard) if heard else "", 260, WHITE)
        onde(c, t, y=1080, buco=True)
        if heard == 5 and t >= T_RIV[-1] + 0.4:
            centered(c, 1150, "ERANO 5. DUE ERANO NASCOSTI.", 34, fade(MUTED, k(T_RIV[-1] + 0.4)), "sans", 700, 3)
        return
    centered(c, 470, "TU QUANTI", 160, fade(WHITE, k(CHIUDI)))
    centered(c, 630, "NE AVEVI SENTITI?", 120, fade(style.PINK, k(CHIUDI + 0.15)))
    centered(c, 840, "SI CHIAMA MASCHERAMENTO", 30, fade(MUTED, k(CHIUDI + 0.4)), "sans", 700, 4)


def centered_x(c, x, y, s, size, fill):
    c.text((x, y), s, font("display", size), fill=fill, anchor="ma")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "mascheramento-b.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=61)
    print("scritto", out)
