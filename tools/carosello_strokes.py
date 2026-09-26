"""Carosello Julian Casablancas, stile editoriale. Uso: python tools/carosello_strokes.py <cartella_output>"""
import math, os, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from reels.style import Canvas, font, TEXT, MUTED, LINE, PINK, PINK_SOFT, INK

W, H, M = 1080, 1350, 90
N = 7
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
BRAND = "ERIN · HOME RECORDING STUDIO"


def page(i, seed, glow=(0.85, 0.9)):
    c = Canvas(W, H, seed, glow)
    c.header(BRAND, f"{i:02d} / {N:02d}")
    return c


def footer_note(c, s):
    c.line([(M, H - 120), (W - M, H - 120)])
    c.text((M, H - 92), s, font("sans", 20, 500), fill=MUTED, tracking=2)


def waveform(c, x0, x1, ymid, amp, seed, squash=1.0, color=PINK, width=1.6, step=6):
    """Forma d'onda realistica: colpi con attacco rapido e coda, più rumore."""
    rng = np.random.default_rng(seed)
    n = int((x1 - x0) / step)
    env = np.zeros(n)
    k = 0
    while k < n:
        a = rng.uniform(0.35, 1.0); L = int(rng.integers(6, 22))
        env[k:k + L] = np.maximum(env[k:k + L], a * np.exp(-np.arange(min(L, n - k)) / (L / 3)))
        k += int(rng.integers(4, 14))
    env = env * rng.uniform(0.75, 1.0, n) + 0.03
    env = np.tanh(env * 2.2 * squash) / np.tanh(2.2 * squash)
    for k in range(n):
        x = x0 + k * step
        h = amp * env[k]
        c.line([(x, ymid - h), (x, ymid + h)], fill=color, width=width)


slides = []

# 01 — copertina
c = page(1, 11, glow=(0.2, 0.75))
c.kicker(M, 200, "THE STROKES · LA VOCE")
c.text((M - 6, 250), "JULIAN", font("display", 250), fill=TEXT)
c.text((M - 6, 470), "CASABLANCAS", font("display", 172), fill=PINK)
waveform(c, M, W - M, 800, 90, 3, squash=0.6, color=PINK_SOFT, width=2, step=8)
c.paragraph(M, 930, ["La voce “rotta” che ha rimesso", "in piedi il rock dei primi 2000."],
            font("serif", 50, 400), fill=TEXT, leading=1.25)
c.line([(M, H - 120), (W - M, H - 120)])
c.text((M, H - 92), "HOME RECORDING · STORIA", font("sans", 20, 500), fill=MUTED, tracking=2)
c.text((W - M, H - 92), "SCORRI  →", font("sans", 20, 700), fill=PINK_SOFT, anchor="ra", tracking=3)
slides.append(c)

# 02 — chi è
c = page(2, 12)
c.kicker(M, 200, "01 — CHI È")
c.text((M - 4, 245), "NEW YORK, 1978", font("display", 150), fill=TEXT)
c.paragraph(M, 430, ["Cantante e principale autore dei brani", "di The Strokes."], font("sans", 38, 400), leading=1.4)
rows = [("FAMIGLIA", ["Figlio di John Casablancas,", "fondatore dell’agenzia di modelle Elite."]),
        ("LA BAND", ["In un collegio in Svizzera conosce", "Albert Hammond Jr., futuro chitarrista.", "Gli altri li trova a New York."])]
y = 600
for lab, lines in rows:
    c.line([(M, y), (W - M, y)])
    c.text((M, y + 34), lab, font("sans", 20, 700), fill=PINK_SOFT, tracking=3)
    y = c.paragraph(330, y + 28, lines, font("sans", 34, 400), leading=1.45) + 40
c.d.text(((W - M + 10) * 2, (H - 150) * 2), "NYC", font=font("display", 270), fill=(20, 18, 24),
         stroke_width=3, stroke_fill=(90, 60, 80), anchor="rs")
