#!/usr/bin/env python3
"""Code-drawn scenes for Bayt wa Hikaya — Al-Mutanabbi, 'The verse that killed him'.
1080x1920, one image per script line. Silhouettes only, no faces, no blood.
Fonts: Noto Sans Arabic Bold (narration) / Noto Naskh Arabic Bold (verses) —
Thmanyah Sans is NOT available in this VM.
Arabic text: Pillow's raqm engine shapes logical text natively
(direction='rtl', language='ar'). Do NOT pre-shape with arabic_reshaper/bidi —
that garbles the text (verified empirically in this VM)."""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.expanduser("~/workspace/bayt-wa-hikaya/mutanabbi-video")
OUT = f"{BASE}/build/stills"
os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
CRIMSON = (184, 72, 58)
GOLD = (232, 193, 90)
GOLD_LT = (242, 210, 122)
CREAM = (245, 234, 214)
PAPER = (240, 228, 205)
INK = (28, 24, 22)

F_NARR = "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"
F_VERSE = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"

def font(path, size):
    return ImageFont.truetype(path, size)

# --- RTL text helpers (raqm shapes logical Arabic text) ---
def tlen(d, text, fnt):
    return d.textlength(text, font=fnt, direction="rtl", language="ar")

def tbbox(d, text, fnt):
    return d.textbbox((0, 0), text, font=fnt, direction="rtl", language="ar")

def ttext(d, xy, text, fnt, fill):
    d.text(xy, text, font=fnt, fill=fill, direction="rtl", language="ar")

def ttext_c(d, cx, y, text, fnt, fill):
    """Draw text centred on cx, top at y."""
    b = tbbox(d, text, fnt)
    ttext(d, (cx - (b[2] - b[0]) / 2 - b[0], y - b[1]), text, fnt, fill)
    return b[3] - b[1]

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def gradient(img, top, bottom):
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp(top, bottom, y / H))

def glow(d, x, y, r, col, alpha=60):
    """Soft halo: drawn on a separate overlay and alpha-composited, because
    semi-transparent fills drawn directly on an RGBA image do NOT blend —
    converting to RGB then shows the fill colour at full strength."""
    img = d._image
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for rr, a in [(r * 0.5, 26), (r * 0.75, 16), (r * 1.0, 9)]:
        od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (a,))
    img.alpha_composite(ov)

def stars(d, n, seed, ymax=900):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.randint(20, W - 20); y = rnd.randint(60, ymax)
        r = rnd.choice([1, 1, 2, 2, 3])
        a = rnd.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 214, a))

def dune_layer(d, y0, amp, col, phase):
    pts = [(0, H)]
    for x in range(0, W + 40, 40):
        y = y0 + amp * math.sin((x / W) * math.pi * 2 + phase) + amp * 0.4 * math.sin((x / W) * math.pi * 5 + phase * 2)
        pts.append((x, y))
    pts += [(W, H)]
    d.polygon(pts, fill=col + (255,))

def dunes(d, palette, seed=1):
    dune_layer(d, 1450, 60, palette["dune3"], 0.4)
    dune_layer(d, 1560, 80, palette["dune2"], 2.1)
    dune_layer(d, 1700, 70, palette["dune1"], 4.0)

def person(d, x, y, h, col, cape=True, sword=False, arm_up=False):
    """Silhouette person, head top at (x,y), height h. No face.
    Keep figures clear of the caption band (y 1170-1410): call with y+h <= 1150,
    or place them entirely below y 1430."""
    r = h * 0.09
    d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
    d.polygon([(x - h*0.16, y + r*0.8), (x + h*0.16, y + r*0.8),
               (x + h*0.26, y + h), (x - h*0.26, y + h)], fill=col + (255,))
    if cape:
        d.polygon([(x + h*0.10, y + r), (x + h*0.34, y + h*0.75), (x + h*0.18, y + h*0.9)],
                  fill=lerp(col, (0, 0, 0), 0.25) + (255,))
    if arm_up:
        d.line([(x + h*0.14, y + h*0.30), (x + h*0.38, y + h*0.05)], fill=col + (255,), width=14)
    if sword:
        hx, hy = x + h*0.38, y + h*0.05
        d.line([(hx, hy), (hx + h*0.10, hy - h*0.42)], fill=(220, 220, 215, 255), width=10)
        d.line([(hx - 12, hy), (hx + 12, hy)], fill=GOLD + (255,), width=8)

