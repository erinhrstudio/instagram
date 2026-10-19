"""Reel "Non piangi per la canzone" (musica triste): voce di Giuseppe, sfondi d'atmosfera,
sottotitoli parola per parola e una dimostrazione al pianoforte (Do maggiore -> Do minore).

La voce arriva dai memo in posts/musica-triste/ con la trascrizione di Whisper
(tools/trascrivi.py): i tagli sono intervalli in secondi dei memo, i sottotitoli usano
i tempi delle parole.

Uso: python -m tools.reel_triste media/tiktok/musica-triste.mp4
"""
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.signal import sosfilt

from reels import style
from tools.voce_vera import leggi

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "posts" / "musica-triste"
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR, FPS, W, H = 44100, 30, 1080, 1920
FONTS = ROOT / "assets" / "fonts"
style.set_accent("azzurro")
ACC = style.PINK  # con l'accento azzurro attivo

# (memo, inizio, fine nel memo, inizio nel Reel, sfondo)
TAGLI = [
    ("memo", 10.55, 13.05, 0.0, 3),    # Non piangi perché quella canzone è triste.
    ("memo", 23.00, 34.05, 7.0, 6),    # Mentre ascolti ... circuiti della ricompensa.
    ("memo", 38.50, 42.60, 18.6, 4),   # Poi ci sono canzoni che conservano i nostri ricordi.
    ("memo", 42.70, 45.85, 22.8, 5),   # Sono persone, luoghi, momenti che non torneranno più.
    ("memo", 46.52, 51.60, 26.6, 2),   # non piangi per la canzone ma ... ti ha restituito qualcuno.
    ("memo", 51.70, 53.85, 32.0, 1),   # E magari quel qualcuno eri proprio tu.
]
ACCORDI = 3.0          # Do maggiore a 3.0 s, Do minore a 4.9 s
DOMANDA = 35.8         # dopo 1,5 s di silenzio vero
END = 40.0
CORREZIONI = {"consoni": "canzoni"}


# ---------------------------------------------------------------- audio
def biquad_shelf(f0, gain_db, q=0.7):
    a = 10 ** (gain_db / 40); w = 2 * np.pi * f0 / SR
    al = np.sin(w) / (2 * q); c = np.cos(w); s = 2 * np.sqrt(a) * al
    b0 = a * ((a + 1) + (a - 1) * c + s); b1 = -2 * a * ((a - 1) + (a + 1) * c); b2 = a * ((a + 1) + (a - 1) * c - s)
    a0 = (a + 1) - (a - 1) * c + s; a1 = 2 * ((a - 1) - (a + 1) * c); a2 = (a + 1) - (a - 1) * c - s
    return np.array([[b0 / a0, b1 / a0, b2 / a0, 1, a1 / a0, a2 / a0]])


def voce(x):
    """Memo ovattato: +7 dB sopra i 3 kHz, compressione leggera."""
    x = sosfilt(biquad_shelf(3000, 7), x)
    h = int(0.02 * SR)
    env = np.sqrt(np.convolve(x ** 2, np.ones(h) / h, "same")) + 1e-6
    thr = np.percentile(env[env > env.max() * 0.05], 60)
    g = np.where(env > thr, (thr / env) ** 0.5, 1.0)
    g = np.convolve(g, np.ones(h) / h, "same")
    return x * g


def nota(f, dur, vel=1.0):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > SR / 2:
            break
        y += np.sin(2 * np.pi * fk * t) / k ** 1.4 * np.exp(-t * (0.9 + 0.55 * k))
    att = np.minimum(1, t / 0.004)
    rel = np.minimum(1, (dur - t) / 0.25)
    return vel * y * att * np.clip(rel, 0, 1)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def accordo(midi, dur, vel=1.0):
    return sum(nota(hz(m), dur, vel * (0.9 if i else 1.0)) for i, m in enumerate(midi))


