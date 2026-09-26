"""Carosello 1080x1350 su Julian Casablancas, stile erin.recordingstudio."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1080, 1350
PINK, PINK2, BG, WHITE, SOFT = (214, 36, 110), (255, 90, 160), (14, 12, 18), (255, 255, 255), (200, 190, 215)
B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
_f = {}
def f(size, bold=True):
    k = (size, bold)
    if k not in _f: _f[k] = ImageFont.truetype(B if bold else R, size)
    return _f[k]

def base(seed):
    """Sfondo scuro con 'rumore' a righe tipo nastro e bagliore rosa."""
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W, 3), np.float32) + np.array(BG, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = W * rng.uniform(0.2, 0.8), H * rng.uniform(0.55, 0.95)
    g = np.exp(-(((xx - cx) / 520) ** 2 + ((yy - cy) / 420) ** 2))
    a += g[..., None] * np.array([70, 8, 40], np.float32)
    a += rng.normal(0, 6, (H, 1, 1)).astype(np.float32)  # righe orizzontali
    a += rng.normal(0, 4, (H, W, 1)).astype(np.float32)  # grana
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def pill(d, text, cx, cy, size, fill=PINK, fg=WHITE, pad=(30, 14)):
    lines = text.split("\n"); ft = f(size); lh = size + 12
    ws = [d.textlength(l, font=ft) for l in lines]
    h = lh * len(lines) + pad[1] * 2 - 12; y = cy - h // 2
    for i, w in enumerate(ws):
        d.rounded_rectangle([cx - w / 2 - pad[0], y + i * lh, cx + w / 2 + pad[0], y + (i + 1) * lh + pad[1] * 2 - 12], radius=24, fill=fill)
    for i, (l, w) in enumerate(zip(lines, ws)):
        d.text((cx - w / 2, y + i * lh + pad[1] - 3), l, font=ft, fill=fg)
    return y + h

def para(d, lines, x, y, size=40, fill=WHITE, gap=None, bold=False, center=False):
    gap = gap or int(size * 1.45)
    for l in lines:
        ft = f(size, bold)
        xx = (W - d.textlength(l, font=ft)) / 2 if center else x
        d.text((xx, y), l, font=ft, fill=fill); y += gap
    return y

def footer(d, n):
    d.text((70, H - 80), "ERIN HOME RECORDING STUDIO", font=f(26), fill=(170, 160, 180))
    s = f"{n}/7"
    d.text((W - 70 - d.textlength(s, font=f(26)), H - 80), s, font=f(26), fill=(170, 160, 180))

def mic(d, cx, cy, s):
    """Microfono stilizzato (vintage) disegnato a mano."""
    d.rounded_rectangle([cx - 70 * s, cy - 150 * s, cx + 70 * s, cy + 60 * s], radius=int(70 * s), outline=WHITE, width=int(8 * s))
    for k in range(-5, 6):
        y = cy - 45 * s + k * 16 * s
        half = math.sqrt(max(0, (62 * s) ** 2 - (k * 9 * s) ** 2))
        d.line([cx - half * 0.85, y, cx + half * 0.85, y], fill=SOFT, width=max(2, int(3 * s)))
    d.line([cx, cy + 60 * s, cx, cy + 190 * s], fill=WHITE, width=int(10 * s))
    d.rounded_rectangle([cx - 90 * s, cy + 185 * s, cx + 90 * s, cy + 205 * s], radius=int(10 * s), fill=WHITE)

slides = []

# 1 — copertina
im = base(1); d = ImageDraw.Draw(im)
mic(d, W / 2, 470, 1.35)
pill(d, "JULIAN\nCASABLANCAS", W / 2, 860, 86)
pill(d, "La voce 'rotta' che ha rimesso\nin piedi il rock dei 2000", W / 2, 1060, 38, fill=WHITE, fg=PINK)
d.text((W - 250, H - 150), "Scorri  →", font=f(40), fill=PINK2)
footer(d, 1); slides.append(im)

# 2 — chi è
im = base(2); d = ImageDraw.Draw(im)
pill(d, "CHI È", W / 2, 170, 70)
para(d, ["Nato a New York nel 1978,", "è il cantante e principale autore", "dei brani di The Strokes."], 90, 300, 42)
pill(d, "FIGLIO D'ARTE (MA NON DI MUSICA)", W / 2, 560, 34, fill=WHITE, fg=PINK)
para(d, ["Suo padre è John Casablancas,", "fondatore dell'agenzia di modelle Elite."], 90, 650, 40, fill=SOFT)
pill(d, "LA BAND NASCE A SCUOLA", W / 2, 850, 34, fill=WHITE, fg=PINK)
para(d, ["In un collegio in Svizzera conosce", "Albert Hammond Jr., futuro chitarrista.", "Gli altri li trova tra le scuole di New York."], 90, 940, 40, fill=SOFT)
footer(d, 2); slides.append(im)

# 3 — Is This It
im = base(3); d = ImageDraw.Draw(im)
pill(d, "2001: IS THIS IT", W / 2, 170, 70)
big = "11 brani"
d.text(((W - d.textlength(big, font=f(150))) / 2, 290), big, font=f(150), fill=PINK2)
para(d, ["meno di 40 minuti, zero fronzoli"], 0, 480, 42, center=True)
para(d, ["Registrato con il produttore Gordon Raphael", "in un piccolo studio nel seminterrato", "a New York, con un budget ridotto."], 90, 640, 40, fill=SOFT)
pill(d, "Suono crudo, secco, 'da garage'", W / 2, 950, 40, fill=WHITE, fg=PINK)
para(d, ["Mentre tutti lucidavano i mix,", "loro hanno fatto l'opposto."], 0, 1060, 40, center=True)
footer(d, 3); slides.append(im)

# 4 — la voce
im = base(4); d = ImageDraw.Draw(im)
pill(d, "IL SEGRETO:\nLA VOCE", W / 2, 210, 74)
# forma d'onda "schiacciata" e saturata
rng = np.random.default_rng(9)
x = np.linspace(0, 1, 900)
env = np.clip(np.abs(np.sin(x * 23)) * 1.6 + 0.2, 0, 1)
sig = np.tanh(3 * env * np.sin(x * 900) * rng.uniform(0.7, 1, 900))
mid = 560
for i, v in enumerate(sig):
    h = abs(v) * 110
    d.line([90 + i, mid - h, 90 + i, mid + h], fill=PINK2)
para(d, ["Non urla, sembra quasi annoiata.", "Ma è sporca, compressa e 'stretta',", "come uscita da un telefono", "o da un vecchio amplificatore."], 90, 760, 42)
para(d, ["È diventata il suono di un'epoca."], 90, 1080, 40, fill=PINK2, bold=True)
footer(d, 4); slides.append(im)

# 5 — rifallo nel tuo home studio (curva EQ)
im = base(5); d = ImageDraw.Draw(im)
pill(d, "RIFALLO NEL TUO\nHOME STUDIO", W / 2, 180, 64)
gx0, gx1, gy0, gy1 = 110, 970, 340, 600
d.rectangle([gx0, gy0, gx1, gy1], outline=(70, 60, 80), width=2)
def fx(hz): return gx0 + (math.log10(hz) - math.log10(20)) / (math.log10(20000) - math.log10(20)) * (gx1 - gx0)
for hz, lab in [(100, "100"), (300, "300"), (1000, "1k"), (5000, "5k"), (10000, "10k")]:
    d.line([fx(hz), gy0, fx(hz), gy1], fill=(50, 44, 60), width=1)
    d.text((fx(hz) - d.textlength(lab, font=f(24)) / 2, gy1 + 10), lab, font=f(24), fill=SOFT)
pts = []
for i in range(400):
    hz = 20 * (1000 ** (i / 399))
    g = -12 * math.log2(300 / hz) if hz < 300 else 0
    g += -12 * math.log2(hz / 5000) if hz > 5000 else 0
    g += 4 * math.exp(-((math.log2(hz / 1500)) ** 2) / 0.8)
    y = gy0 + (gy1 - gy0) / 2 - g * 5
    pts.append((fx(hz), min(max(y, gy0 + 4), gy1 - 4)))
d.line(pts, fill=PINK2, width=7)
steps = [("1", "Taglia sotto i 300 Hz e sopra i 5 kHz"),
         ("2", "Aggiungi saturazione o un amp simulator"),
         ("3", "Compressore deciso: 4:1 o più, attacco veloce"),
         ("4", "Niente riverbero: voce secca e davanti")]
y = 690
for n, t in steps:
    d.ellipse([90, y, 150, y + 60], fill=PINK)
    d.text((120 - d.textlength(n, font=f(36)) / 2, y + 8), n, font=f(36), fill=WHITE)
    d.text((175, y + 10), t, font=f(36, False), fill=WHITE)
    y += 100
para(d, ["Punto di partenza, poi regola a orecchio."], 0, 1110, 32, fill=SOFT, center=True)
footer(d, 5); slides.append(im)

# 6 — dopo gli Strokes
im = base(6); d = ImageDraw.Draw(im)
pill(d, "E DOPO?", W / 2, 170, 74)
items = [("2009", "Primo disco solista:", "Phrazes for the Young"),
         ("2013", "Canta 'Instant Crush'", "con i Daft Punk"),
         ("2014", "Nasce il progetto più", "sperimentale: The Voidz"),
         ("2021", "Grammy per il miglior album rock", "con 'The New Abnormal'")]
y = 320
for yr, a, b in items:
    d.rounded_rectangle([90, y, 270, y + 76], radius=24, fill=PINK)
    d.text((180 - d.textlength(yr, font=f(40)) / 2, y + 14), yr, font=f(40), fill=WHITE)
    d.text((300, y), a, font=f(38), fill=WHITE)
    d.text((300, y + 50), b, font=f(34, False), fill=SOFT)
    y += 200
footer(d, 6); slides.append(im)

# 7 — CTA
im = base(7); d = ImageDraw.Draw(im)
pill(d, "VUOI SENTIRE\nIL PRIMA/DOPO?", W / 2, 420, 76)
para(d, ["Scrivi \"VOCE\" nei commenti:", "se arriviamo a 20, faccio il Reel", "con la voce trattata come Julian."], 0, 640, 42, center=True)
pill(d, "Salva il post per il tuo prossimo mix", W / 2, 1000, 38, fill=WHITE, fg=PINK)
footer(d, 7); slides.append(im)

for i, s in enumerate(slides, 1):
    s.convert("RGB").save(f"{OUT}/strokes_{i}.jpg", quality=93)
print("ok", len(slides))
