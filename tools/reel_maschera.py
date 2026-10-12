"""Reel "mascheramento": dei bip nascosti in un rumore, poi gli stessi bip con un buco nel rumore.

Il volume dei bip non cambia mai: cambia solo il rumore intorno alla loro frequenza.

Uso: python -m tools.reel_maschera media/tiktok/mascheramento.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
F0 = 1000.0
NOTCH = (700, 1400)
NASC, SILENZIO, BUCO, SPIEGA, FINE, END = 0.0, 6.4, 7.2, 13.2, 18.6, 23.0
BEEP, PASSO = 0.25, 0.5


def noise(n, notch, rng):
    """Rumore rosa, con o senza buco intorno a F0 (filtrato in frequenza)."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = 1 / np.sqrt(np.maximum(f, 40))
    g[(f < 40) | (f > 16000)] = 0
    if notch:
        g[(f > NOTCH[0]) & (f < NOTCH[1])] = 0
    return np.fft.irfft(spec * g, n)


def beeps(t0, t1, amp):
    t = np.arange(int((t1 - t0) * SR)) / SR
    on = (t % PASSO) < BEEP
    ph = (t % PASSO)
    env = np.clip(np.minimum(ph / 0.01, (BEEP - ph) / 0.01), 0, 1) * on
    return amp * env * np.sin(2 * np.pi * F0 * t)


def build():
    rng = np.random.default_rng(7)
    a = np.zeros(int(END * SR))
    full = noise(int(SILENZIO * SR), False, rng)
    full /= np.sqrt(np.mean(full ** 2))
    # potenza del rumore nella banda critica intorno a 1 kHz: il bip sta 10 dB sotto
    spec = np.abs(np.fft.rfft(full)) ** 2
    f = np.fft.rfftfreq(len(full), 1 / SR)
    band = spec[(f > 935) & (f < 1065)].sum() / spec.sum()          # quota di potenza in ~1 ERB
    amp = np.sqrt(2 * band) * 10 ** (-10 / 20)
    seg = lambda x0, x1: slice(int(x0 * SR), int(x0 * SR) + int((x1 - x0) * SR))
    a[seg(NASC, SILENZIO)] = full + beeps(NASC, SILENZIO, amp)
    hole = noise(int((SPIEGA - BUCO) * SR), True, rng) / np.sqrt(np.mean(noise(len(full), False, rng) ** 2))
    a[seg(BUCO, SPIEGA)] = hole + beeps(BUCO, SPIEGA, amp)
    # finale: di nuovo il rumore pieno con i bip, per il riascolto
    tail = noise(int((END - FINE) * SR), False, rng)
    tail /= np.sqrt(np.mean(tail ** 2))
    a[seg(FINE, END)] = tail + beeps(FINE, END, amp)
    for x0, x1 in [(NASC, SILENZIO), (BUCO, SPIEGA), (FINE, END)]:
        s = seg(x0, x1)
        n = s.stop - s.start
        e = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.03 * SR))
        a[s] *= e
    return a


def spectrum(c, t, notch, y0=760, y1=1130, x0=140, x1=W - 140, k=1.0):
    """Barre di rumore su un asse in frequenza, con il bip come linea che sale quando suona."""
    rng = np.random.default_rng(int(t * 12))
    n = 48
    c.line([(x0, y1 + 8), (x1, y1 + 8)], fill=LINE, width=2)
    c.text((x0, y1 + 24), "GRAVI", font("sans", 22, 700), fill=MUTED, anchor="la", tracking=3)
    c.text((x1, y1 + 24), "ACUTI", font("sans", 22, 700), fill=MUTED, anchor="ra", tracking=3)
    fb = 40 * (16000 / 40) ** (np.arange(n) / (n - 1))
    bw = (x1 - x0) / n
    for i, fr in enumerate(fb):
        if notch and NOTCH[0] < fr < NOTCH[1]:
            continue
        h = (y1 - y0) * (0.48 + 0.12 * rng.random()) * k
        x = x0 + i * bw
        c.rect((x + 2, y1 - h, x + bw - 2, y1), fill=fade((120, 116, 128), 0.75))
    on = (t % PASSO) < BEEP
    xb = x0 + (np.log(F0 / 40) / np.log(16000 / 40)) * (x1 - x0)
    hb = (y1 - y0) * 0.36 * k
    if on:
        c.rect((xb - 4, y1 - hb, xb + 4, y1), fill=style.PINK)
        c.ellipse((xb - 12, y1 - hb - 12, xb + 12, y1 - hb + 12), fill=style.PINK)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < SILENZIO:
        c.kicker(0, 300, "TEST · ALZA IL VOLUME", center=True)
        centered(c, 360, "QUANTI BIP", 150, WHITE)
        centered(c, 510, "SENTI?", 150, style.PINK)
        spectrum(c, t, False)
        centered(c, 1215, "CONTALI", 30, MUTED, "sans", 700, 4)
        return
    if t < BUCO:
        centered(c, 640, "NESSUNO?", 200, fade(WHITE, k(SILENZIO)))
        return
    if t < SPIEGA:
        c.kicker(0, 300, "STESSI BIP · STESSO VOLUME", center=True)
        centered(c, 360, "HO SOLO TOLTO", 130, fade(WHITE, k(BUCO)))
        centered(c, 490, "IL RUMORE INTORNO.", 130, fade(style.PINK, k(BUCO + 0.2)))
        spectrum(c, t, True)
        centered(c, 1215, "ERANO LÌ ANCHE PRIMA", 30, fade(MUTED, k(BUCO + 1.5)), "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "MASCHERAMENTO", center=True)
        centered(c, 360, "UN SUONO NE", 130, fade(WHITE, k(SPIEGA)))
        centered(c, 490, "CANCELLA UN ALTRO.", 130, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Se due suoni stanno sulle stesse frequenze,",
                           "il più forte copre l'altro. Nel mix succede",
                           "a voce e chitarre: non serve alzare,",
                           "serve fare il buco con l'EQ.",
                           "",
                           "· È anche il principio con cui l'MP3 risparmia spazio"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "RIASCOLTA", 160, fade(WHITE, k(FINE)))
    centered(c, 560, "L'INIZIO.", 160, fade(WHITE, k(FINE + 0.2)))
    centered(c, 720, "ADESSO LI SENTI?", 110, fade(style.PINK, k(FINE + 0.4)))
    spectrum(c, t, False, y0=930, y1=1150, k=k(FINE + 0.6, 0.6))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "mascheramento.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=53)
    print("scritto", out)