footer_note(c, "LA SCUOLA DOVE È NATA UNA BAND")
slides.append(c)

# 03 — Is This It
c = page(3, 13, glow=(0.8, 0.25))
c.kicker(M, 200, "02 — IL DEBUTTO")
c.text((W - M + 10, 180), "2001", font("display", 330), fill=INK, anchor="ra")
c.d.text(((W - M + 10) * 2, 180 * 2), "2001", font=font("display", 330), fill=(20, 18, 24),
         stroke_width=3, stroke_fill=(90, 60, 80), anchor="ra")
c.text((M - 4, 470), "IS THIS IT", font("display", 170), fill=TEXT)
cols = [("11", "BRANI"), ("<40", "MINUTI"), ("1", "SEMINTERRATO")]
cw = (W - 2 * M) / 3
for k, (big, lab) in enumerate(cols):
    x = M + k * cw
    if k:
        c.line([(x, 700), (x, 860)])
    c.text((x + (24 if k else 0), 690), big, font("display", 130), fill=PINK)
    c.text((x + (24 if k else 0), 830), lab, font("sans", 20, 700), fill=MUTED, tracking=3)
c.paragraph(M, 930, ["Registrato con il produttore Gordon Raphael", "in un piccolo studio di New York, con pochi soldi.",
                     "Mentre tutti lucidavano i mix, loro hanno", "scelto un suono crudo, secco, da garage."],
            font("sans", 34, 400), leading=1.45)
footer_note(c, "MENO È DI PIÙ")
slides.append(c)

# 04 — la voce
c = page(4, 14, glow=(0.5, 0.55))
c.kicker(M, 200, "03 — IL SEGRETO")
c.text((M - 4, 245), "LA VOCE", font("display", 220), fill=TEXT)
yb = 640
for dy in (-80, 80):
    for x in range(M, W - M, 16):
        c.line([(x, yb + dy), (x + 8, yb + dy)], fill=(80, 70, 90), width=1)
waveform(c, M, W - M, yb, 110, 7, squash=0.9, color=PINK, width=2, step=7)
c.text((W - M, yb - 110), "SOGLIA DEL COMPRESSORE", font("sans", 16, 600), fill=MUTED, anchor="ra", tracking=2)
c.paragraph(M, 800, ["“Non urla.", "Sembra quasi annoiata.”"], font("serif", 58, 400), fill=PINK_SOFT, leading=1.18)
c.paragraph(M, 970, ["Ma è sporca, compressa e “stretta”, come uscita", "da un telefono o da un vecchio amplificatore.",
                     "È diventata il suono di un’epoca."], font("sans", 34, 400), leading=1.45)
footer_note(c, "SUONO SPORCO, INTENZIONE PRECISA")
slides.append(c)

# 05 — la catena
c = page(5, 15, glow=(0.15, 0.2))
c.kicker(M, 200, "04 — RIFALLO NEL TUO HOME STUDIO")
c.text((M - 4, 245), "LA CATENA", font("display", 170), fill=TEXT)
gx0, gx1, gy0, gy1 = M, W - M, 470, 690
def fx(hz): return gx0 + (math.log10(hz) - math.log10(20)) / 3 * (gx1 - gx0)
def gain(hz):
    g = -12 * math.log2(300 / hz) if hz < 300 else 0
    g += -12 * math.log2(hz / 5000) if hz > 5000 else 0
    return g + 3.5 * math.exp(-((math.log2(hz / 1500)) ** 2) / 0.8)
def gy(g): return min(gy1, max(gy0, (gy0 + gy1) / 2 - g * 7))
for hz, lab in [(100, "100"), (300, "300"), (1000, "1K"), (5000, "5K"), (10000, "10K")]:
    c.line([(fx(hz), gy0), (fx(hz), gy1)], fill=(42, 38, 48))
    c.text((fx(hz), gy1 + 16), lab, font("sans", 16, 600), fill=MUTED, anchor="ma", tracking=1)
