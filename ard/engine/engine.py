"""Vox-style paper collage engine: shared helpers for drawing scenes."""
import math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1920, 1080, 30
FD = '/home/claude/vox/fonts/'

PAPER = (238, 231, 217)
CARD = (250, 247, 240)
INK = (26, 24, 22)
GREY = (120, 112, 100)
YELLOW = (247, 211, 59)
RED = (214, 52, 40)
BLUE = (47, 104, 168)
SEA = (196, 211, 208)


# ---------------------------------------------------------------- fonts
@functools.lru_cache(None)
def font(name, size, weight=None):
    path = {'cairo': 'Cairo.ttf', 'kufi': 'NotoKufi.ttf', 'oswald': 'Oswald.ttf',
            'plex': 'IBMPlexSansArabic-Medium.ttf', 'plexb': 'IBMPlexSansArabic-Bold.ttf',
            'lalezar': 'Lalezar-Regular.ttf'}[name]
    f = ImageFont.truetype(FD + path, size, layout_engine=ImageFont.Layout.RAQM)
    if weight is not None:
        axes = f.get_variation_axes()
        vals = []
        for a in axes:
            vals.append(weight if a['name'] == b'Weight' else a['default'])
        f.set_variation_by_axes(vals)
    return f


def is_ar(s):
    return any('؀' <= c <= 'ۿ' for c in s)


@functools.lru_cache(512)
def text_img(text, fname, size, weight=None, fill=INK, pad=6):
    """Tight RGBA image of a single line of text (Arabic shaped RTL)."""
    f = font(fname, size, weight)
    kw = dict(direction='rtl', language='ar') if is_ar(text) else {}
    tmp = Image.new('L', (10, 10))
    d = ImageDraw.Draw(tmp)
    l, t, r, b = d.textbbox((0, 0), text, font=f, **kw)
    w, h = r - l + 2 * pad, b - t + 2 * pad
    im = Image.new('RGBA', (w, h), fill[:3] + (0,))
    d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), text, font=f, fill=fill, **kw)
    return im


# ---------------------------------------------------------------- textures
def _noise(shape, sigma, seed):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, shape).astype(np.float32)
    im = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8))
    if sigma:
        im = im.filter(ImageFilter.GaussianBlur(sigma))
    a = np.asarray(im).astype(np.float32) - 128
    return a / (a.std() + 1e-6)


def make_paper(color=PAPER, seed=1, w=W, h=H, strength=1.0):
    """Flat colour sheet; the paper texture is applied to the whole frame in finish()."""
    return Image.new('RGB', (w, h), tuple(color))


