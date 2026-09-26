"""Genera un Reel "Ascolta la differenza" (prima/dopo un effetto audio), 1080x1920.

Uso: python -m reels.render <id_episodio> <output.mp4>
Gli episodi sono in reels/episodes.json. Tutto gratuito: numpy + Pillow + FFmpeg.
"""
import json, os, subprocess, sys, tempfile, wave, zlib
from pathlib import Path

import numpy as np
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR, FPS, W, H = 44100, 30, 1080, 1920
PINK, PINK2, BG, WHITE, GREY = (214, 36, 110), (255, 90, 160), (14, 12, 18), (255, 255, 255), (90, 80, 100)
HERE = Path(__file__).parent
EPISODES = json.loads((HERE / "episodes.json").read_text(encoding="utf-8"))
FONT = next(p for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"] if os.path.exists(p))

T_HOOK, T_BEFORE, T_AFTER, T_END = 2.5, 8.0, 8.0, 4.5
TOTAL = T_HOOK + T_BEFORE + T_AFTER + T_END


# ---------------------------------------------------------------- audio
def make_loop(seed, bpm, bars=4):
    """Loop di batteria + basso sintetizzato, con dinamica volutamente irregolare."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm

    def env(n, tau): return np.exp(-np.arange(n) / (tau * SR))

    def kick(v):
        n = int(0.45 * SR); t = np.arange(n) / SR
        f = 45 + 110 * np.exp(-t * 28)
        return v * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.16)

    def snare(v):
        n = int(0.3 * SR); t = np.arange(n) / SR
        nz = rng.standard_normal(n); nz = nz - 0.6 * np.roll(nz, 1)
        return v * (0.55 * nz * env(n, 0.07) + 0.5 * np.sin(2 * np.pi * 190 * t) * env(n, 0.05))

    def hat(v):
        n = int(0.06 * SR); nz = rng.standard_normal(n)
        return v * 0.35 * np.diff(nz, prepend=0) * env(n, 0.012)

    def bass(freq, dur, v):
        n = int(dur * SR); t = np.arange(n) / SR
        s = sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 7))
        return v * 0.45 * s * np.minimum(1, t / 0.005) * env(n, 0.35)

    L = int(bars * 4 * beat * SR)
    mix = np.zeros(L + SR)

    def put(sig, t):
        i = int(t * SR); mix[i:i + len(sig)] += sig[: len(mix) - i]

    roots = [[55.0, 55.0, 65.41, 49.0], [41.2, 49.0, 55.0, 49.0], [49.0, 43.65, 55.0, 41.2]][seed % 3]
    for b in range(bars):
        t0 = b * 4 * beat
        for s in range(8):
            put(hat(rng.uniform(0.25, 1.0)), t0 + s * beat / 2)
        put(kick(rng.uniform(0.35, 1.0)), t0); put(kick(rng.uniform(0.3, 0.9)), t0 + 2.5 * beat)
        put(snare(rng.uniform(0.2, 1.0)), t0 + beat); put(snare(rng.uniform(0.2, 1.0)), t0 + 3 * beat)
        for dt, du in [(0, 0.7), (1.5, 0.4), (2.5, 0.9), (3.5, 0.4)]:
            put(bass(roots[b], du * beat, rng.uniform(0.2, 1.0)), t0 + dt * beat)
    x = mix[:L]
    return np.stack([x, x], 1)  # stereo (dual mono)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def read_wav(path):
    with wave.open(str(path)) as w:
        d = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, w.getnchannels())
    d = d.astype(np.float64) / 32767
    return d if d.shape[1] == 2 else np.repeat(d, 2, 1)


def ffmpeg_filter(x, af, tmp):
    if not af:
        return x
    write_wav(tmp / "in.wav", x)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(tmp / "in.wav"), "-af", af,
                    "-ar", str(SR), "-ac", "2", str(tmp / "out.wav")], check=True)
    y = read_wav(tmp / "out.wav")[: len(x)]
    return np.pad(y, ((0, len(x) - len(y)), (0, 0)))


def reverb(x, seconds=1.8, wet=0.35, seed=3):
    """Riverbero a convoluzione con risposta all'impulso sintetica (L/R decorrelati)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR); t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / seconds)
        ir[: int(0.02 * SR)] = 0  # pre-delay 20 ms
        ir /= np.sqrt(np.sum(ir ** 2))
        m = len(x) + n
        y = np.fft.irfft(np.fft.rfft(x[:, ch], m) * np.fft.rfft(ir, m), m)[: len(x)]
        # coda del loop precedente: il loop suona continuo
        tail = np.fft.irfft(np.fft.rfft(x[:, ch], m) * np.fft.rfft(ir, m), m)[len(x): m]
        y[: len(tail)] += tail[: len(y)]
        out[:, ch] = y
    return (1 - wet) * x + wet * out * (np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(out ** 2)) + 1e-12))


