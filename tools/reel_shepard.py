"""Due Reel sulle illusioni di Shepard (toni fatti solo di ottave, senza un'altezza assoluta).

scala   la scala infinita (Shepard 1964, glissando continuo di Risset): sale per 14 s e finisce
        esattamente dov'era partita; prova onesta inizio/fine e video che si chiude in loop.
tritono il paradosso del tritono (Diana Deutsch, 1986): due coppie di note a mezza ottava,
        c'è chi le sente salire e chi scendere.

Uso: python -m tools.reel_shepard scala|tritono media/tiktok/<nome>.mp4
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
SR, FPS, W, H = 44100, 30, 1080, 1920
WHITE = (255, 255, 255)
NOCT = 8                 # ottave nello spettro (componenti)
FMIN = 27.5              # Hz della componente più bassa
CENTER, SIGMA = 4.2, 1.1  # campana delle ampiezze, in ottave sopra FMIN


def amp(oct_):
    return np.exp(-0.5 * ((oct_ - CENTER) / SIGMA) ** 2)


def fade(rgb, k):
    return tuple(int(v * k + 31 * (1 - k)) for v in rgb)


def centered(c, y, s, size, fill, kind="display", weight=400, tracking=0):
    c.text((W / 2, y), s, font(kind, size, weight), fill=fill, anchor="ma", tracking=tracking)


def paragraph(c, y, lines, k0, k):
    for i, l in enumerate(lines):
        last = l.startswith("·")
        c.text((W / 2, y), l.lstrip("· "), font("sans", 28 if last else 40, 600 if last else 400),
               fill=fade(MUTED if last else TEXT, k(k0 + 0.15 * i)), anchor="ma", tracking=2 if last else 0)
        y += 64


# Chiusura da serie (dal 24/10): negli ultimi secondi annuncia la prossima illusione,
# così chi guarda ha un motivo per seguire. La prossima è il Reel con audio proprio
# che viene dopo questo in state/coda.json.
TITOLI = {
    "fischio-silenzio": "IL FISCHIO NEL SILENZIO",
    "rumore-nota": "IL RUMORE CHE DIVENTA NOTA",
    "battito-binaurale": "IL BATTITO CHE ESISTE SOLO IN TESTA",
    "scale-zigzag": "LE SCALE CHE IL CERVELLO RIORDINA",
    "galoppo": "IL GALOPPO CHE SI SPEZZA IN DUE",
}
SERIE_DURATA = 4.5


def prossima_illusione(nome):
    """Titolo della prossima illusione in coda dopo `nome`, "" se `nome` non è nella serie."""
    import json
    from reels.coda import audio_proprio
    coda = json.loads((ROOT / "state" / "coda.json").read_text())["post"]
    if nome not in coda or nome not in TITOLI:
        return ""
    for n in coda[coda.index(nome) + 1:]:
        if n in TITOLI and audio_proprio(n):
            return TITOLI[n]
    return "ALTRE ILLUSIONI IN ARRIVO"


def chiusura_serie(c, t, end, titolo):
    k = min(1, max(0, (t - (end - SERIE_DURATA)) / 0.4))
    if not titolo or k <= 0:
        return
    y = 1250
    c.line([(140, y), (W - 140, y)], fill=fade(LINE, k), width=2)
    centered(c, y + 34, "PROSSIMA ILLUSIONE", 26, fade(style.PINK, k), "sans", 700, 5)
    size = 64 if len(titolo) <= 26 else 54
    centered(c, y + 82, titolo, size, fade(WHITE, k))
    centered(c, y + 82 + size + 20, "SEGUI @ERIN.RECORDINGSTUDIO PER NON PERDERLA", 26, fade(TEXT, k), "sans", 600, 2)


def write_mp4(out, audio, end, draw, seed):
    titolo = prossima_illusione(Path(out).stem)
    style.set_accent("azzurro")
    base = Canvas(W, H, seed=seed, bg="pieno")
    base.header("ERIN · HOME RECORDING STUDIO", "PSICOACUSTICA")
    base_img = base.img.copy()
    audio = audio[:int(end * SR)]
    audio = audio / np.abs(audio).max() * 0.89
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
            st = audio if audio.ndim == 2 else np.repeat(audio[:, None], 2, 1)
            w.writeframes((st * 32767).astype("<i2").tobytes())
        p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                              "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                              str(out)], stdin=subprocess.PIPE)
        for f in range(int(end * FPS)):
            c = Canvas.__new__(Canvas)
            c.w, c.h = W, H
            c.img = base_img.copy()
            c.d = ImageDraw.Draw(c.img)
            draw(c, f / FPS)
            chiusura_serie(c, f / FPS, end, titolo)
            p.stdin.write(np.asarray(c.final().convert("RGB")).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg non ha completato il video")


def spectrum(c, offset, y0, y1, k=1.0, x0=W / 2 - 300, x1=W / 2 + 300):
    """Le componenti come barre orizzontali su un asse in ottave: la luminosità è l'ampiezza."""
    c.line([(x0 - 30, y1), (x0 - 30, y0)], fill=LINE, width=2)
    c.text((x0 - 50, y0 - 10), "ACUTI", font("sans", 22, 700), fill=MUTED, anchor="rm", tracking=3)
    c.text((x0 - 50, y1 + 10), "BASSI", font("sans", 22, 700), fill=MUTED, anchor="rm", tracking=3)
    for j in range(NOCT):
        o = (j + offset) % NOCT
        a = float(amp(o)) * k
        y = y1 - (y1 - y0) * o / NOCT
        col = tuple(int(31 + (v - 31) * a) for v in style.PINK)
        c.rect((x0, y - 7, x1, y + 7), fill=col, radius=7)