def _smooth_noise(rng, h, w, cell):
    small = rng.normal(0, 1, (h // cell + 3, w // cell + 3)).astype(np.float32)
    im = Image.fromarray(small, 'F').resize((w + 3 * cell, h + 3 * cell), Image.BICUBIC)
    return np.asarray(im)[cell:cell + h, cell:cell + w]


@functools.lru_cache(None)
def paper_lum():
    rng = np.random.default_rng(5)
    lum = (1 + 0.012 * _smooth_noise(rng, H, W, 90) + 0.008 * _smooth_noise(rng, H, W, 12)
           + 0.018 * rng.normal(0, 1, (H, W)).astype(np.float32))
    fib = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(fib)
    r = random.Random(9)
    for _ in range(2600):
        x, y = r.uniform(0, W), r.uniform(0, H)
        a = r.uniform(0, math.pi)
        ln = r.uniform(5, 22)
        d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=r.randint(40, 120), width=1)
    fib = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
    lum -= fib * 0.05
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    lum *= 1 - 0.2 * np.clip(rr - 0.6, 0, 1) ** 1.5
    return lum[..., None]


@functools.lru_cache(None)
def paper_bg():
    return Image.new('RGB', (W, H), PAPER)


@functools.lru_cache(None)
def card_tex():
    return Image.new('RGB', (W, H), CARD)


@functools.lru_cache(None)
def grains():
    rng = np.random.default_rng(77)
    return [rng.normal(0, 1.7, (H // 2, W // 2)).astype(np.float32) for _ in range(4)]


def finish(img, t):
    """Paper texture multiply + vignette + animated grain (changes at 12 fps)."""
    a = np.asarray(img.convert('RGB')).astype(np.float32)
    g = grains()[int(t * 12) % 4]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[:H, :W]
    a = a * paper_lum() + g[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


# ---------------------------------------------------------------- easing / time
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, t0, d):
    return clamp((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_io(x):
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.7):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def jitter(key, t, amp=1.6):
    """Stop-motion wobble: new offset 12 times a second."""
    r = random.Random(hash((key, int(t * 12))))
    return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-0.25, 0.25)


# ---------------------------------------------------------------- compositing
def paste(base, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0, anchor='c'):
    """Alpha-paste RGBA im onto base (RGB/RGBA) centred at cx,cy."""
    if alpha <= 0 or scale <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel('A').point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    if anchor == 'c':
        x, y = cx - im.width / 2, cy - im.height / 2
    elif anchor == 'r':  # right-middle (RTL text start)
        x, y = cx - im.width, cy - im.height / 2
    elif anchor == 'l':
        x, y = cx, cy - im.height / 2
    else:
        x, y = cx, cy
    base.alpha_composite(im, (int(round(x)), int(round(y)))) if base.mode == 'RGBA' else base.paste(im, (int(round(x)), int(round(y))), im)


def shadowed(im, off=(10, 14), blur=14, opacity=0.38):
    """Return im with a soft drop shadow (bigger canvas)."""
    pad = blur * 3 + max(abs(off[0]), abs(off[1]))
    w, h = im.width + pad * 2, im.height + pad * 2
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    a = im.getchannel('A')
    sh = Image.new('RGBA', (w, h), (20, 15, 10, 0))
    m = Image.new('L', (w, h), 0)
    m.paste(a, (pad + off[0], pad + off[1]))
    m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * opacity))
    sh.putalpha(m)
    out.alpha_composite(sh)
    out.alpha_composite(im, (pad, pad))
    return out


def card(w, h, tex=None, torn=False, seed=0):
    """Paper card RGBA (w x h) with optional torn edge."""
    tex = tex or card_tex()
    r = random.Random(seed)
    x0, y0 = r.randint(0, tex.width - w - 1), r.randint(0, tex.height - h - 1)
    im = tex.crop((x0, y0, x0 + w, y0 + h)).convert('RGBA')
    if torn:
        m = Image.new('L', (w, h), 255)
        d = ImageDraw.Draw(m)
        pts = [(0, 0)]
        x = 0
        while x < w:
            pts.append((x, r.uniform(0, 7)))
            x += r.uniform(6, 14)
        pts += [(w, 0)]
        d.polygon(pts, fill=0)
        pts = [(0, h)]
        x = 0
        while x < w:
            pts.append((x, h - r.uniform(0, 7)))
            x += r.uniform(6, 14)
        pts += [(w, h)]
        d.polygon(pts, fill=0)
        im.putalpha(m)
    return im


def multiply_rect(img, box, color, alpha=1.0):
    """Highlighter: multiply a colour over box on RGB/RGBA img (in place)."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    reg = img.crop((x0, y0, x1, y1))
    a = np.asarray(reg).astype(np.float32)
    c = np.array(color, np.float32) / 255
    rgb = a[..., :3]
    mixed = rgb * (1 - alpha + alpha * c)
    a[..., :3] = mixed
    img.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8), reg.mode), (x0, y0))


def highlight_text(base, text_im, cx, cy, p, color=YELLOW, rtl=True, padx=14, rot=0):
    """Draw marker highlight sweeping under text (progress p), then the text."""
    w, h = text_im.width, text_im.height
    x0, y0 = cx - w / 2 - padx, cy - h * 0.18
    x1, y1 = cx + w / 2 + padx, cy + h * 0.40
    if p > 0:
        ww = (x1 - x0) * ease_out(p)
        box = (x1 - ww, y0, x1, y1) if rtl else (x0, y0, x0 + ww, y1)
        multiply_rect(base, box, color)
    paste(base, text_im, cx, cy, rot=rot)


def stroke_path(draw, pts, p, fill=RED, width=8):
    """Draw first p fraction of polyline pts."""
    if p <= 0 or len(pts) < 2:
        return
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg)
    target = total * p
    acc = 0
    out = [pts[0]]
    for i, s in enumerate(seg):
        if acc + s >= target:
            f = (target - acc) / s if s else 0
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f))
            break
        out.append(pts[i + 1])
        acc += s
    draw.line(out, fill=fill, width=width, joint='curve')
    r = width / 2
    for q in (out[0], out[-1]):
        draw.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=fill)


def marker_ellipse(cx, cy, rx, ry, seed=3, turns=1.12):
    r = random.Random(seed)
    pts = []
    n = 90
    for i in range(n + 1):
        a = -math.pi * 0.6 + 2 * math.pi * turns * i / n
        k = 1 + 0.05 * math.sin(i * 0.31 + r.random()) + 0.04 * i / n
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return pts


def camera(img, t, dur, z0=1.0, z1=1.04, cx=0.5, cy=0.5):
    """Slow push-in of the whole frame."""
    z = z0 + (z1 - z0) * ease_io(clamp(t / max(dur, 0.01)))
    if abs(z - 1) < 1e-4:
        return img
    w, h = W / z, H / z
    x0, y0 = (W - w) * cx, (H - h) * cy
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))


def label(text, size=40, fname='plexb', fill=INK, bg=CARD, padx=22, pady=12, seed=0, weight=None):
    """Text on a little paper tag with shadow (RGBA)."""
    ti = text_img(text, fname, size, weight, fill)
    c = card(ti.width + padx * 2, ti.height + pady * 2, seed=seed)
    if bg != CARD:
        tint = Image.new('RGBA', c.size, bg + (255,))
        c = Image.composite(ImageChops.multiply(c, tint), c, c.getchannel('A'))
    c.alpha_composite(ti, (padx, pady))
    return c