def fallen_person(d, x, y, col):
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (255,))
    d.polygon([(x + 20, y - 10), (x + 150, y + 18), (x + 140, y + 52), (x + 10, y + 30)], fill=col + (255,))

def horse(d, x, y, s, col):
    """Walking horse silhouette, body centre (x,y). Legs reach y+110*s."""
    d.ellipse([x - 90*s, y - 55*s, x + 90*s, y + 45*s], fill=col + (255,))
    # neck rising steeply, head low and forward (horse, not camel)
    d.line([(x + 62*s, y - 25*s), (x + 98*s, y - 105*s)], fill=col + (255,), width=int(22*s))
    d.ellipse([x + 88*s, y - 128*s, x + 132*s, y - 98*s], fill=col + (255,))
    for lx, lean in ((-70, 6), (-30, -4), (30, 4), (70, -6)):
        d.line([(x + lx*s, y + 30*s), (x + (lx + lean)*s, y + 110*s)], fill=col + (255,), width=int(14*s))
    d.line([(x - 90*s, y - 30*s), (x - 130*s, y + 60*s)], fill=col + (255,), width=int(12*s))

def spears(d, xs, y0, h, col, tilt=0):
    for x in xs:
        d.line([(x, y0), (x + tilt, y0 - h)], fill=col + (255,), width=8)
        d.polygon([(x + tilt - 10, y0 - h), (x + tilt + 10, y0 - h), (x + tilt, y0 - h - 34)],
                  fill=(210, 210, 200, 255))

def pen_sword(d, x, y, length, angle_deg, progress, col=INK):
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    blade = length * (0.35 + 0.65 * progress)
    ex, ey = x + dx * blade, y + dy * blade
    d.line([(x, y), (ex, ey)], fill=(225, 225, 218, 255) if progress > 0.5 else col + (255,), width=16)
    d.polygon([(ex, ey), (ex - dy*14 - dx*26, ey + dx*14 - dy*26),
               (ex + dy*14 - dx*26, ey - dx*14 - dy*26)], fill=(225, 225, 218, 255))
    gx, gy = x - dx*30, y - dy*30
    d.line([(gx - dy*22, gy + dx*22), (gx + dy*22, gy - dx*22)], fill=GOLD + (255,), width=10)
    d.line([(gx, gy), (gx - dx*90, gy - dy*90)], fill=col + (255,), width=20)
    if progress < 0.6:
        for ox, oy, r in [(30, 40, 9), (-18, 62, 6), (52, 10, 5)]:
            d.ellipse([x+ox-r, y+oy-r, x+ox+r, y+oy+r], fill=col + (255,))

def ink_drops(d, cx, cy, n, seed, col=INK):
    rnd = random.Random(seed)
    for _ in range(n):
        x = cx + rnd.randint(-260, 260); y = cy + rnd.randint(-60, 140)
        r = rnd.randint(3, 12)
        d.ellipse([x-r, y-r, x+r, y+r], fill=col + (200,))

def paper_sheet(d, x0, y0, x1, y1, col=PAPER):
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=col + (255,))
    d.line([(x1-70, y0), (x1, y0+70)], fill=(200, 185, 150, 255), width=3)

