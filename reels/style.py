"""Stile grafico "editoriale" di Erin Home Recording Studio.

Si disegna a risoluzione doppia e poi si riduce: linee e testi escono più fini.
Font (licenza OFL, gratuiti): Bebas Neue per i titoli, Inter per i testi, Playfair Display Italic per le citazioni.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
S = 2  # supersampling

INK = (12, 11, 14)
PAPER = (242, 238, 234)
TEXT = (222, 216, 226)
MUTED = (140, 132, 150)
LINE = (58, 52, 64)
# rosa tenue "Morrissey": colore di default della pagina
PINK = (237, 133, 145)
PINK_SOFT = (247, 184, 191)

_cache = {}


def font(kind, size, weight=400):
    """kind: 'display' (Bebas), 'sans' (Inter), 'serif' (Playfair Italic). size in pixel finali."""
    key = (kind, size, weight)
    if key not in _cache:
        if kind == "display":
            f = ImageFont.truetype(str(FONTS / "BebasNeue.ttf"), size * S)
        elif kind == "sans":
            f = ImageFont.truetype(str(FONTS / "Inter.ttf"), size * S)
            f.set_variation_by_axes([min(32, max(14, size)), weight])
        else:
            f = ImageFont.truetype(str(FONTS / "PlayfairDisplay-Italic.ttf"), size * S)
            f.set_variation_by_axes([weight])
        _cache[key] = f
    return _cache[key]


CHARCOAL = (31, 31, 31)
BAND = (236, 133, 143)  # rosa delle fasce (campionato dal post Morrissey)
GLOW = (40, 14, 20)
DIM = ((90, 52, 60), (150, 80, 92), (70, 44, 50))  # accento scurito: onde e barre EQ

# Colori d'accento per serie: stessa luminosità e saturazione del rosa, cambia solo la tinta.
ACCENTS = {
    "rosa": dict(PINK=(237, 133, 145), PINK_SOFT=(247, 184, 191), BAND=(236, 133, 143),
                 GLOW=(40, 14, 20), DIM=((90, 52, 60), (150, 80, 92), (70, 44, 50))),
    "azzurro": dict(PINK=(133, 194, 237), PINK_SOFT=(184, 221, 247), BAND=(133, 193, 236),
                    GLOW=(14, 29, 40), DIM=((52, 74, 90), (80, 121, 150), (44, 59, 70))),
}


def set_accent(name="rosa"):
    globals().update(ACCENTS[name])

# Sfondi di default dei caroselli: antracite granuloso + fascia rosa.
# Ogni fascia è un poligono con coordinate relative (x, y da 0 a 1).
BACKDROPS = {
    "sale":      [(0, 0.60), (1, 0.115), (1, 0.48), (0, 0.97)],   # diagonale che sale
    "scende":    [(0, 0.195), (1, 0.60), (1, 0.97), (0, 0.564)],  # diagonale che scende
    "sale-dolce": [(0, 0.438), (1, 0.183), (1, 0.564), (0, 0.824)],
    "fascia":    [(0, 0.183), (1, 0.183), (1, 0.556), (0, 0.556)],  # fascia orizzontale
    "base":      [(0, 0.613), (1, 0.613), (1, 1.0), (0, 1.0)],      # blocco in basso
    "pieno":     [],                                                # solo antracite
}


def charcoal(W, H, seed=0):
    """Antracite con macchie morbide e grana fine, come carta o lavagna."""
    rng = np.random.default_rng(seed)
    low = Image.fromarray((rng.normal(128, 40, (H // 90 + 2, W // 90 + 2))).clip(0, 255).astype(np.uint8))
    low = np.asarray(low.resize((W, H), Image.BICUBIC), np.float32) - 128
    mid = Image.fromarray((rng.normal(128, 40, (H // 12 + 2, W // 12 + 2))).clip(0, 255).astype(np.uint8))
    mid = np.asarray(mid.resize((W, H), Image.BICUBIC), np.float32) - 128
    a = np.full((H, W), CHARCOAL[0], np.float32) + low * 0.06 + mid * 0.035
    a += rng.normal(0, 3.0, (H, W)).astype(np.float32)
    return a[..., None].repeat(3, 2)


def backdrop(name, W, H, seed=0):
    a = charcoal(W, H, seed)
    poly = BACKDROPS[name]
    if poly:
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([(x * W, y * H) for x, y in poly], fill=255)
        m = np.asarray(m, np.float32)[..., None] / 255
        pink = np.array(BAND, np.float32) + np.random.default_rng(seed + 1).normal(0, 2.0, (H, W, 1)).astype(np.float32)
        a = a * (1 - m) + pink * m
    return np.clip(a, 0, 255).astype(np.uint8)


class Canvas:
    def __init__(self, w, h, seed=0, glow=(0.85, 0.9), bg=None):
        self.w, self.h = w, h
        rng = np.random.default_rng(seed)
        W, H = w * S, h * S
        if bg:
            self.img = Image.fromarray(backdrop(bg, W, H, seed))
            self.d = ImageDraw.Draw(self.img)
            return
        a = np.zeros((H, W, 3), np.float32) + np.array(INK, np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        gx, gy = glow
        g = np.exp(-(((xx - gx * W) / (0.55 * W)) ** 2 + ((yy - gy * H) / (0.45 * H)) ** 2))
        a += g[..., None] * np.array(GLOW, np.float32)
        a += rng.normal(0, 3.2, (H, W, 1)).astype(np.float32)  # grana da pellicola
        self.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        self.d = ImageDraw.Draw(self.img)

    # --- primitive (coordinate in pixel finali)
    def text(self, xy, s, f, fill=TEXT, anchor="la", tracking=0):
        x, y = xy
        if not tracking:
            self.d.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)
            return self.textlength(s, f)
        if anchor[0] in "mr":
            total = self.textlength(s, f, tracking)
            x -= total / 2 if anchor[0] == "m" else total
        for ch in s:
            self.d.text((x * S, y * S), ch, font=f, fill=fill, anchor="l" + anchor[1])
            x += f.getlength(ch) / S + tracking
        return x

    def textlength(self, s, f, tracking=0):
        return f.getlength(s) / S + tracking * max(0, len(s) - 1)

    def line(self, pts, fill=LINE, width=1):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=max(1, int(width * S)))

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        b = [v * S for v in box]
        if radius:
            self.d.rounded_rectangle(b, radius=radius * S, fill=fill, outline=outline, width=int(width * S))
        else:
            self.d.rectangle(b, fill=fill, outline=outline, width=int(width * S))

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.d.ellipse([v * S for v in box], fill=fill, outline=outline, width=int(width * S))

    def paragraph(self, x, y, lines, f, fill=TEXT, leading=1.45, size=None):
        step = (size or f.size / S) * leading
        for l in lines:
            self.text((x, y), l, f, fill=fill)
            y += step
        return y

    # --- elementi ricorrenti
    def header(self, left, right, margin=90, y=84):
        f = font("sans", 20, 600)
        self.text((margin, y), left, f, fill=MUTED, tracking=3)
        self.text((self.w - margin, y), right, f, fill=MUTED, anchor="ra", tracking=3)
        self.line([(margin, y + 44), (self.w - margin, y + 44)], fill=LINE, width=1)

    def kicker(self, x, y, s, center=False):
        f = font("sans", 22, 700)
        if center:
            w = self.textlength(s, f, 4)
            x = (self.w - w) / 2
            self.rect((x - 50, y + 12, x - 22, y + 15), fill=PINK)
            self.rect((x + w + 22, y + 12, x + w + 50, y + 15), fill=PINK)
            self.text((x, y), s, f, fill=PINK_SOFT, tracking=4)
            return
        self.rect((x, y + 9, x + 28, y + 12), fill=PINK)
        self.text((x + 44, y), s, f, fill=PINK_SOFT, tracking=4)

    def portrait(self, path, focus=(0.5, 0.35), zoom=1.0, fade_from=0.45, darken=0.15):
        """Foto a tutto schermo in bianco e nero, primo piano, con sfumatura scura in basso per il testo.

        focus: punto (0-1) della foto da tenere al centro, es. gli occhi. zoom > 1 stringe il primo piano.
        """
        from PIL import ImageOps
        W, H = self.w * S, self.h * S
        ph = ImageOps.grayscale(Image.open(path))
        ph = ImageOps.autocontrast(ph, cutoff=1)
        scale = max(W / ph.width, H / ph.height) * zoom
        ph = ph.resize((int(ph.width * scale) + 1, int(ph.height * scale) + 1), Image.LANCZOS)
        cx, cy = focus[0] * ph.width, focus[1] * ph.height
        left = int(min(max(cx - W / 2, 0), ph.width - W))
        top = int(min(max(cy - H * 0.4, 0), ph.height - H))
        ph = ph.crop((left, top, left + W, top + H))
        a = np.asarray(ph, np.float32)[..., None].repeat(3, 2)
        a = a * (1 - darken) + np.array(INK, np.float32) * darken  # leggero abbassamento
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        grad = np.clip((yy - fade_from) / (1 - fade_from), 0, 1) ** 1.2
        a = a * (1 - 0.92 * grad) + np.array(INK, np.float32) * 0.92 * grad
        top_grad = np.clip((0.16 - yy) / 0.16, 0, 1) ** 0.8  # velo in alto per l'intestazione
        a = a * (1 - 0.85 * top_grad) + np.array(INK, np.float32) * 0.85 * top_grad
        a += np.random.default_rng(1).normal(0, 5, (H, W, 1)).astype(np.float32)
        self.img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        self.d = ImageDraw.Draw(self.img)

    def final(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)