c.line([(gx0, (gy0 + gy1) / 2), (gx1, (gy0 + gy1) / 2)], fill=(52, 46, 58))
pts = [(fx(20 * 1000 ** (i / 399)), gy(gain(20 * 1000 ** (i / 399)))) for i in range(400)]
for x, y in pts[::2]:
    c.line([(x, y), (x, gy1)], fill=(60, 18, 38), width=1.2)
c.line(pts, fill=PINK, width=3)
steps = [("EQ", "Taglia sotto i 300 Hz e sopra i 5 kHz"),
         ("SATURAZIONE", "Drive o amp simulator, senza paura"),
         ("COMPRESSORE", "4:1 o più, attacco veloce"),
         ("SPAZIO", "Niente riverbero: voce secca e davanti")]
y = 770
for k, (lab, txt) in enumerate(steps, 1):
    c.line([(M, y), (W - M, y)])
    c.text((M, y + 22), f"{k:02d}", font("display", 56), fill=PINK)
    c.text((M + 90, y + 24), lab, font("sans", 18, 700), fill=PINK_SOFT, tracking=3)
    c.text((M + 90, y + 52), txt, font("sans", 32, 400), fill=TEXT)
    y += 105
footer_note(c, "PUNTO DI PARTENZA, POI REGOLA A ORECCHIO")
slides.append(c)

# 06 — dopo
c = page(6, 16, glow=(0.9, 0.3))
c.kicker(M, 200, "05 — DOPO GLI STROKES")
c.text((M - 4, 245), "E POI?", font("display", 190), fill=TEXT)
items = [("2009", "Primo disco solista", "Phrazes for the Young"),
         ("2013", "“Instant Crush” con i Daft Punk", "voce su Random Access Memories"),
         ("2014", "Nasce The Voidz", "il suo progetto più sperimentale"),
         ("2021", "Grammy come miglior album rock", "con The New Abnormal")]
x_line, y = M + 150, 520
c.line([(x_line, y - 10), (x_line, y + 3 * 170 + 60)], fill=(80, 60, 80), width=1.2)
for yr, a, b in items:
    c.text((M, y - 6), yr, font("display", 60), fill=PINK)
    c.ellipse((x_line - 7, y + 16, x_line + 7, y + 30), fill=PINK)
    c.text((x_line + 40, y), a, font("sans", 34, 600), fill=TEXT)
    c.text((x_line + 40, y + 50), b, font("sans", 28, 400), fill=MUTED)
    y += 170
footer_note(c, "DAL GARAGE AI GRAMMY")
slides.append(c)

# 07 — CTA
c = page(7, 17, glow=(0.5, 0.95))
c.kicker(M, 200, "IL PROSSIMO REEL")
c.text((M - 4, 250), "VUOI SENTIRE", font("display", 150), fill=TEXT)
c.text((M - 4, 390), "IL PRIMA / DOPO?", font("display", 150), fill=PINK)
c.paragraph(M, 610, ["Scrivi “VOCE” nei commenti."], font("serif", 58, 400), fill=PINK_SOFT)
c.paragraph(M, 720, ["Se arriviamo a 20, faccio il Reel con una voce", "trattata come quella di Julian, passo dopo passo."],
            font("sans", 34, 400), leading=1.45)
c.rect((M, 930, W - M, 1040), outline=(110, 80, 100), width=1.2, radius=55)
c.text((W / 2, 985), "SALVA IL POST PER IL TUO PROSSIMO MIX", font("sans", 22, 700), fill=TEXT, anchor="mm", tracking=3)
footer_note(c, "SEGUI PER ALTRI TRUCCHI DI HOME RECORDING")
slides.append(c)

for i, c in enumerate(slides, 1):
    c.final().convert("RGB").save(f"{OUT}/strokes_{i}.jpg", quality=94, subsampling=0)
print("ok", len(slides))