def palm(d, x, y, h, col):
    """Palm with base at (x,y), height h. Keep base below the caption band or top above it."""
    d.line([(x, y), (x + 12, y - h)], fill=col + (255,), width=16)
    for ang in (-70, -40, -10, 20, 55):
        a = math.radians(ang - 90)
        ex, ey = x + 12 + math.cos(a) * h * 0.55, y - h + math.sin(a) * h * 0.55
        d.arc([ex - 60, ey - 30, ex + 60, ey + 30], start=0, end=180, fill=col + (255,), width=10)

def logo_badge(d):
    d.rounded_rectangle([906, 52, 1028, 174], radius=22, fill=PAPER + (255,))
    d.rounded_rectangle([906, 52, 1028, 174], radius=22, outline=(120, 100, 70, 255), width=3)
    ttext_c(d, 967, 62, "ب", font(F_NARR, 84), CRIMSON + (255,))

def wrap_text(d, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tlen(d, trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def caption(img, d, text, kind, big=False):
    """Lower caption band y ~1170-1410. Band is composited FIRST, text drawn
    on top of it (drawing text first then compositing the band dims it)."""
    if big:
        return
    size = 72 if kind in ("verse", "speech") else 60
    fnt = font(F_VERSE if kind == "verse" else F_NARR, size)
    lines = wrap_text(d, text, fnt, 980)
    while len(lines) > 3 and size > 44:
        size -= 6
        fnt = font(F_VERSE if kind == "verse" else F_NARR, size)
        lines = wrap_text(d, text, fnt, 980)
    band_h = 60 + len(lines) * (size + 14)
    y0 = 1410 - band_h
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.rounded_rectangle([36, y0, W-36, 1410], radius=26, fill=(10, 8, 8, 175))
    img.alpha_composite(band)
    d2 = ImageDraw.Draw(img)
    col = GOLD_LT if kind in ("verse", "speech") else CREAM
    y = y0 + 26
    for ln in lines:
        ttext_c(d2, W/2, y, ln, fnt, col + (255,))
        y += size + 14

def vignette(img):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, 90], fill=(0, 0, 0, 70))
    d.rectangle([0, H-90, W, H], fill=(0, 0, 0, 70))
    img.alpha_composite(ov)

PALETTES = {
    "gold":   {"top": (196, 138, 62), "bot": (84, 52, 28),  "dune1": (122, 84, 44), "dune2": (150, 106, 56), "dune3": (176, 130, 70), "sil": (46, 28, 16)},
    "dark":   {"top": (16, 20, 44),  "bot": (58, 44, 78),  "dune1": (22, 24, 46), "dune2": (32, 32, 58), "dune3": (44, 42, 72), "sil": (8, 8, 16)},
    "night":  {"top": (10, 16, 40),  "bot": (38, 58, 96),  "dune1": (16, 20, 40), "dune2": (24, 28, 52), "dune3": (34, 38, 66), "sil": (6, 8, 14)},
    "crimson":{"top": (120, 32, 28), "bot": (52, 14, 18),  "dune1": (70, 22, 20), "dune2": (92, 30, 26), "dune3": (116, 40, 32), "sil": (20, 8, 8)},
    "paper":  {"top": (226, 214, 190), "bot": (196, 180, 152), "dune1": (180, 162, 130), "dune2": (200, 184, 152), "dune3": (216, 200, 172), "sil": (60, 48, 36)},
    "cold":   {"top": (52, 78, 110), "bot": (22, 34, 58),  "dune1": (30, 44, 66), "dune2": (42, 58, 84), "dune3": (56, 74, 102), "sil": (12, 18, 30)},
}

def scene_palette(sid):
    return {
        "hook": "dark", "price": "dark", "who": "gold", "walks": "gold",
        "verse1a": "night", "verse1b": "night", "tongue": "gold", "satire": "dark",
        "waits": "night", "years": "gold", "return": "cold", "road": "cold",
        "ambush": "night", "son": "night", "flee": "night", "boy": "night",
        "verse2a": "night", "verse2b": "night", "turns": "crimson",
        "killedme": "crimson", "fights": "crimson", "spears": "crimson",
        "died": "paper", "lives": "paper", "question1": "paper",
        "question2": "paper", "cta": "paper",
    }[sid]

