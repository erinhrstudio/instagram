"""Reel "il fischio nel silenzio" v2 (20/11): rifatto dopo i commenti "non si sente".

Cosa cambia rispetto a tools/reel_zwicker.py (la v1 resta com'era):
- rumore rosa invece che bianco: meno sibilo acuto, meno fastidioso, e il bordo basso del buco
  ha più energia rispetto agli acuti;
- buco di un'ottava (2-4 kHz) invece di mezza ottava (2,8-4 kHz);
- livello circa -16 LUFS invece di -8,5: gli altoparlanti del telefono non distorcono
  (la distorsione riempie il buco) e nessuno abbassa il volume per il fastidio;
- prima del rumore: cartello grande "headphones on", non una riga piccola;
- due tentativi: dopo il primo silenzio si sente per 2 secondi un tono VERO e debole, dichiarato
  come tale, per far capire che cosa cercare; poi rumore e silenzio una seconda volta.

Uso: python -m tools.reel_zwicker_v2 out/fischio-silenzio-v2.mp4
"""
import sys
from pathlib import Path

import numpy as np

import tools.reel_shepard as rs
from reels import style
from reels.style import MUTED, TEXT
from tools.reel_shepard import SR, WHITE, centered, fade, paragraph, write_mp4
from tools.reel_zwicker import spectrum as spectrum_v1
import tools.reel_zwicker as z1

ROOT = Path(__file__).resolve().parent.parent
NOTCH = (2000, 4000)
TONO = 2300            # tono di riferimento, dentro il buco vicino al bordo basso
R1, S1 = 0.3, 10.3     # rumore 1, silenzio 1
REF, REF_END = 14.8, 17.3
R2, S2 = 17.8, 25.8    # rumore 2, silenzio 2
SPIEGA, FINE, END = 30.8, 36.0, 40.0
LUFS_TARGET = -16.0


def rumore(n, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.zeros_like(f)
    ok = (f > 80) & (f < 12000)
    g[ok] = 1 / np.sqrt(f[ok])              # rosa: -3 dB per ottava
    g[(f > NOTCH[0]) & (f < NOTCH[1])] = 0
    x = np.fft.irfft(X * g, n)
    x /= np.sqrt((x ** 2).mean())           # rms 1
    r = int(0.4 * SR)
    x[:r] *= np.linspace(0, 1, r)
    e = int(0.02 * SR)                      # fine netta: il fischio arriva quando il rumore sparisce
    x[-e:] *= np.linspace(1, 0, e)
    return x


def build():
    rng = np.random.default_rng(9)
    a = np.zeros(int(END * SR))
    for t0, t1 in ((R1, S1), (R2, S2)):
        x = rumore(int((t1 - t0) * SR), rng)
        a[int(t0 * SR):int(t0 * SR) + len(x)] = x * 0.1          # rms -20 dBFS circa
    t = np.arange(int((REF_END - REF) * SR)) / SR
    env = np.minimum(1, np.minimum(t / 0.3, (t[-1] - t) / 0.3))
    a[int(REF * SR):int(REF * SR) + len(t)] = 0.012 * env * np.sin(2 * np.pi * TONO * t)  # debole, ~-38 dBFS
    return a


def spectrum(c, t, on=True, ghost=0.0):
    z1.NOTCH = NOTCH
    spectrum_v1(c, t, on=on, ghost=ghost)


def draw(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    ghost = lambda t0: 0.35 + 0.35 * np.sin((t - t0) * 3) ** 2 if t > t0 + 1 else 0
    if t < S1:
        centered(c, 300, "HEADPHONES ON.", 130, WHITE)
        centered(c, 440, "SOUND UP. QUIET ROOM.", 90, style.PINK)
        centered(c, 580, "LISTEN TO THE NOISE, THEN THE SILENCE", 34, TEXT, "sans", 700, 3)
        spectrum(c, t)
        left = max(1, int(np.ceil(S1 - t)))
        centered(c, 1240, f"SILENCE IN {left} SECOND{'S' if left > 1 else ''}", 30, MUTED, "sans", 700, 4)
        return
    if t < REF:
        c.kicker(0, 300, "NOTHING IS PLAYING NOW", center=True)
        centered(c, 360, "DO YOU HEAR", 150, fade(WHITE, k(S1)))
        centered(c, 510, "A WHISTLE?", 150, fade(style.PINK, k(S1 + 0.2)))
        spectrum(c, t, on=False, ghost=ghost(S1))
        centered(c, 1240, "THE VIDEO IS SILENT, I SWEAR", 30, fade(MUTED, k(S1 + 2.0)), "sans", 700, 4)
        return
    if t < R2:
        c.kicker(0, 300, "HEARD NOTHING?", center=True)
        centered(c, 360, "THIS IS A REAL TONE.", 110, fade(WHITE, k(REF - 0.3)))
        centered(c, 490, "LISTEN FOR SOMETHING LIKE IT.", 80, fade(style.PINK, k(REF)))
        centered(c, 1240, "SECOND TRY IN A MOMENT", 30, fade(MUTED, k(REF + 0.5)), "sans", 700, 4)
        return
    if t < S2:
        c.kicker(0, 300, "SECOND TRY", center=True)
        centered(c, 360, "NOISE AGAIN.", 130, WHITE)
        centered(c, 500, "FOCUS ON THE SILENCE.", 90, style.PINK)
        spectrum(c, t)
        left = max(1, int(np.ceil(S2 - t)))
        centered(c, 1240, f"SILENCE IN {left} SECOND{'S' if left > 1 else ''}", 30, MUTED, "sans", 700, 4)
        return
    if t < SPIEGA:
        c.kicker(0, 300, "NOTHING IS PLAYING NOW", center=True)
        centered(c, 360, "NOW?", 190, fade(style.PINK, k(S2)))
        spectrum(c, t, on=False, ghost=ghost(S2))
        centered(c, 1240, "THE VIDEO IS SILENT, I SWEAR", 30, fade(MUTED, k(S2 + 1.5)), "sans", 700, 4)
        return
    if t < FINE:
        c.kicker(0, 300, "ZWICKER TONE", center=True)
        centered(c, 360, "THE WHISTLE", 140, fade(WHITE, k(SPIEGA)))
        centered(c, 500, "IS IN YOUR HEAD.", 120, fade(style.PINK, k(SPIEGA + 0.2)))
        paragraph(c, 710, ["The noise had a slice of frequencies missing.",
                           "When the noise stops, your hearing",
                           "fills that gap for a few seconds",
                           "with a faint note that doesn't exist.",
                           "Not everyone hears it, and that's normal.",
                           "",
                           "· Eberhard Zwicker · 1964"], SPIEGA + 0.5, k)
        return
    centered(c, 420, "FIRST TRY, SECOND,", 130, fade(WHITE, k(FINE)))
    centered(c, 570, "OR NEVER?", 160, fade(style.PINK, k(FINE + 0.3)))
    centered(c, 780, "TELL ME IN THE COMMENTS", 40, fade(TEXT, k(FINE + 0.8)), "sans", 700, 3)
    centered(c, 860, "FOLLOW @ERIN.SOUNDLAB FOR MORE", 34, fade(MUTED, k(FINE + 1.2)), "sans", 700, 3)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "fischio-silenzio-v2.mp4")
    out.parent.mkdir(exist_ok=True)
    rs.NUMERI[out.stem] = 4          # etichetta "AUDIO ILLUSION #4", senza chiusura "next illusion"
    audio = build()
    write_mp4(out, audio, END, draw, seed=59, picco=np.abs(audio).max())  # nessuna normalizzazione al picco
    print("scritto", out)
