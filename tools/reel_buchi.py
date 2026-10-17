"""Reel "il cervello riempie i buchi" (ripristino fonemico, Warren 1970).

Nella frase tolgo la S di "batterista" e al suo posto metto una tosse: quasi nessuno nota che manca.
Poi la stessa frase con il silenzio al posto della tosse: il buco si sente subito.

Uso: python -m tools.reel_buchi media/tiktok/buchi.mp4
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import font, MUTED, TEXT, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4
from tools.voce import tts

ROOT = Path(__file__).resolve().parent.parent
FRASE = "Il batterista suonava a tempo perfetto"
TOSSE1, TOSSE2, DOMANDA, BUCO1, BUCO2, SPIEGA, FINE, END = 0.5, 3.9, 7.2, 9.6, 12.9, 16.4, 22.4, 27.0


def tosse(n, rng):
    """Colpo di tosse sintetico: soffio rauco con le formanti di una "e" aperta, attacco non troppo secco
    e una coda lunga, più un po' di voce (ronzio a ~130 Hz) per non sembrare un colpo di martello."""
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = sum(a / (1 + ((f - fc) / bw) ** 2) for fc, bw, a in [(550, 180, 1.0), (1700, 260, 0.7), (2600, 350, 0.45), (3800, 600, 0.25)])
    g *= (f > 150)
    x = np.fft.irfft(X * g, n)
    x /= np.abs(x).max()
    f0 = 130 * (1 + 0.03 * np.sin(2 * np.pi * 7 * t))                       # voce rauca, leggermente instabile
    ph = 2 * np.pi * np.cumsum(f0) / SR
    voce = sum(np.sin(k * ph) / k for k in range(1, 12))
    voce *= 1 + 0.4 * rng.standard_normal(n)
    voce /= np.abs(voce).max()
    env = np.minimum(t / 0.018, 1) * np.exp(-np.maximum(t - 0.035, 0) / 0.11)
    y = (0.75 * x + 0.3 * voce) * env
    return y / np.abs(y).max()


VOCE_VERA = ROOT / "posts" / "buchi" / "voce_giuseppe.wav"   # la voce di Giuseppe (17/10), terza registrazione, ultima presa
S_VERA = (0.871, 0.992)                                       # la S di "batteri-S-ta" in quel file, trovata dall'energia sopra 4 kHz


def clips():
    if VOCE_VERA.exists():
        from scipy.io import wavfile
        sr, voce = wavfile.read(VOCE_VERA)
        assert sr == SR
        voce = voce.astype(float) / 32768
        s0, d = S_VERA[0], S_VERA[1] - S_VERA[0]
    else:
        voce, fon = tts(FRASE)
        s0, d = [(a, b) for p, a, b in fon if p == "s"][0]      # la prima S: "batteri-S-ta"
    voce = voce / np.abs(voce).max() * 0.8
    i0, i1 = int(s0 * SR), int((s0 + d) * SR)
    r = int(0.004 * SR)
    buco = voce.copy()
    buco[i0:i1] = 0
    buco[i0 - r:i0] *= np.linspace(1, 0, r)
    buco[i1:i1 + r] *= np.linspace(0, 1, r)
    rng = np.random.default_rng(3)
    m = int(0.02 * SR)
    c = tosse(i1 - i0 + 2 * m + int(0.10 * SR), rng) * 0.7
    con_tosse = buco.copy()
    con_tosse[i0 - m:i0 - m + len(c)] += c
    return con_tosse, buco, (s0, s0 + d)


CON, BUCO, GAP = clips()
DUR = len(CON) / SR


def build():
    a = np.zeros(int(END * SR))
    for t0, x in [(TOSSE1, CON), (TOSSE2, CON), (BUCO1, BUCO), (BUCO2, BUCO), (FINE + 0.6, CON)]:
        i = int(t0 * SR)
        a[i:i + len(x)] += x
    return a


def onda(c, y, x, t_rel, gap_col=None, k=1.0):
    """Forma d'onda della frase con il punto di ascolto; gap_col evidenzia dove manca la S."""
    n = 90
    env = np.array([np.abs(seg).max() for seg in np.array_split(x, n)])
    x0, x1 = 120, W - 120
    bw = (x1 - x0) / n
    for j, e in enumerate(env):
        xa = x0 + j * bw
        tj = (j + 0.5) / n * DUR
        played = t_rel is not None and tj <= t_rel
        col = (200, 196, 210) if played else (110, 106, 118)
        if gap_col and GAP[0] - 0.03 <= tj <= GAP[1] + 0.03:
            col = gap_col
        h = max(2, e * 150) * k
        c.rect((xa + 2, y - h, xa + bw - 2, y + h), fill=fade(col, k))


def playing(t, starts):
    for t0 in starts:
        if t0 <= t < t0 + DUR:
            return t - t0
    return None


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    if t < DOMANDA:
        c.kicker(0, 300, "ASCOLTA LA FRASE", center=True)
        centered(c, 360, "C'È UN COLPO.", 140, WHITE)
        centered(c, 500, "CAPISCI TUTTO?", 140, style.PINK)
        onda(c, 900, CON, playing(t, [TOSSE1, TOSSE2]))
        centered(c, 1240, "ASCOLTALA DUE VOLTE", 30, MUTED, "sans", 700, 4)
        return
    if t < BUCO1:
        centered(c, 520, "HAI SENTITO", 160, fade(WHITE, k(DOMANDA)))
        centered(c, 680, "TUTTE LE PAROLE?", 120, fade(style.PINK, k(DOMANDA + 0.3)))
        centered(c, 860, "SÌ, VERO?", 90, fade(TEXT, k(DOMANDA + 1.0)))
        return
    if t < SPIEGA:
        c.kicker(0, 300, "ORA SENZA IL COLPO", center=True)
        centered(c, 360, "STESSA FRASE.", 140, fade(WHITE, k(BUCO1)))
        centered(c, 500, "SENTI IL BUCO?", 140, fade(style.PINK, k(BUCO1 + 0.2)))
        onda(c, 900, BUCO, playing(t, [BUCO1, BUCO2]), gap_col=style.PINK)
        centered(c, 1150, "IL BATTERI _ TA", 70, fade(TEXT, k(BUCO2)))
        centered(c, 1240, "MANCA UNA LETTERA", 30, fade(MUTED, k(BUCO2 + 0.5)), "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "RIPRISTINO FONEMICO", center=True)
        centered(c, 360, "LA S NON C'ERA", 130, fade(WHITE, k(SPIEGA)))
        centered(c, 490, "NEANCHE PRIMA.", 130, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 700, ["Nella prima versione ho tolto la S",
                           "di \"batterista\" e ci ho messo un colpo.",
                           "Il cervello sa che dovrebbe esserci",
                           "e la ricostruisce da solo.",
                           "Senti una lettera che non c'è.",
                           "",
                           "· Richard Warren · 1970"], SPIEGA + 0.5, k)
        return
    centered(c, 400, "RIASCOLTA", 160, fade(WHITE, k(FINE)))
    centered(c, 560, "CON IL COLPO.", 140, fade(WHITE, k(FINE + 0.2)))
    centered(c, 720, "ORA LA SENTI MANCARE?", 100, fade(style.PINK, k(FINE + 0.4)))
    onda(c, 1000, CON, playing(t, [FINE + 0.6]), gap_col=style.PINK, k=k(FINE + 0.5, 0.4))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "buchi.mp4")
    out.parent.mkdir(exist_ok=True)
    write_mp4(out, build(), END, draw, seed=57)
    print("scritto", out)
