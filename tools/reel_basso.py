"""Reel "basso fantasma": la fondamentale mancante, da provare sul telefono.

A: sinusoide pura a 55 Hz (il telefono quasi non la riproduce).
B: la stessa nota con solo le armoniche 3-10 (165-550 Hz): nessuna energia a 55 Hz,
   ma il cervello sente comunque la nota bassa.
Poi un riff originale suonato solo con le armoniche. Tutto sintetizzato, niente campioni.

Uso: python -m tools.reel_basso media/basso-fantasma.mp4
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
    1920: dict(title=300, scale=1.0, small=1560, spectrum=1300, expl=380, end=700),
    1350: dict(title=175, scale=0.85, small=1195, spectrum=1030, expl=230, end=440),
    "tiktok": dict(title=280, scale=1.0, small=1330, spectrum=1150, expl=360, end=640),  # testi lontani da barra e pulsanti di TikTok
}
L = LAYOUTS[H]
WHITE = (255, 255, 255)
F0 = 55.0
HARM = range(3, 11)
END = 23.5

# (inizio, fine, titolo, riga piccola, suono)
SCENES = [
    (0.0, 3.7, ["IL TUO TELEFONO", "NON PUÒ SUONARE", "QUESTA NOTA"], "ASCOLTALO DAL TELEFONO · LA 55 HZ", "pura"),
    (3.9, 7.6, ["E ADESSO", "LA SENTI?"], "STESSA NOTA", "fantasma"),
    (7.8, 11.4, ["A 55 HZ", "NON C'È NIENTE"], "SOLO MULTIPLI: 165, 220, 275 HZ…", "fantasma"),
    (11.6, 16.0, ["IL CERVELLO", "LA RICOSTRUISCE"], "UN RIFF SENZA NESSUNA NOTA BASSA", "riff"),
]
SPIEGA = 16.2


def tone(f, dur, harm=None, pluck=False):
    t = np.arange(int(dur * SR)) / SR
    if harm is None:
        x = np.sin(2 * np.pi * f * t)
    else:
        x = sum(np.sin(2 * np.pi * f * h * t + h) / h ** 0.3 for h in harm)
    env = np.minimum(1, t / 0.02) * np.minimum(1, (dur - t) / 0.08)
    if pluck:
        env *= np.exp(-t * 2.2)
    return (x * env).astype(np.float32)


def rms(x, v):
    return x * (v / (np.sqrt(np.mean(x ** 2)) + 1e-9))


def riff():
    # riff originale in mi minore: (semitoni da E1, durata)
    notes = [(0, .45), (0, .25), (3, .45), (5, .45), (0, .45), (10, .45), (7, .9)]
    out = []
    for semi, d in notes:
        out.append(rms(tone(41.2 * 2 ** (semi / 12), d, HARM, pluck=True), 0.12))
    return np.concatenate(out)


def build_audio():
    a = np.zeros(int(END * SR), np.float32)

    def put(t0, x):
        s = int(t0 * SR)
        a[s:s + len(x)] += x[:len(a) - s]
    put(0.5, rms(tone(F0, 3.0), 0.12))
    put(4.3, rms(tone(F0, 3.0, HARM), 0.12))
    put(8.2, rms(tone(F0, 3.0, HARM), 0.12))
    r = riff()
    put(12.0, r)
    return a / np.abs(a).max() * 0.8


def spectrum(audio, t, bins):
    n = 8192
    s = max(0, int(t * SR) - n // 2)
    seg = audio[s:s + n]
    if len(seg) < n:
        seg = np.pad(seg, (0, n - len(seg)))
    X = np.abs(np.fft.rfft(seg * np.hanning(n)))
    f = np.fft.rfftfreq(n, 1 / SR)
    out = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = X[(f >= lo) & (f < hi)]
        v = m.max() if len(m) else 0
        out.append(np.clip((20 * np.log10(v + 1e-9) + 5) / 55, 0, 1))
    return np.array(out)


def fade(rgb, k):
    return tuple(int(v * k + 31 * (1 - k)) for v in rgb)


def frame(c, t, audio, bins):
    k = lambda t0: min(1, max(0, (t - t0) / 0.25))
    scene = next((s for s in SCENES if s[0] <= t < s[1] + 0.2), None)
    if t < SPIEGA and scene:
        t0, _, title, small, kind = scene
        y, size = L["title"], int((150 if len(title) < 3 else 130) * L["scale"])
        for i, l in enumerate(title):
            col = WHITE if i < len(title) - 1 else style.PINK
            c.text((W / 2, y), l, font("display", size), fill=fade(col, k(t0)), anchor="ma")
            y += size
        c.text((W / 2, L["small"]), small, font("sans", 28, 600), fill=MUTED, anchor="ma", tracking=3)
        # spettro 30 Hz - 2 kHz; sotto i 150 Hz la zona che un telefono riproduce a fatica
        gx0, gx1, gy = 110, W - 110, L["spectrum"]
        lx = lambda hz: gx0 + (np.log10(hz) - np.log10(bins[0])) / (np.log10(bins[-1]) - np.log10(bins[0])) * (gx1 - gx0)
        c.rect((gx0, gy - 380, lx(150), gy), fill=(40, 40, 44))
        c.text(((gx0 + lx(150)) / 2, gy - 430), "IL TELEFONO", font("sans", 20, 700), fill=MUTED, anchor="ma", tracking=2)
        c.text(((gx0 + lx(150)) / 2, gy - 404), "QUI NON ARRIVA", font("sans", 20, 700), fill=MUTED, anchor="ma", tracking=2)
        sp = np.max([spectrum(audio, t - d, bins) * (1 - d / 0.3) for d in (0, 0.08, 0.16)], axis=0)
        bw = (gx1 - gx0) / len(sp)
        for j, v in enumerate(sp):
            h = 4 + v * 300
            c.rect((gx0 + j * bw + 2, gy - h, gx0 + (j + 1) * bw - 2, gy), fill=style.PINK)
        c.line([(gx0, gy), (gx1, gy)], fill=LINE)
        if kind != "pura" and t >= t0 + 0.4:
            x = lx(F0)
            for yy in range(int(gy - 300), int(gy), 16):
                c.line([(x, yy), (x, yy + 8)], fill=WHITE, width=2)
            c.text((x, gy - 330), "55 HZ", font("sans", 22, 700), fill=WHITE, anchor="ma", tracking=2)
        for hz, lab in [(55, "55"), (150, "150"), (500, "500"), (1000, "1K")]:
            c.text((lx(hz), gy + 22), lab, font("sans", 22, 600), fill=MUTED, anchor="ma", tracking=1)
        return
    if t < END - 3.2:
        c.kicker(0, L["expl"], "LA FONDAMENTALE MANCANTE", center=True)
        c.text((W / 2, L["expl"] + 80), "NON SENTI LA NOTA.", font("display", 120), fill=fade(WHITE, k(SPIEGA)), anchor="ma")
        c.text((W / 2, L["expl"] + 200), "LA CALCOLI.", font("display", 120), fill=fade(style.PINK, k(SPIEGA)), anchor="ma")
        lines = ["165, 220, 275 Hz sono tutti multipli di 55.",
                 "Il cervello trova il passo comune",
                 "e ti fa sentire la nota che manca.",
                 "",
                 "È il trucco dei plugin «bass enhancer»:",
                 "far sentire il basso anche dove non può suonare."]
        y = L["expl"] + 420
        for i, l in enumerate(lines):
            c.text((W / 2, y), l, font("sans", 38), fill=fade(TEXT, k(SPIEGA + 0.3 + 0.15 * i)), anchor="ma")
            y += 60
        return
    t0 = END - 3.2
    c.text((W / 2, L["end"]), "ORA RIASCOLTALO", font("display", 130), fill=fade(WHITE, k(t0)), anchor="ma")
    c.text((W / 2, L["end"] + 130), "IN CUFFIA", font("display", 130), fill=fade(style.PINK, k(t0)), anchor="ma")
    c.line([(W / 2 - 80, L["end"] + 330), (W / 2 + 80, L["end"] + 330)], fill=style.PINK, width=2)
    c.text((W / 2, L["end"] + 380), "E MANDALO A CHI GIURA DI SENTIRE IL BASSO DAL TELEFONO", font("sans", 26, 700),
           fill=fade(style.PINK_SOFT, k(t0 + 0.5)), anchor="ma", tracking=2)


def render(out, height=1920, page="PSICOACUSTICA", layout=None):
    global H, L
    H, L = height, LAYOUTS[layout or height]
    style.set_accent("azzurro")
    audio = build_audio()
    bins = np.geomspace(30, 2000, 49)
    base = Canvas(W, H, seed=21, bg="pieno")
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
            frame(c, f / FPS, audio, bins)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "basso-fantasma.mp4")
    out.parent.mkdir(exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "tiktok":  # versione per TikTok: ... out.mp4 tiktok
        render(out, layout="tiktok")
    elif len(sys.argv) > 2 and sys.argv[2] == "4:5":  # slide video del carosello: ... out.mp4 4:5 "02 / 06"
        render(out, 1350, sys.argv[3] if len(sys.argv) > 3 else "PSICOACUSTICA")
    else:
        render(out)
    print("scritto", out)
