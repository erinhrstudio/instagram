"""Misura i toni del test udito negli stream audio scaricati da YouTube. Uso: python tools/misura_yt.py file..."""
import subprocess, sys, numpy as np
FREQ = [8000, 10000, 12000, 14000, 15000, 16000, 17000, 18000, 19000]
T0, PASSO, DUR = 1.2, 1.7, 1.3
for f in sys.argv[1:]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); sr = 48000
    out = []
    for i, fr in enumerate(FREQ):
        a = int((T0 + i * PASSO + 0.3) * sr); seg = x[a:a + int(0.7 * sr)]
        S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) / len(seg) * 4
        fq = np.fft.rfftfreq(len(seg), 1 / sr); m = abs(fq - fr) < 100
        out.append(f"{fr//1000}k:{20*np.log10(S[m].max()+1e-12):.0f}dB")
    print(f, " ".join(out))
