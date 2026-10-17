"""Prepara una registrazione vocale di Giuseppe (memo del telefono) per un Reel.

Trova le prese (frasi separate da pause), tiene la più lunga tra quelle complete o quella indicata,
toglie i bassi sotto 80 Hz, attenua un po' il rumore di fondo e stampa dove sono le S (energia sopra 4 kHz).

Uso: python -m tools.voce_vera <memo.m4a> <uscita.wav> [numero_presa]
"""
import subprocess, sys, tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, istft, sosfiltfilt, stft

SR = 44100


def leggi(path):
    with tempfile.TemporaryDirectory() as d:
        w = Path(d) / "x.wav"
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-v", "error", "-i", str(path),
                        "-ac", "1", "-ar", str(SR), str(w)], check=True)
        _, x = wavfile.read(w)
    x = x.astype(float) / 32768
    return sosfiltfilt(butter(4, 80, "hp", fs=SR, output="sos"), x)


def prese(x, pausa=0.18):
    """Intervalli (inizio, fine) in secondi delle frasi, separate da pause di almeno `pausa` secondi."""
    h = int(0.01 * SR)
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + h] ** 2)) + 1e-9) for i in range(0, len(x) - h, h)])
    soglia = np.percentile(db, 15) + 0.35 * (db.max() - np.percentile(db, 15))
    att = db > soglia
    out, s, ultimo = [], None, 0
    for i, a in enumerate(att):
        if a:
            if s is None:
                s = i
            ultimo = i
        elif s is not None and i - ultimo > pausa * 100:
            if (ultimo - s) > 80:          # almeno 0,8 s: una frase, non un respiro
                out.append((s / 100, ultimo / 100 + 0.01))
            s = None
    if s is not None and ultimo - s > 80:
        out.append((s / 100, ultimo / 100 + 0.01))
    return out, db, soglia


def esse(x, t0, t1):
    f, t, Z = stft(x[int(t0 * SR):int(t1 * SR)], SR, nperseg=256, noverlap=256 - 44)
    P = np.abs(Z) ** 2
    r = 10 * np.log10(P[f > 4000].sum(0) / (P[(f > 100) & (f < 3000)].sum(0) + 1e-12) + 1e-12)
    lvl = 10 * np.log10(P.sum(0) + 1e-12)
    on = (r > 0) & (lvl > lvl.max() - 30)
    out, s = [], None
    for i, a in enumerate(on):
        if a and s is None:
            s = i
        if not a and s is not None:
            if t[i] - t[s] > 0.04:
                out.append((round(t[s], 3), round(t[i], 3)))
            s = None
    return out


def pulisci(x, t0, t1, rumore):
    seg = x[int(t0 * SR):int(t1 * SR)]
    n = 1024
    _, _, N = stft(rumore, SR, nperseg=n)
    prof = np.mean(np.abs(N), 1, keepdims=True)
    _, _, Z = stft(seg, SR, nperseg=n)
    g = np.clip(1 - 1.5 * prof / (np.abs(Z) + 1e-9), 0.3, 1)   # al massimo -10 dB
    _, y = istft(Z * g, SR, nperseg=n)
    y = y[:len(seg)]
    r = int(0.02 * SR)
    y[:r] *= np.linspace(0, 1, r)
    y[-r:] *= np.linspace(1, 0, r)
    return y / np.abs(y).max() * 0.9


if __name__ == "__main__":
    x = leggi(sys.argv[1])
    ps, db, soglia = prese(x)
    print("prese:", [(round(a, 2), round(b, 2)) for a, b in ps])
    k = int(sys.argv[3]) - 1 if len(sys.argv) > 3 else int(np.argmax([b - a for a, b in ps]))
    a, b = ps[k]
    a, b = max(0, a - 0.15), min(len(x) / SR, b + 0.2)
    quiete = db < soglia - 6
    idx = np.where(quiete)[0]
    rumore = np.concatenate([x[i * int(0.01 * SR):(i + 1) * int(0.01 * SR)] for i in idx]) if len(idx) > 20 else x[:int(0.3 * SR)]
    y = pulisci(x, a, b, rumore)
    wavfile.write(sys.argv[2], SR, (y * 32767).astype(np.int16))
    print(f"presa {k + 1}: {a:.2f}-{b:.2f} s, durata {b - a:.2f} s")
    print("S nel file:", esse(y, 0, b - a))