def render_scene(idx, line):
    sid, kind, text = line["id"], line["kind"], line["text"]
    pal = PALETTES[scene_palette(sid)]
    prog = idx / 26.0
    img = Image.new("RGBA", (W, H), pal["bot"] + (255,))
    gradient(img, pal["top"], pal["bot"])
    d = ImageDraw.Draw(img)
    dark = scene_palette(sid) in ("dark", "night", "crimson")
    if dark:
        stars(d, 90, seed=idx + 7)
    sun_x = 240 + (idx * 97) % 600
    sun_y = 300 + (idx * 53) % 260
    if scene_palette(sid) == "gold":
        d.ellipse([sun_x-90, sun_y-90, sun_x+90, sun_y+90], fill=(255, 214, 130, 255))
        glow(d, sun_x, sun_y, 260, (255, 190, 90), 60)
    elif dark:
        d.ellipse([sun_x-55, sun_y-55, sun_x+55, sun_y+55], fill=(235, 228, 200, 255))
        glow(d, sun_x, sun_y, 180, (200, 200, 220), 45)
    sil = pal["sil"]

    if sid == "hook":
        paper_sheet(d, 140, 480, 940, 1080)
        pen_sword(d, 540, 780, 420, -38, 0.55)
        ink_drops(d, 540, 900, 14, idx)
        f = font(F_NARR, 58)
        t = "بيت شعر واحد... قتله!"
        bw = tlen(d, t, f) + 70
        d.rounded_rectangle([(W-bw)/2, 300, (W+bw)/2, 300+104], radius=16, fill=CRIMSON + (255,))
        ttext_c(d, W/2, 322, t, f, (255, 255, 255, 255))
        d.ellipse([830, 950, 870, 990], fill=CRIMSON + (255,))
    elif sid == "price":
        paper_sheet(d, 140, 520, 940, 1060)
        pen_sword(d, 500, 800, 380, -30, 0.35)
        ink_drops(d, 540, 920, 10, idx)
        ttext_c(d, 540, 560, "الخيل والليل...", font(F_VERSE, 56), INK + (255,))
    elif sid in ("who", "walks"):
        dunes(d, pal, idx)
        if sid == "who":
            person(d, 540, 760, 380, sil, cape=True, sword=True, arm_up=True)
            d.line([(760, 780), (760, 980)], fill=sil + (255,), width=8)
            d.polygon([(760, 780), (880, 810), (760, 860)], fill=CRIMSON + (255,))
        else:
            person(d, 420, 800, 320, sil, cape=True)
            for i, fx in enumerate([300, 360, 480, 560]):
                d.ellipse([fx, 1620 + i*8, fx+26, 1632 + i*8], fill=lerp(sil, (0, 0, 0), 0.2) + (255,))
            horse(d, 820, 1550, 0.9, sil)
    elif sid == "verse1a":
        dunes(d, pal, idx)
        for ex in (420, 660):
            d.ellipse([ex-52, 700, ex+52, 760], fill=GOLD + (255,))
            d.ellipse([ex-20, 716, ex+20, 744], fill=(20, 16, 10, 255))
        person(d, 540, 820, 280, sil)
    elif sid == "verse1b":
        dunes(d, pal, idx)
        paper_sheet(d, 340, 900, 740, 1120)
        for i, r in enumerate([90, 170, 250, 330]):
            d.arc([540-r, 1010-r, 540+r, 1010+r], start=200, end=340, fill=GOLD + (220 - i*40,), width=8)
            d.arc([540-r, 1010-r, 540+r, 1010+r], start=20, end=160, fill=GOLD + (220 - i*40,), width=8)
        person(d, 540, 860, 240, sil)
    elif sid == "tongue":
        dunes(d, pal, idx)
        pen_sword(d, 540, 900, 520, -25, 0.75)
        glow(d, 540, 700, 200, GOLD, 50)
    elif sid == "satire":
        paper_sheet(d, 140, 560, 940, 1040)
        rnd = random.Random(3)
        for _ in range(26):
            x = rnd.randint(180, 900); y = rnd.randint(600, 1000); r = rnd.randint(12, 46)
            d.ellipse([x-r, y-r, x+r, y+r], fill=INK + (220,))
        pen_sword(d, 540, 800, 300, -40, 0.45)
    elif sid == "waits":
        dunes(d, pal, idx)
        for ex in (300, 540, 780):
            d.ellipse([ex-26, 640, ex+26, 672], fill=(255, 220, 120, 255))
            d.ellipse([ex-9, 650, ex+9, 662], fill=(10, 10, 10, 255))
        pen_sword(d, 540, 950, 380, 65, 0.6)
    elif sid == "years":
        dunes(d, pal, idx)
        for i, (sx, sy) in enumerate([(260, 500), (540, 380), (820, 500)]):
            d.ellipse([sx-46, sy-46, sx+46, sy+46], fill=(255, 214, 130, 200 - i*40))
        person(d, 540, 840, 280, sil)
    elif sid in ("return", "road"):
        dunes(d, pal, idx)
        for i, cx in enumerate([240, 430, 620, 810]):
            d.ellipse([cx-70, 1560, cx+70, 1640], fill=sil + (255,))
            person(d, cx, 1480, 150, sil, cape=False)
        palm(d, 180, 1720, 260, sil)
        if sid == "road":
            d.ellipse([700, 900, 900, 980], fill=(120, 160, 190, 255))
            palm(d, 900, 1700, 220, sil)
    elif sid == "ambush":
        dunes(d, pal, idx)
        spears(d, [180, 320, 460, 620, 780, 920], 1650, 520, sil, tilt=30)
        person(d, 540, 820, 300, sil, sword=True, arm_up=True)
    elif sid == "son":
        dunes(d, pal, idx)
        fallen_person(d, 380, 1520, sil)
        person(d, 760, 760, 360, sil, cape=True)
        ink_drops(d, 540, 1200, 8, idx)
    elif sid == "flee":
        dunes(d, pal, idx)
        horse(d, 540, 1550, 1.15, sil)
        person(d, 820, 1500, 300, sil, cape=True)
    elif sid == "boy":
        dunes(d, pal, idx)
        pen_sword(d, 540, 950, 420, -20, 0.85)
        d.ellipse([700, 620, 740, 680], fill=INK + (255,))
        person(d, 400, 820, 300, sil)
        person(d, 760, 880, 220, sil, cape=False)
    elif sid in ("verse2a", "verse2b"):
        dunes(d, pal, idx)
        if sid == "verse2a":
            horse(d, 300, 1550, 1.0, sil)
            horse(d, 780, 1580, 0.85, sil)
            person(d, 540, 800, 320, sil, sword=True, arm_up=True)
        else:
            pen_sword(d, 300, 900, 300, -30, 1.0)
            spears(d, [540], 1100, 380, sil)
            paper_sheet(d, 700, 850, 950, 1050)
            d.ellipse([825, 930, 855, 960], fill=GOLD + (255,))
            glow(d, 540, 800, 260, GOLD, 40)
    elif sid == "turns":
        dunes(d, pal, idx)
        person(d, 540, 780, 360, sil, cape=True, sword=True, arm_up=True)
        glow(d, 540, 900, 240, CRIMSON, 70)
    elif sid == "killedme":
        f = font(F_NARR, 118)
        ttext_c(d, W/2, 780, "قَتَلْتَنِي..", f, GOLD_LT + (255,))
        ttext_c(d, W/2, 970, "قَتَلَكَ اللَّهُ!", f, GOLD_LT + (255,))
        pen_sword(d, 830, 1420, 240, -45, 1.0)
    elif sid == "fights":
        dunes(d, pal, idx)
        d.arc([240, 500, 840, 1100], start=200, end=340, fill=(245, 245, 240, 255), width=22)
        person(d, 420, 800, 320, sil, sword=True, arm_up=True)
        person(d, 720, 860, 280, sil)
        d.ellipse([760, 620, 800, 660], fill=CRIMSON + (255,))
    elif sid == "spears":
        dunes(d, pal, idx)
        spears(d, [240, 420, 600, 780, 920], 1650, 600, sil, tilt=-18)
        spears(d, [300, 500, 700, 880], 1650, 560, (90, 30, 26), tilt=18)
        person(d, 540, 900, 280, sil)
    elif sid in ("died", "lives"):
        paper_sheet(d, 140, 480, 940, 1080)
        if sid == "died":
            pen_sword(d, 540, 780, 300, -35, 0.2)
            ink_drops(d, 540, 950, 6, idx)
        else:
            pen_sword(d, 540, 780, 300, -35, 0.0)
            glow(d, 540, 780, 260, GOLD, 60)
            d.ellipse([520, 760, 560, 800], fill=GOLD + (255,))
        palm(d, 180, 1720, 200, sil)
    elif sid in ("question1", "question2"):
        paper_sheet(d, 140, 520, 940, 1060)
        d.line([(540, 560), (540, 700)], fill=INK + (255,), width=10)
        d.line([(380, 700), (700, 700)], fill=INK + (255,), width=10)
        tilt = -14 if sid == "question2" else 0
        for px, label in [(380, "البيت"), (700, "الحياة")]:
            yy = 700 + (tilt if px < 540 else -tilt)
            d.line([(px, yy), (px, yy+70)], fill=INK + (255,), width=6)
            d.arc([px-70, yy+40, px+70, yy+120], start=0, end=180, fill=INK + (255,), width=8)
            ttext_c(d, px, yy+140, label, font(F_NARR, 40), INK + (255,))
        if sid == "question2":
            d.ellipse([520, 980, 560, 1020], fill=CRIMSON + (255,))
    elif sid == "cta":
        ttext_c(d, W/2, 560, "ب", font(F_NARR, 150), CRIMSON + (255,))
        ttext_c(d, W/2, 820, "البيت الذي قتله", font(F_NARR, 62), INK + (255,))
        ttext_c(d, W/2, 910, "بيتٌ وحكاية", font(F_NARR, 62), INK + (255,))
    # vignette first, then caption text and logo on top of it
    vignette(img)
    d = ImageDraw.Draw(img)
    caption(img, d, text, kind, big=(sid == "killedme"))
    logo_badge(ImageDraw.Draw(img))
    img.convert("RGB").save(f"{OUT}/{idx+1:02d}_{sid}.jpg", quality=88)
    return f"{OUT}/{idx+1:02d}_{sid}.jpg"

def render_end_card():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    gradient(img, (240, 230, 208), (206, 190, 160))
    d = ImageDraw.Draw(img)
    ttext_c(d, W/2, 420, "ب", font(F_NARR, 320), CRIMSON + (255,))
    ttext_c(d, W/2, 900, "اكتب في التعليقات: كبرياء", font(F_NARR, 64), CRIMSON + (255,))
    ttext_c(d, W/2, 1010, "البيت الذي قتله", font(F_NARR, 72), INK + (255,))
    ttext_c(d, W/2, 1120, "بيتٌ وحكاية", font(F_NARR, 72), INK + (255,))
    pen_sword(d, 540, 1450, 260, -30, 0.0)
    vignette(img)
    img.convert("RGB").save(f"{OUT}/28_endcard.jpg", quality=88)
    return f"{OUT}/28_endcard.jpg"

if __name__ == "__main__":
    timeline = json.load(open(f"{BASE}/build/timeline.json"))
    for i, line in enumerate(timeline):
        p = render_scene(i, line)
        print(i+1, line["id"], p)
    print("end card:", render_end_card())
