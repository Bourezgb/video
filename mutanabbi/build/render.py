#!/usr/bin/env python3
"""render_v3 — Mutanabbi scenes rebuilt under the 8 mandatory scene-quality
rules (scene-kit.md, from the v2 critique). Only the DRAWING changed vs v2.
Same timeline, audio, music, script and plan.
1080x1920, silhouettes only, no faces, no blood.
Text: Pillow raqm RTL shaping (direction='rtl', language='ar') — do NOT use
arabic_reshaper/bidi, that garbles text."""
import json, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.expanduser("~/workspace/bayt-wa-hikaya/mutanabbi-video")
OUT = f"{BASE}/build/stills_v3"
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

def tlen(d, text, fnt):
    return d.textlength(text, font=fnt, direction="rtl", language="ar")

def tbbox(d, text, fnt):
    return d.textbbox((0, 0), text, font=fnt, direction="rtl", language="ar")

def ttext(d, xy, text, fnt, fill):
    d.text(xy, text, font=fnt, fill=fill, direction="rtl", language="ar")

def ttext_c(d, cx, y, text, fnt, fill):
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
    img = d._image
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for rr, a in [(r * 0.5, 26), (r * 0.75, 16), (r * 1.0, 9)]:
        od.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (a,))
    img.alpha_composite(ov)

