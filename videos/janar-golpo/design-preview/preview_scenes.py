import math, random
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import render as R

W, H, S = R.W, R.H, R.S
NAVY, TEAL, AMB, GOLD = R.NAVY, R.TEAL, R.AMB, R.GOLD
CREAM, TERRA, BRN, GREEN = R.CREAM, R.TERRA, R.BRN, R.GREEN

def out(im, name):
    im.convert('RGB').resize((540, 960)).save(f'preview_{name}.png')
    print(name)

def fix(c):
    c.im = c.im.convert('RGBA'); c.d = ImageDraw.Draw(c.im); return c

def glow(im, box, color, radius=60):
    pad = radius * 2
    w, h = box[2] - box[0], box[3] - box[1]
    g = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.rounded_rectangle([pad, pad, pad + w, pad + h], radius, fill=color)
    g = g.filter(ImageFilter.GaussianBlur(radius))
    im.alpha_composite(g, (int(box[0] - pad), int(box[1] - pad)))

# ---------- 1. KABA: Kaaba silhouette + dense stars + kiswah gold band ----------
def kaba():
    c = R.Cv([(0, (6, 10, 26)), (.6, (14, 26, 52)), (1, (6, 12, 24))]);fix(c)
    c.stars(140, 1500, 21)
    c.crescent(1060, 230, 62, (255, 232, 170))
    c.rect(0, 1900, W, H, (4, 7, 16))
    cx, bw, bh, by = 648, 620, 700, 950
    glow(c.im, (cx - bw // 2, by, cx + bw // 2, by + bh), (255, 201, 60, 45), 50)
    c.rect(cx - bw // 2, by, cx + bw // 2, by + bh, (14, 12, 12))
    c.rect(cx - bw // 2, by - 26, cx + bw // 2, by - 2, (30, 24, 18))
    c.rect(cx - bw // 2, by + 620, cx + bw // 2, by + 660, (255, 201, 60))
    dx = 90
    c.rect(cx - dx, 520, cx + dx, 560, (8, 8, 10), (255, 201, 60), 6)
    c.rect(0, 1880, W, 1900, (10, 16, 30))
    out(c.im, 'kaba')

# ---------- 2. GREEN DOME: Masjid an-Nabawi silhouette + glow ----------
def green_dome():
    c = R.Cv([(0, (8, 16, 34)), (.55, (18, 40, 60)), (1, (10, 20, 34))]);fix(c)
    c.stars(90, 900, 33)
    glow(c.im, (480, 560, 820, 900), (80, 220, 150, 60), 90)
    d = 210
    c.poly([(648 - d, 1600), (648 - d, 1100), (648, 660), (648 + d, 1100), (648 + d, 1600)], (10, 22, 20))
    c.rect(648 - d, 1500, 648 + d, 1740, (10, 22, 20))
    for sx in (200, 1096):
        c.rect(sx - 26, 820, sx + 26, 1740, (9, 18, 17))
        c.ell(sx - 40, 730, sx + 40, 830, (9, 18, 17))
        c.rect(sx - 40, 690, sx + 40, 716, (13, 28, 24))
    c.ell(648 - 30, 620, 648 + 30, 680, (46, 158, 107))
    c.line([(648, 560), (648, 630)], (46, 158, 107), 6)
    c.rect(0, 1720, W, H, (6, 12, 20))
    for wxx in (500, 648, 796):
        c.rect(wxx - 22, 1580, wxx + 22, 1720, (255, 220, 140, 70))
    out(c.im, 'green_dome')

# ---------- 3. QURAN CLOSEUP: open Quran on rehal + warm lamp ----------
def quran():
    c = R.Cv([(0, (26, 16, 10)), (.6, (52, 32, 18)), (1, (22, 13, 8))]);fix(c)
    glow(c.im, (180, 300, 1116, 1250), (255, 190, 90, 55), 110)
    d = 320
    c.poly([(648, 1650), (648 - d, 1600), (648, 1450), (648 + d, 1600)], (58, 36, 22))
    c.poly([(648, 1450), (648 - 210, 1520), (648, 1650), (648 + 210, 1520)], (74, 48, 28))
    c.rect(648, 1750 - 60, 648 + 460, 1810 - 60, (74, 48, 28))
    for sx in (-1, 1):
        x0 = 648 + (30 if sx > 0 else -420)
        c.poly([(648 + sx * 30, 1150), (648 + sx * 420, 1180), (648 + sx * 420, 1560), (648 + sx * 30, 1530)],
               (240, 228, 198))
        c.line([(648 + sx * 30, 1150), (648 + sx * 30, 1530)], (180, 160, 130), 4)
    for sy in range(1220, 1520, 60):
        c.line([(648 - 340, sy), (648 - 80, sy + 8)], (190, 172, 140), 3)
        c.line([(648 + 80, sy + 8), (648 + 340, sy)], (190, 172, 140), 3)
    c.rect(0, 1830, W, H, (18, 10, 6))
    out(c.im, 'quran')

# ---------- 4. RAIN WINDOW: rainy night window + warm lantern ----------
def rain():
    c = R.Cv([(0, (10, 14, 26)), (.6, (20, 28, 44)), (1, (8, 10, 20))]);fix(c)
    c.rect(150, 300, 1146, 1560, (12, 18, 32), (60, 74, 96), 14, r=18)
    c.line([(648, 300), (648, 1560)], (60, 74, 96), 12)
    c.line([(150, 930), (1146, 930)], (60, 74, 96), 12)
    rnd = random.Random(7)
    for _ in range(90):
        x = rnd.uniform(170, 1130); y = rnd.uniform(320, 1540); ln = rnd.uniform(40, 120)
        c.line([(x, y), (x - ln * .25, y + ln)], (110, 140, 180), 2)
    lx, ly = 648, 1750
    glow(c.im, (lx - 60, ly - 130, lx + 60, ly + 10), (255, 178, 80, 80), 60)
    c.rect(lx - 26, ly - 120, lx + 26, ly, (26, 16, 10), (255, 178, 80), 6, r=10)
    c.line([(lx - 40, ly - 130), (lx + 40, ly - 130)], (255, 178, 80), 8)
    c.rect(0, 1830, W, H, (6, 8, 16))
    out(c.im, 'rain')

# ---------- 5. DUNE SUNSET: desert dunes + setting sun + caravan ----------
def dunes():
    c = R.Cv([(0, (40, 20, 34)), (.45, (120, 52, 40)), (.75, (200, 96, 48)), (1, (238, 140, 60))]);fix(c)
    c.circ(648, 1450, 150, (255, 214, 130))
    glow(c.im, (498, 1300, 798, 1600), (255, 170, 80, 90), 90)
    c.poly([(0, 1650), (400, 1500), (900, 1680), (W, 1560), (W, H), (0, H)], (60, 28, 26))
    c.poly([(0, 1780), (500, 1650), (1000, 1800), (W, 1700), (W, H), (0, H)], (36, 16, 18))
    def camel(x, y, s, col=(16, 8, 10)):
        c.ell(x - 40 * s, y - 44 * s, x + 40 * s, y - 8 * s, col)
        c.circ(x - 18 * s, y - 40 * s, 22 * s, col)
        c.circ(x + 18 * s, y - 40 * s, 22 * s, col)
        c.line([(x - 36 * s, y - 28 * s), (x - 52 * s, y - 62 * s)], col, max(3, int(9 * s)))
        c.ell(x - 66 * s, y - 74 * s, x - 42 * s, y - 58 * s, col)
        for lx in (-32, -20, 20, 32):
            c.line([(x + lx * s, y - 12 * s), (x + lx * s, y)], col, max(3, int(6 * s)))
        c.line([(x + 38 * s, y - 40 * s), (x + 48 * s, y - 16 * s)], col, max(2, int(4 * s)))
    camel(600, 1665, 2.2)
    camel(780, 1700, 1.9)
    camel(920, 1730, 1.6)
    out(c.im, 'dunes')

# ---------- 6. PATTERN LIGHT: geometric star pattern wall + light shaft ----------
def pattern():
    c = R.Cv([(0, (16, 14, 22)), (.6, (34, 26, 34)), (1, (14, 11, 18))]);fix(c)
    for qy in range(8):
        for qx in range(6):
            x = 100 + qx * 200; y = 160 + qy * 250; r = 78
            pts = [(x + r * math.cos(math.pi / 4 + i * math.pi / 4), y + r * math.sin(math.pi / 4 + i * math.pi / 4)) for i in range(8)]
            c.poly(pts, None, (90, 72, 60), 4)
            c.poly([(x, y - r // 2), (x + r // 2, y), (x, y + r // 2), (x - r // 2, y)], None, (70, 55, 50), 3)
    sh = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.polygon([(0, 0), (700, 0), (250, H * S // 1), (0, H * S)], fill=(255, 220, 150, 40))
    c.im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    out(c.im, 'pattern')

import sys
names = {'kaba': kaba, 'green_dome': green_dome, 'quran': quran, 'rain': rain, 'dunes': dunes, 'pattern': pattern}
if len(sys.argv) > 1:
    for n in sys.argv[1:]:
        names[n]()
else:
    for k, f in names.items():
        f()
