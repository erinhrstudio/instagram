"""Generatore di caroselli dallo spec JSON di un post. Tutti i testi sono centrati.

Uso: python -m reels.carousel posts/<nome>
Legge posts/<nome>/spec.json e scrive posts/<nome>/01.jpg, 02.jpg, ... più caption.txt e musica.txt

Tipi di slide:
  cover  foto (bianco e nero, primo piano) o sfondo, con kicker / titolo / titolo2 / sottotitolo
  band   sfondo con fascia rosa ("bg"), frase principale sulla fascia, testo breve nella zona scura
  list   antracite: kicker, titolo e punti (etichetta + testo)
  eq     antracite: kicker, titolo, curva EQ e punti
"""
import json, math, sys
from pathlib import Path

from reels.style import BACKDROPS, Canvas, font, MUTED, PINK, PINK_SOFT, TEXT

W, H, M = 1080, 1350, 90
WHITE = (255, 255, 255)
BRAND = "ERIN · HOME RECORDING STUDIO"
CX = W / 2


def band_center(bg, x=0.5):
    """Centro e spessore (0-1) della fascia rosa nel punto x."""
    poly = BACKDROPS[bg]
    top = poly[0][1] + (poly[1][1] - poly[0][1]) * x
    bot = poly[3][1] + (poly[2][1] - poly[3][1]) * x
    return (top + bot) / 2, abs(bot - top)


def fit(c, lines, kind, size, maxw, weight=400):
    while size > 24 and max(c.textlength(l, font(kind, size, weight)) for l in lines) > maxw:
        size -= 2
    return size


def centered(c, y, lines, kind, size, fill, weight=400, leading=1.4, maxw=W - 2 * M):
    size = fit(c, lines, kind, size, maxw, weight)
    f = font(kind, size, weight)
    step = size * leading
    for l in lines:
        c.text((CX, y), l, f, fill=fill, anchor="ma")
        y += step
    return y


def block_height(lines, size, leading):
    return size * leading * len(lines)


def footer(c, text, right=None, rule=True):
    if rule:
        c.line([(M, H - 120), (W - M, H - 120)])
    if right:
        c.text((M, H - 92), text, font("sans", 20, 500), fill=MUTED, tracking=2)
        c.text((W - M, H - 92), right, font("sans", 20, 700), fill=PINK_SOFT, anchor="ra", tracking=3)
    elif text:
        c.text((CX, H - 92), text, font("sans", 20, 500), fill=MUTED, anchor="ma", tracking=2)


def heading(c, s, y=190):
    c.kicker(0, y, s["kicker"], center=True)
    size = fit(c, [s["title"]], "display", s.get("title_size", 150), W - 2 * M)
    c.text((CX, y + 50), s["title"], font("display", size), fill=TEXT, anchor="ma")
    return y + 50 + size * 0.95


def slide_cover(c, s, i, n, root):
    if s.get("photo"):
        c.portrait(root / s["photo"], focus=tuple(s.get("focus", (0.5, 0.35))), zoom=s.get("zoom", 1.0))
    c.header(BRAND, f"{i:02d} / {n:02d}")
    y = 800
    c.kicker(0, y, s["kicker"], center=True)
    t1 = fit(c, [s["title"]], "display", 190, W - 2 * M)
    c.text((CX, y + 44), s["title"], font("display", t1), fill=TEXT, anchor="ma")
    y += 44 + t1 * 0.86
    if s.get("title2"):
        t2 = fit(c, [s["title2"]], "display", 150, W - 2 * M)
        c.text((CX, y), s["title2"], font("display", t2), fill=PINK, anchor="ma")
        y += t2 * 0.92
    if s.get("subtitle"):
        centered(c, y + 16, [s["subtitle"]], "serif", 36, TEXT)
    footer(c, s.get("footer", "HOME RECORDING · STORIA"), "SCORRI  →")


def slide_band(c, s, i, n, root):
    c.header(BRAND, f"{i:02d} / {n:02d}")
    cy, thick = band_center(s["bg"])
    lines = s["statement"]
    size = fit(c, lines, "display", s.get("size", 104), W * 0.72)
    lh = size * 0.98
    top = cy * H - lh * len(lines) / 2 + size * 0.06
    y = top
    for l in lines:
        c.text((CX, y), l, font("display", size), fill=WHITE, anchor="ma")
        y += lh
    body = s.get("body", [])
    need = (60 if s.get("kicker") else 0) + (len(body) * 48 if body else 0)
    col, (ztop, zbot) = free_zone(s["bg"], need=max(need, 1))
    x0, x1 = col
    cxz = (x0 + x1) / 2
    bsize = 34 if x1 - x0 > 700 else 30
    h = 60 + (block_height(body, bsize, 1.42) if body else 0)
    y = ztop + max(0, (zbot - ztop - h) / 2)
    if s.get("kicker"):
        kicker_at(c, cxz, y, s["kicker"])
    if body:
        size = fit(c, body, "sans", bsize, x1 - x0 - 20)
        f = font("sans", size, 400)
        yy = y + 60
        for l in body:
            c.text((cxz, yy), l, f, fill=TEXT, anchor="ma")
            yy += size * 1.42
    footer(c, s.get("footer", ""), rule=not BACKDROPS[s["bg"]])