def light_beam(d, x, y_top, w_top, w_bot, col, alpha=28):
    """Soft diagonal light beam from the sky."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.polygon([(x - w_top, y_top), (x + w_top, y_top),
                (x + w_bot, 1180), (x - w_bot, 1180)], fill=col + (alpha,))
    img = d._image
    img.alpha_composite(ov)

def stars(d, n, seed, ymax=900):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.randint(20, W - 20); y = rnd.randint(60, ymax)
        r = rnd.choice([1, 1, 2, 2, 3])
        a = rnd.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 244, 214, a))

def clouds(d, seed, col, ymax=700, n=5):
    """Soft horizontal cloud bands (drawn blurred on an overlay)."""
    rnd = random.Random(seed)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for _ in range(n):
        cx = rnd.randint(80, W - 80); cy = rnd.randint(120, ymax)
        cw = rnd.randint(180, 420); ch = rnd.randint(26, 60)
        od.ellipse([cx - cw, cy - ch, cx + cw, cy + ch], fill=col + (38,))
    ov = ov.filter(ImageFilter.GaussianBlur(18))
    d._image.alpha_composite(ov)

def dust(d, seed, n, col, ymin=900, ymax=1500):
    rnd = random.Random(seed)
    for _ in range(n):
        x = rnd.randint(30, W - 30); y = rnd.randint(ymin, ymax)
        r = rnd.randint(2, 7)
        a = rnd.randint(40, 130)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))

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

def foreground_crest(d, col, y0=1560):
    """Dark dune crest across the very bottom (below the caption band)."""
    pts = [(0, H)]
    for x in range(0, W + 40, 40):
        y = y0 + 55 * math.sin((x / W) * math.pi * 2 + 1.2)
        pts.append((x, y))
    pts += [(W, H)]
    d.polygon(pts, fill=col + (255,))
    # a few grass tufts / stones on the crest
    for x in (140, 420, 880):
        d.line([(x, y0 + 30), (x - 18, y0 - 30)], fill=col + (255,), width=6)
        d.line([(x, y0 + 30), (x + 14, y0 - 40)], fill=col + (255,), width=6)

def rocks(d, col, y=1500):
    rnd = random.Random(11)
    for _ in range(6):
        x = rnd.randint(40, W - 120); w = rnd.randint(50, 130); h = rnd.randint(24, 60)
        d.polygon([(x, y + h), (x + w * 0.3, y), (x + w * 0.8, y + h * 0.3), (x + w, y + h)],
                  fill=col + (255,))

def palm(d, x, y, h, col, lean=0):
    """Rule 3: lean varies the palms so no two are identical."""
    tx = x + 12 + lean
    d.line([(x, y), (tx, y - h)], fill=col + (255,), width=16)
    for ang in (-70, -40, -10, 20, 55):
        a = math.radians(ang - 90)
        ex, ey = tx + math.cos(a) * h * 0.55, y - h + math.sin(a) * h * 0.55
        d.arc([ex - 60, ey - 30, ex + 60, ey + 30], start=0, end=180, fill=col + (255,), width=10)

def palm_fronds_top(d, col, side="left"):
    """Framing fronds hanging in from a top corner, above the caption band."""
    x0 = -40 if side == "left" else W + 40
    for ang, ln in [(-35, 320), (-10, 380), (15, 340), (40, 280)]:
        a = math.radians(ang if side == "left" else 180 - ang)
        ex = x0 + math.cos(a) * ln; ey = 60 + abs(math.sin(a)) * ln * 0.7
        d.line([(x0, 20), (ex, ey)], fill=col + (255,), width=12)
        for t in (0.35, 0.6, 0.85):
            px, py = x0 + (ex - x0) * t, 20 + (ey - 20) * t
            d.line([(px, py), (px - 26, py + 34)], fill=col + (255,), width=6)
            d.line([(px, py), (px + 26, py + 30)], fill=col + (255,), width=6)

def city_silhouette(d, y_base, col, scale=1.0):
    """Distant city on the horizon: domes, minarets, walls."""
    # wall band
    d.rectangle([0, y_base - 26 * scale, W, y_base + 10], fill=col + (255,))
    rnd = random.Random(5)
    x = 30
    while x < W - 40:
        w = rnd.randint(90, 190) * scale
        # dome building
        d.rectangle([x, y_base - 60 * scale, x + w, y_base], fill=col + (255,))
        cx = x + w / 2
        d.ellipse([cx - w * 0.32, y_base - 60 * scale - w * 0.30, cx + w * 0.32, y_base - 60 * scale + w * 0.12],
                  fill=col + (255,))
        d.line([(cx, y_base - 60 * scale - w * 0.30), (cx, y_base - 60 * scale - w * 0.42)], fill=col + (255,), width=5)
        x += w + rnd.randint(20, 70)
    # minarets
    for mx in (180, 760, 980):
        d.rectangle([mx, y_base - 170 * scale, mx + 22 * scale, y_base], fill=col + (255,))
        d.polygon([(mx - 6, y_base - 170 * scale), (mx + 28 * scale, y_base - 170 * scale),
                   (mx + 11 * scale, y_base - 215 * scale)], fill=col + (255,))

def river(d, y0, y1, col):
    d.polygon([(0, y0), (W, y0 + 40), (W, y1), (0, y1 - 30)], fill=col + (255,))
    for x in (200, 480, 760, 940):
        d.arc([x - 70, y0 + 20, x + 70, y0 + 70], start=200, end=340, fill=(220, 235, 245, 160), width=5)

def banner(d, x, y_base, h, col, flag_col):
    d.line([(x, y_base), (x, y_base - h)], fill=col + (255,), width=10)
    d.polygon([(x, y_base - h), (x + 150, y_base - h + 34), (x + 118, y_base - h + 72), (x, y_base - h + 58)],
              fill=flag_col + (255,))

def spears_persp(d, col, y_base=1660, seed=3):
    """Rule 3: a row of spears with perspective AND seeded variation —
    height +-15%, spacing and lean +-5 deg, so no two spears are identical."""
    rnd = random.Random(seed)
    x = 60
    while x < W - 60:
        s = rnd.uniform(0.55, 1.0)
        lean = math.radians(rnd.uniform(-5, 5))
        h = 560 * s
        dx = math.tan(lean) * h
        d.line([(x, y_base), (x + 26 * s + dx, y_base - h)], fill=col + (255,), width=max(5, int(9 * s)))
        tx, ty = x + 26 * s + dx, y_base - h
        d.polygon([(tx - 11 * s, ty), (tx + 11 * s, ty), (tx, ty - 38 * s)], fill=(210, 210, 200, 255))
        x += int(rnd.uniform(105, 165))

def mound_y(y_feet, cx, width, y_base, x):
    """Ground height of a mound whose crest is y_feet at cx (quartic falloff,
    so the surface stays near the crest across the figures' range)."""
    t = (x - cx) / max(1.0, width / 2.0)
    return y_feet + (y_base - y_feet) * min(1.0, t ** 4)

def ground_mound(d, y_feet, col, cx=540, width=1080, y_base=1460):
    """Rule 1: a ground hill whose crest passes exactly through y_feet at cx.
    Draw BEFORE the figure so its feet touch ground; y_base hides behind
    the caption gradient / lower frame."""
    pts = [(0, y_base)]
    for x in range(0, W + 40, 40):
        pts.append((x, mound_y(y_feet, cx, width, y_base, x)))
    pts += [(W, y_base)]
    d.polygon(pts, fill=col + (255,))

def contact_shadow(d, x, y_feet, w=90):
    """Rule 1: ground-contact oval shadow under feet / hooves."""
    d.ellipse([x - w, y_feet - 10, x + w, y_feet + 14], fill=(0, 0, 0, 110))

def pfeet(y, h):
    """Feet y of a person2 figure whose head top is y and height h."""
    return int(y + h * 1.02)

def place_on_mound(y_feet, cx, width, y_base, x, h):
    """Top-y for person2 so its feet rest exactly on the mound at x."""
    return int(mound_y(y_feet, cx, width, y_base, x) - h * 1.02)

# ---------- figures (v2: cloaks with folds, turbans, varied stances) ----------
def person2(d, x, y, h, col, stance="proud", sword=False, cloak_col=None):
    """Silhouette person, head top at (x,y), height h. No face.
    stance: proud | walk | flee | kneel | turn | point
    Keep y+h <= 1150 unless the figure is meant to stand below the caption band."""
    cc = cloak_col or col
    r = h * 0.072  # rule 2: head:body 1:7, pure silhouette
    # head + turban: larger round head, wrapped cap with a band and a small tail
    d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))
    d.pieslice([x - r * 1.05, y - r * 1.35, x + r * 1.05, y + r * 0.15], start=180, end=360,
               fill=lerp(col, (255, 255, 255), 0.18) + (255,))
    d.rectangle([x - r, y - r * 0.25, x + r, y + r * 0.15], fill=lerp(col, (0, 0, 0), 0.3) + (255,))
    d.polygon([(x + r * 0.7, y - r * 0.1), (x + r * 1.5, y + r * 0.9), (x + r * 0.9, y + r * 0.7)],
              fill=lerp(col, (0, 0, 0), 0.25) + (255,))
    # cloak: sloped shoulders, tapered waist, slight flare to a pointed hem —
    # narrower than v2 (the old wide rectangle read as a tombstone)
    sh, wa, hem = h * 0.11, h * 0.13, h * 0.18  # rule 2: a 1:7 figure is slender
    top_y = y + r * 0.9
    # rule 5: the cloak billows — a fixed sway baked from sin(T*3) at mid-scene
    # (stills are static; the zoompan push-in supplies the motion in video)
    sw = h * 0.045
    pts = [(x - sh, top_y), (x + sh, top_y),
           (x + wa, top_y + h * 0.45), (x + hem + sw, top_y + h * 0.80),
           (x + hem * 0.45 + sw, top_y + h * 0.96), (x, top_y + h * 0.88),
           (x - hem * 0.45 + sw * 0.5, top_y + h * 0.96), (x - hem + sw * 0.5, top_y + h * 0.80),
           (x - wa, top_y + h * 0.45)]
    d.polygon(pts, fill=cc + (255,))
    # fold shading: two darker vertical folds
    fold = lerp(cc, (0, 0, 0), 0.30)
    d.line([(x - h * 0.07, top_y + h * 0.2), (x - h * 0.11, top_y + h * 0.85)], fill=fold + (255,), width=7)
    d.line([(x + h * 0.08, top_y + h * 0.2), (x + h * 0.13, top_y + h * 0.85)], fill=fold + (255,), width=7)
    # sash
    d.rectangle([x - wa, top_y + h * 0.42, x + wa, top_y + h * 0.48], fill=GOLD + (220,))
    # legs / feet for walk & flee stances (protruding below the hem)
    if stance in ("walk", "flee"):
        fwd = 1 if stance == "flee" else -1
        leg = lerp(col, (0, 0, 0), 0.15)
        d.polygon([(x - h * 0.05, top_y + h * 0.9), (x + h * 0.22 * fwd, top_y + h * 1.02),
                   (x + h * 0.26 * fwd, top_y + h * 1.02), (x + h * 0.06, top_y + h * 0.9)], fill=leg + (255,))
        d.polygon([(x + h * 0.02, top_y + h * 0.9), (x - h * 0.18 * fwd, top_y + h * 1.0),
                   (x - h * 0.14 * fwd, top_y + h * 1.0), (x + h * 0.10, top_y + h * 0.9)], fill=leg + (255,))
    # arm
    ax, ay = x + h * 0.15, top_y + h * 0.22
    if stance == "thrust":
        # rule 5: a real thrust — arm drives forward, sword along the arm,
        # torso leaning into the blow (caller places the opponent within reach)
        d.line([(ax, ay), (x + h * 0.52, top_y + h * 0.10)], fill=col + (255,), width=16)
        hx, hy = x + h * 0.52, top_y + h * 0.10
        d.line([(hx, hy), (hx + h * 0.34, hy - h * 0.10)], fill=(228, 228, 222, 255), width=11)
        d.line([(hx - 10, hy + 6), (hx + 10, hy - 6)], fill=GOLD + (255,), width=9)
    elif stance == "proud" or sword:
        d.line([(ax, ay), (x + h * 0.40, top_y - h * 0.02)], fill=col + (255,), width=15)
        hx, hy = x + h * 0.40, top_y - h * 0.02
        if sword:
            d.line([(hx, hy), (hx + h * 0.16, hy - h * 0.46)], fill=(228, 228, 222, 255), width=11)
            d.line([(hx - 14, hy), (hx + 14, hy)], fill=GOLD + (255,), width=9)
    elif stance == "point":
        d.line([(ax, ay), (x + h * 0.48, top_y + h * 0.12)], fill=col + (255,), width=15)
    elif stance == "flee":
        # arm swept back, cloak billowing
        d.polygon([(x + h * 0.12, top_y + h * 0.1), (x + h * 0.52, top_y + h * 0.35),
                   (x + h * 0.44, top_y + h * 0.5), (x + h * 0.05, top_y + h * 0.3)],
                  fill=lerp(cc, (0, 0, 0), 0.2) + (255,))
    else:
        d.line([(ax, ay), (x + h * 0.20, top_y + h * 0.52)], fill=col + (255,), width=14)
    if stance == "kneel":
        pass  # kneeling is handled by calling with a shorter h and lower y

