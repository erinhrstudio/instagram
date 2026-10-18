"""Reel "fischi che diventano parole" (sine-wave speech, Remez e colleghi 1981).

Una frase viene ridotta a tre fischi che seguono le sue formanti (le risonanze della voce).
Al primo ascolto sembrano uccellini o un modem. Dopo aver sentito la frase vera,
la maggior parte delle persone non riesce più a non capirla.

Uso: python -m tools.reel_fischi media/tiktok/fischi-parole.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4
from tools.voce import tts

ROOT = Path(__file__).resolve().parent.parent
FRASE = "Il basso suonava troppo forte nel ritornello"
HOP = 0.01


def lpc(x, order):
    r = np.correlate(x, x, "full")[len(x) - 1:len(x) + order]
    if r[0] <= 0:
        return None
    a = np.zeros(order + 1); a[0] = 1.0
    e = r[0]
    for i in range(1, order + 1):
        k = -(r[i] + a[1:i] @ r[i - 1:0:-1]) / e
        a[1:i] = a[1:i] + k * a[i - 1:0:-1]
        a[i] = k
        e *= 1 - k * k
    return a


def formanti(voce):
    """Tracce di F1, F2, F3 (Hz) e ampiezze, una ogni 10 ms."""
    fs = 11025
    idx = np.arange(0, len(voce), SR / fs).astype(int)
    x = voce[idx]
    x = np.append(x[0], x[1:] - 0.94 * x[:-1])
    win = int(0.03 * fs); hop = int(HOP * fs)
    nfr = (len(x) - win) // hop
    F = np.zeros((nfr, 3)); A = np.zeros((nfr, 3))
    rms = np.array([np.sqrt(np.mean(voce[int(i * HOP * SR):int(i * HOP * SR) + int(0.03 * SR)] ** 2)) for i in range(nfr)])
    prev = np.array([500.0, 1500.0, 2500.0])
    bands = [(200, 1000), (700, 2600), (1700, 3600)]
    for i in range(nfr):
        fr = x[i * hop:i * hop + win] * np.hamming(win)
        a = lpc(fr, 12)
        if a is None:
            F[i] = prev; continue
        roots = [r for r in np.roots(a) if np.imag(r) > 0]
        cand = sorted((np.angle(r) * fs / (2 * np.pi), -fs / np.pi * np.log(abs(r))) for r in roots)
        cand = [f for f, bw in cand if bw < 500 and 180 < f < 3800]
        cur = prev.copy()
        used = set()
        for j, (lo, hi) in enumerate(bands):
            opts = [f for f in cand if lo <= f <= hi and f not in used and (j == 0 or f > cur[j - 1] + 150)]
            if opts:
                cur[j] = min(opts, key=lambda f: abs(f - prev[j]))
                used.add(cur[j])
        F[i] = cur; prev = cur
        # ampiezza: guadagno dell'inviluppo LPC alla frequenza della formante
        for j in range(3):
            w = 2 * np.pi * cur[j] / fs
            A[i, j] = 1 / abs(np.polyval(a[::-1], np.exp(-1j * w)))
    # lisciatura (mediana su 5 frame) e ampiezze legate all'energia della voce
    from numpy.lib.stride_tricks import sliding_window_view as sw
    Fp = np.pad(F, ((2, 2), (0, 0)), mode="edge")
    F = np.median(sw(Fp, 5, axis=0), axis=-1)
    A = A / (A.max(axis=1, keepdims=True) + 1e-9) * (rms / rms.max())[:, None] * np.array([1.0, 0.6, 0.35])
    A[rms < rms.max() * 0.04] = 0
    return F, A


def sinewave(F, A, n):
    t = np.arange(n) / SR
    tf = np.arange(len(F)) * HOP + 0.015
    out = np.zeros(n)
    for j in range(3):
        f = np.interp(t, tf, F[:, j]); a = np.interp(t, tf, A[:, j])
        out += a * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return out / np.abs(out).max() * 0.8


VOCE_VERA = ROOT / "posts" / "fischi-parole" / "voce_giuseppe.wav"   # la frase detta da Giuseppe
if VOCE_VERA.exists():
    from scipy.io import wavfile
    VOCE = wavfile.read(VOCE_VERA)[1].astype(float) / 32768
else:
    VOCE, _ = tts(FRASE, speed=120)
VOCE = VOCE / np.abs(VOCE).max() * 0.8
F_TR, A_TR = formanti(VOCE)
FISCHI = sinewave(F_TR, A_TR, len(VOCE))
DUR = len(VOCE) / SR
# i tempi seguono la durata della frase
S1 = 0.4
S2 = S1 + DUR + 0.3
DOMANDA = S2 + DUR + 0.3
VERA = DOMANDA + 2.4
S3 = VERA + DUR + 0.6
SPIEGA = S3 + DUR + 0.5
FINE = SPIEGA + 5.6
END = FINE + 0.4 + DUR + 0.6


def build():
    a = np.zeros(int(END * SR))
    # la voce vera allo stesso volume medio dei fischi (con un limite sui picchi)
    rms = lambda x: np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2))
    voce = VOCE * min(rms(FISCHI) / rms(VOCE) * 0.75, 2.0)
    voce = 0.92 * np.tanh(voce / 0.92)
    for t0, x in [(S1, FISCHI), (S2, FISCHI), (VERA, voce), (S3, FISCHI), (FINE + 0.4, FISCHI)]:
        i = int(t0 * SR)
        a[i:i + len(x)] += x
    return a


def tracce(c, y0, y1, trel, k=1.0, col=None):
    """Le tre tracce dei fischi su un asse tempo/frequenza, con il punto d'ascolto."""
    x0, x1 = 120, W - 120
    c.line([(x0, y1 + 8), (x1, y1 + 8)], fill=fade(LINE, k), width=2)
    n = len(F_TR)
    for i in range(0, n, 2):
        x = x0 + i / n * (x1 - x0)
        t = i * HOP
        played = trel is not None and t <= trel
        for j in range(3):
            if A_TR[i, j] <= 0:
                continue
            y = y1 - (F_TR[i, j] - 150) / 3500 * (y1 - y0)
            r = 3 + 6 * min(1, A_TR[i, j] / 0.5)
            cc = (col or style.PINK) if played else (110, 106, 118)
            c.ellipse((x - r, y - r, x + r, y + r), fill=fade(cc, k))


