"""Sette illusioni nuove (24/11/2026) per lo Short giornaliero su YouTube, dalla lista strategia/30-idee-soundlab.md.
Tutto l'audio è sintetizzato qui: niente campioni e niente brani di altri.

stesso-volume  stesso livello nel file, 125 Hz e 3000 Hz: il grave sembra molto più basso (curve isofoniche)
campana        la nota di una campana è virtuale: tolgo hum e prime e la nota resta (strike note)
neonati        pianto che sale e pianto che scende: neonati francesi e tedeschi (Mampe et al. 2009)
balena-52      la balena dei 52 Hz, confrontata con il canto di una balenottera azzurra (~18 Hz)
vino           musica francese o tedesca al supermercato (North, Hargreaves & McKendrick, Nature 1997)
ratti-tempo    i ratti muovono la testa a tempo soprattutto tra 120 e 140 BPM (Ito et al. 2022)
gomma          ritornello originale che resta in testa; la gomma da masticare aiuta (Beaman et al. 2015)

Uso: python -m tools.reel_dicembre <nome> media/youtube/en/<nome>.mp4
     (per YouTube: SERIE=youtube PIATTAFORMA=youtube)
"""
import sys
from pathlib import Path

import numpy as np

from reels import style
from reels.style import MUTED, LINE
from tools.reel_shepard import SR, W, WHITE, centered, fade, paragraph, write_mp4

ROOT = Path(__file__).resolve().parent.parent
RNG = np.random.default_rng(7)
GRIGIO = (70, 66, 78)


# ---------------------------------------------------------------- sintesi

def tt(dur):
    return np.arange(int(dur * SR)) / SR


def inviluppo(dur, att=0.01, rel=0.05):
    t = tt(dur)
    return np.clip(t / att, 0, 1) * np.clip((dur - t) / rel, 0, 1)


def metti(a, x, t0, g=1.0):
    j = int(t0 * SR)
    a[j:j + len(x)] += x[:max(0, len(a) - j)] * g


def fase(f):
    """Fase da una frequenza istantanea (array)."""
    return 2 * np.pi * np.cumsum(f) / SR


def saw(ph, armoniche=20):
    return sum(np.sin(h * ph) / h for h in range(1, armoniche + 1))


def passabanda(x, f0, q=4.0):
    """Risonatore a due poli (formante): semplice e sufficiente per colorare il timbro."""
    r = np.exp(-np.pi * f0 / q / SR)
    c1, c2 = 2 * r * np.cos(2 * np.pi * f0 / SR), -r * r
    y = np.zeros_like(x)
    y1 = y2 = 0.0
    g = 1 - r
    for i in range(len(x)):
        v = g * x[i] + c1 * y1 + c2 * y2
        y[i] = v
        y2, y1 = y1, v
    return y


def norma(x):
    return x / (np.abs(x).max() + 1e-9)


# ---------------------------------------------------------------- grafica comune

def kf(t):
    return lambda t0, d=0.25: min(1, max(0, (t - t0) / d))


def bottoni(c, t, voci, y=950):
    """Cerchi A / B: si accende quello che sta suonando. voci = [(etichetta, inizio, durata)]."""
    n = len(voci)
    for i, (lab, t0, dur) in enumerate(voci):
        x = W / 2 + (i - (n - 1) / 2) * 400
        on = t0 <= t < t0 + dur
        r = 120 if on else 95
        c.ellipse((x - r, y - r, x + r, y + r), outline=style.PINK if on else GRIGIO, width=6)
        c.text((x, y), lab, style.font("display", 120), fill=WHITE if on or t > t0 else MUTED, anchor="mm")


def domanda(c, kicker, r1, r2, s1=150, s2=150):
    c.kicker(0, 300, kicker, center=True)
    centered(c, 360, r1, s1, WHITE)
    centered(c, 510, r2, s2, style.PINK)


def spiega(c, t, t0, kicker, r1, r2, righe, s1=150, s2=140):
    k = kf(t)
    c.kicker(0, 300, kicker, center=True)
    centered(c, 360, r1, s1, fade(WHITE, k(t0)))
    centered(c, 510, r2, s2, fade(style.PINK, k(t0 + 0.2)))
    paragraph(c, 720, righe, t0 + 0.5, k)


