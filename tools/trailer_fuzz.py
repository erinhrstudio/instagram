"""Trailer Reel della serie "Diario di un fuzz" (episodio 0) con l'audio vero del crepitio.

Uso: python -m tools.trailer_fuzz out/diario-di-un-fuzz-trailer.mp4
"""
import subprocess, sys, tempfile, wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

from reels.style import Canvas, font, MUTED, PINK, PINK_SOFT, TEXT, LINE

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
SR, FPS, W, H = 48000, 30, 1080, 1920
CLIP = ROOT / "assets" / "audio" / "crepitio-y1.wav"
GAP = 0.35
WHITE = (255, 255, 255)


def load_clip():
    raw = subprocess.run([FF, "-v", "quiet", "-i", str(CLIP), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return x / np.abs(x).max() * 0.79


def build_audio(clip):
    gap = np.zeros(int(GAP * SR), np.float32)
    parts, starts, t = [], [], 0.0
    for _ in range(3):
        starts.append(t)
        parts += [clip, gap]
        t += (len(clip) + len(gap)) / SR
    tail = np.zeros(int(4.2 * SR), np.float32)
    return np.concatenate(parts + [tail]), starts


def clicks(clip):
    d = np.abs(np.diff(clip))
    idx = np.where(d > 0.15 * 0.79 / 0.816)[0]
    out, last = [], -10**9
    for i in idx:
        if i - last > SR * 0.004:
            out.append(i / SR)
        last = i
    return out


# testi per sezione (inizio, fine, righe grandi, riga piccola)
SCENES = [
    (0.0, 4.2, ["SENTI QUESTO", "SCHIFO?"], "USA LE CUFFIE"),
    (4.45, 8.7, ["MI HA RUBATO", "MESI."], "UN PLUGIN FUZZ. UN DIFETTO CHE NON VOLEVA MORIRE."),
    (8.9, 11.0, ["NON ERA", "L'ALIASING."], "E NEANCHE IL TIMING."),
    (11.0, 13.2, ["E ALLORA", "COS'ERA?"], ""),
]


def render(out):
    clip = load_clip()
    audio, starts = build_audio(clip)
    total = len(audio) / SR
    cl = []
    dur = len(clip) / SR
    # forma d'onda del clip: picchi per colonna
    gx0, gx1, gy = 90, W - 90, 1010
    cols = gx1 - gx0
    seg = np.array_split(clip, cols)
    peaks = np.array([np.abs(s).max() for s in seg])

    base = Canvas(W, H, seed=7, bg="pieno")
    base.header("ERIN · HOME RECORDING STUDIO", "EP 00")
    base_img = base.img.copy()

    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((audio * 32767).astype("<i2").tobytes())
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
                             stdin=subprocess.PIPE)
        for f in range(int(total * FPS)):
            t = f / FPS
            c = Canvas.__new__(Canvas)
            c.w, c.h = W, H
            c.img = base_img.copy()
            from PIL import ImageDraw
            c.d = ImageDraw.Draw(c.img)
            frame(c, t, starts, dur, cl, peaks, gx0, gy, total)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")


def frame(c, t, starts, dur, cl, peaks, gx0, gy, total):
    # posizione di riproduzione dentro il clip (None se fra un clip e l'altro)
    pos = next((t - s for s in starts if 0 <= t - s < dur), None)
    finale = t >= starts[-1] + dur + GAP
    if not finale:
        # forma d'onda: parte suonata in rosa, resto in grigio
        played = int(len(peaks) * (pos / dur)) if pos is not None else (len(peaks) if t > starts[0] else 0)
        for k, pk in enumerate(peaks):
            h = max(2, pk * 230)
            col = PINK if k < played else (70, 64, 76)
            c.line([(gx0 + k, gy - h), (gx0 + k, gy + h)], fill=col, width=1)
        c.line([(gx0, gy), (gx0 + len(peaks), gy)], fill=LINE)
        if pos is not None:
            x = gx0 + len(peaks) * pos / dur
            c.line([(x, gy - 260), (x, gy + 260)], fill=WHITE, width=2)
        for s0, s1, big, small in SCENES:
            if s0 <= t < s1:
                a = min(1, (t - s0) / 0.25)
                col = tuple(int(v * a + 31 * (1 - a)) for v in WHITE)
                y = 330
                for i, l in enumerate(big):
                    fill = col if i == 0 else tuple(int(v * a + 31 * (1 - a)) for v in PINK)
                    c.text((W / 2, y), l, font("display", 150), fill=fill, anchor="ma")
                    y += 150
                if small:
                    c.text((W / 2, 1500), small, font("sans", 30, 500), fill=MUTED, anchor="ma", tracking=2)
        return
    # finale: titolo della serie
    k = min(1, (t - (starts[-1] + dur + GAP)) / 0.4)
    fade = lambda rgb: tuple(int(v * k + 31 * (1 - k)) for v in rgb)
    c.kicker(0, 560, "UNA STORIA VERA IN 10 EPISODI", center=True)
    c.text((W / 2, 640), "DIARIO", font("display", 230), fill=fade(WHITE), anchor="ma")
    c.text((W / 2, 850), "DI UN FUZZ", font("display", 230), fill=fade(PINK), anchor="ma")
    c.text((W / 2, 1120), "Episodio 1 · giovedì, ore 21:00", font("serif", 48), fill=fade(TEXT), anchor="ma")
    c.line([(W / 2 - 80, 1230), (W / 2 + 80, 1230)], fill=PINK, width=2)
    c.text((W / 2, 1290), "SEGUI PER NON PERDERLO", font("sans", 30, 700), fill=fade(PINK_SOFT), anchor="ma", tracking=5)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "diario-di-un-fuzz-trailer.mp4")
    out.parent.mkdir(exist_ok=True)
    render(out)
    print("scritto", out)