# --------------------------------------------------------------------------- scala infinita

RATE = 1 / 7            # ottave al secondo: in 14 s sale di 2 ottave esatte
RISE = 14.0


def spectrogram(c, tnow, y0, y1, k=1.0, window=10.0, x0=150, x1=W - 150, span=2.2):
    """Spettrogramma che scorre: ogni ottava è una diagonale che sale, nasce in basso e svanisce in alto."""
    c.line([(x0, y1 + 14), (x1, y1 + 14)], fill=LINE, width=2)
    c.text((x0, y0 - 34), "ACUTI", font("sans", 22, 700), fill=MUTED, anchor="la", tracking=3)
    c.text((x0, y1 + 30), "BASSI", font("sans", 22, 700), fill=MUTED, anchor="la", tracking=3)
    n = 60
    ts = tnow - window + window * np.arange(n + 1) / n
    xs = x1 - (tnow - ts) / window * (x1 - x0)
    for j in range(NOCT):
        o = (j + RATE * ts) % NOCT
        for i in range(n):
            if ts[i] < 0 or o[i + 1] < o[i]:
                continue
            a = float(amp(o[i])) * k * (0.35 + 0.65 * i / n)
            if a < 0.03:
                continue
            col = tuple(int(31 + (v - 31) * a) for v in style.PINK)
            ya = y1 - (y1 - y0) * (o[i] - CENTER + span) / (2 * span)
            yb = y1 - (y1 - y0) * (o[i + 1] - CENTER + span) / (2 * span)
            if min(ya, yb) < y0 or max(ya, yb) > y1:
                continue
            c.line([(xs[i], ya), (xs[i + 1], yb)], fill=col, width=9)
    # testina: dove siamo adesso
    for j in range(NOCT):
        o = (j + RATE * tnow) % NOCT
        a = float(amp(o)) * k
        if a > 0.05:
            y = y1 - (y1 - y0) * (o - CENTER + span) / (2 * span)
            if not y0 <= y <= y1:
                continue
            r = 6 + 10 * a
            c.ellipse((x1 - r, y - r, x1 + r, y + r), fill=tuple(int(31 + (v - 31) * a) for v in WHITE))


def glissando(t):
    """Glissando di Shepard-Risset: componenti a un'ottava l'una dall'altra che salgono insieme."""
    sig = np.zeros_like(t)
    for j in range(NOCT):
        o = (j + RATE * t) % NOCT
        f = FMIN * 2 ** o
        ph = 2 * np.pi * np.cumsum(f) / SR
        sig += amp(o) * np.sin(ph)
    return sig