def chiusura(c, t, t0, r1, r2, sotto, s=120):
    k = kf(t)
    centered(c, 400, r1, s, fade(WHITE, k(t0)))
    centered(c, 540, r2, s, fade(style.PINK, k(t0 + 0.2)))
    centered(c, 700, sotto, 32, fade(MUTED, k(t0 + 0.4)), "sans", 700, 4)


def scritta(c, y, s, col=MUTED):
    centered(c, y, s, 32, col, "sans", 700, 4)


# ================================================================ 1. stesso-volume

class StessoVolume:
    seed, picco = 91, 0.22
    TA, TB, DUR = 0.8, 4.6, 3.2
    RIPETI = 8.2           # A e B alternati, piu' brevi
    VOTO = RIPETI + 4 * 0.9 + 0.2
    SPIEGA = VOTO + 2.6
    CTA = SPIEGA + 8.5
    END = CTA + 7.0
    FA, FB = 125.0, 3000.0

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        tono = lambda f, d: np.sin(2 * np.pi * f * tt(d)) * inviluppo(d, 0.03, 0.08)
        metti(a, tono(self.FA, self.DUR), self.TA)
        metti(a, tono(self.FB, self.DUR), self.TB)
        for i in range(4):
            metti(a, tono(self.FA if i % 2 == 0 else self.FB, 0.7), self.RIPETI + i * 0.9)
        return a[:int(self.END * SR)]

    def suona(self, t):
        if self.TA <= t < self.TA + self.DUR:
            return "A"
        if self.TB <= t < self.TB + self.DUR:
            return "B"
        if self.RIPETI <= t < self.RIPETI + 3.6:
            i = int((t - self.RIPETI) / 0.9)
            if (t - self.RIPETI) - i * 0.9 < 0.7:
                return "AB"[i % 2]
        return ""

    def meter(self, c, x, lab, on, k=1.0):
        y0, y1 = 760, 1160
        c.rect((x - 40, y0, x + 40, y1), outline=fade(LINE, k), width=3, radius=8)
        if on:
            liv = 0.7 + 0.01 * np.sin(len(lab) * 3)
            c.rect((x - 32, y1 - (y1 - y0) * liv, x + 32, y1 - 8), fill=fade(style.PINK, k), radius=6)
        c.text((x, y1 + 50), lab, style.font("display", 90), fill=fade(WHITE if on else MUTED, k), anchor="ma")

    def draw(self, c, t):
        if t < self.SPIEGA:
            domanda(c, "SAME LEVEL IN THE FILE", "WHICH ONE", "IS LOUDER?", 150, 150)
            s = self.suona(t)
            self.meter(c, W / 2 - 200, "A", s == "A")
            self.meter(c, W / 2 + 200, "B", s == "B")
            centered(c, 700, "BOTH METERS HIT THE SAME LEVEL", 28, MUTED, "sans", 700, 4)
            if t >= self.VOTO:
                scritta(c, 1320, "COMMENT A OR B")
            return
        if t < self.CTA:
            spiega(c, t, self.SPIEGA, "SAME DECIBELS. NOT THE SAME LOUDNESS", "SAME LEVEL.", "B WINS.",
                   ["A is a low tone at 125 Hz, B a high one",
                    "at 3,000 Hz. In the file they are exactly",
                    "the same level. Your ears are far less",
                    "sensitive to low notes, and most sensitive",
                    "around 2,000-5,000 Hz. Small speakers",
                    "make the gap even bigger.",
                    "",
                    "· Equal-loudness contours · Fletcher & Munson, 1933"])
            return
        chiusura(c, t, self.CTA, "THAT'S WHY", "BASS NEEDS MORE dB", "SEND IT TO SOMEONE WHO MIXES", 110)


# ================================================================ 2. campana

