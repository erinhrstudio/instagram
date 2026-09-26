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
PINK = (236, 58, 128)
PINK_SOFT = (255, 140, 185)

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


class Canvas:
    def __init__(self, w, h, seed=0, glow=(0.85, 0.9)):
        self.w, self.h = w, h
        rng = np.random.default_rng(seed)
        W, H = w * S, h * S
        a = np.zeros((H, W, 3), np.float32) + np.array(INK, np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        gx, gy = glow
        g = np.exp(-(((xx - gx * W) / (0.55 * W)) ** 2 + ((yy - gy * H) / (0.45 * H)) ** 2))
        a += g[..., None] * np.array([48, 6, 26], np.float32)
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

    def kicker(self, x, y, s):
        self.rect((x, y + 9, x + 28, y + 12), fill=PINK)
        self.text((x + 44, y), s, font("sans", 22, 700), fill=PINK_SOFT, tracking=4)

    def final(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)
