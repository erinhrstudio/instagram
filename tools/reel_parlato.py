"""Reel "parlato che diventa canto" (illusione speech-to-song di Diana Deutsch, 1995).

Una frase detta una volta dentro un discorso, poi ripetuta identica in loop: dopo qualche
ripetizione quasi tutti la sentono cantata. Voce italiana sintetica (espeak-ng + mbrola it4).

Uso: python -m tools.reel_parlato media/tiktok/parlato-canto.mp4
"""
import subprocess, sys, tempfile, wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import ImageDraw

from reels import style
from reels.style import Canvas, font, MUTED, TEXT

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
SR, FPS, W, H = 16000, 30, 1080, 1920
WHITE = (255, 255, 255)
PREFIX = "Quando ascolto un vocale,"
FRASE = "a volte suona così strano"
REPS = 7
GAP = 0.45
END = 40.0  # ricalcolato in build_audio


def tts(text, path):
    subprocess.run(["espeak-ng", "-v", "mb-it4", "-s", "140", "-p", "55", text, "-w", str(path)], check=True)
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    nz = np.flatnonzero(np.abs(x) > 0.01)
    return x[nz[0]:nz[-1] + 1]


def build_audio(td):
    global END
    pre, fr = tts(PREFIX, td / "p.wav"), tts(FRASE, td / "f.wav")
    a = np.zeros(int(END * SR), np.float32)
    events = []                       # (inizio, fine, numero ripetizione)
    t = 0.3
    s = int(t * SR); a[s:s + len(pre)] = pre
    t += len(pre) / SR + 0.12
    for i in range(REPS + 1):         # 0 = dentro la frase, poi le ripetizioni
        s = int(t * SR); a[s:s + len(fr)] = fr
        events.append((t, t + len(fr) / SR, i))
        t += len(fr) / SR + (0.25 if i == 0 else GAP)
        if i == 0:
            t += 0.6
    END = round(events[-1][1] + 0.3 + 3.2 + 4.8 + 3.0, 2)
    a = a[:int(END * SR)]
    return a / np.abs(a).max() * 0.89, events


def centered(c, y, s, size, fill, kind="display", weight=400, tracking=0):
    c.text((W / 2, y), s, font(kind, size, weight), fill=fill, anchor="ma", tracking=tracking)


def fade(rgb, k):
    return tuple(int(v * k + 31 * (1 - k)) for v in rgb)


def frame(c, t, events):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    loop_end = events[-1][1]
    if t < loop_end + 0.3:
        cur = max((e for e in events if e[0] - 0.1 <= t), key=lambda e: e[0], default=events[0])
        n = cur[2]
        c.kicker(0, 300, "ESPERIMENTO · ALZA IL VOLUME", center=True)
        if n == 0:
            centered(c, 380, "ASCOLTA", 150, WHITE)
            centered(c, 530, "QUESTA FRASE", 150, style.PINK)
        else:
            centered(c, 380, "ORA SOLO", 150, WHITE)
            centered(c, 530, "LEI, IN LOOP", 150, style.PINK)
        centered(c, 760, f"«{FRASE}»", 46, TEXT, "serif")
        if n > 0:
            centered(c, 860, f"{n}", 300, fade(WHITE, k(cur[0] - 0.1, 0.1)))
            centered(c, 1180, "CANTA GIÀ?" if n >= 5 else "RIPETIZIONE", 30, MUTED, "sans", 700, 4)
        return
    t0 = loop_end + 0.3
    if t < t0 + 3.2:
        centered(c, 520, "LA STAI", 180, fade(WHITE, k(t0)))
        centered(c, 700, "CANTANDO?", 180, fade(style.PINK, k(t0 + 0.3)))
        return
    t1 = t0 + 3.2
    if t < END - 3.0:
        c.kicker(0, 330, "SPEECH-TO-SONG", center=True)
        centered(c, 400, "NON HO CAMBIATO", 130, fade(WHITE, k(t1)))
        centered(c, 535, "NIENTE.", 130, fade(style.PINK, k(t1 + 0.2)))
        lines = ["Ripetendola, il cervello smette di",
                 "ascoltare il significato e segue",
                 "le altezze della voce: la melodia",
                 "che c'era già.",
                 "",
                 "Illusione scoperta da Diana Deutsch, 1995"]
        y = 760
        for i, l in enumerate(lines):
            last = i == len(lines) - 1
            c.text((W / 2, y), l, font("sans", 28 if last else 40, 600 if last else 400),
                   fill=fade(MUTED if last else TEXT, k(t1 + 0.4 + 0.15 * i)), anchor="ma", tracking=2 if last else 0)
            y += 64
        return
    t2 = END - 3.0
    centered(c, 560, "RIASCOLTALO", 160, fade(WHITE, k(t2)))
    centered(c, 720, "DALL'INIZIO", 160, fade(style.PINK, k(t2 + 0.2)))
    centered(c, 960, "LA PRIMA VOLTA ADESSO CANTA", 32, fade(style.PINK_SOFT, k(t2 + 0.6)), "sans", 700, 3)


def render(out):
    style.set_accent("azzurro")
    base = Canvas(W, H, seed=44, bg="pieno")
    base.header("ERIN · HOME RECORDING STUDIO", "PSICOACUSTICA")
    base_img = base.img.copy()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        audio, events = build_audio(td)
        wav = td / "a.wav"
        st = np.repeat(audio[:, None], 2, 1)
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((st * 32767).astype("<i2").tobytes())
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart",
                              str(out)], stdin=subprocess.PIPE)
        for f in range(int(END * FPS)):
            c = Canvas.__new__(Canvas)
            c.w, c.h = W, H
            c.img = base_img.copy()
            c.d = ImageDraw.Draw(c.img)
            frame(c, f / FPS, events)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")
        print("fine loop a", round(events[-1][1], 1), "s")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "parlato-canto.mp4")
    out.parent.mkdir(exist_ok=True)
    render(out)
    print("scritto", out)