def fallen_person(d, x, y, col):
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (255,))
    d.polygon([(x + 20, y - 10), (x + 150, y + 18), (x + 140, y + 52), (x + 10, y + 30)], fill=col + (255,))

def horse2(d, x, y, s, col, pose="walk", direction=1):
    """Horse profile, body centre (x,y), scale s. direction +1 faces right.
    v2 fix: smooth ellipse barrel (no angular polygon), thick CURVED neck,
    short thick legs that do not cross, tail as a soft curve. The v1/v2
    angular body + long thin crossing legs read as a camel/dog."""
    dir_ = direction
    def X(v):
        return x + v * s * dir_
    def Y(v):
        return y + v * s
    # tail first (behind the body): soft S-curve
    d.line([(X(-88), Y(-28)), (X(-128), Y(0)), (X(-138), Y(52)), (X(-118), Y(92))],
           fill=col + (255,), width=int(18 * s), joint="curve")
    # legs: short, thick, two-segment, hooves on the ground line Y(108)
    if pose == "gallop":
        legs = [(-62, -78, -96, 108), (-28, -46, -58, 108), (34, 58, 84, 108), (64, 84, 108, 108)]
    elif pose == "stand":
        legs = [(-62, -58, -56, 108), (-26, -50, -28, 108), (28, -50, 30, 108), (62, -58, 58, 108)]
    else:  # walk
        legs = [(-62, -58, -44, 108), (-26, -50, -40, 108), (28, -50, 46, 108), (62, -58, 52, 108)]
    for (lx, lx2, lx3, ly) in legs:
        d.line([(X(lx), Y(18)), (X(lx2), Y(66)), (X(lx3), Y(ly))], fill=col + (255,),
               width=int(19 * s), joint="curve")
        d.ellipse([X(lx3) - 11 * s, Y(ly) - 8 * s, X(lx3) + 11 * s, Y(ly) + 8 * s], fill=col + (255,))
    # body: smooth ellipse barrel
    d.ellipse([X(-96), Y(-58), X(92), Y(42)], fill=col + (255,))
    # neck: one thick curved line from shoulder to poll (smooth arch)
    d.line([(X(58), Y(-30)), (X(88), Y(-72)), (X(108), Y(-108)), (X(122), Y(-128))],
           fill=col + (255,), width=int(36 * s), joint="curve")
    # mane: dark jagged ridge on the upper edge of the neck
    d.polygon([(X(52), Y(-52)), (X(78), Y(-92)), (X(70), Y(-70)), (X(94), Y(-108)),
               (X(88), Y(-82)), (X(110), Y(-124)), (X(104), Y(-94)), (X(120), Y(-128)),
               (X(128), Y(-100)), (X(100), Y(-58)), (X(74), Y(-28))],
              fill=lerp(col, (0, 0, 0), 0.35) + (255,))
    # head: long muzzle pointing forward-down, two ears
    d.polygon([(X(112), Y(-136)), (X(152), Y(-124)), (X(166), Y(-104)), (X(146), Y(-90)),
               (X(122), Y(-98))], fill=col + (255,))
    d.polygon([(X(110), Y(-138)), (X(114), Y(-162)), (X(124), Y(-136))], fill=col + (255,))
    d.polygon([(X(124), Y(-138)), (X(134), Y(-160)), (X(140), Y(-132))], fill=col + (255,))
    # rider is drawn separately by the caller (person2 on the horse's back)

