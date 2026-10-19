"""Trascrive un memo vocale con Whisper (faster-whisper), con il tempo di ogni parola.

Gira su GitHub Actions (il modello si scarica da Hugging Face). Scrive <audio>.trascrizione.json
accanto al file e stampa le frasi con i tempi.

Uso: python -m tools.trascrivi posts/<nome>/memo.m4a [modello]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


def carica(audio):
    """Audio a 16 kHz mono con ffmpeg (evita il decoder av di faster-whisper)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def main():
    audio = Path(sys.argv[1])
    modello = sys.argv[2] if len(sys.argv) > 2 else "medium"
    m = WhisperModel(modello, device="cpu", compute_type="int8")
    segs, info = m.transcribe(carica(audio), language="it", word_timestamps=True, vad_filter=True)
    out = []
    for s in segs:
        parole = [{"w": w.word.strip(), "t0": round(w.start, 2), "t1": round(w.end, 2), "p": round(w.probability, 2)}
                  for w in (s.words or [])]
        out.append({"t0": round(s.start, 2), "t1": round(s.end, 2), "testo": s.text.strip(), "parole": parole})
        print(f"{s.start:6.2f}-{s.end:6.2f}  {s.text.strip()}")
    dest = audio.with_name(audio.stem + ".trascrizione.json")
    dest.write_text(json.dumps({"durata": round(info.duration, 2), "frasi": out}, ensure_ascii=False, indent=1))
    print("scritto", dest)


if __name__ == "__main__":
    main()
