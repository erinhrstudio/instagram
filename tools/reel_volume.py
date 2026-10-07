"""Reel "più forte = migliore": blind test A/B dove B è lo stesso identico loop, solo 3 dB più forte.

Poi la rivelazione, lo stesso confronto a volume pari e la spiegazione (curve isofoniche,
Fletcher e Munson 1933). Loop di batteria e basso sintetizzato (reels.render.make_loop).

Uso: python -m tools.reel_volume media/tiktok/piu-forte.mp4
"""
import subprocess, sys, tempfile, wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import ImageDraw

from reels import style
from reels.render import make_loop, SR
from reels.style import Canvas, font, MUTED, TEXT, LINE

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent.parent
FPS, W, H = 30, 1080, 1920
WHITE = (255, 255, 255)
BAR = 2.4          # una battuta a 100 bpm
DB = 3.0           # quanto è più forte B
END = 24.5

# (inizio, lettera, guadagno in dB) — il contenuto audio è sempre lo stesso loop
PLAY = [(0.0, "A", 0), (BAR, "B", DB), (2 * BAR, "A", 0), (3 * BAR, "B", DB),     # blind test
        (14.0, "A", 0), (14.0 + BAR, "B", 0)]                                       # volume pari
BLIND_END = 4 * BAR
REVEAL, HONEST, SPIEGA, FINE = 11.0, 14.0, 14.0 + 2 * BAR, 21.6


def build_audio():
    loop = make_loop(seed=4, bpm=100, bars=1)[:, 0]
    loop = loop[:int(BAR * SR)]
    loop *= np.minimum(1, np.arange(len(loop)) / (0.003 * SR))
    a = np.zeros(int(END * SR))
    for t0, _, g in PLAY:
        s = int(t0 * SR)
        a[s:s + len(loop)] += loop * 10 ** (g / 20)
    peak_b = np.abs(loop).max() * 10 ** (DB / 20)
    return (a / peak_b * 0.89).astype(np.float32)   # B arriva a circa -1 dBFS, niente clipping


def fade(rgb, k):
    return tuple(int(v * k + 31 * (1 - k)) for v in rgb)


def centered(c, y, s, size, fill, kind="display", weight=400, tracking=0):
    c.text((W / 2, y), s, font(kind, size, weight), fill=fill, anchor="ma", tracking=tracking)


def pulse(c, t, t0, y):
    """Indicatore di riproduzione con altezza fissa: non deve rivelare quale è più forte."""
    for j in range(15):
        h = 40 + 30 * np.sin(t * 9 + j * 0.8) ** 2
        x = W / 2 + (j - 7) * 36
        c.rect((x - 8, y - h / 2, x + 8, y + h / 2), fill=style.PINK)


def meters(c, y, kA, kB):
    for x, lab, db, k in [(W / 2 - 170, "A", 0, kA), (W / 2 + 170, "B", DB, kB)]:
        h = 420 * 10 ** ((db - DB) / 20)
        c.rect((x - 70, y - 420, x + 70, y), outline=LINE, width=2)
        c.rect((x - 70, y - h * k, x + 70, y), fill=style.PINK if lab == "B" else (120, 120, 126))
        c.text((x, y + 30), lab, font("display", 90), fill=WHITE, anchor="ma")
        c.text((x, y - h - 50), "+3 dB" if lab == "B" else "0 dB", font("sans", 30, 700),
               fill=fade(WHITE, k), anchor="ma", tracking=2)


def frame(c, t):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    cur = next((p for p in PLAY if p[0] <= t < p[0] + BAR), None)
    if t < BLIND_END:
        c.kicker(0, 300, "BLIND TEST · IN CUFFIA", center=True)
        centered(c, 360, "QUALE SUONA", 140, WHITE)
        centered(c, 500, "MEGLIO?", 140, style.PINK)
        if cur:
            centered(c, 700, cur[1], 520, WHITE)
            pulse(c, t, cur[0], 1235)
        centered(c, 1305, "PRIMO ASCOLTO" if t < 2 * BAR else "ANCORA UNA VOLTA", 28, MUTED, "sans", 600, 4)
        return
    if t < REVEAL:
        centered(c, 620, "SCEGLI.", 200, fade(WHITE, k(BLIND_END)))
        centered(c, 860, "SCOMMETTO B.", 120, fade(style.PINK, k(BLIND_END + 0.7)))
        return
    if t < HONEST:
        centered(c, 300, "SONO IDENTICI.", 150, fade(WHITE, k(REVEAL)))
        centered(c, 460, "STESSO LOOP, STESSO MIX.", 34, fade(TEXT, k(REVEAL + 0.4)), "sans", 600, 3)
        centered(c, 510, "B È SOLO PIÙ FORTE.", 34, fade(style.PINK_SOFT, k(REVEAL + 0.8)), "sans", 700, 3)
        meters(c, 1080, k(REVEAL + 1.0, 0.6), k(REVEAL + 1.0, 0.6))
        return
    if t < SPIEGA:
        c.kicker(0, 300, "ORA ALLO STESSO VOLUME", center=True)
        centered(c, 360, "LA DIFFERENZA", 140, WHITE)
        centered(c, 500, "C'È ANCORA?", 140, style.PINK)
        if cur:
            centered(c, 700, cur[1], 520, WHITE)
            pulse(c, t, cur[0], 1235)
        return
    if t < FINE:
        c.kicker(0, 330, "PERCHÉ CI CASCHI", center=True)
        centered(c, 400, "PIÙ FORTE", 150, fade(WHITE, k(SPIEGA)))
        centered(c, 550, "SEMBRA MEGLIO", 150, fade(style.PINK, k(SPIEGA)))
        lines = ["A volume basso l'orecchio sente meno",
                 "bassi e meno acuti. Alzando, tornano.",
                 "Il cervello lo scambia per qualità.",
                 "",
                 "Curve isofoniche · Fletcher e Munson, 1933"]
        y = 820
        for i, l in enumerate(lines):
            col = MUTED if i == 4 else TEXT
            c.text((W / 2, y), l, font("sans", 40 if i < 4 else 28, 400 if i < 4 else 600),
                   fill=fade(col, k(SPIEGA + 0.3 + 0.2 * i)), anchor="ma", tracking=0 if i < 4 else 2)
            y += 64
        return
    centered(c, 420, "PRIMA DI GIUDICARE", 110, fade(WHITE, k(FINE)))
    centered(c, 540, "UN PLUGIN:", 110, fade(WHITE, k(FINE)))
    centered(c, 680, "STESSO VOLUME.", 150, fade(style.PINK, k(FINE + 0.3)))
    c.line([(W / 2 - 80, 920), (W / 2 + 80, 920)], fill=style.PINK, width=2)
    centered(c, 970, "TU QUALE AVEVI SCELTO? A O B", 32, fade(style.PINK_SOFT, k(FINE + 0.8)), "sans", 700, 3)


def render(out):
    style.set_accent("azzurro")
    audio = build_audio()
    base = Canvas(W, H, seed=33, bg="pieno")
    base.header("ERIN · HOME RECORDING STUDIO", "PSICOACUSTICA")
    base_img = base.img.copy()
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.repeat(audio[:, None], 2, 1) * 32767).astype("<i2").tobytes())
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                              str(out)], stdin=subprocess.PIPE)
        for f in range(int(END * FPS)):
            c = Canvas.__new__(Canvas)
            c.w, c.h = W, H
            c.img = base_img.copy()
            c.d = ImageDraw.Draw(c.img)
            frame(c, f / FPS)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "piu-forte.mp4")
    out.parent.mkdir(exist_ok=True)
    render(out)
    print("scritto", out)