def letto(t0, t1):
    """Arpeggio lento in La minore (Am F C G), molto basso sotto la voce."""
    giri = [[45, 52, 57, 60, 64], [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62]]
    out = np.zeros(int((t1 - t0) * SR) + SR * 3)
    passo = 0.55
    t, i = 0.0, 0
    while t < t1 - t0:
        ch = giri[(i // 8) % 4]
        m = ch[[0, 2, 3, 4, 3, 2, 1, 2][i % 8]]
        n = nota(hz(m), 2.4, 0.5)
        j = int(t * SR)
        out[j:j + len(n)] += n
        t += passo; i += 1
    out = out[:int((t1 - t0) * SR)]
    k = np.ones_like(out)
    r = int(3 * SR); k[-r:] = np.linspace(1, 0, r)
    r = int(1.5 * SR); k[:r] = np.linspace(0, 1, r)
    return out * k


def costruisci_audio():
    a = np.zeros(int(END * SR))
    memo = {"memo": leggi(DIR / "memo.m4a")}
    for m, s0, s1, t0, _ in TAGLI:
        seg = voce(memo[m])[int(s0 * SR):int(s1 * SR)].copy()
        r = int(0.03 * SR)
        seg[:r] *= np.linspace(0, 1, r); seg[-r:] *= np.linspace(1, 0, r)
        seg /= np.sqrt(np.mean(seg[np.abs(seg) > 0.01] ** 2)) + 1e-9
        i = int(t0 * SR)
        a[i:i + len(seg)] += seg * 0.16
    # una nota di pianoforte, subito
    n = nota(hz(57), 3.0, 0.5); a[:len(n)] += n * 0.05
    # dimostrazione: Do-Sol-Mi-Do poi Do-Sol-Mib-Do (il Do resta sopra e sotto)
    for t0, mid in [(ACCORDI, [48, 55, 64, 72]), (ACCORDI + 1.9, [48, 55, 63, 72])]:
        c = accordo(mid, 2.0); i = int(t0 * SR); a[i:i + len(c)] += c * 0.14
    bed = letto(7.0, 32.0) * 0.022
    a[int(7.0 * SR):int(7.0 * SR) + len(bed)] += bed
    return a / np.abs(a).max() * 0.89


# ---------------------------------------------------------------- testo
def parole():
    d = json.loads((DIR / "memo.trascrizione.json").read_text())
    tutte = [w for s in d["frasi"] for w in s["parole"]]
    out = []
    for _, s0, s1, t0, _ in TAGLI:
        for w in tutte:
            if s0 - 0.05 <= w["t0"] and w["t1"] <= s1 + 0.1:
                testo = CORREZIONI.get(w["w"].strip(",.…?"), None)
                ww = w["w"] if testo is None else w["w"].replace(w["w"].strip(",.…?"), testo)
                out.append((t0 + w["t0"] - s0, t0 + w["t1"] - s0, ww))
    # "non" all'inizio del quinto taglio diventa "Non"
    return [(a, b, w[0].upper() + w[1:] if i == 0 or out[i - 1][2].endswith((".", "?")) else w)
            for i, (a, b, w) in enumerate(out)]


def gruppi(ps, n=4):
    """Righe di sottotitoli: al massimo n parole, si va a capo dopo un punto."""
    g, cur = [], []
    for p in ps:
        cur.append(p)
        if len(cur) >= n or p[2].endswith((".", ",", "?")) and len(cur) >= 2:
            g.append(cur); cur = []
    if cur:
        g.append(cur)
    return g


# ---------------------------------------------------------------- video
def F(name, size, wght=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if wght:
        f.set_variation_by_axes([min(32, max(14, size)), wght])
    return f


SFONDI = {i: Image.open(DIR / "sfondi" / f"{i}.png").convert("RGB") for i in range(1, 7)}


def sfondo(i, k):
    """Zoom lentissimo (1.0 -> 1.07) sull'immagine i, k da 0 a 1."""
    im = SFONDI[i]
    z = 1.0 + 0.07 * k
    w, h = im.size
    cw, ch = w / z, h / z
    x0, y0 = (w - cw) / 2, (h - ch) * 0.45
    return im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


VELO = None


def velo():
    global VELO
    if VELO is None:
        y = np.linspace(0, 1, H)[:, None]
        a = 0.25 + 0.55 * np.clip((y - 0.5) / 0.35, 0, 1)
        VELO = (np.repeat(a, W, 1) * 255).astype(np.uint8)
    return VELO


def sezioni():
    """(inizio, fine, sfondo) di ogni scena."""
    s = [(0.0, 7.0, 3)]
    for i, (_, s0, s1, t0, bg) in enumerate(TAGLI[1:], 1):
        nxt = TAGLI[i + 1][3] if i + 1 < len(TAGLI) else END
        s.append((t0 - 0.4, nxt, bg))
    return s


def ombra(d, xy, s, f, fill, anchor="ma"):
    x, y = xy
    for dx, dy in [(0, 3), (2, 3), (-2, 3)]:
        d.text((x + dx, y + dy), s, font=f, fill=(0, 0, 0), anchor=anchor)
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)


def frame(t, righe):
    sc = sezioni()
    cur = [x for x in sc if x[0] <= t < x[1]]
    a, b, bg = cur[-1]
    img = sfondo(bg, (t - a) / (b - a))
    if len(cur) > 1:  # dissolvenza tra due scene
        pa, pb, pbg = cur[0]
        k = min(1, (t - a) / 0.4)
        img = Image.blend(sfondo(pbg, (t - pa) / (pb - pa)), img, k)
    nero = Image.new("RGB", (W, H))
    img = Image.composite(nero, img, Image.fromarray(velo()))
    d = ImageDraw.Draw(img)
    kf = lambda t0, dd=0.3: max(0, min(1, (t - t0) / dd))
    col = lambda rgb, k: tuple(int(v * k) for v in rgb)
    d.text((W / 2, 150), "ERIN · PSICOACUSTICA", font=F("Inter.ttf", 26, 700), fill=(200, 200, 205), anchor="ma")
    if t < 7.0:
        ombra(d, (W / 2, 330), "NON PIANGI", F("BebasNeue.ttf", 170), (255, 255, 255))
        ombra(d, (W / 2, 490), "PER LA CANZONE", F("BebasNeue.ttf", 130), ACC)
    if ACCORDI - 0.2 <= t < 7.0:
        maj = t < ACCORDI + 1.9
        f = F("BebasNeue.ttf", 96)
        ombra(d, (W / 2, 760), "DO · MI · SOL" if maj else "DO · MI BEMOLLE · SOL", f,
              (255, 255, 255) if maj else ACC)
        ombra(d, (W / 2, 880), "DO MAGGIORE" if maj else "DO MINORE", F("Inter.ttf", 40, 600), (225, 225, 230))
        if not maj:
            ombra(d, (W / 2, 960), "STESSO DO. UN SEMITONO SOTTO.", F("Inter.ttf", 34, 700),
                  col((235, 235, 240), kf(ACCORDI + 2.3)))
    if t >= DOMANDA:
        k = kf(DOMANDA, 0.6)
        ombra(d, (W / 2, 640), "QUAL È LA CANZONE", F("BebasNeue.ttf", 120), col((255, 255, 255), k))
        ombra(d, (W / 2, 770), "CHE TI RIPORTA", F("BebasNeue.ttf", 120), col((255, 255, 255), k))
        ombra(d, (W / 2, 900), "INDIETRO? 👇".replace(" 👇", ""), F("BebasNeue.ttf", 120), col(ACC, k))
        ombra(d, (W / 2, 1060), "SCRIVILA NEI COMMENTI", F("Inter.ttf", 34, 700), col((225, 225, 230), kf(DOMANDA + 0.5)))
    # sottotitoli
    for r in righe:
        if r[0][0] - 0.1 <= t <= r[-1][1] + 0.25:
            f = F("Inter.ttf", 58, 800)
            parts = [w for _, _, w in r]
            total = sum(d.textlength(p + " ", font=f) for p in parts)
            x = (W - total) / 2
            for (a0, a1, w) in r:
                fill = ACC if a0 <= t <= a1 + 0.05 else (255, 255, 255)
                ombra(d, (x, 1390), w, f, fill, anchor="la")
                x += d.textlength(w + " ", font=f)
            break
    return img


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "out" / "musica-triste.mp4")
    out.parent.mkdir(exist_ok=True)
    audio = costruisci_audio()
    righe = gruppi(parole())
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.repeat(audio[:, None], 2, 1) * 32767).astype("<i2").tobytes())
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)],
                             stdin=subprocess.PIPE)
        for i in range(int(END * FPS)):
            p.stdin.write(np.asarray(frame(i / FPS, righe)).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")
    print("scritto", out)


if __name__ == "__main__":
    main()
