"""Voce italiana sintetica (espeak-ng + MBROLA it4) con i tempi di ogni fonema.

tts("frase") -> (audio float32 a 44.1 kHz, [(fonema, inizio_s, durata_s), ...])
Si genera il file .pho con espeak-ng e lo si fa leggere a mbrola, così i tempi coincidono.
"""
import subprocess, tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np

SR = 44100
FF = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "/usr/share/mbrola/it4/it4"


def tts(text, speed=135, pitch=50):
    pho = subprocess.run(["espeak-ng", "-v", "mb-it4", "-s", str(speed), "-p", str(pitch), "-q", "--pho", text],
                         capture_output=True, text=True, check=True).stdout
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.pho"
        p.write_text(pho)
        wav = Path(td) / "x.wav"
        subprocess.run(["mbrola", "-e", VOICE, str(p), str(wav)], capture_output=True, check=True)
        raw = subprocess.run([FF, "-v", "quiet", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32).copy()
    times, t = [], 0.0
    for line in pho.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        d = int(parts[1]) / 1000
        times.append((parts[0], t, d))
        t += d
    return audio, times


def pho_audio(pho):
    """Sintetizza direttamente un testo .pho di MBROLA (fonemi, durate e intonazione scelte a mano)."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.pho"
        p.write_text(pho)
        wav = Path(td) / "x.wav"
        subprocess.run(["mbrola", "-e", VOICE, str(p), str(wav)], capture_output=True, check=True)
        raw = subprocess.run([FF, "-v", "quiet", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