class Campana:
    seed, picco = 93, 0.85
    NOMINALE = 1046.5          # do6: lo strike note sta un'ottava sotto, do5
    # (rapporto rispetto alla nominale, ampiezza, decadimento in s) di una campana ben accordata
    PARZIALI = [("HUM", 0.25, 0.55, 7.0), ("PRIME", 0.5, 0.6, 5.0), ("TIERCE", 0.6, 0.7, 4.0),
                ("QUINT", 0.75, 0.25, 3.0), ("NOMINAL", 1.0, 1.0, 2.6), ("SUPERQUINT", 1.5, 0.55, 1.6),
                ("OCTAVE NOMINAL", 2.0, 0.45, 1.2), ("", 2.5, 0.25, 0.8), ("", 2.67, 0.2, 0.7),
                ("", 3.0, 0.18, 0.6), ("", 4.0, 0.12, 0.4)]
    TA, TB, DUR = 0.8, 5.6, 4.6
    VOTO = TB + DUR - 0.6
    SPIEGA = VOTO + 2.4
    TC = SPIEGA + 7.5          # la prova: la campana senza prime, poi la nota prime da sola
    CTA = TC + 5.2
    END = CTA + 7.0

    def colpo(self, senza=(), solo=None, dur=None):
        dur = dur or self.DUR
        t = tt(dur)
        x = np.zeros_like(t)
        for nome, r, amp, dec in self.PARZIALI:
            if nome in senza or (solo and nome != solo):
                continue
            f = self.NOMINALE * r * (1 + 0.0007 * RNG.standard_normal())
            x += amp * np.sin(2 * np.pi * f * t) * np.exp(-t * 3.0 / dec)
        return x * np.clip(t / 0.002, 0, 1) * np.clip((dur - t) / 0.2, 0, 1)

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        metti(a, self.colpo(), self.TA, 0.5)
        metti(a, self.colpo(senza=("HUM", "PRIME")), self.TB, 0.5)
        metti(a, self.colpo(senza=("HUM", "PRIME"), dur=2.4), self.TC, 0.5)
        metti(a, np.sin(2 * np.pi * self.NOMINALE * 0.5 * tt(2.4)) * inviluppo(2.4, 0.01, 0.3), self.TC + 2.6, 0.3)
        return a[:int(self.END * SR)]

    def spettro(self, c, senza, k=1.0, y0=760, y1=1160, evid=None):
        x0, x1 = 150, W - 150
        fx = lambda r: x0 + (x1 - x0) * np.log2(r / 0.2) / np.log2(4.5 / 0.2)
        c.line([(x0, y1), (x1, y1)], fill=fade(LINE, k), width=2)
        for nome, r, amp, _ in self.PARZIALI:
            x = fx(r)
            via = nome in senza
            col = GRIGIO if via else (style.PINK if nome == evid else WHITE)
            h = (y1 - y0) * amp
            if via:
                c.rect((x - 9, y1 - h, x + 9, y1), outline=fade(col, k), width=2, radius=4)
            else:
                c.rect((x - 9, y1 - h, x + 9, y1), fill=fade(col, k), radius=4)
            if nome in ("HUM", "PRIME", "NOMINAL"):
                c.text((x, y1 + 18), nome, style.font("sans", 20, 700), fill=fade(MUTED, k), anchor="ma")

    def draw(self, c, t):
        if t < self.SPIEGA:
            domanda(c, "LISTEN TO BOTH BELLS", "DID THE NOTE", "CHANGE?", 140, 150)
            b = t >= self.TB
            self.spettro(c, ("HUM", "PRIME") if b else ())
            scritta(c, 1240, "B: THE PARTIAL AT THAT NOTE IS GONE" if b else "A: A FULL BELL", WHITE if b else MUTED)
            bottoni(c, t, [("A", self.TA, self.DUR), ("B", self.TB, self.DUR)], y=1420)
            return
        if t < self.TC:
            spiega(c, t, self.SPIEGA, "THE STRIKE NOTE IS VIRTUAL", "SAME NOTE.", "YOUR BRAIN'S.",
                   ["The note you hear in a bell is not one",
                    "of its partials. Your brain builds it from",
                    "three upper ones, the nominal, superquint",
                    "and octave nominal (ratios 2 : 3 : 4),",
                    "one octave below the nominal.",
                    "So removing the partial at that note",
                    "barely changes it. Here's the proof.",
                    "",
                    "· Strike note, or virtual pitch · hibberts.co.uk"], 150, 140)
            return
        if t < self.CTA:
            k = kf(t)
            c.kicker(0, 300, "BELL WITHOUT THAT PARTIAL, THEN THE NOTE ALONE", center=True)
            centered(c, 360, "SAME PITCH?", 150, fade(WHITE, k(self.TC)))
            solo = t >= self.TC + 2.6
            self.spettro(c, ("HUM", "PRIME"), evid=None)
            if solo:
                x0, x1 = 150, W - 150
                x = x0 + (x1 - x0) * np.log2(0.5 / 0.2) / np.log2(4.5 / 0.2)
                c.rect((x - 9, 1160 - 360, x + 9, 1160), fill=style.PINK, radius=4)
            scritta(c, 1240, "THE NOTE ALONE" if solo else "BELL, NO PARTIAL AT THAT NOTE", style.PINK if solo else WHITE)
            return
        chiusura(c, t, self.CTA, "THE BELL'S NOTE", "ISN'T IN THE BELL", "SEND IT TO A MUSICIAN", 110)


