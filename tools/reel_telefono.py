"""Reel "SA o FA?": lo stesso effetto di Yanny/Laurel, in italiano, con la banda del telefono.

Le sillabe sono sintetizzate una volta con espeak-ng + MBROLA (voce mb-it4) e salvate in
assets/audio/voce-sa.wav e voce-fa.wav. Qui vengono filtrate a 300-3400 Hz (banda telefonica)
e montate in un quiz: prima al telefono, poi senza filtro.

Uso: python -m tools.reel_telefono out/sa-o-fa.mp4           (Reel 9:16)
     python -m tools.reel_telefono posts/x/07.mp4 4:5 "07 / 08"  (slide video del carosello)
"""
import subprocess, sys, tempfile, wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import ImageDraw

from reels import style
from reels.style import Canvas, font, MUTED, TEXT, LINE

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
SR, FPS, W, H = 48000, 30, 1080, 1920
# posizioni verticali: 9:16 per il Reel, 4:5 per la slide video del carosello
LAYOUTS = {
    1920: dict(title=330, small=1500, labels=470, spectrum=1220, end=520),
    1350: dict(title=190, small=1190, labels=330, spectrum=920, end=270),
    "tiktok": dict(title=300, small=1340, labels=440, spectrum=1120, end=480),  # testi lontani da barra e pulsanti di TikTok
}
L = LAYOUTS[H]
WHITE = (255, 255, 255)
ORDER = ["sa", "fa", "fa", "sa"]
STEP = 1.6
ROUND1, ROUND2 = 2.4, 10.8
END = 22.4
LO, HI = 300, 3400


