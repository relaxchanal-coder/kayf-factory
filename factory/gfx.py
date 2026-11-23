"""أدوات الرسم: الخطوط، النص العربي، الإيموجي، الحركة."""
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
EMOJI_DIR = os.path.join(ROOT, "assets", "twemoji")

# ألوان كل حلقة: (خلفية غامقة 1، خلفية غامقة 2، لون مميز، لون ثانوي)
THEMES = {
    "cyan":   ((6, 14, 38), (12, 40, 78), (0, 220, 255), (255, 214, 0)),
    "orange": ((28, 10, 6), (70, 26, 10), (255, 140, 0), (255, 230, 120)),
    "purple": ((16, 6, 36), (52, 18, 92), (190, 110, 255), (0, 230, 200)),
    "green":  ((4, 24, 18), (10, 62, 46), (40, 240, 140), (255, 220, 80)),
    "red":    ((30, 4, 10), (84, 12, 28), (255, 70, 90), (255, 210, 120)),
    "blue":   ((4, 10, 30), (16, 36, 96), (70, 150, 255), (255, 190, 60)),
}
WHITE = (255, 255, 255)
LANG = ["ar"]  # لغة الحلقة الحالية: ar (من اليمين) أو en (من اليسار)
SHADOW = [True]  # ظل النصوص الافتراضي (يُطفأ مع اللوحات الفاتحة)


def is_rtl():
    return LANG[0] == "ar"


def _dl():
    return ("rtl", "ar") if is_rtl() else ("ltr", "en")


# ---------- الحركة ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_out_back(t, s=1.7):
    t = clamp(t)
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_out(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else 1.0


# ---------- الخطوط ----------
@lru_cache(maxsize=256)
def font(size, weight=800, family="Cairo"):
    size = max(8, int(size))
    if family == "Cairo":
        f = ImageFont.truetype(os.path.join(FONTS, "Cairo.ttf"), size,
                               layout_engine=ImageFont.Layout.RAQM)
        f.set_variation_by_axes([weight, 0])
        return f
    path = {"Lalezar": "Lalezar.ttf", "Tajawal": "Tajawal-ExtraBold.ttf"}[family]
    return ImageFont.truetype(os.path.join(FONTS, path), size,
                              layout_engine=ImageFont.Layout.RAQM)


def text_width(txt, f):
    d, l = _dl()
    return f.getlength(txt, direction=d, language=l)


def wrap(txt, f, max_w):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if text_width(test, f) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_img(txt, size, color=WHITE, weight=800, max_w=None, family="Cairo",
             shadow=None, line_gap=0.15):
    """يرجع صورة RGBA للنص (أسطر متمركزة)."""
    if shadow is None:
        shadow = SHADOW[0]
    return _text_img(txt, size, color, weight, max_w, family, shadow, line_gap, LANG[0])


@lru_cache(maxsize=512)
def _text_img(txt, size, color, weight, max_w, family, shadow, line_gap, lang):
    dr, lg = _dl()
    f = font(size, weight, family)
    lines = wrap(txt, f, max_w) if max_w else [txt]
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * (1 + line_gap))
    w = int(max(text_width(l, f) for l in lines)) + 20
    h = lh * len(lines) + 20
    pad = 16
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for i, l in enumerate(lines):
            lw = text_width(l, f)
            sd.text(((im.width - lw) / 2 + 3, pad + i * lh + 5), l, font=f,
                    fill=(0, 0, 0, 170), direction=dr, language=lg)
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5)))
        d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = text_width(l, f)
        d.text(((im.width - lw) / 2, pad + i * lh), l, font=f, fill=color,
               direction=dr, language=lg)
    bb = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    if bb:  # قص على حدود الحبر الفعلية ليكون التمركز بصرياً صحيحاً
        m = 14
        im = im.crop((max(0, bb[0] - m), max(0, bb[1] - m),
                      min(im.width, bb[2] + m), min(im.height, bb[3] + m)))
    return im


# ---------- الإيموجي (Twemoji - CC BY 4.0) ----------
def _emoji_file(e):
    cps = [f"{ord(c):x}" for c in e]
    for cand in ("-".join(cps), "-".join(c for c in cps if c != "fe0f")):
        p = os.path.join(EMOJI_DIR, cand + ".svg")
        if os.path.exists(p):
            return p
    for c in cps:  # آخر محاولة: أول رمز فقط
        p = os.path.join(EMOJI_DIR, c + ".svg")
        if os.path.exists(p):
            return p
    return os.path.join(EMOJI_DIR, "2753.svg")  # ❓


@lru_cache(maxsize=256)
def emoji_img(e, size):
    import io
    import cairosvg
    png = cairosvg.svg2png(url=_emoji_file(e), output_width=int(size),
                           output_height=int(size))
    return Image.open(io.BytesIO(png)).convert("RGBA")


# ---------- أشكال ----------
@lru_cache(maxsize=256)
def rounded(w, h, r, fill, outline=None, width=0):
    im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, int(w) - 1, int(h) - 1], int(r),
                                         fill=fill, outline=outline, width=width)
    return im


@lru_cache(maxsize=128)
def glow(size, color, strength=0.55):
    s = int(size)
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([s * .2, s * .2, s * .8, s * .8],
                               fill=color + (int(255 * strength),))
    return im.filter(ImageFilter.GaussianBlur(s * 0.12))


@lru_cache(maxsize=64)
def circle(d, fill, outline=None, width=0):
    im = Image.new("RGBA", (int(d), int(d)), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, int(d) - 1, int(d) - 1], fill=fill,
                               outline=outline, width=width)
    return im


# ---------- اللصق مع تحجيم وشفافية ----------
def blit(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        img = img.resize((max(1, int(img.width * scale)),
                          max(1, int(img.height * scale))), Image.BILINEAR)
    if abs(rot) > 0.1:
        img = img.rotate(rot, resample=Image.BILINEAR, expand=True)
    if alpha < 0.99:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2))) \
        if _inside(canvas, img, cx, cy) else _safe_paste(canvas, img, cx, cy)


def _inside(c, im, cx, cy):
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    return x >= 0 and y >= 0 and x + im.width <= c.width and y + im.height <= c.height


def _safe_paste(c, im, cx, cy):
    x, y = int(cx - im.width / 2), int(cy - im.height / 2)
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0))
    layer.paste(im, (x, y))
    c.alpha_composite(layer)