# ================================================================ 3. neonati

class Neonati:
    seed, picco = 95, 0.45
    TA, TB, DUR = 0.8, 5.0, 3.6
    VOTO = TB + DUR + 0.2
    SPIEGA = VOTO + 2.8
    CTA = SPIEGA + 8.5
    END = CTA + 7.0

    def pianto(self, sale, dur=1.0):
        t = tt(dur)
        u = t / dur
        # francese: il picco arriva tardi (melodia che sale); tedesco: il picco arriva presto (scende)
        p = 0.78 if sale else 0.22
        arco = np.exp(-0.5 * ((u - p) / 0.28) ** 2)
        f0 = 380 + 170 * arco + 6 * np.sin(2 * np.pi * 7 * t) + 3 * RNG.standard_normal(len(t)).cumsum() / np.sqrt(len(t))
        x = saw(fase(f0), 14)
        x = passabanda(x, 1100, 3) + 0.7 * passabanda(x, 2600, 4) + 0.3 * passabanda(x, 3800, 5)
        x += 0.03 * RNG.standard_normal(len(t))
        amp = (0.35 + 0.65 * arco) * np.clip(u / 0.06, 0, 1) * np.clip((1 - u) / 0.12, 0, 1)
        return norma(x) * amp

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        for t0, sale in ((self.TA, True), (self.TB, False)):
            for i in range(3):
                metti(a, self.pianto(sale, 0.95 + 0.1 * i), t0 + i * 1.2, 0.6)
        return a[:int(self.END * SR)]

    def curva(self, c, sale, y0, y1, k=1.0, x0=None, x1=None, lab=""):
        x0 = x0 or 160
        x1 = x1 or W - 160
        u = np.linspace(0, 1, 60)
        p = 0.78 if sale else 0.22
        arco = np.exp(-0.5 * ((u - p) / 0.28) ** 2)
        pts = [(x0 + (x1 - x0) * a, y1 - (y1 - y0) * b) for a, b in zip(u, arco)]
        c.line(pts, fill=fade(style.PINK, k), width=7)
        if lab:
            c.text(((x0 + x1) / 2, y1 + 24), lab, style.font("sans", 26, 700), fill=fade(WHITE, k), anchor="ma")

    def draw(self, c, t):
        if t < self.SPIEGA:
            domanda(c, "ONE IS FRENCH. ONE IS GERMAN", "WHICH BABY", "IS FRENCH?", 150, 150)
            bottoni(c, t, [("A", self.TA, self.DUR), ("B", self.TB, self.DUR)])
            centered(c, 700, "NEWBORNS, 3 TO 5 DAYS OLD", 28, MUTED, "sans", 700, 4)
            if t >= self.VOTO:
                scritta(c, 1240, "COMMENT A OR B")
            return
        if t < self.CTA:
            k = kf(t)
            spiega(c, t, self.SPIEGA, "THEY LEARN IT BEFORE BIRTH", "A IS FRENCH.", "B IS GERMAN.",
                   ["A study recorded the cries of 60 newborns.",
                    "French babies cried with a rising melody,",
                    "German babies with a falling one, just",
                    "like the two languages. They heard their",
                    "mothers' voices in the womb.",
                    "These cries are synthesized, same shapes.",
                    "",
                    "· Mampe et al., Current Biology, 2009"])
            self.curva(c, True, 1360, 1480, k(self.SPIEGA + 1), 160, W / 2 - 40, "A · RISING")
            self.curva(c, False, 1360, 1480, k(self.SPIEGA + 1), W / 2 + 40, W - 160, "B · FALLING")
            return
        chiusura(c, t, self.CTA, "YOU HAD AN ACCENT", "BEFORE WORDS", "SEND IT TO A NEW PARENT", 110)