def rms(x): return np.sqrt(np.mean(x ** 2))


def build_audio(ep, tmp):
    seed = zlib.crc32(ep["id"].encode()) % 1000
    base = make_loop(seed, ep.get("bpm", 96))
    before = ffmpeg_filter(base, ep.get("before", ""), tmp)
    after = ffmpeg_filter(base, ep.get("after", ""), tmp)
    if ep.get("after_py") == "reverb":
        after = reverb(after)
    before = before / np.max(np.abs(before))
    if ep.get("match", "peak") == "rms":
        after = after * rms(before) / rms(after)
    else:
        after = after / np.max(np.abs(after))
    g = 0.79 / max(np.max(np.abs(before)), np.max(np.abs(after)))  # picco -2 dBFS: margine per la compressione AAC
    return before * g, after * g


def timeline(before, after):
    def tile(x, sec):
        n = int(sec * SR); return np.tile(x, (n // len(x) + 1, 1))[:n].copy()
    a1, a2 = tile(before, T_HOOK + T_BEFORE), tile(after, T_AFTER + T_END)
    f = int(0.01 * SR)
    a1[-f:] *= np.linspace(1, 0, f)[:, None]; a2[:f] *= np.linspace(0, 1, f)[:, None]
    audio = np.concatenate([a1, a2])
    fo = int(0.6 * SR); audio[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return audio


# ---------------------------------------------------------------- grafica
_fonts = {}
def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def fit(d, lines, size, maxw=W - 140):
    while size > 24 and max(d.textlength(l, font=font(size)) for l in lines) > maxw:
        size -= 2
    return size


def pill(d, text, cy, size, fill=PINK, fg=WHITE, pad=(38, 18)):
    lines = text.split("\n")
    size = fit(d, lines, size)
    f = font(size); lh = size + 14
    ws = [d.textlength(l, font=f) for l in lines]
    h = lh * len(lines) + pad[1] * 2 - 14
    y = cy - h // 2
    for i, w in enumerate(ws):
        x = (W - w) / 2
        d.rounded_rectangle([x - pad[0], y + i * lh, x + w + pad[0], y + (i + 1) * lh + pad[1] * 2 - 14],
                            radius=28, fill=fill)
    for i, (l, w) in enumerate(zip(lines, ws)):
        d.text(((W - w) / 2, y + i * lh + pad[1] - 4), l, font=f, fill=fg)


def text_block(d, lines, y, size=44, fill=WHITE, gap=62):
    size = fit(d, lines, size)
    for l in lines:
        d.text(((W - d.textlength(l, font=font(size))) / 2, y), l, font=font(size), fill=fill)
        y += gap


def waveform(d, mono, i, top, height, color):
    seg = mono[max(0, i - int(1.6 * SR)): i + 1]
    if len(seg) < 2:
        return
    cols = 900; step = max(1, len(seg) // cols); n = len(seg) // step
    blocks = np.abs(seg[: n * step]).reshape(n, step).max(1)
    x0 = (W - cols) // 2 + (cols - n); mid = top + height // 2
    for yy in (mid - height // 4, mid + height // 4):  # riferimento -6 dB
        d.line([((W - cols) // 2, yy), ((W + cols) // 2, yy)], fill=(70, 60, 80), width=2)
    for k, v in enumerate(blocks):
        hh = max(2, int(v * height / 2))
        d.line([(x0 + k, mid - hh), (x0 + k, mid + hh)], fill=color)


def stereo_meter(d, audio, i, top):
    """Barre L/R: mostrano quanto il segnale e' largo (utile per effetto Haas, riverbero)."""
    seg = audio[max(0, i - int(0.05 * SR)): i + 1]
    for ch, (lab, y) in enumerate([("L", top), ("R", top + 64)]):
        db = 20 * np.log10(rms(seg[:, ch]) + 1e-9)
        frac = float(np.clip((db + 40) / 40, 0, 1))
        d.text((90, y + 4), lab, font=font(34), fill=(200, 190, 210))
        d.rounded_rectangle([140, y, W - 90, y + 40], radius=20, fill=(40, 34, 48))
        if frac > 0.03:
            d.rounded_rectangle([140, y, 140 + int((W - 230) * frac), y + 40], radius=20, fill=PINK2)
    wide = audio[max(0, i - int(0.4 * SR)): i + 1]  # finestra più lunga: valore stabile
    side = wide[:, 0] - wide[:, 1]; mid = wide[:, 0] + wide[:, 1]
    width = float(np.clip(rms(side) / (rms(mid) + 1e-3), 0, 1))
    d.text((90, top + 124), f"Larghezza stereo: {int(width * 100)}%", font=font(34), fill=(200, 190, 210))


def background(d):
    for r in range(6):
        d.ellipse([W / 2 - 700 + r * 90, 1150 + r * 45, W / 2 + 700 - r * 90, 2300 - r * 45],
                  fill=(26 + r * 5, 14, 30 + r * 4))


def brand(d):
    s = "ERIN HOME RECORDING STUDIO"
    d.text(((W - d.textlength(s, font=font(34))) / 2, H - 150), s, font=font(34), fill=(170, 160, 180))


def frame(ep, audio, mono, t):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    background(d)
    i = min(int(t * SR), len(audio) - 1)
    if t < T_HOOK:
        pill(d, ep["label"], 520, 56)
        pill(d, ep["hook"], 800, 96)
        pill(d, "Metti le cuffie e ascolta", 1100, 44, fill=WHITE, fg=PINK)
    elif t < T_HOOK + T_BEFORE + T_AFTER:
        after = t >= T_HOOK + T_BEFORE
        pill(d, "DOPO" if after else "PRIMA", 330, 96, fill=PINK if after else GREY)
        pill(d, ep["after_label"] if after else ep["before_label"], 520, 56, fill=WHITE, fg=PINK)
        waveform(d, mono, i, 690, 560, PINK2 if after else (200, 190, 215))
        stereo_meter(d, audio, i, 1310)
        text_block(d, (ep["after_tip"] if after else ep["before_tip"]).split("\n"), 1520)
    else:
        pill(d, ep["outro_title"], 470, 80)
        text_block(d, ep["outro_lines"], 760, gap=66)
        pill(d, "Salvalo per il\ntuo prossimo mix", 1250, 64, fill=WHITE, fg=PINK)
    brand(d)
    return img


def render(ep_id, out):
    ep = next(e for e in EPISODES if e["id"] == ep_id)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        audio = timeline(*build_audio(ep, tmp))
        write_wav(tmp / "track.wav", audio)
        mono = audio.mean(1)
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(tmp / "track.wav"),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest",
                              "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
        for f in range(int(TOTAL * FPS)):
            p.stdin.write(frame(ep, audio, mono, f / FPS).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")
    return ep


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
    print("scritto", sys.argv[2])