def scala(out):
    seg = lambda a, b: np.arange(int(a * SR), int(b * SR)) / SR
    S_START, S_END = 14.6, 16.4             # "ascolta l'inizio"
    E_START, E_END = 16.9, 18.7             # "e la fine"
    SPIEGA, FINE, END = 19.6, 24.6, 28.6
    a = np.zeros(int(END * SR))
    g = glissando(seg(0, RISE))
    env = np.minimum(1, np.arange(len(g)) / (0.02 * SR))
    a[:len(g)] = g * env * np.minimum(1, (len(g) - np.arange(len(g))) / (0.15 * SR))
    snip = glissando(seg(0, 1.8))
    w = np.minimum(1, np.minimum(np.arange(len(snip)), len(snip) - np.arange(len(snip))) / (0.05 * SR))
    end_snip = glissando(seg(RISE, RISE + 1.8))     # stesso istante di fase: RISE * RATE = 2 ottave
    a[int(S_START * SR):int(S_START * SR) + len(snip)] += snip * w
    a[int(E_START * SR):int(E_START * SR) + len(end_snip)] += end_snip * w
    # dal finale riparte la scala, così il video si richiude su se stesso
    g2 = glissando(seg(0, END - FINE))
    a[int(FINE * SR):int(FINE * SR) + len(g2)] += g2 * np.minimum(1, np.arange(len(g2)) / (0.8 * SR)) * 0.9

    def draw(c, t):
        k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
        if t < RISE + 0.4:
            c.kicker(0, 300, "ESPERIMENTO · ASCOLTA FINO IN FONDO", center=True)
            centered(c, 360, "QUESTO SUONO", 140, WHITE)
            centered(c, 500, "SALE PER SEMPRE", 140, style.PINK)
            spectrogram(c, min(t, RISE), 740, 1150)
            msg = ("SALE DA 1 SECONDO" if int(t) == 1 else "SALE DA %d SECONDI" % int(t)) if t >= 1 else "SALE…"
            if t >= 8:
                msg = "ORMAI DOVREBBE ESSERE ALTISSIMO"
            centered(c, 1222, msg, 30, MUTED, "sans", 700, 4)
            return
        if t < SPIEGA:
            c.kicker(0, 300, "LA PROVA", center=True)
            centered(c, 360, "ASCOLTA L'INIZIO…", 120, fade(WHITE, k(RISE + 0.4)))
            centered(c, 490, "…E LA FINE.", 120, fade(style.PINK, k(E_START - 0.3)))
            on_s = S_START <= t < S_END
            on_e = E_START <= t < E_END
            for x, lab, on, kk in [(W / 2 - 200, "INIZIO", on_s, k(S_START - 0.3)),
                                   (W / 2 + 200, "FINE", on_e, k(E_START - 0.3))]:
                spectrum(c, 0, 720, 1020, k=0.35 + 0.65 * on, x0=x - 120, x1=x + 120) if kk > 0 else None
                c.text((x, 1060), lab, font("sans", 30, 700), fill=fade(WHITE if on else MUTED, kk),
                       anchor="ma", tracking=4)
            if t >= E_END:
                centered(c, 1150, "SONO IDENTICI.", 90, fade(style.PINK, k(E_END)))
            return
        if t < FINE:
            c.kicker(0, 300, "SCALA DI SHEPARD", center=True)
            centered(c, 360, "NON SALE.", 140, fade(WHITE, k(SPIEGA)))
            centered(c, 500, "GIRA IN TONDO.", 140, fade(style.PINK, k(SPIEGA + 0.2)))
            paragraph(c, 720, ["Ogni nota è fatta di più ottave insieme.",
                               "In alto svaniscono, in basso rientrano",
                               "piano: il cervello sente solo la salita.",
                               "",
                               "· Roger Shepard 1964 · Jean-Claude Risset"], SPIEGA + 0.5, k)
            return
        centered(c, 420, "RIASCOLTALO", 150, fade(WHITE, k(FINE)))
        centered(c, 570, "E TROVA IL PUNTO", 150, fade(WHITE, k(FINE + 0.2)))
        centered(c, 720, "IN CUI RICOMINCIA.", 150, fade(style.PINK, k(FINE + 0.4)))
        spectrogram(c, t - FINE, 960, 1190, k=k(FINE + 0.6, 0.8), window=4.0)

    write_mp4(out, a, END, draw, seed=51)


# --------------------------------------------------------------------------- paradosso del tritono

NOTE = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"]
PAIRS = [(0, 6), (9, 3)]           # DO→FA#, LA→RE#: entrambe mezza ottava esatta
TONE, GAPT = 0.55, 0.12


def shepard_tone(pc, dur):
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for j in range(NOCT):
        o = j + pc / 12
        sig += amp(o) * np.sin(2 * np.pi * FMIN * 2 ** o * t)
    e = np.minimum(1, np.minimum(t / 0.02, (dur - t) / 0.06))
    return sig * e