# ================================================================ 4. balena-52

class Balena:
    seed, picco = 97, 0.6
    TA, DURA = 0.8, 6.4
    TB, DURB = 8.0, 4.0
    VOTO = TB + DURB + 0.2
    SPIEGA = VOTO + 2.4
    CTA = SPIEGA + 9.0
    END = CTA + 7.0

    def canto(self, f, dur, armoniche=(1, 2, 3, 4, 5)):
        """Un richiamo lungo e piatto, come quelli dei grandi cetacei, con armoniche
        perché un telefono non riproduce quasi niente sotto i 100 Hz."""
        t = tt(dur)
        ff = f * (1 + 0.004 * np.sin(2 * np.pi * 0.3 * t))
        ph = fase(ff)
        x = sum(np.sin(h * ph) / h ** 1.2 for h in armoniche)
        return x * inviluppo(dur, 0.4, 0.6)

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        metti(a, self.canto(52, 2.8), self.TA, 0.6)
        metti(a, self.canto(52, 2.8), self.TA + 3.4, 0.6)
        metti(a, self.canto(18, self.DURB, (1, 2, 3)), self.TB, 0.6)
        return a[:int(self.END * SR)]

    def onda(self, c, t, f, t0, y, k=1.0, col=None):
        x0, x1 = 150, W - 150
        xs = np.linspace(x0, x1, 200)
        att = 1.0 if t0 <= t else 0.15
        ys = y - 90 * att * np.sin(2 * np.pi * (xs - x0) / (x1 - x0) * f / 8 - t * 6)
        c.line(list(zip(xs, ys)), fill=fade(col or style.PINK, k), width=5)

    def draw(self, c, t):
        if t < self.SPIEGA:
            domanda(c, "HEADPHONES ON", "THE LONELIEST", "WHALE", 140, 160)
            a = self.TA <= t < self.TA + self.DURA
            b = self.TB <= t < self.TB + self.DURB
            self.onda(c, t, 52, self.TA, 860, col=style.PINK if a else GRIGIO)
            c.text((150, 980), "A · 52 HZ · THE LONELY WHALE", style.font("sans", 26, 700),
                   fill=WHITE if a else MUTED, tracking=3)
            if t >= self.TB - 0.4:
                self.onda(c, t, 18, self.TB, 1160, col=style.PINK if b else GRIGIO)
                c.text((150, 1280), "B · ~18 HZ · A BLUE WHALE", style.font("sans", 26, 700),
                       fill=WHITE if b else MUTED, tracking=3)
            if t >= self.VOTO:
                scritta(c, 1420, "COULD YOU HEAR B?")
            return
        if t < self.CTA:
            spiega(c, t, self.SPIEGA, "A VOICE NO OTHER WHALE USES", "52 HZ.", "SINCE 1989.",
                   ["The US Navy's hydrophones have picked up",
                    "this call since 1989. It sings at 52 Hz,",
                    "much higher than blue whales (10-39 Hz)",
                    "and fin whales (about 20 Hz). Nobody has",
                    "ever identified it. 52 Hz is close to a",
                    "low G sharp on a bass. Most phones can't",
                    "play B at all. Synthesized calls, same pitch.",
                    "",
                    "· The 52-hertz whale · Watkins et al., 2004"])
            return
        chiusura(c, t, self.CTA, "STILL SINGING.", "STILL UNSEEN.", "SEND IT TO SOMEONE WHO FEELS ALONE", 120)


# ================================================================ 5. vino