def playing(t, starts):
    for t0 in starts:
        if t0 <= t < t0 + DUR:
            return t - t0
    return None


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < DOMANDA:
        c.kicker(0, 300, "TRE FISCHI", center=True)
        centered(c, 360, "COSA", 160, WHITE)
        centered(c, 520, "DICONO?", 160, style.PINK)
        tracce(c, 760, 1120, playing(t, [S1, S2]))
        centered(c, 1240, "ASCOLTA DUE VOLTE", 30, MUTED, "sans", 700, 4)
        return
    if t < VERA:
        centered(c, 520, "NIENTE?", 190, fade(WHITE, k(DOMANDA)))
        centered(c, 720, "ORA LA FRASE VERA.", 100, fade(style.PINK, k(DOMANDA + 0.6)))
        return
    if t < S3:
        c.kicker(0, 300, "LA FRASE ORIGINALE", center=True)
        centered(c, 420, "IL BASSO SUONAVA", 110, fade(WHITE, k(VERA)))
        centered(c, 540, "TROPPO FORTE", 110, fade(WHITE, k(VERA + 0.3)))
        centered(c, 660, "NEL RITORNELLO", 110, fade(style.PINK, k(VERA + 0.6)))
        tracce(c, 820, 1120, playing(t, [VERA]), col=(200, 196, 210))
        return
    if t < SPIEGA:
        c.kicker(0, 300, "DI NUOVO I FISCHI", center=True)
        centered(c, 360, "E ADESSO", 160, fade(WHITE, k(S3)))
        centered(c, 520, "LA CAPISCI?", 160, fade(style.PINK, k(S3 + 0.2)))
        tracce(c, 760, 1120, playing(t, [S3]))
        return
    if t < FINE:
        c.kicker(0, 300, "SINE-WAVE SPEECH", center=True)
        centered(c, 360, "IL CERVELLO", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 510, "CAMBIA MODALITÀ.", 130, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 720, ["Ho tolto la voce e lasciato solo tre fischi",
                           "che seguono le sue risonanze.",
                           "Finché non sai che è una frase, senti fischi.",
                           "Quando lo sai, il cervello la sente come voce",
                           "e non torna più indietro.",
                           "",
                           "· Remez, Rubin, Pisoni e Carrell · 1981"], SPIEGA + 0.5, k)
        return
    centered(c, 420, "PROVA A NON", 160, fade(WHITE, k(FINE)))
    centered(c, 580, "CAPIRLA.", 160, fade(WHITE, k(FINE + 0.2)))
    centered(c, 760, "MANDALO A CHI NON L'HA ANCORA SENTITA", 36, fade(style.PINK, k(FINE + 0.6)), "sans", 700, 2)
    tracce(c, 900, 1150, playing(t, [FINE + 0.4]), k=k(FINE + 0.4, 0.4))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "fischi-parole.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=62)
    print("scritto", out)