def tritono(out):
    # (inizio, coppia): ogni coppia due volte
    plays = [(0.2, 0), (1.9, 0), (4.6, 1), (6.3, 1)]
    VOTA, RIVELA, SPIEGA, FINE, END = 8.2, 11.0, 15.4, 20.8, 24.6
    a = np.zeros(int(END * SR))
    for t0, i in plays:
        for n, pc in enumerate(PAIRS[i]):
            s = shepard_tone(pc, TONE)
            p = int((t0 + n * (TONE + GAPT)) * SR)
            a[p:p + len(s)] += s
    # riascolto finale della coppia 1, per il loop
    for n, pc in enumerate(PAIRS[0]):
        s = shepard_tone(pc, TONE)
        p = int((FINE + 1.2 + n * (TONE + GAPT)) * SR)
        a[p:p + len(s)] += s

    def playing(t, extra=()):
        for t0, i in list(plays) + list(extra):
            for n, pc in enumerate(PAIRS[i]):
                s = t0 + n * (TONE + GAPT)
                if s <= t < s + TONE:
                    return i, n, pc
        return None

    def wheel(c, cx, cy, r, lit=(), dim=False):
        c.ellipse((cx - r, cy - r, cx + r, cy + r), outline=LINE, width=2)
        if len(lit) == 2:
            pts = [(cx + r * np.cos(np.pi / 2 - 2 * np.pi * q / 12), cy - r * np.sin(np.pi / 2 - 2 * np.pi * q / 12))
                   for q in sorted(lit)]
            c.line(pts, fill=style.PINK, width=3)
        for pc in range(12):
            ang = np.pi / 2 - 2 * np.pi * pc / 12
            x, y = cx + r * np.cos(ang), cy - r * np.sin(ang)
            on = pc in lit
            rr = 30 if on else 12
            c.ellipse((x - rr, y - rr, x + rr, y + rr), fill=style.PINK if on else (90, 86, 98))
            lx, ly = cx + (r + 62) * np.cos(ang), cy - (r + 62) * np.sin(ang)
            c.text((lx, ly), NOTE[pc], font("sans", 24, 700), fill=TEXT if on else MUTED, anchor="mm")

    def draw(c, t):
        k = lambda t0, d=0.25: min(1, max(0, (t - t0) / d))
        if t < VOTA:
            cur = playing(t)
            i = 0 if t < 4.3 else 1
            c.kicker(0, 300, "TEST · NON C'È UNA RISPOSTA GIUSTA", center=True)
            centered(c, 360, "SALE", 150, WHITE)
            centered(c, 510, "O SCENDE?", 150, style.PINK)
            lit = {cur[2]} if cur else set()
            wheel(c, W / 2, 930, 180, lit)
            centered(c, 1222, f"COPPIA {i + 1} DI 2", 30, MUTED, "sans", 700, 4)
            return
        if t < RIVELA:
            centered(c, 470, "SCRIVILO", 200, fade(WHITE, k(VOTA)))
            centered(c, 690, "SU O GIÙ?", 200, fade(style.PINK, k(VOTA + 0.4)))
            centered(c, 950, "PRIMA COPPIA, SECONDA COPPIA", 32, fade(TEXT, k(VOTA + 0.9)), "sans", 600, 3)
            return
        if t < SPIEGA:
            c.kicker(0, 300, "IL TRUCCO", center=True)
            centered(c, 360, "È ESATTAMENTE", 120, fade(WHITE, k(RIVELA)))
            centered(c, 480, "MEZZA OTTAVA.", 120, fade(style.PINK, k(RIVELA + 0.2)))
            wheel(c, W / 2, 870, 170, {0, 6} if t < RIVELA + 2.2 else {9, 3})
            centered(c, 1175, "NÉ SOPRA NÉ SOTTO: DI FRONTE", 30, fade(TEXT, k(RIVELA + 0.6)), "sans", 700, 3)
            return
        if t < FINE:
            c.kicker(0, 300, "PARADOSSO DEL TRITONO", center=True)
            centered(c, 360, "IL TUO CERVELLO", 130, fade(WHITE, k(SPIEGA)))
            centered(c, 490, "HA SCELTO PER TE.", 130, fade(style.PINK, k(SPIEGA + 0.2)))
            paragraph(c, 720, ["Queste note non hanno un'ottava precisa:",
                               "decide il cervello. Persone diverse",
                               "sentono direzioni opposte, e conta",
                               "anche la lingua con cui sei cresciuto.",
                               "",
                               "· Diana Deutsch · 1986 e 1991"], SPIEGA + 0.5, k)
            return
        centered(c, 420, "MANDALO", 170, fade(WHITE, k(FINE)))
        centered(c, 590, "A UN AMICO", 170, fade(WHITE, k(FINE + 0.2)))
        centered(c, 760, "E CHIEDIGLI COSA SENTE.", 90, fade(style.PINK, k(FINE + 0.4)))
        cur = playing(t, [(FINE + 1.2, 0)])
        wheel(c, W / 2, 1065, 100, {cur[2]} if cur else set())

    write_mp4(out, a, END, draw, seed=52)


if __name__ == "__main__":
    kind = sys.argv[1]
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "out" / f"{kind}.mp4")
    out.parent.mkdir(exist_ok=True)
    {"scala": scala, "tritono": tritono}[kind](out)
    print("scritto", out)