class Vino:
    seed, picco = 99, 0.85
    TA, TB, DUR = 0.8, 6.2, 4.9
    VOTO = TB + DUR + 0.2
    SPIEGA = VOTO + 2.6
    CTA = SPIEGA + 8.5
    END = CTA + 7.0

    def fisarmonica(self, f, dur):
        t = tt(dur)
        x = saw(fase(np.full(len(t), f)), 12) + saw(fase(np.full(len(t), f * 1.004)), 12)
        x += 0.6 * np.sign(np.sin(2 * np.pi * f * 0.998 * t))     # ancia
        x *= 1 + 0.15 * np.sin(2 * np.pi * 5.5 * t)                 # mantice
        return x * inviluppo(dur, 0.03, 0.06) * 0.25

    def ottone(self, f, dur, brillante=1.0):
        t = tt(dur)
        env = inviluppo(dur, 0.04, 0.06)
        x = sum(np.sin(2 * np.pi * f * h * t) * (brillante / h) ** 0.9 for h in range(1, 12))
        return x * env * 0.2

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        # A: valzer musette originale in 3/4, la minore, 160 BPM
        b = 60 / 160
        mel = [(659.3, 1), (622.3, 1), (659.3, 1), (880, 2), (659.3, 1), (587.3, 1), (523.3, 1), (587.3, 1),
               (659.3, 3), (523.3, 1), (493.9, 1), (440, 1), (493.9, 2), (523.3, 1), (440, 3)]
        t0 = self.TA
        for f, d in mel:
            metti(a, self.fisarmonica(f, d * b * 0.95), t0)
            t0 += d * b
        acc = [(110, (261.6, 329.6)), (110, (261.6, 329.6)), (82.4, (246.9, 329.6)), (110, (261.6, 329.6))]
        for i in range(int(self.DUR / (3 * b))):
            basso, accordo = acc[i % len(acc)]
            tb = self.TA + i * 3 * b
            metti(a, self.fisarmonica(basso, b * 0.8), tb, 0.8)
            for j in (1, 2):
                for f in accordo:
                    metti(a, self.fisarmonica(f, b * 0.5), tb + j * b, 0.35)
        # B: oom-pah originale in 2/4, si bemolle maggiore, 120 BPM
        b = 60 / 120
        mel = [(466.2, 1), (587.3, 1), (698.5, 1.5), (587.3, 0.5), (698.5, 1), (784, 1), (698.5, 2),
               (622.3, 1), (523.3, 1), (466.2, 2)]
        t0 = self.TB
        for f, d in mel:
            metti(a, self.ottone(f, d * b * 0.9, 1.3), t0)
            t0 += d * b
        for i in range(int(self.DUR / (b / 1))):
            tb = self.TB + i * b
            if i % 2 == 0:
                metti(a, self.ottone(58.3 if (i // 4) % 2 == 0 else 87.3, b * 0.6, 0.8), tb, 1.6)
            else:
                for f in (233.1, 293.7, 349.2):
                    metti(a, self.ottone(f, b * 0.35, 1.0), tb, 0.5)
        return a[:int(self.END * SR)]

    def draw(self, c, t):
        if t < self.SPIEGA:
            domanda(c, "YOU'RE IN A SUPERMARKET", "WHICH WINE", "DO YOU BUY?", 150, 150)
            bottoni(c, t, [("A", self.TA, self.DUR), ("B", self.TB, self.DUR)])
            centered(c, 700, "A FRENCH ONE OR A GERMAN ONE", 28, MUTED, "sans", 700, 4)
            if t >= self.VOTO:
                scritta(c, 1240, "DEPENDS ON THE MUSIC?")
            return
        if t < self.CTA:
            spiega(c, t, self.SPIEGA, "IN-STORE MUSIC CHANGES WHAT YOU BUY", "FRENCH MUSIC,", "FRENCH WINE.",
                   ["For two weeks a supermarket played French",
                    "accordion music or German beer-hall music",
                    "next to French and German wines.",
                    "With French music, French wine outsold",
                    "German. With German music, the opposite.",
                    "Almost nobody said the music mattered.",
                    "",
                    "· North, Hargreaves & McKendrick, Nature, 1997"])
            return
        chiusura(c, t, self.CTA, "LISTEN NEXT TIME", "YOU GO SHOPPING", "SEND IT TO A WINE LOVER", 110)


# ================================================================ 6. ratti-tempo

class Ratti:
    seed, picco = 101, 0.85
    TEMPI = [(75, 0.8, 4.0), (132, 5.4, 5.6), (264, 11.6, 3.6)]
    VOTO = 15.4
    SPIEGA = VOTO + 2.4
    CTA = SPIEGA + 8.5
    END = CTA + 7.0

    def groove(self, bpm, dur):
        x = np.zeros(int(dur * SR) + SR)
        b = 60 / bpm
        n = int(dur / b)
        for i in range(n):
            t = tt(0.25)
            kick = np.sin(fase(50 + 110 * np.exp(-t * 30))) * np.exp(-t * 14)
            metti(x, kick, i * b, 0.9 if i % 2 == 0 else 0.5)
            if i % 2 == 1:
                sn = RNG.standard_normal(int(0.15 * SR)) * np.exp(-tt(0.15) * 25)
                metti(x, sn, i * b, 0.35)
            hat = RNG.standard_normal(int(0.04 * SR))
            hat = np.diff(hat, prepend=0) * np.exp(-tt(0.04) * 90)
            metti(x, hat, i * b + b / 2, 0.15)
            f = [110, 110, 130.8, 98][(i // 2) % 4]
            metti(x, np.sin(2 * np.pi * f * tt(b * 0.8)) * inviluppo(b * 0.8, 0.01, 0.05), i * b, 0.35)
        return x[:int(dur * SR)]

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        for bpm, t0, d in self.TEMPI:
            metti(a, self.groove(bpm, d), t0)
        return a[:int(self.END * SR)]

    def draw(self, c, t):
        if t < self.SPIEGA:
            domanda(c, "WATCH YOUR OWN HEAD", "WHICH TEMPO", "MOVES YOU?", 150, 150)
            cur = None
            for bpm, t0, d in self.TEMPI:
                if t0 <= t < t0 + d:
                    cur = (bpm, t0)
            for i, (bpm, t0, d) in enumerate(self.TEMPI):
                x = W / 2 + (i - 1) * 300
                on = cur and cur[0] == bpm
                c.text((x, 1240), f"{bpm}", style.font("display", 90), fill=WHITE if on or t > t0 else MUTED, anchor="ma")
                c.text((x, 1340), "BPM", style.font("sans", 22, 700), fill=MUTED, anchor="ma", tracking=4)
            if cur:
                b = 60 / cur[0]
                ph = ((t - cur[1]) % b) / b
                y = 960 - 160 * np.exp(-ph * 6)
                r = 70
                c.ellipse((W / 2 - r, y - r, W / 2 + r, y + r), fill=style.PINK)
            if t >= self.VOTO:
                scritta(c, 1460, "COMMENT YOUR TEMPO")
            return
        if t < self.CTA:
            spiega(c, t, self.SPIEGA, "IT'S NOT JUST HUMANS", "RATS BOB", "AT 120-140 BPM.", [
                "Researchers in Tokyo played music to rats",
                "with tiny motion sensors on their heads.",
                "They moved most in time with the beat",
                "between 120 and 140 BPM, just like us.",
                "One of the tracks was Mozart at 132 BPM,",
                "the middle tempo you just heard.",
                "",
                "· Ito et al., Science Advances, 2022"], 150, 120)
            return
        chiusura(c, t, self.CTA, "DID YOUR HEAD", "MOVE ON 132?", "SEND IT TO SOMEONE WITH A PET RAT", 120)


# ================================================================ 7. gomma

class Gomma:
    seed, picco = 103, 0.85
    BPM = 118
    T0 = 0.8
    GIRI = 2
    SPIEGA = 0.8 + 2 * 32 * 30 / 118 + 0.3
    CTA = SPIEGA + 8.5
    END = CTA + 7.0
    # ritornello originale di 4 battute (note in Hz, durata in crome)
    MEL = [(784, 1), (784, 1), (880, 1), (784, 1), (659.3, 2), (587.3, 2),
           (523.3, 1), (587.3, 1), (659.3, 1), (784, 1), (659.3, 4),
           (784, 1), (784, 1), (880, 1), (1046.5, 1), (987.8, 2), (880, 2),
           (784, 1), (880, 1), (784, 1), (659.3, 1), (587.3, 2), (523.3, 2)]

    def synth(self, f, dur):
        t = tt(dur)
        x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t)
        return x * np.exp(-t * 2.5) * inviluppo(dur, 0.005, 0.04)

    def build(self):
        a = np.zeros(int(self.END * SR) + SR)
        cr = 60 / self.BPM / 2
        giro = sum(d for _, d in self.MEL) * cr
        for g in range(self.GIRI):
            t0 = self.T0 + g * giro
            for f, d in self.MEL:
                metti(a, self.synth(f, d * cr * 1.2), t0, 0.5)
                t0 += d * cr
            for i in range(16):
                tb = self.T0 + g * giro + i * 2 * cr
                bass = [130.8, 130.8, 110, 110, 87.3, 87.3, 98, 98][i // 2]
                metti(a, np.sin(2 * np.pi * bass * tt(2 * cr * 0.9)) * inviluppo(2 * cr * 0.9, 0.01, 0.05), tb, 0.4)
                t = tt(0.2)
                metti(a, np.sin(fase(50 + 100 * np.exp(-t * 30))) * np.exp(-t * 14), tb, 0.5 if i % 2 == 0 else 0)
                if i % 2 == 1:
                    metti(a, RNG.standard_normal(int(0.12 * SR)) * np.exp(-tt(0.12) * 25), tb, 0.2)
        return a[:int(self.END * SR)]

    def draw(self, c, t):
        cr = 60 / self.BPM / 2
        giro = sum(d for _, d in self.MEL) * cr
        if t < self.SPIEGA:
            g = int((t - self.T0) / giro) + 1 if t >= self.T0 else 0
            domanda(c, "LISTEN ONCE. JUST ONCE", "THIS WILL GET", "STUCK.", 140, 170)
            # piano roll del ritornello
            x0, x1, y0, y1 = 150, W - 150, 780, 1160
            tot = sum(d for _, d in self.MEL)
            pos = ((t - self.T0) % giro) / giro if t >= self.T0 else -1
            acc = 0
            for f, d in self.MEL:
                xa = x0 + (x1 - x0) * acc / tot
                xb = x0 + (x1 - x0) * (acc + d) / tot - 6
                y = y1 - (y1 - y0) * np.log2(f / 500) / np.log2(1100 / 500)
                on = acc / tot <= pos < (acc + d) / tot
                c.rect((xa, y - 14, xb, y + 14), fill=style.PINK if on else GRIGIO, radius=8)
                acc += d
            if g:
                scritta(c, 1260, f"TIME {min(g, self.GIRI)} OF {self.GIRI}", WHITE)
            return
        if t < self.CTA:
            spiega(c, t, self.SPIEGA, "HOW TO GET RID OF AN EARWORM", "CHEW", "GUM.", [
                "In a 2015 study, people heard catchy songs",
                "and then tried not to think about them.",
                "Chewing gum cut how often the song came",
                "back, and how much they 'heard' it.",
                "Tapping a finger helped less. Chewing",
                "keeps busy the same system you use",
                "to sing in your head.",
                "· Beaman et al., Q. J. Exp. Psychology, 2015"], 170, 170)
            return
        chiusura(c, t, self.CTA, "IS IT STUCK NOW?", "GOT ANY GUM?", "SEND IT TO A FRIEND. SORRY.", 120)


REEL = {"stesso-volume": StessoVolume, "campana": Campana, "neonati": Neonati, "balena-52": Balena,
        "vino": Vino, "ratti-tempo": Ratti, "gomma": Gomma}

if __name__ == "__main__":
    nome = sys.argv[1]
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "out" / f"{nome}.mp4")
    out.parent.mkdir(exist_ok=True)
    r = REEL[nome]()
    write_mp4(out, r.build(), r.END, r.draw, seed=r.seed, picco=r.picco)
    print("scritto", out)
