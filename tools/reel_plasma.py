"""Pedali impossibili #01 · Gamechanger Plasma: "questa distorsione è un fulmine".

Audio interamente ricostruito da noi (nessuna demo altrui): un riff di chitarra sintetizzato
(Karplus-Strong) prima pulito, poi passato in un modello del principio del Plasma:
soglia (la scintilla scocca solo sopra un certo livello, quindi fa anche da gate),
clipping estremo e "scoppiettio" irregolare della scarica. I due ascolti hanno lo stesso volume (RMS).

Fatti (Sound on Sound, Music Connection, sito Gamechanger): il segnale viene alzato fino a 3.500 V
da un trasformatore e scocca in un tubo allo xeno; un'antenna raccoglie la scarica e la riporta in audio;
sotto soglia la scintilla non parte. Ruvidità e allarme: Arnal et al., Current Biology 2015 (le urla).

Uso: python -m tools.reel_plasma media/tiktok/pedale-plasma.mp4
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
WHITE = (255, 255, 255)
BPM = 112
BEAT = 60 / BPM
RIFF_LEN = 8 * BEAT           # due battute
# (inizio, tipo): il riff suona tre volte
PLAY = [(0.0, "plasma"), (3.2, "pulito"), (3.2 + RIFF_LEN + 0.4, "plasma")]
SPIEGA = PLAY[2][0] + RIFF_LEN + 0.3
CERVELLO = SPIEGA + 5.2
CHIUSURA = CERVELLO + 4.6
END = CHIUSURA + 4.5


# ---------------------------------------------------------------- audio
def corda(f, dur, rng):
    """Karplus-Strong: una corda pizzicata."""
    n = int(dur * SR)
    p = int(SR / f)
    buf = rng.uniform(-1, 1, p)
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        j = (i + 1) % p
        buf[i % p] = 0.4985 * (buf[i % p] + buf[j])
    return out


def riff(seed=3):
    rng = np.random.default_rng(seed)
    E2 = 82.41
    # power chord sulle corde basse: (beat, semitoni sopra E2, durata in beat)
    note = [(0, 0, 1.5), (1.5, 0, 0.5), (2, 3, 1), (3, 5, 1), (4, 0, 1.5), (5.5, 0, 0.5), (6, 7, 0.75), (6.75, 6, 0.5), (7.25, 5, 0.75)]
    out = np.zeros(int(RIFF_LEN * SR) + SR)
    for b, st, d in note:
        s = int(b * BEAT * SR)
        dur = d * BEAT
        tone = np.zeros(int(dur * SR) + 1)
        for k in (0, 7, 12):            # fondamentale, quinta, ottava
            c = corda(E2 * 2 ** ((st + k) / 12), dur, rng)
            tone[:len(c)] += c * (1 if k == 0 else 0.7)
        env = np.ones(len(tone))
        rel = int(0.03 * SR)
        env[-rel:] = np.linspace(1, 0, rel)       # palm-mute: la nota si chiude
        out[s:s + len(tone)] += tone * env
    out = out[:int(RIFF_LEN * SR)]
    return out / np.abs(out).max()


def plasma(x, seed=5):
    """Modello del principio: soglia (gate), clipping estremo, scarica irregolare."""
    rng = np.random.default_rng(seed)
    # inviluppo per la soglia
    k = int(0.004 * SR)
    env = np.convolve(np.abs(x), np.ones(k) / k, mode="same")
    acceso = env > 0.08                                   # sotto soglia la scintilla non scocca
    y = np.sign(x) * acceso
    # la scarica non è continua: scoppietta a raffiche irregolari (ruvidità)
    n = len(x)
    raffica = np.repeat(rng.uniform(0.25, 1.0, n // 120 + 1), 120)[:n]
    crepitio = (rng.random(n) < 0.02) * rng.uniform(-1, 1, n)
    y = y * raffica + crepitio * acceso * 0.8
    # tubo e antenna: niente sotto i 120 Hz, taglio sopra i 7 kHz
    Y = np.fft.rfft(y)
    f = np.fft.rfftfreq(n, 1 / SR)
    Y *= (f > 120) * (1 / (1 + (f / 7000) ** 4))
    return np.fft.irfft(Y, n)


def build_audio():
    pulito = riff()
    elettrico = plasma(pulito)
    rms = lambda a: np.sqrt(np.mean(a ** 2))
    elettrico *= rms(pulito) / rms(elettrico)            # stesso volume percepito di base: stesso RMS
    a = np.zeros(int(END * SR))
    for t0, tipo in PLAY:
        s = int(t0 * SR)
        src = elettrico if tipo == "plasma" else pulito
        a[s:s + len(src)] += src
    return (a / np.abs(a).max() * 0.89).astype(np.float32), elettrico


# ---------------------------------------------------------------- video
def fade(rgb, k):
    return tuple(int(v * k + 31 * (1 - k)) for v in rgb)


def centered(c, y, s, size, fill, kind="display", weight=400, tracking=0):
    c.text((W / 2, y), s, font(kind, size, weight), fill=fill, anchor="ma", tracking=tracking)


def fulmine(c, t, livello, y0=820, y1=1180):
    """Due elettrodi e una scarica a zig-zag che cambia a ogni fotogramma."""
    rng = np.random.default_rng(int(t * FPS))
    for y in (y0, y1):
        c.rect((W / 2 - 60, y - 14, W / 2 + 60, y + 14), fill=(90, 96, 92))
    c.rect((W / 2 - 150, y0 - 40, W / 2 + 150, y1 + 40), outline=LINE, width=2, radius=40)
    if livello < 0.05:
        return
    for rami in range(1 + int(livello * 3)):
        pts, y = [], y0 + 14
        x = W / 2
        while y < y1 - 14:
            pts.append((x, y))
            y += rng.uniform(18, 40)
            x = W / 2 + rng.uniform(-90, 90) * livello
        pts.append((W / 2, y1 - 14))
        col = style.PINK_SOFT if rami == 0 else style.PINK
        c.line(pts, fill=col, width=4 if rami == 0 else 2)


def livello_audio(t, elettrico):
    for t0, tipo in PLAY:
        if tipo == "plasma" and t0 <= t < t0 + RIFF_LEN:
            s = int((t - t0) * SR)
            return min(1, np.abs(elettrico[s:s + SR // FPS]).mean() * 3)
    return 0


def frame(c, t, elettrico):
    k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
    c.kicker(0, 210, "PEDALI IMPOSSIBILI · 01", center=True)
    if t < PLAY[1][0]:
        centered(c, 330, "QUESTA DISTORSIONE", 120, WHITE)
        centered(c, 460, "È UN FULMINE.", 150, style.PINK)
        fulmine(c, t, livello_audio(t, elettrico))
        centered(c, 1290, "IN CUFFIA", 28, MUTED, "sans", 600, 4)
        return
    if t < SPIEGA:
        pulito = t < PLAY[2][0]
        centered(c, 330, "PRIMA: PULITA" if pulito else "POI: NEL FULMINE", 120, WHITE if pulito else style.PINK)
        centered(c, 470, "STESSO RIFF, STESSO VOLUME", 30, MUTED, "sans", 600, 3)
        fulmine(c, t, livello_audio(t, elettrico))
        return
    if t < CERVELLO:
        centered(c, 300, "3.500 VOLT", 170, fade(style.PINK, k(SPIEGA)))
        centered(c, 480, "IN UN TUBO ALLO XENO", 70, fade(WHITE, k(SPIEGA + 0.2)))
        righe = ["Il Plasma di Gamechanger Audio alza",
                 "il segnale della chitarra fino a far",
                 "scoccare una scintilla vera.",
                 "Un'antenna la raccoglie e la rende suono.",
                 "Sotto una certa soglia la scintilla",
                 "non parte: fa anche da noise gate."]
        y = 680
        for i, l in enumerate(righe):
            c.text((W / 2, y), l, font("sans", 40), fill=fade(TEXT, k(SPIEGA + 0.5 + 0.25 * i)), anchor="ma")
            y += 62 + (30 if i == 3 else 0)
        return
    if t < CHIUSURA:
        centered(c, 300, "PERCHÉ CI SEMBRA", 120, fade(WHITE, k(CERVELLO)))
        centered(c, 430, "ENERGIA?", 150, fade(style.PINK, k(CERVELLO)))
        righe = ["La scarica fa tremare il suono",
                 "in modo veloce e irregolare.",
                 "È la stessa «ruvidità» delle urla:",
                 "il cervello la legge come allarme."]
        y = 700
        for i, l in enumerate(righe):
            c.text((W / 2, y), l, font("sans", 42), fill=fade(TEXT, k(CERVELLO + 0.4 + 0.25 * i)), anchor="ma")
            y += 66
        c.text((W / 2, y + 40), "ARNAL ET AL., CURRENT BIOLOGY 2015", font("sans", 24, 600),
               fill=fade(MUTED, k(CERVELLO + 1.6)), anchor="ma", tracking=2)
        return
    centered(c, 360, "MANDALO", 150, fade(WHITE, k(CHIUSURA)))
    centered(c, 510, "AL TUO CHITARRISTA", 110, fade(style.PINK, k(CHIUSURA + 0.2)))
    c.line([(W / 2 - 80, 700), (W / 2 + 80, 700)], fill=style.PINK, width=2)
    centered(c, 760, "PROSSIMO PEDALE IMPOSSIBILE", 30, fade(style.PINK_SOFT, k(CHIUSURA + 0.6)), "sans", 700, 4)
    centered(c, 810, "IL RING MODULATOR", 80, fade(WHITE, k(CHIUSURA + 0.8)))
    centered(c, 1290, "RICOSTRUZIONE ERIN DEL PRINCIPIO, NON IL PEDALE ORIGINALE", 22,
             fade(MUTED, k(CHIUSURA + 1.0)), "sans", 600, 2)


def render(out):
    style.set_accent("verde")
    audio, elettrico = build_audio()
    base = Canvas(W, H, seed=41, bg="pieno")
    base.header("ERIN · HOME RECORDING STUDIO", "PEDALI")
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
            frame(c, f / FPS, elettrico)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "pedale-plasma.mp4")
    out.parent.mkdir(exist_ok=True)
    render(out)
    print("scritto", out)