def ink_stroke(d, pts, w0, col=INK, alpha=255):
    """Flowing calligraphy stroke through pts (list of (x,y)), tapering width."""
    n = len(pts)
    for i in range(n - 1):
        t = i / max(1, n - 2)
        w = max(3, int(w0 * (1 - t * 0.75)))
        d.line([pts[i], pts[i + 1]], fill=col + (alpha,), width=w, joint="curve")
    # splatter at the start and a tapered tip at the end
    rnd = random.Random(7)
    for _ in range(8):
        ox, oy = pts[0][0] + rnd.randint(-40, 40), pts[0][1] + rnd.randint(-25, 25)
        r = rnd.randint(2, 7)
        d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=col + (200,))

def paper2(d, x0, y0, x1, y1, col=PAPER):
    """Manuscript sheet: shadow, ruled faint lines, folded corner, deckled edge."""
    d.rounded_rectangle([x0 + 14, y0 + 18, x1 + 14, y1 + 18], radius=18, fill=(0, 0, 0, 60))
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=col + (255,))
    d.rounded_rectangle([x0, y0, x1, y1], radius=18, outline=(170, 150, 110, 255), width=3)
    for yy in range(y0 + 90, y1 - 60, 64):
        d.line([(x0 + 44, yy), (x1 - 44, yy)], fill=(190, 172, 130, 160), width=3)
    d.polygon([(x1 - 70, y0), (x1, y0), (x1, y0 + 70)], fill=(214, 198, 162, 255))
    d.line([(x1 - 70, y0), (x1, y0 + 70)], fill=(170, 150, 110, 255), width=3)

def pen_sword(d, x, y, length, angle_deg, progress, col=INK):
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    blade = length * (0.35 + 0.65 * progress)
    ex, ey = x + dx * blade, y + dy * blade
    d.line([(x, y), (ex, ey)], fill=(225, 225, 218, 255) if progress > 0.5 else col + (255,), width=16)
    d.polygon([(ex, ey), (ex - dy * 14 - dx * 26, ey + dx * 14 - dy * 26),
               (ex + dy * 14 - dx * 26, ey - dx * 14 - dy * 26)], fill=(225, 225, 218, 255))
    gx, gy = x - dx * 30, y - dy * 30
    d.line([(gx - dy * 22, gy + dx * 22), (gx + dy * 22, gy - dx * 22)], fill=GOLD + (255,), width=10)
    d.line([(gx, gy), (gx - dx * 90, gy - dy * 90)], fill=col + (255,), width=20)

def ink_drops(d, cx, cy, n, seed, col=INK):
    rnd = random.Random(seed)
    for _ in range(n):
        x = cx + rnd.randint(-260, 260); y = cy + rnd.randint(-60, 140)
        r = rnd.randint(3, 12)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (200,))

def eyes_in_dark(d, pairs, col=(255, 220, 120)):
    for (ex, ey, s) in pairs:
        for dx in (-1, 1):
            d.ellipse([ex + dx * 34 * s - 26 * s, ey - 14 * s, ex + dx * 34 * s + 26 * s, ey + 14 * s],
                      fill=col + (255,))
            d.ellipse([ex + dx * 34 * s - 9 * s, ey - 6 * s, ex + dx * 34 * s + 9 * s, ey + 6 * s],
                      fill=(10, 10, 10, 255))

def balance_scale(d, cx, y0, tilt_deg, col=INK, s=1.0):
    """The balance of verse vs life. s scales it — the sky balance is huge."""
    d.line([(cx, y0), (cx, y0 + 180 * s)], fill=col + (255,), width=max(6, int(10 * s)))
    a = math.radians(tilt_deg)
    dx, dy = math.cos(a) * 190 * s, math.sin(a) * 190 * s
    d.line([(cx - dx, y0 - dy), (cx + dx, y0 + dy)], fill=col + (255,), width=max(6, int(10 * s)))
    for (px, py, label) in [(cx - dx, y0 - dy, "البيت"), (cx + dx, y0 + dy, "الحياة")]:
        d.line([(px, py), (px, py + 70 * s)], fill=col + (255,), width=6)
        d.arc([px - 70 * s, py + 40 * s, px + 70 * s, py + 120 * s], start=0, end=180, fill=col + (255,), width=8)
        ttext_c(d, px, py + 140 * s, label, font(F_NARR, int(40 * s)), col + (255,))

# ---------- shared frame furniture (kept from v1, working) ----------
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