def load(name):
    raw = subprocess.run([FF, "-v", "quiet", "-i", str(ROOT / "assets" / "audio" / f"voce-{name}.wav"),
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def telefono(x):
    """Passa-banda 300-3400 Hz con bordi morbidi (FFT, niente fase)."""
    n = len(x) + SR // 2
    X = np.fft.rfft(x, n)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.clip((f - LO * 0.8) / (LO * 0.2), 0, 1) * np.clip((HI * 1.08 - f) / (HI * 0.08), 0, 1)
    return np.fft.irfft(X * g, n)[:len(x)].astype(np.float32)


def level(x, rms=0.12):
    return x * (rms / (np.sqrt(np.mean(x ** 2)) + 1e-9))


def build_audio():
    clips = {n: load(n) for n in set(ORDER)}
    audio = np.zeros(int(END * SR), np.float32)
    events = []  # (inizio, durata, sillaba, filtrato, clip)
    for r0, filt in [(ROUND1, True), (ROUND2, False)]:
        for i, n in enumerate(ORDER):
            c = level(telefono(clips[n]) if filt else clips[n])
            s = int((r0 + i * STEP) * SR)
            audio[s:s + len(c)] += c
            events.append((r0 + i * STEP, len(c) / SR, n, filt, i))
    peak = np.abs(audio).max()
    return audio / peak * 0.8, events


def spectrum(audio, t, bins):
    """Barre di spettro (dB normalizzati) su una finestra di 46 ms centrata in t."""
    n = 2048
    s = int(t * SR) - n // 2
    seg = audio[max(0, s):max(0, s) + n]
    if len(seg) < n:
        seg = np.pad(seg, (0, n - len(seg)))
    X = np.abs(np.fft.rfft(seg * np.hanning(n)))
    f = np.fft.rfftfreq(n, 1 / SR)
    out = []
    for a, b in zip(bins[:-1], bins[1:]):
        m = X[(f >= a) & (f < b)]
        v = m.max() if len(m) else 0
        out.append(np.clip((20 * np.log10(v + 1e-9) + 22) / 52, 0, 1))
    return np.array(out)


def fade(rgb, k):
    return tuple(int(v * k + 31 * (1 - k)) for v in rgb)


def big(c, y, lines, k, second=None):
    for i, l in enumerate(lines):
        col = fade(WHITE if i == 0 else (second or style.PINK), k)
        c.text((W / 2, y), l, font("display", 150), fill=col, anchor="ma")
        y += 150


def frame(c, t, audio, events, bins):
    k = lambda t0: min(1, max(0, (t - t0) / 0.25))
    if t < ROUND1:
        big(c, L["title"], ["AL TELEFONO", "SA O FA?"], k(0))
        c.text((W / 2, L["small"]), "USA LE CUFFIE · QUATTRO SILLABE", font("sans", 30, 500), fill=MUTED, anchor="ma", tracking=2)
    elif t < END - 5.2:
        filt = t < ROUND2
        r0 = ROUND1 if filt else ROUND2
        if filt and t >= ROUND1 + 4 * STEP:
            big(c, L["title"], ["QUALI ERANO", "LE S?"], k(ROUND1 + 4 * STEP))
            c.text((W / 2, L["small"]), "SCRIVILO NEI COMMENTI, POI ASCOLTA SENZA FILTRO", font("sans", 28, 500),
                   fill=MUTED, anchor="ma", tracking=2)
        else:
            c.kicker(0, L["title"], "AL TELEFONO · 300–3400 HZ" if filt else "SENZA FILTRO · TUTTE LE FREQUENZE", center=True)
            for i, n in enumerate(ORDER):
                x = W / 2 + (i - 1.5) * 210
                on = r0 + i * STEP <= t
                playing = any(e[0] <= t < e[0] + e[1] and e[3] == filt and e[4] == i for e in events)
                lab = f"{i + 1}" if filt else ("S" if n == "sa" else "F")
                col = WHITE if playing else (style.PINK if on else (70, 64, 76))
                c.text((x, L["labels"]), lab, font("display", 170), fill=col, anchor="ma")
        # spettro: la zona fuori banda è grigia nel giro al telefono
        gx0, gx1, gy = 110, W - 110, L["spectrum"]
        c.line([(gx0, gy), (gx1, gy)], fill=LINE)
        # barre con rilascio lento: restano visibili per qualche frame dopo la sillaba
        sp = np.max([spectrum(audio, t - d, bins) * (1 - d / 0.3) for d in (0, 0.06, 0.12, 0.18, 0.24)], axis=0)
        bw = (gx1 - gx0) / len(sp)
        lx = lambda hz: gx0 + (np.log10(hz) - np.log10(bins[0])) / (np.log10(bins[-1]) - np.log10(bins[0])) * (gx1 - gx0)
        for j, v in enumerate(sp):
            mid = (bins[j] + bins[j + 1]) / 2
            inside = LO <= mid <= HI
            col = style.PINK if (inside or not filt) else (70, 64, 76)
            h = 6 + v * 300
            c.rect((gx0 + j * bw + 2, gy - h, gx0 + (j + 1) * bw - 2, gy), fill=col)
        if filt:
            for hz in (LO, HI):
                c.line([(lx(hz), gy - 330), (lx(hz), gy + 12)], fill=style.PINK_SOFT, width=2)
        for hz, lab in [(300, "300"), (1000, "1K"), (3400, "3,4K"), (7000, "7K")]:
            c.text((lx(hz), gy + 22), lab, font("sans", 22, 600), fill=MUTED, anchor="ma", tracking=1)
        c.text((W / 2, gy + 80), "LA S VIVE SOPRA I 4 KHZ", font("sans", 26, 700), fill=style.PINK_SOFT,
               anchor="ma", tracking=4)
    else:
        t0 = END - 5.2
        c.kicker(0, L["end"], "PSICOACUSTICA", center=True)
        big(c, L["end"] + 80, ["IL TELEFONO", "TAGLIA LA S"], k(t0))
        c.text((W / 2, L["end"] + 440), "Per questo diciamo", font("serif", 52), fill=fade(TEXT, k(t0 + 0.4)), anchor="ma")
        c.text((W / 2, L["end"] + 510), "“S come Savona, F come Firenze”.", font("serif", 52),
               fill=fade(TEXT, k(t0 + 0.4)), anchor="ma")
        c.line([(W / 2 - 80, L["end"] + 650), (W / 2 + 80, L["end"] + 650)], fill=style.PINK, width=2)
        c.text((W / 2, L["end"] + 710), "STESSO TRUCCO DI YANNY / LAUREL", font("sans", 30, 700),
               fill=fade(style.PINK_SOFT, k(t0 + 0.8)), anchor="ma", tracking=5)


def render(out, height=1920, page="PSICOACUSTICA", layout=None):
    global H, L
    H, L = height, LAYOUTS[layout or height]
    style.set_accent("azzurro")
    audio, events = build_audio()
    bins = np.geomspace(150, 8000, 41)
    base = Canvas(W, H, seed=11, bg="pieno")
    base.header("ERIN · HOME RECORDING STUDIO", page)
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
        for f in range(int(END * FPS)):
            c = Canvas.__new__(Canvas)
            c.w, c.h = W, H
            c.img = base_img.copy()
            c.d = ImageDraw.Draw(c.img)
            frame(c, f / FPS, audio, events, bins)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")


if __name__ == "__main__":
    # python -m tools.reel_telefono out.mp4 [4:5 "07 / 08"]
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "sa-o-fa.mp4")
    out.parent.mkdir(exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "tiktok":  # versione per TikTok: ... out.mp4 tiktok
        render(out, layout="tiktok")
    elif len(sys.argv) > 2 and sys.argv[2] == "4:5":
        render(out, 1350, sys.argv[3] if len(sys.argv) > 3 else "PSICOACUSTICA")
    else:
        render(out)
    print("scritto", out)