def kicker_at(c, cx, y, text):
    f = font("sans", 22, 700)
    w = c.textlength(text, f, 4)
    x = cx - w / 2
    c.rect((x - 50, y + 12, x - 22, y + 15), fill=PINK)
    c.rect((x + w + 22, y + 12, x + w + 50, y + 15), fill=PINK)
    c.text((x, y), text, f, fill=PINK_SOFT, tracking=4)


def free_zone(bg, need, top=150, bottom=H - 140, pad=36):
    """Trova la zona scura più ampia (colonna intera, sinistra o destra) dove il testo non tocca la fascia."""
    from PIL import Image, ImageDraw
    poly = BACKDROPS[bg]
    m = Image.new("L", (W, H), 0)
    if poly:
        ImageDraw.Draw(m).polygon([(x * W, y * H) for x, y in poly], fill=1)
    import numpy as np
    m = np.asarray(m)
    best = None
    for col in [(M, W - M), (M, W / 2 + 40), (W / 2 - 40, W - M)]:
        rows = m[:, int(col[0]):int(col[1])].any(1)
        run_start = None
        for y in range(top, bottom + 1):
            free = y < bottom and not rows[max(0, y - pad):y + pad].any()
            if free and run_start is None:
                run_start = y
            if not free and run_start is not None:
                hgt = y - run_start
                width = col[1] - col[0]
                score = (hgt >= need, width if hgt >= need else hgt)
                if best is None or score > best[0]:
                    best = (score, col, (run_start, y))
                run_start = None
    return best[1], best[2]


def items_block(c, y, items, gap=36):
    for k, (lab, txt) in enumerate(items, 1):
        if k > 1:
            c.line([(CX - 60, y), (CX + 60, y)], fill=PINK, width=1.5)
            y += gap
        c.text((CX, y), f"{k:02d} · {lab.upper()}", font("sans", 20, 700), fill=PINK_SOFT, anchor="ma", tracking=4)
        y = centered(c, y + 38, txt if isinstance(txt, list) else [txt], "sans", 33, TEXT, leading=1.35) + gap - 10
    return y


def slide_list(c, s, i, n, root):
    c.header(BRAND, f"{i:02d} / {n:02d}")
    y = heading(c, s) + 50
    items_block(c, y, s["items"], gap=s.get("gap", 38))
    footer(c, s.get("footer", ""))


def slide_eq(c, s, i, n, root):
    c.header(BRAND, f"{i:02d} / {n:02d}")
    y = heading(c, s) + 40
    lo, hi, boost = s.get("lowcut", 300), s.get("highcut", 5000), s.get("boost", (1500, 3))
    gx0, gx1, gy0, gy1 = M + 20, W - M - 20, y, y + 200

    def fx(hz): return gx0 + (math.log10(hz) - math.log10(20)) / 3 * (gx1 - gx0)

    def gain(hz):
        g = -12 * math.log2(lo / hz) if hz < lo else 0
        g += -12 * math.log2(hz / hi) if hz > hi else 0
        return g + boost[1] * math.exp(-((math.log2(hz / boost[0])) ** 2) / 0.8)

    def gy(g): return min(gy1, max(gy0, (gy0 + gy1) / 2 - g * 7))
    ticks, seen = [], []
    for hz, lab in sorted([(100, "100"), (lo, str(lo)), (1000, "1K"), (hi, f"{hi // 1000}K"), (10000, "10K")]):
        if all(abs(fx(hz) - x) > 45 for x in seen):
            ticks.append((hz, lab)); seen.append(fx(hz))
    for hz, lab in ticks:
        c.line([(fx(hz), gy0), (fx(hz), gy1)], fill=(52, 50, 54))
        c.text((fx(hz), gy1 + 14), lab, font("sans", 16, 600), fill=MUTED, anchor="ma", tracking=1)
    pts = [(fx(20 * 1000 ** (k / 399)), gy(gain(20 * 1000 ** (k / 399)))) for k in range(400)]
    for x, yy in pts[::2]:
        c.line([(x, yy), (x, gy1)], fill=(70, 44, 50), width=1.2)
    c.line(pts, fill=PINK, width=3)
    items_block(c, gy1 + 80, s["items"], gap=s.get("gap", 30))
    footer(c, s.get("footer", ""))


KINDS = {"cover": slide_cover, "band": slide_band, "list": slide_list, "eq": slide_eq}


def build(folder):
    folder = Path(folder)
    spec = json.loads((folder / "spec.json").read_text(encoding="utf-8"))
    slides = spec["slides"]
    for old in folder.glob("[0-9][0-9].jpg"):
        old.unlink()
    for i, s in enumerate(slides, 1):
        bg = s.get("bg", "pieno") if s["type"] != "cover" or not s.get("photo") else "pieno"
        c = Canvas(W, H, seed=i, bg=bg)
        KINDS[s["type"]](c, s, i, len(slides), folder)
        c.final().convert("RGB").save(folder / f"{i:02d}.jpg", quality=94, subsampling=0)
    (folder / "caption.txt").write_text(spec["caption"].strip() + "\n", encoding="utf-8")
    if spec.get("music"):
        (folder / "musica.txt").write_text(spec["music"] + "\n", encoding="utf-8")
    return len(slides)


if __name__ == "__main__":
    print("slide:", build(sys.argv[1]))