def shade_band(img, y_top=1020, y_bot=1410, max_alpha=175):
    """Rule 7: a soft vertical gradient — transparent at the top, dark at the
    text — that melts into the ground instead of a solid caption box."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(y_top, y_bot):
        a = int(max_alpha * ((y - y_top) / max(1, y_bot - y_top)) ** 1.6)
        od.line([(0, y), (W, y)], fill=(8, 6, 6, a))
    img.alpha_composite(ov)

def caption(img, d, text, kind, big=False):
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
    shade_band(img, y_top=max(1000, y0 - 90), y_bot=1410)
    d2 = ImageDraw.Draw(img)
    col = GOLD_LT if kind in ("verse", "speech") else CREAM
    y = y0 + 26
    for ln in lines:
        ttext_c(d2, W / 2, y, ln, fnt, col + (255,))
        y += size + 14

def vignette(img):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, 90], fill=(0, 0, 0, 70))
    d.rectangle([0, H - 90, W, H], fill=(0, 0, 0, 70))
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

def sky(d, pal, idx, dark, sun_xy=None):
    """Background layer: sun/moon + halo, stars or clouds, dust in the air."""
    if dark:
        stars(d, 110, seed=idx + 7)
    else:
        clouds(d, seed=idx + 3, col=(255, 220, 160), ymax=600)
    sx, sy = sun_xy or (240 + (idx * 97) % 600, 300 + (idx * 53) % 260)
    if scene_palette("who") and False:
        pass
    if dark:
        d.ellipse([sx - 55, sy - 55, sx + 55, sy + 55], fill=(235, 228, 200, 255))
        glow(d, sx, sy, 190, (200, 200, 220), 45)
    else:
        d.ellipse([sx - 90, sy - 90, sx + 90, sy + 90], fill=(255, 214, 130, 255))
        glow(d, sx, sy, 270, (255, 190, 90), 60)
    dust(d, seed=idx + 21, n=26, col=(255, 220, 160) if not dark else (200, 200, 220),
         ymin=700, ymax=1150)

def render_scene(idx, line):
    sid, kind, text = line["id"], line["kind"], line["text"]
    pal = PALETTES[scene_palette(sid)]
    dark = scene_palette(sid) in ("dark", "night", "crimson")
    img = Image.new("RGBA", (W, H), pal["bot"] + (255,))
    gradient(img, pal["top"], pal["bot"])
    d = ImageDraw.Draw(img)
    sil = pal["sil"]
    sky(d, pal, idx, dark)

    if sid == "hook":
        # CLOSE-UP: giant ink sword diagonally across a dark paper sky
        paper2(d, 120, 420, 960, 1120)
        ink_stroke(d, [(220, 1000), (400, 880), (560, 760), (720, 640), (860, 560)], 26)
        pen_sword(d, 540, 760, 560, -38, 0.9)
        ink_drops(d, 540, 900, 10, idx)
        f = font(F_NARR, 58)
        t = "بيت شعر واحد... قتله!"
        bw = tlen(d, t, f) + 70
        d.rounded_rectangle([(W - bw) / 2, 270, (W + bw) / 2, 374], radius=16, fill=CRIMSON + (255,))
        ttext_c(d, W / 2, 292, t, f, (255, 255, 255, 255))
        d.ellipse([830, 950, 872, 992], fill=CRIMSON + (255,))
    elif sid == "price":
        # MEDIUM: poet writing at a desk in the background, paper close in front
        ground_mound(d, pfeet(420, 300), pal["dune2"], cx=700, width=760, y_base=1120)
        person2(d, 700, 420, 300, sil, stance="walk")
        contact_shadow(d, 700, pfeet(420, 300), 70)
        ink_stroke(d, [(620, 700), (700, 660), (780, 700)], 14)
        paper2(d, 120, 780, 960, 1140)
        pen_sword(d, 480, 980, 380, -28, 0.4)
        ink_drops(d, 540, 1040, 8, idx)
        glow(d, 540, 960, 240, GOLD, 35)
    elif sid == "who":
        # MEDIUM: proud figure large centre-right, banner, sun halo
        dunes(d, pal, idx)
        glow(d, 640, 620, 300, (255, 190, 90), 55)
        banner(d, 830, 1130, 420, sil, CRIMSON)
        ground_mound(d, pfeet(560, 520), pal["dune2"], cx=560, width=900, y_base=1420)
        person2(d, 560, 560, 520, sil, stance="proud", sword=True)
        contact_shadow(d, 560, pfeet(560, 520), 90)
        rocks(d, sil, y=1520)
        foreground_crest(d, sil, y0=1620)
    elif sid == "walks":
        # WIDE: tiny walker on the horizon, footprints, huge low sun
        dunes(d, pal, idx)
        # rule 6: the sky() sun is the only sun — no second disc here
        ground_mound(d, pfeet(940, 180), pal["dune2"], cx=540, width=560, y_base=1400)
        person2(d, 540, 940, 180, sil, stance="walk")
        contact_shadow(d, 540, pfeet(940, 180), 40)
        for i, fx in enumerate(range(300, 820, 65)):
            d.ellipse([fx, 1128 + (i % 2) * 10, fx + 22, 1140 + (i % 2) * 10], fill=lerp(sil, (0, 0, 0), 0.2) + (255,))
        rocks(d, sil, y=1560)
        foreground_crest(d, sil, y0=1640)
    elif sid == "verse1a":
        # CLOSE-UP: head and shoulders, huge, glowing eyes in the dark
        glow(d, 540, 420, 260, GOLD, 40)
        # rule 2: pure silhouette — NO eyes on the face (lurking eyes live only
        # in the dark of the "waits" scene). A medium shot on a mound: the
        # giant bust read as a monolith, so the figure stands on the ground
        # like every other scene (rule 1)
        glow(d, 540, 420, 260, GOLD, 40)
        ground_mound(d, 1091, pal["dune2"], cx=540, width=900, y_base=1420)
        person2(d, 540, 520, 560, sil, stance="proud")
        contact_shadow(d, 540, 1091, 80)
        dunes(d, pal, idx)
    elif sid == "verse1b":
        # MEDIUM: pen radiating sound waves over a paper
        dunes(d, pal, idx)
        # rule 4: no manuscript sheet here — the pen itself radiates the sound
        for i, r in enumerate([90, 170, 250, 330]):
            d.arc([540 - r, 760 - r, 540 + r, 760 + r], start=200, end=340, fill=GOLD + (220 - i * 40,), width=8)
            d.arc([540 - r, 760 - r, 540 + r, 760 + r], start=20, end=160, fill=GOLD + (220 - i * 40,), width=8)
        pen_sword(d, 540, 700, 320, -30, 0.3)
        glow(d, 540, 700, 220, GOLD, 45)
    elif sid == "tongue":
        # CLOSE-UP: the pen-sword fills the frame diagonally
        glow(d, 540, 700, 320, GOLD, 60)
        ink_stroke(d, [(120, 1080), (340, 900), (560, 720), (820, 520), (980, 420)], 30)
        pen_sword(d, 540, 760, 620, -32, 0.95)
        dust(d, seed=idx + 5, n=30, col=(255, 220, 160), ymin=500, ymax=1150)
    elif sid == "satire":
        # MEDIUM: manuscript sheet with ink spreading like fire
        paper2(d, 140, 480, 940, 1060)
        # rule 4 (satire keeps the sheet) — ink as thin flowing streaks, not bubbles
        rnd = random.Random(3)
        for _ in range(10):
            x = rnd.randint(200, 880); y = rnd.randint(620, 980); r = rnd.randint(5, 14)
            d.ellipse([x - r, y - r, x + r, y + r], fill=INK + (220,))
        ink_stroke(d, [(240, 1000), (420, 860), (600, 760), (800, 660)], 22)
        pen_sword(d, 540, 800, 300, -40, 0.45)
    elif sid == "waits":
        # MEDIUM: watchers in the dark, a sword hanging
        dunes(d, pal, idx)
        eyes_in_dark(d, [(300, 620, 1.0), (540, 560, 1.2), (780, 640, 0.9)])
        pen_sword(d, 540, 950, 420, 65, 0.6)
        glow(d, 540, 500, 180, (200, 200, 220), 40)
        rocks(d, sil, y=1540)
        foreground_crest(d, sil, y0=1640)
    elif sid == "years":
        # WIDE: three suns in a row, small walker crossing the dunes
        dunes(d, pal, idx)
        # rule 6: ONE sun (drawn by sky()) travelling an arc east->west —
        # the dotted arc is its path across the sky
        for k in range(9):
            ang = math.radians(-155 + k * 16)
            ax, ay = 530 + 390 * math.cos(ang), 900 + 390 * math.sin(ang)
            r = max(3, 11 - k)
            d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=(255, 214, 130, 110))
        ground_mound(d, pfeet(940, 170), pal["dune2"], cx=540, width=560, y_base=1400)
        person2(d, 540, 940, 170, sil, stance="walk")
        contact_shadow(d, 540, pfeet(940, 170), 40)
        dust(d, seed=idx + 9, n=30, col=(255, 220, 160), ymin=900, ymax=1400)
        foreground_crest(d, sil, y0=1640)
    elif sid == "return":
        # WIDE: caravan on a road toward a distant domed city
        dunes(d, pal, idx)
        city_silhouette(d, 1150, lerp(sil, (255, 255, 255), 0.15), scale=0.9)
        ground_mound(d, 1115, pal["dune2"], cx=560, width=1080, y_base=1420)
        # rule 3: seeded variation — no two mounts alike
        rnd = random.Random(31)
        for i, cx in enumerate([280, 470, 660, 840]):
            s = rnd.uniform(0.66, 0.86)
            jx = rnd.randint(-18, 18)
            hx = cx + jx
            hy = int(mound_y(1115, 560, 1080, 1420, hx) - 108 * s)
            horse2(d, hx, hy, s, sil, pose="walk", direction=1)
            person2(d, hx - 10, int(hy - 110 * s), int(130 * s), sil, stance="walk")
            contact_shadow(d, hx, int(mound_y(1115, 560, 1080, 1420, hx)), 55)
        palm(d, 150, 1500, 240, sil, lean=15)
        foreground_crest(d, sil, y0=1660)
    elif sid == "road":
        # WIDE: river band, palms, city far, small travellers on the far bank
        dunes(d, pal, idx)
        city_silhouette(d, 980, lerp(sil, (255, 255, 255), 0.2), scale=0.7)
        d.polygon([(0, 960), (W, 940), (W, 1010), (0, 1030)], fill=pal["dune2"] + (255,))
        river(d, 1030, 1170, (110, 150, 185))
        palm(d, 160, 1000, 320, sil, lean=-25)
        palm(d, 920, 1000, 240, sil, lean=30)
        horse2(d, 540, 900, 0.75, sil, pose="walk", direction=1)
        person2(d, 530, 770, 130, sil, stance="walk")
        contact_shadow(d, 540, 981, 60)
        foreground_crest(d, sil, y0=1680)
    elif sid == "ambush":
        # MEDIUM-WIDE: spear row with perspective, dust, figures closing in
        dunes(d, pal, idx)
        dust(d, seed=idx + 4, n=44, col=(200, 200, 220), ymin=800, ymax=1400)
        spears_persp(d, sil)
        ground_mound(d, 1086, pal["dune2"], cx=540, width=1080, y_base=1420)
        person2(d, 300, place_on_mound(1086, 540, 1080, 1420, 300, 300), 300, sil, stance="proud", sword=True)
        person2(d, 780, place_on_mound(1086, 540, 1080, 1420, 780, 260), 260, sil, stance="flee")
        contact_shadow(d, 300, mound_y(1086, 540, 1080, 1420, 300), 75)
        contact_shadow(d, 780, mound_y(1086, 540, 1080, 1420, 780), 65)
        glow(d, 540, 600, 220, (200, 200, 220), 35)
    elif sid == "son":
        # MEDIUM: fallen boy on a dune, poet kneeling beside him
        dunes(d, pal, idx)
        glow(d, 430, 1000, 260, (200, 200, 220), 45)
        ground_mound(d, 1106, pal["dune2"], cx=540, width=1080, y_base=1420)
        fallen_person(d, 360, 1095, sil)
        person2(d, 720, place_on_mound(1106, 540, 1080, 1420, 720, 320), 320, sil, stance="walk")
        contact_shadow(d, 720, mound_y(1106, 540, 1080, 1420, 720), 70)
        ink_drops(d, 540, 1100, 8, idx)
        foreground_crest(d, sil, y0=1660)
    elif sid == "flee":
        # MEDIUM-WIDE: proper galloping horse with rider leaning forward
        dunes(d, pal, idx)
        dust(d, seed=idx + 6, n=50, col=(200, 200, 220), ymin=900, ymax=1150)
        ground_mound(d, 1084, pal["dune2"], cx=500, width=1000, y_base=1400)
        horse2(d, 500, 960, 1.15, sil, pose="gallop", direction=1)
        person2(d, 440, 660, 280, sil, stance="flee", cloak_col=lerp(sil, (0, 0, 0), 0.1))
        contact_shadow(d, 500, 1084, 110)
        rocks(d, sil, y=1560)
    elif sid == "boy":
        # MEDIUM: boy pointing, poet turning back, ink sword glowing between them
        dunes(d, pal, idx)
        glow(d, 540, 800, 260, GOLD, 50)
        pen_sword(d, 540, 850, 460, -18, 0.95)
        ground_mound(d, 1110, pal["dune2"], cx=540, width=1080, y_base=1420)
        person2(d, 300, place_on_mound(1110, 540, 1080, 1420, 300, 260), 260, sil, stance="point")
        person2(d, 820, place_on_mound(1110, 540, 1080, 1420, 820, 340), 340, sil, stance="turn")
        contact_shadow(d, 300, mound_y(1110, 540, 1080, 1420, 300), 60)
        contact_shadow(d, 820, mound_y(1110, 540, 1080, 1420, 820), 75)
    elif sid == "verse2a":
        # CLOSE-UP: horse's head and rider filling the frame under the moon
        glow(d, 760, 420, 300, (200, 200, 220), 50)
        ground_mound(d, 1093, pal["dune2"], cx=430, width=1000, y_base=1420)
        horse2(d, 430, 920, 1.6, sil, pose="stand", direction=1)
        contact_shadow(d, 430, 1093, 130)
        person2(d, 360, 520, 380, sil, stance="proud", sword=True)
        dust(d, seed=idx + 8, n=30, col=(200, 200, 220), ymin=900, ymax=1400)
        dunes(d, pal, idx)
        foreground_crest(d, sil, y0=1660)
    elif sid == "verse2b":
        # MEDIUM: the four symbols in a row, each glowing
        dunes(d, pal, idx)
        glow(d, 540, 800, 300, GOLD, 40)
        # rule 4: no big manuscript sheet — the four symbols stand on the dune,
        # the "paper" is a small rolled scroll, not a sheet in the middle
        ground_mound(d, 1120, pal["dune2"], cx=540, width=1080, y_base=1420)
        pen_sword(d, 250, 1080, 320, -28, 1.0)
        d.line([(520, 1120), (520, 740)], fill=sil + (255,), width=10)
        d.polygon([(510, 740), (530, 740), (520, 680)], fill=(210, 210, 200, 255))
        d.rounded_rectangle([680, 960, 920, 1120], radius=16, fill=PAPER + (255,))
        d.rounded_rectangle([680, 960, 920, 1120], radius=16, outline=(170, 150, 110, 255), width=3)
        d.ellipse([672, 980, 700, 1100], fill=(214, 198, 162, 255))
        d.ellipse([900, 980, 928, 1100], fill=(214, 198, 162, 255))
        d.ellipse([790, 1020, 820, 1050], fill=GOLD + (255,))
        d.line([(800, 820), (800, 950)], fill=INK + (255,), width=14)
        d.polygon([(792, 950), (808, 950), (800, 980)], fill=INK + (255,))
    elif sid == "turns":
        # MEDIUM: figure walking back toward the crimson light
        dunes(d, pal, idx)
        glow(d, 540, 700, 320, CRIMSON, 70)
        light_beam(d, 540, 0, 200, 440, CRIMSON, 30)
        ground_mound(d, 1108, pal["dune2"], cx=540, width=900, y_base=1420)
        person2(d, 540, 720, 380, sil, stance="walk", sword=True)
        contact_shadow(d, 540, 1108, 80)
        rocks(d, sil, y=1540)
        foreground_crest(d, sil, y0=1660)
    elif sid == "killedme":
        # CLOSE-UP: full-screen crimson, huge gold words, ink sword at the edge
        f = font(F_NARR, 118)
        ttext_c(d, W / 2, 780, "قَتَلْتَنِي..", f, GOLD_LT + (255,))
        ttext_c(d, W / 2, 970, "قَتَلَكَ اللَّهُ!", f, GOLD_LT + (255,))
        pen_sword(d, 860, 1100, 260, -45, 1.0)
        ink_stroke(d, [(120, 1150), (300, 1080), (480, 1020)], 18)
        dust(d, seed=idx + 2, n=30, col=(255, 220, 160), ymin=500, ymax=1100)
    elif sid == "fights":
        # MEDIUM: the two fighters LOCKED together — a real thrust, a flash,
        # no white arc over two men standing apart (rule 5)
        dunes(d, pal, idx)
        ground_mound(d, 1105, pal["dune2"], cx=540, width=1000, y_base=1420)
        glow(d, 540, 820, 300, CRIMSON, 70)
        glow(d, 565, 900, 170, (255, 240, 200), 95)
        for (sx1, sy1, sx2, sy2) in [(565, 900, 470, 810), (565, 900, 660, 820),
                                     (565, 900, 490, 990), (565, 900, 650, 990)]:
            d.line([(sx1, sy1), (sx2, sy2)], fill=(255, 244, 220, 220), width=7)
        person2(d, 420, place_on_mound(1105, 540, 1000, 1420, 420, 330), 330, sil, stance="thrust")
        person2(d, 640, place_on_mound(1105, 540, 1000, 1420, 640, 300), 300, sil, stance="flee")
        contact_shadow(d, 420, mound_y(1105, 540, 1000, 1420, 420), 80)
        contact_shadow(d, 640, mound_y(1105, 540, 1000, 1420, 640), 70)
        dust(d, seed=idx + 10, n=40, col=(255, 200, 180), ymin=900, ymax=1400)
        foreground_crest(d, sil, y0=1660)
    elif sid == "spears":
        # MEDIUM: crossing spears in the foreground, fallen figure behind
        dunes(d, pal, idx)
        d.line([(180, 1650), (900, 700)], fill=sil + (255,), width=14)
        d.line([(900, 1650), (180, 700)], fill=lerp(sil, (255, 255, 255), 0.15) + (255,), width=14)
        d.polygon([(890, 700), (910, 700), (900, 640)], fill=(210, 210, 200, 255))
        d.polygon([(170, 700), (190, 700), (180, 640)], fill=(210, 210, 200, 255))
        ground_mound(d, 1085, pal["dune2"], cx=540, width=1080, y_base=1420)
        fallen_person(d, 480, 1095, sil)
        person2(d, 780, place_on_mound(1085, 540, 1080, 1420, 780, 260), 260, sil, stance="walk")
        contact_shadow(d, 780, mound_y(1085, 540, 1080, 1420, 780), 60)
    elif sid == "died":
        # CLOSE-UP: paper close, the ink sword lying still, one drop falling
        paper2(d, 140, 420, 940, 1080)
        pen_sword(d, 540, 760, 320, -35, 0.15)
        ink_drops(d, 540, 950, 5, idx)
        d.ellipse([530, 1000, 556, 1040], fill=INK + (255,))
        glow(d, 540, 760, 240, (220, 220, 230), 40)
    elif sid == "lives":
        # MEDIUM: no paper — the verse itself lives on: an ink stroke rises
        # from the dune and hardens into a small sword, a figure walks away
        dunes(d, pal, idx)
        glow(d, 540, 850, 320, GOLD, 65)
        ground_mound(d, 1100, pal["dune2"], cx=540, width=900, y_base=1420)
        ink_stroke(d, [(300, 1080), (480, 1000), (640, 920), (780, 860)], 16)
        pen_sword(d, 780, 860, 200, -35, 0.15)
        person2(d, 300, place_on_mound(1100, 540, 900, 1420, 300, 150), 150, sil, stance="walk")
        contact_shadow(d, 300, mound_y(1100, 540, 900, 1420, 300), 40)
    elif sid == "question1":
        # MEDIUM: rule 4 — the balance HUGE in the sky over the dunes, no sheet
        dunes(d, pal, idx)
        glow(d, 540, 700, 300, GOLD, 45)
        ground_mound(d, 1120, pal["dune1"], cx=540, width=1080, y_base=1420)
        balance_scale(d, 440, 480, 0, s=1.5)
    elif sid == "question2":
        # MEDIUM-CLOSE: the tilted balance huge in the sky, a crimson drop
        # falling from the lower (verse) pan — no sheet (rule 4)
        dunes(d, pal, idx)
        glow(d, 540, 700, 300, GOLD, 45)
        ground_mound(d, 1120, pal["dune1"], cx=540, width=1080, y_base=1420)
        balance_scale(d, 440, 480, -14, s=1.5)
        d.ellipse([150, 730, 182, 772], fill=CRIMSON + (255,))
    elif sid == "cta":
        ttext_c(d, W / 2, 520, "ب", font(F_NARR, 170), CRIMSON + (255,))
        ink_stroke(d, [(300, 1080), (480, 1020), (700, 980), (860, 940)], 16)
        ttext_c(d, W / 2, 800, "البيت الذي قتله", font(F_NARR, 62), INK + (255,))
        ttext_c(d, W / 2, 890, "بيتٌ وحكاية", font(F_NARR, 62), INK + (255,))
        dunes(d, pal, idx)

    vignette(img)
    d = ImageDraw.Draw(img)
    # rule 8: the end-card sentence is NOCAP and hides the corner badge —
    # its words already live on the paper end card that follows
    if sid != "cta":
        caption(img, d, text, kind, big=(sid == "killedme"))
        logo_badge(ImageDraw.Draw(img))
    img.convert("RGB").save(f"{OUT}/{idx+1:02d}_{sid}.jpg", quality=88)
    return f"{OUT}/{idx+1:02d}_{sid}.jpg"

def render_end_card():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    gradient(img, (240, 230, 208), (206, 190, 160))
    d = ImageDraw.Draw(img)
    ttext_c(d, W / 2, 420, "ب", font(F_NARR, 320), CRIMSON + (255,))
    ttext_c(d, W / 2, 900, "اكتب في التعليقات: كبرياء", font(F_NARR, 64), CRIMSON + (255,))
    ttext_c(d, W / 2, 1010, "البيت الذي قتله", font(F_NARR, 72), INK + (255,))
    ttext_c(d, W / 2, 1120, "بيتٌ وحكاية", font(F_NARR, 72), INK + (255,))
    pen_sword(d, 540, 1450, 260, -30, 0.0)
    vignette(img)
    img.convert("RGB").save(f"{OUT}/28_endcard.jpg", quality=88)
    return f"{OUT}/28_endcard.jpg"

if __name__ == "__main__":
    timeline = json.load(open(f"{BASE}/build/timeline.json"))
    for i, line in enumerate(timeline):
        p = render_scene(i, line)
        print(i + 1, line["id"], p)
    print("end card:", render_end_card())
