"""محرك الموشن جرافيك: يرسم كل مشهد إطاراً بإطار ويضخّه إلى FFmpeg.

الشكل كله يأتي من «ستايل» الحلقة (style.py): الألوان، الخلفية، الخط، الانتقالات،
الترجمة، الإطارات… حتى تختلف الحلقات عن بعضها بوضوح.
"""
import math
import os
import random
import subprocess
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, ImageDraw, ImageFilter

import gfx
import style as stylemod
from gfx import (blit, circle, clamp, ease_in_out, ease_out_back, ease_out_cubic, emoji_img,
                 font, glow, is_rtl, prog, rounded, text_img, text_width)

FPS = 30
CHANNELS = {"ar": os.environ.get("KAYF_CHANNEL") or "كيف يعمل؟",
            "en": os.environ.get("KAYF_CHANNEL_EN") or "How It Works?"}


def channel():
    return CHANNELS[gfx.LANG[0]]


SUBSCRIBE = {"ar": "اشترك", "en": "Subscribe"}
DIDYOU = {"ar": "هل تعلم؟", "en": "Did you know?"}


class Ctx:
    def __init__(self, W, H, style):
        if isinstance(style, str):  # توافق قديم: اسم لوحة فقط
            style = dict(stylemod.pick("000"), palette=style if style in stylemod.PALETTES else "cyan")
        self.st = style
        self.W, self.H = W, H
        self.portrait = H > W
        self.s = (W / 1080) if self.portrait else (H / 1080) * 1.0
        (self.bg1, self.bg2, self.acc, self.acc2, self.fg, self.ink,
         self.light) = stylemod.PALETTES[style["palette"]]
        gfx.SHADOW[0] = not self.light
        self.hf = style.get("font", "Cairo")                  # خط العناوين
        self.rad = float(style.get("radius", 1.0))             # استدارة البطاقات
        self.cy = H * (0.39 if self.portrait else 0.45)        # مركز المحتوى
        self.sub_y = H * (0.735 if self.portrait else 0.86)    # مكان الترجمة
        self.maxw = W * (0.84 if self.portrait else 0.62)

    def tint(self, a):
        """لون شفاف للبطاقات يناسب الخلفية الغامقة أو الفاتحة."""
        return (255, 255, 255, a) if not self.light else (20, 24, 40, int(a * 0.8))

    def panel(self):
        return (0, 0, 0, 90) if not self.light else (255, 255, 255, 190)

    def r(self, px):
        return int(px * self.s * self.rad)

    def head(self, txt, size, color, maxw=None):
        """نص عنوان بخط الحلقة."""
        if self.hf == "Cairo":
            return text_img(txt, size, color, 900, maxw)
        return text_img(txt, int(size * (1.08 if self.hf == "Lalezar" else 1.0)), color,
                        900, maxw, family=self.hf)


# ---------------- الخلفية ----------------
_BG = {}


def _gradient(ctx):
    W, H = ctx.W, ctx.H
    kind = ctx.st.get("gradient", "vertical")
    if kind == "radial":
        n = 512
        g = Image.new("L", (n, n))
        px = g.load()
        for y in range(n):
            for x in range(n):
                d = math.hypot(x - n / 2, y - n * 0.42) / (n * 0.7)
                px[x, y] = int(255 * clamp(d))
        mask = g.resize((W, H), Image.BILINEAR)
    else:
        g = Image.new("L", (256, 256))
        px = g.load()
        for y in range(256):
            for x in range(256):
                k = (x + y) / 510 if kind == "diagonal" else y / 255
                px[x, y] = int(255 * k)
        mask = g.resize((W, H), Image.BILINEAR)
    a = Image.new("RGB", (W, H), ctx.bg1 if not ctx.light else ctx.bg1)
    b = Image.new("RGB", (W, H), ctx.bg2)
    if kind == "radial":  # المركز أفتح/أغمق حسب اللوحة
        a, b = (Image.new("RGB", (W, H), ctx.bg2), Image.new("RGB", (W, H), ctx.bg1))
    return Image.composite(b, a, mask).convert("RGBA")


def _pattern(ctx, sp):
    """طبقة النمط أكبر من الشاشة بخطوة واحدة حتى تتحرك بسلاسة."""
    W, H = ctx.W, ctx.H
    kind = ctx.st.get("bg", "grid")
    col = (ctx.fg if ctx.light else ctx.acc)
    al = 22 if ctx.light else 16
    im = Image.new("RGBA", (W + sp, H + sp), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == "grid":
        for x in range(0, W + sp, sp):
            d.line([(x, 0), (x, H + sp)], fill=col + (al,), width=1)
        for y in range(0, H + sp, sp):
            d.line([(0, y), (W + sp, y)], fill=col + (al,), width=1)
    elif kind == "dots":
        r = max(2, int(4 * ctx.s))
        for y in range(0, H + sp, sp // 2):
            for x in range(0, W + sp, sp // 2):
                d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(al * 2.2),))
    elif kind == "diag":
        w = max(2, int(14 * ctx.s))
        for x in range(-H - sp, W + sp, sp):
            d.line([(x, H + sp), (x + H + sp, 0)], fill=col + (int(al * 0.9),), width=w)
    elif kind == "waves":
        amp, wl = 18 * ctx.s, 260 * ctx.s
        for y0 in range(0, H + sp, sp):
            pts = [(x, y0 + amp * math.sin(x / wl * math.tau)) for x in range(0, W + sp + 8, 8)]
            d.line(pts, fill=col + (int(al * 1.6),), width=max(2, int(3 * ctx.s)))
    return im


def background(ctx):
    key = (ctx.W, ctx.H, ctx.st.get("palette"), ctx.st.get("bg"), ctx.st.get("gradient"),
           ctx.st.get("particles"))
    if key in _BG:
        return _BG[key]
    W, H = ctx.W, ctx.H
    bg = _gradient(ctx)
    g = glow(int(max(W, H) * 1.1), ctx.acc, 0.10 if ctx.light else 0.16)
    bg.alpha_composite(g, (int(W / 2 - g.width / 2), int(ctx.cy - g.height / 2)))
    if ctx.st.get("bg") == "rings":  # حلقات ثابتة حول مركز المحتوى
        d = ImageDraw.Draw(bg)
        col = (ctx.fg if ctx.light else ctx.acc)
        for k in range(1, 14):
            r = k * 120 * ctx.s
            d.ellipse([W / 2 - r, ctx.cy - r, W / 2 + r, ctx.cy + r], outline=col + (18,),
                      width=max(2, int(3 * ctx.s)))
    sp = int(90 * ctx.s)
    pat = _pattern(ctx, sp)
    rng = random.Random(7)
    kind = ctx.st.get("particles", "float")
    if kind == "bokeh":
        parts = [(rng.random() * W, rng.random() * H, rng.uniform(40, 120) * ctx.s,
                  rng.uniform(3, 10) * ctx.s, rng.random() * 6.28) for _ in range(12)]
    elif kind == "stars":
        parts = [(rng.random() * W, rng.random() * H, rng.uniform(1.5, 4) * ctx.s,
                  0, rng.random() * 6.28) for _ in range(70)]
    elif kind == "none":
        parts = []
    else:
        parts = [(rng.random() * W, rng.random() * H, rng.uniform(2, 6) * ctx.s,
                  rng.uniform(8, 30) * ctx.s, rng.random() * 6.28) for _ in range(34)]
    blobs = {}
    if kind == "bokeh":
        for p in parts:
            blobs[int(p[2])] = glow(int(p[2] * 2.6), ctx.acc if not ctx.light else ctx.acc2, 0.5)
    _BG[key] = (bg, pat, sp, parts, blobs)
    return _BG[key]


def draw_bg(ctx, T):
    bg, pat, sp, parts, blobs = background(ctx)
    frame = bg.copy()
    if ctx.st.get("bg") not in ("plain", "rings"):
        off = int((T * 18 * ctx.s) % sp)
        oy = off if ctx.st.get("bg") != "waves" else int((T * 10 * ctx.s) % sp)
        frame.alpha_composite(pat.crop((off, oy, off + ctx.W, oy + ctx.H)))
    kind = ctx.st.get("particles", "float")
    d = ImageDraw.Draw(frame)
    col = ctx.acc if not ctx.light else ctx.acc2
    for x, y, r, v, ph in parts:
        if kind == "bokeh":
            yy = (y - T * v) % ctx.H
            xx = x + math.sin(T * 0.3 + ph) * 30 * ctx.s
            blit(frame, blobs[int(r)], xx, yy, 1, 0.35 + 0.25 * math.sin(T * 0.8 + ph))
        elif kind == "stars":
            a = int(clamp(0.5 + 0.5 * math.sin(T * 2.2 + ph * 3)) * (120 if not ctx.light else 90))
            d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))
        else:
            yy = (y - T * v) % ctx.H
            xx = x + math.sin(T * 0.6 + ph) * 20 * ctx.s
            a = int(60 + 60 * math.sin(T * 1.5 + ph))
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=col + (a,))
    return frame


def _rays(size, color, a=26):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(16):
        a0 = i * math.tau / 16
        a1 = a0 + math.tau / 40
        d.polygon([(c, c), (c + c * math.cos(a0), c + c * math.sin(a0)),
                   (c + c * math.cos(a1), c + c * math.sin(a1))], fill=color + (a,))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(size * 0.15))
    im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), mask))
    return im


_RAYS = {}


def rays(size, color):
    k = (size, color)
    if k not in _RAYS:
        _RAYS[k] = _rays(size, color)
    return _RAYS[k]


def emoji_frame(L, ctx, x, y, size, t, p):
    """الإطار خلف الأيقونة الرئيسية: حلقات تموج / بلاطة / مدار."""
    s = ctx.s
    kind = ctx.st.get("frame", "rings")
    if kind == "tile":
        tw = int(size * 1.35)
        rot = math.sin(t * 1.6) * 3
        blit(L, rounded(tw, tw, ctx.r(60), ctx.tint(34), ctx.acc + (255,), max(3, int(6 * s))),
             x, y, p, clamp(p), rot=rot)
        blit(L, glow(int(size * 1.6), ctx.acc, 0.3), x, y, 1, p)
    elif kind == "orbit":
        R = size * 0.82
        blit(L, circle(int(R * 2), None, ctx.acc + (110,), max(2, int(3 * s))), x, y, p, clamp(p))
        blit(L, glow(int(size * 1.7), ctx.acc, 0.4), x, y, 1, p)
        for k in range(3):
            a = t * 1.3 + k * math.tau / 3
            blit(L, circle(int(30 * s), (ctx.acc2 if k else ctx.acc) + (255,)),
                 x + math.cos(a) * R, y + math.sin(a) * R, p)
    else:
        for k in range(3):  # حلقات تموج
            ph = (t * 0.7 + k / 3) % 1
            blit(L, circle(int(size * 1.24), None, ctx.acc + (255,), max(2, int(5 * s))),
                 x, y, 0.8 + ph * 0.9, (1 - ph) * 0.5 * p)
        blit(L, glow(int(size * 1.8), ctx.acc, 0.45), x, y, 1, p)


# ---------------- المشاهد ----------------
def sc_hook(L, ctx, sc, t, dur):
    s = ctx.s
    p = ease_out_back(prog(t, 0, 0.55))
    es = 330 if ctx.portrait else 250
    q = ease_out_cubic(prog(t, 0.2, 0.5))
    mw = int(ctx.maxw if ctx.portrait else ctx.W * 0.85)
    text_top = ctx.st.get("hook") == "text_top" and ctx.portrait
    size = 92
    tx = ctx.head(sc.get("text", ""), int(size * s), ctx.fg, mw)
    if text_top:  # النص فوق والأيقونة تحته
        while tx.height > 520 * s and size > 50:
            size -= 6
            tx = ctx.head(sc.get("text", ""), int(size * s), ctx.fg, mw)
        ty = ctx.H * 0.13 + 40 * s + tx.height / 2
        blit(L, tx, ctx.W / 2, ty - (1 - q) * 60 * s, 1, q)
        bw = int(ctx.maxw * 0.5 * ease_out_cubic(prog(t, 0.5, 0.6)))
        if bw > 4:
            blit(L, rounded(bw, int(12 * s), int(6 * s), ctx.acc + (255,)), ctx.W / 2,
                 ty + tx.height / 2 + 10 * s)
        ey = max(ty + tx.height / 2 + es * s * 0.75, ctx.cy + 60 * s) + math.sin(t * 2.4) * 14 * s
        ey = min(ey, ctx.sub_y - es * s * 0.7)
    else:
        ey = ctx.cy - (170 if ctx.portrait else 190) * s + math.sin(t * 2.4) * 14 * s
        top = ey + es * s * 0.62
        while top + tx.height + 30 * s > ctx.sub_y - 70 * s and size > 50:  # لا يغطي الترجمة
            size -= 6
            tx = ctx.head(sc.get("text", ""), int(size * s), ctx.fg, mw)
        ty = top + tx.height / 2
    blit(L, rays(int(900 * s), ctx.acc), ctx.W / 2, ey, 1, 0.9 * p, rot=t * 12)
    blit(L, glow(int(560 * s), ctx.acc, 0.5), ctx.W / 2, ey, 1, p)
    blit(L, emoji_img(sc.get("emoji", "❓"), int(es * s)), ctx.W / 2, ey, p)
    if not text_top:
        blit(L, tx, ctx.W / 2, ty + (1 - q) * 60 * s, 1, q)
        bw = int(ctx.maxw * 0.5 * ease_out_cubic(prog(t, 0.5, 0.6)))
        if bw > 4:
            blit(L, rounded(bw, int(12 * s), int(6 * s), ctx.acc + (255,)), ctx.W / 2,
                 ty + tx.height / 2 + 6 * s)


def sc_icon(L, ctx, sc, t, dur):
    s = ctx.s
    p = ease_out_back(prog(t, 0, 0.5))
    pulse = 1 + 0.06 * math.sin(t * 4)
    ey = ctx.cy - 110 * s
    emoji_frame(L, ctx, ctx.W / 2, ey, 340 * s, t, p)
    blit(L, emoji_img(sc.get("emoji", "💡"), int(340 * s)), ctx.W / 2, ey,
         p * (pulse if ctx.st.get("frame") != "tile" else 1))
    cap = sc.get("caption") or sc.get("text")
    if cap:
        q = ease_out_cubic(prog(t, 0.25, 0.45))
        tx = text_img(cap, int(68 * s), ctx.fg, 800, int(ctx.maxw - 80 * s))
        box = rounded(tx.width + int(50 * s), tx.height + int(10 * s), ctx.r(40),
                      ctx.acc + (60,), ctx.acc + (255,), max(2, int(4 * s)))
        cy = ctx.cy + 220 * s + tx.height / 2
        blit(L, box, ctx.W / 2, cy + (1 - q) * 50 * s, 1, q)
        blit(L, tx, ctx.W / 2, cy + (1 - q) * 50 * s, 1, q)


def _reveal_times(n, dur, lead=0.15):
    span = max(0.6, dur - 0.8)
    return [lead + i * span / n for i in range(n)]


def sc_steps(L, ctx, sc, t, dur):
    s = ctx.s
    items = sc.get("items", [])[:5]
    n = len(items)
    top = ctx.cy - 330 * s
    if sc.get("title"):
        q = ease_out_cubic(prog(t, 0, 0.4))
        tt = ctx.head(sc["title"], int(70 * s), ctx.acc, int(ctx.maxw))
        blit(L, tt, ctx.W / 2, top + (1 - q) * -30 * s, 1, q)
        top += tt.height / 2 + 40 * s
    ch = int((130 if n <= 4 else 110) * s)
    gap = int(26 * s)
    cw = int(ctx.maxw + 40 * s)
    times = _reveal_times(n, dur)
    for i, it in enumerate(items):
        q = ease_out_cubic(prog(t, times[i], 0.4))
        if q <= 0:
            continue
        cy = top + ch / 2 + i * (ch + gap)
        cx = ctx.W / 2 + (1 - q) * 120 * s
        active = (i == n - 1 and t >= times[i]) or (i < n - 1 and times[i] <= t < times[i + 1])
        card = rounded(cw, ch, ctx.r(30), ctx.tint(34 if active else 20),
                       ctx.acc + (255 if active else 90,), max(2, int(3 * s)))
        blit(L, card, cx, cy, 1, q)
        sg = 1 if is_rtl() else -1  # جهة الرقم: يمين للعربي، يسار للإنجليزي
        edge = cx + sg * cw / 2
        d = int(ch * 0.66)
        ncx = edge - sg * (d / 2 + 20 * s)
        if ctx.rad < 0.6:
            blit(L, rounded(d, d, ctx.r(30), ctx.acc + (255,)), ncx, cy, 1, q)
        else:
            blit(L, circle(d, ctx.acc + (255,)), ncx, cy, 1, q)
        num = text_img(str(i + 1), int(d * 0.62), ctx.ink, 900, shadow=False)
        blit(L, num, ncx, cy + 2 * s, 1, q)
        tx = text_img(it, int((54 if len(it) < 26 else 44) * s), ctx.fg, 800,
                      int(cw - d - 70 * s), shadow=False)
        tr = edge - sg * (d + 40 * s)
        blit(L, tx, tr - sg * (tx.width / 2 - 16 * s), cy, 1, q)


def _fmt(v):
    if isinstance(v, (int, float)):
        return f"{int(v):,}"
    return str(v)


def sc_stat(L, ctx, sc, t, dur):
    s = ctx.s
    p = ease_out_back(prog(t, 0, 0.5))
    if sc.get("emoji"):
        blit(L, emoji_img(sc["emoji"], int(210 * s)), ctx.W / 2, ctx.cy - 300 * s, p)
    val = sc.get("number", 0)
    k = ease_out_cubic(prog(t, 0.1, 1.3))
    shown = _fmt(val * k) if isinstance(val, (int, float)) else _fmt(val)
    num = ctx.head(shown, int((180 if len(shown) < 8 else 130) * s), ctx.acc)
    blit(L, glow(int(700 * s), ctx.acc, 0.25), ctx.W / 2, ctx.cy - 30 * s, 1, p)
    blit(L, num, ctx.W / 2, ctx.cy - 40 * s, 0.85 + 0.15 * p, clamp(p))
    q = ease_out_cubic(prog(t, 0.35, 0.4))
    if sc.get("unit"):
        u = text_img(sc["unit"], int(66 * s), ctx.fg, 800, int(ctx.maxw))
        blit(L, u, ctx.W / 2, ctx.cy + 110 * s, 1, q)
    if sc.get("label"):
        lb = text_img(sc["label"], int(50 * s), ctx.acc2, 700, int(ctx.maxw))
        blit(L, lb, ctx.W / 2, ctx.cy + 210 * s + lb.height / 4, 1,
             ease_out_cubic(prog(t, 0.6, 0.4)))


def sc_compare(L, ctx, sc, t, dur):
    s = ctx.s
    a, b = sc.get("right", {}), sc.get("left", {})  # اليمين أولاً (عربي)
    cw = int((ctx.W * 0.42) if ctx.portrait else ctx.W * 0.3)
    chh = int(560 * s)
    gapx = ctx.W * 0.25 if ctx.portrait else ctx.W * 0.19
    first = 1 if is_rtl() else -1
    for side, it, st in ((first, a, 0.0), (-first, b, max(0.6, dur * 0.42))):
        q = ease_out_back(prog(t, st, 0.5))
        if q <= 0:
            continue
        cx = ctx.W / 2 + side * gapx
        col = ctx.acc if side == first else ctx.acc2
        blit(L, rounded(cw, chh, ctx.r(40), ctx.tint(22), col + (255,),
                        max(3, int(4 * s))), cx, ctx.cy, q, clamp(q))
        blit(L, emoji_img(it.get("emoji", "❓"), int(200 * s)), cx, ctx.cy - 120 * s, q)
        lsz = 56 if len(it.get("label", "")) < 18 else 46
        lb = ctx.head(it.get("label", ""), int(lsz * s), col, int(cw - 40 * s))
        ltop = ctx.cy + 10 * s
        blit(L, lb, cx, ltop + lb.height / 2, q, clamp(q))
        if it.get("sub"):
            sb = text_img(it["sub"], int(42 * s), ctx.fg, 700, int(cw - 50 * s))
            blit(L, sb, cx, ltop + lb.height + 6 * s + sb.height / 2, q, clamp(q))
    q = ease_out_back(prog(t, 0.3, 0.5))
    blit(L, circle(int(130 * s), ctx.fg + (255,)), ctx.W / 2, ctx.cy, q)
    blit(L, text_img("VS", int(58 * s), ctx.bg1, 900, shadow=False), ctx.W / 2, ctx.cy, q)


def _arrow(L, x0, y0, x1, y1, col, w, frac):
    if frac <= 0:
        return
    xe, ye = x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac
    d = ImageDraw.Draw(L)
    d.line([(x0, y0), (xe, ye)], fill=col + (255,), width=int(w))
    ang = math.atan2(ye - y0, xe - x0)
    h = w * 2.6
    d.polygon([(xe + math.cos(ang) * h * 0.6, ye + math.sin(ang) * h * 0.6),
               (xe + math.cos(ang + 2.4) * h, ye + math.sin(ang + 2.4) * h),
               (xe + math.cos(ang - 2.4) * h, ye + math.sin(ang - 2.4) * h)], fill=col + (255,))


def sc_flow(L, ctx, sc, t, dur):
    s = ctx.s
    items = sc.get("items", [])[:4]
    n = len(items)
    times = _reveal_times(n, dur)
    if ctx.portrait:
        avail = ctx.H * 0.58
        node = min(210 * s, avail / (n * 1.75))
        step = node * 1.75
        y0 = ctx.cy - (n - 1) * step / 2 - 30 * s
        pos = [(ctx.W / 2, y0 + i * step) for i in range(n)]
    else:
        node = 200 * s
        step = min(ctx.W * 0.22, ctx.W * 0.8 / max(1, n - 1)) if n > 1 else 0
        sg = 1 if is_rtl() else -1
        x0 = ctx.W / 2 + sg * (n - 1) * step / 2
        pos = [(x0 - sg * i * step, ctx.cy - 40 * s) for i in range(n)]
    for i, it in enumerate(items):
        q = ease_out_back(prog(t, times[i], 0.45))
        x, y = pos[i]
        if i > 0:
            fr = ease_in_out(prog(t, times[i] - 0.35, 0.35))
            px, py = pos[i - 1]
            if ctx.portrait:
                _arrow(L, x, py + node * 0.62, x, y - node * 0.62, ctx.acc2, 9 * s, fr)
            else:
                sg = 1 if is_rtl() else -1
                _arrow(L, px - sg * node * 0.62, y, x + sg * node * 0.62, y, ctx.acc2, 9 * s, fr)
        if q <= 0:
            continue
        nd = int(node * 1.12)
        if ctx.rad < 0.6:
            blit(L, rounded(nd, nd, ctx.r(60), ctx.tint(26), ctx.acc + (255,), max(3, int(5 * s))),
                 x, y, q, clamp(q))
        else:
            blit(L, circle(nd, ctx.tint(26), ctx.acc + (255,), max(3, int(5 * s))), x, y, q, clamp(q))
        blit(L, emoji_img(it.get("emoji", "❓"), int(node * 0.7)), x, y, q)
        lb = text_img(it.get("label", ""), int((56 if ctx.portrait else 46) * s), ctx.fg, 800,
                      int(ctx.W * 0.32 if ctx.portrait else step * 0.95 or 400 * s))
        if ctx.portrait:  # التسمية بجانب الدائرة يميناً ويساراً بالتناوب
            side = 1 if i % 2 == 0 else -1
            lx = x + side * (node * 0.62 + 30 * s + lb.width / 2)
            blit(L, lb, lx, y, 1, clamp(q))
        else:
            blit(L, lb, x, y + node * 0.6 + 20 * s + lb.height / 2, 1, clamp(q))


def sc_fact(L, ctx, sc, t, dur):
    s = ctx.s
    q = ease_out_back(prog(t, 0, 0.45))
    badge = ctx.head(sc.get("badge") or DIDYOU[gfx.LANG[0]], int(58 * s), ctx.ink)
    pill = rounded(badge.width + int(40 * s), badge.height, max(ctx.r(badge.height / 2 / s), 6),
                   ctx.acc2 + (255,))
    by = ctx.cy - 380 * s
    blit(L, pill, ctx.W / 2, by, q, clamp(q), rot=math.sin(t * 3) * 2)
    blit(L, badge, ctx.W / 2, by, q, clamp(q), rot=math.sin(t * 3) * 2)
    p = ease_out_back(prog(t, 0.15, 0.5))
    blit(L, glow(int(500 * s), ctx.acc2, 0.4), ctx.W / 2, ctx.cy - 150 * s, 1, p)
    blit(L, emoji_img(sc.get("emoji", "🤯"), int(250 * s)), ctx.W / 2,
         ctx.cy - 150 * s + math.sin(t * 2) * 10 * s, p)
    if sc.get("text"):
        r = ease_out_cubic(prog(t, 0.35, 0.45))
        tx = text_img(sc["text"], int(60 * s), ctx.fg, 800, int(ctx.maxw - 60 * s))
        box = rounded(int(ctx.maxw + 20 * s), tx.height + int(40 * s), ctx.r(34),
                      ctx.panel(), ctx.acc2 + (200,), max(2, int(3 * s)))
        cy = ctx.cy + 120 * s + tx.height / 2
        blit(L, box, ctx.W / 2, cy + (1 - r) * 40 * s, 1, r)
        blit(L, tx, ctx.W / 2, cy + (1 - r) * 40 * s, 1, r)


def sc_outro(L, ctx, sc, t, dur):
    s = ctx.s
    p = ease_out_back(prog(t, 0, 0.6))
    blit(L, rays(int(1000 * s), ctx.acc), ctx.W / 2, ctx.cy - 160 * s, 1, p, rot=t * 15)
    name = text_img(channel(), int(150 * s), ctx.acc, 900, family="Lalezar")
    blit(L, name, ctx.W / 2, ctx.cy - 160 * s, p, clamp(p))
    if sc.get("text"):
        tx = text_img(sc["text"], int(58 * s), ctx.fg, 800, int(ctx.maxw))
        blit(L, tx, ctx.W / 2, ctx.cy + 10 * s, 1, ease_out_cubic(prog(t, 0.3, 0.4)))
    q = ease_out_back(prog(t, 0.6, 0.5))
    pulse = 1 + 0.05 * math.sin(t * 6)
    btn_t = text_img(SUBSCRIBE[gfx.LANG[0]], int(70 * s), (255, 255, 255), 900, shadow=False)
    bw, bh = btn_t.width + int(200 * s), int(130 * s)
    by = ctx.cy + 190 * s
    blit(L, rounded(bw, bh, max(ctx.r(bh / 2 / s), 8), (230, 20, 40, 255)), ctx.W / 2, by, q * pulse)
    sg = 1 if is_rtl() else -1
    blit(L, btn_t, ctx.W / 2 + sg * 40 * s, by + 4 * s, q * pulse)
    bell = emoji_img("🔔", int(80 * s))
    blit(L, bell, ctx.W / 2 - sg * (bw / 2 - 80 * s), by, q * pulse, rot=math.sin(t * 14) * 18)


SCENES = {"hook": sc_hook, "icon": sc_icon, "steps": sc_steps, "stat": sc_stat,
          "compare": sc_compare, "flow": sc_flow, "fact": sc_fact, "outro": sc_outro}


# ---------------- الترجمة المتزامنة ----------------
def chunks(words, ctx, size):
    f = font(size, 800)
    out, cur = [], []
    for w in words:
        test = " ".join(x["w"] for x in cur + [w])
        if cur and (len(cur) >= 4 or text_width(test, f) > ctx.maxw * 0.95):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


_SUB = {}


def sub_img(ctx, chunk, active, size):
    kind = ctx.st.get("subs", "box")
    key = (tuple((w["w"], round(w["t"], 3)) for w in chunk), active, ctx.W, ctx.acc, gfx.LANG[0], kind)
    if key in _SUB:
        return _SUB[key]
    f = font(size, 800)
    space = f.getlength(" ")
    ws = [text_width(w["w"], f) for w in chunk]
    padx, pady = 22 * ctx.s, 10 * ctx.s
    total = sum(ws) + space * (len(ws) - 1) + 2 * padx * len(ws) * 0.5
    asc, desc = f.getmetrics()
    h = int(asc + desc + pady * 2)
    if kind == "band":
        width = ctx.W
    else:
        width = int(total + 60 * ctx.s)
    im = Image.new("RGBA", (width, h + int(24 * ctx.s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == "box":
        d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], int(26 * ctx.s * ctx.rad),
                            fill=(0, 0, 0, 140))
    elif kind == "band":
        d.rectangle([0, 0, im.width, im.height], fill=ctx.bg1 + (205,))
        d.rectangle([0, 0, im.width, max(3, int(5 * ctx.s))], fill=ctx.acc + (255,))
    rtl = is_rtl()
    inner = (width - total) / 2 if kind == "band" else 30 * ctx.s
    x = im.width - inner if rtl else inner
    y = (im.height - (asc + desc)) / 2 - 2 * ctx.s
    dr, lg = gfx._dl()
    for i, w in enumerate(chunk):
        if rtl:
            x -= ws[i] + padx * 0.5
        if kind == "pop":
            col = ctx.acc if i == active else (255, 255, 255)
            d.text((x, y), w["w"], font=f, fill=col, direction=dr, language=lg,
                   stroke_width=max(3, int(7 * ctx.s)), stroke_fill=(0, 0, 0, 255))
        elif kind == "band":
            col = ctx.acc if i == active else (ctx.fg if not ctx.light else (255, 255, 255))
            if ctx.light:  # الشريط بلون الخلفية الفاتح: النص غامق
                col = ctx.acc if i == active else ctx.fg
            d.text((x, y), w["w"], font=f, fill=col, direction=dr, language=lg)
            if i == active:
                d.rectangle([x, y + asc + desc - 2 * ctx.s, x + ws[i], y + asc + desc + 4 * ctx.s],
                            fill=ctx.acc + (255,))
        else:
            if i == active:
                d.rounded_rectangle([x - padx * 0.5, y + 4 * ctx.s, x + ws[i] + padx * 0.5,
                                     y + asc + desc + 2 * ctx.s], int(16 * ctx.s * ctx.rad),
                                    fill=ctx.acc + (255,))
                col = ctx.ink
            else:
                col = (255, 255, 255)
            d.text((x, y), w["w"], font=f, fill=col, direction=dr, language=lg)
        if rtl:
            x -= space + padx * 0.5
        else:
            x += ws[i] + space + padx
    _SUB[key] = im
    return im


# ---------------- الانتقالات ----------------
def _alpha(L, a):
    L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))


def _shift(L, dx, dy):
    out = Image.new("RGBA", L.size, (0, 0, 0, 0))
    out.paste(L, (int(dx), int(dy)))
    return out


def _scale(L, k):
    W, H = L.size
    im = L.resize((max(1, int(W * k)), max(1, int(H * k))), Image.BILINEAR)
    out = Image.new("RGBA", L.size, (0, 0, 0, 0))
    out.paste(im, (int((W - im.width) / 2), int((H - im.height) / 2)))
    return out


def transition(ctx, L, t, dur, first, last):
    kind = ctx.st.get("transition", "fade")
    TIN, TOUT = 0.32, 0.24
    e_in = 1.0 if first else ease_out_cubic(prog(t, 0, TIN))
    e_out = 1.0 if last else clamp((dur - t) / TOUT)
    if e_in >= 0.999 and e_out >= 0.999:
        return L
    sg = -1 if is_rtl() else 1  # الدخول من جهة بداية القراءة
    if kind == "slide":
        dx = -sg * (1 - e_in) * ctx.W * 0.35 + sg * (1 - e_out) * ctx.W * 0.35
        L = _shift(L, dx, 0)
    elif kind == "zoom":
        k = (0.86 + 0.14 * e_in) * (1 + 0.1 * (1 - e_out))
        L = _scale(L, k)
    elif kind == "rise":
        L = _shift(L, 0, (1 - e_in) * ctx.H * 0.07 - (1 - e_out) * ctx.H * 0.05)
    elif kind == "wipe" and e_in < 0.999:  # دائرة تكشف المشهد من المركز
        R = math.hypot(ctx.W, ctx.H) * 0.6 * e_in
        m = Image.new("L", L.size, 0)
        ImageDraw.Draw(m).ellipse([ctx.W / 2 - R, ctx.cy - R, ctx.W / 2 + R, ctx.cy + R], fill=255)
        L.putalpha(Image.composite(L.getchannel("A"), Image.new("L", L.size, 0), m))
        e_in = 1.0
    a = min(e_in, e_out)
    if a < 0.99:
        _alpha(L, a)
    return L


# ---------------- الإطار الكامل ----------------
def make_frame(ctx, timeline, T, total):
    frame = draw_bg(ctx, T)
    idx = 0
    for i, sc in enumerate(timeline):
        if T >= sc["start"]:
            idx = i
    sc = timeline[idx]
    t = T - sc["start"]
    dur = sc["dur"]
    L = Image.new("RGBA", (ctx.W, ctx.H), (0, 0, 0, 0))
    SCENES.get(sc["type"], sc_icon)(L, ctx, sc, t, dur)
    L = transition(ctx, L, t, dur, idx == 0, idx == len(timeline) - 1)
    frame.alpha_composite(L)
    # الترجمة
    size = int((60 if ctx.portrait else 52) * ctx.s)
    for ch in sc["_chunks"]:
        st, en = ch[0]["t"], ch[-1]["t"] + ch[-1]["d"] + 0.25
        if st - 0.05 <= t < en:
            act = max([j for j, w in enumerate(ch) if w["t"] <= t] or [0])
            im = sub_img(ctx, ch, act, size)
            k = ease_out_back(prog(t, st - 0.05, 0.18))
            blit(frame, im, ctx.W / 2, ctx.sub_y, 0.9 + 0.1 * k, clamp(k * 1.3))
            break
    # اسم القناة وشريط التقدم
    s = ctx.s
    tag = text_img(channel(), int(40 * s), (255, 255, 255), 900, family="Lalezar", shadow=False)
    pill = rounded(tag.width + int(30 * s), tag.height + int(4 * s), max(ctx.r(30), 4),
                   (0, 0, 0, 110 if not ctx.light else 170), ctx.acc + (200,), max(2, int(2 * s)))
    ty = ctx.H * (0.075 if ctx.portrait else 0.07)
    corner = ctx.st.get("tag") == "corner" or not ctx.portrait
    side_right = is_rtl()
    if corner:
        tx = (ctx.W - pill.width / 2 - 40 * s) if side_right else (pill.width / 2 + 40 * s)
    else:
        tx = ctx.W / 2
    frame.alpha_composite(pill, (int(tx - pill.width / 2), int(ty - pill.height / 2)))
    frame.alpha_composite(tag, (int(tx - tag.width / 2), int(ty - tag.height / 2)))
    d = ImageDraw.Draw(frame)
    kind = ctx.st.get("progress", "top")
    bh = max(6, int(8 * s))
    if kind == "segments":
        n = len(timeline)
        gap = 10 * s
        segw = (ctx.W * 0.8 - gap * (n - 1)) / n
        y0 = ctx.H * (0.035 if ctx.portrait else 0.025)
        for i, scn in enumerate(timeline):
            fr = clamp((T - scn["start"]) / scn["dur"])
            k = (n - 1 - i) if is_rtl() else i
            x0 = ctx.W * 0.1 + k * (segw + gap)
            d.rounded_rectangle([x0, y0, x0 + segw, y0 + bh], bh // 2, fill=ctx.tint(60))
            if fr > 0:
                if is_rtl():
                    d.rounded_rectangle([x0 + segw * (1 - fr), y0, x0 + segw, y0 + bh], bh // 2,
                                        fill=ctx.acc + (255,))
                else:
                    d.rounded_rectangle([x0, y0, x0 + segw * fr, y0 + bh], bh // 2, fill=ctx.acc + (255,))
    else:
        y0 = 0 if kind == "top" else ctx.H - bh
        d.rectangle([0, y0, ctx.W, y0 + bh], fill=ctx.tint(40))
        if is_rtl():
            d.rectangle([ctx.W - ctx.W * clamp(T / total), y0, ctx.W, y0 + bh], fill=ctx.acc + (255,))
        else:
            d.rectangle([0, y0, ctx.W * clamp(T / total), y0 + bh], fill=ctx.acc + (255,))
    return frame.convert("RGB")


def _render_part(args):
    W, H, style, timeline, start_f, end_f, total, path, lang = args
    gfx.LANG[0] = lang
    ctx = Ctx(W, H, style)
    for sc in timeline:
        sc["_chunks"] = chunks(sc.get("words", []), ctx, int((60 if ctx.portrait else 52) * ctx.s))
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                          "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE)
    for f in range(start_f, end_f):
        p.stdin.write(make_frame(ctx, timeline, f / FPS, total).tobytes())
    p.stdin.close()
    p.wait()
    return path


def render_video(W, H, style, timeline, total, wav, out_mp4, workdir, workers=None, lang="ar"):
    workers = workers or max(1, (os.cpu_count() or 2))
    nf = int(total * FPS)
    per = math.ceil(nf / workers)
    jobs = []
    for i in range(workers):
        a, b = i * per, min(nf, (i + 1) * per)
        if a < b:
            jobs.append((W, H, style, timeline, a, b, total, os.path.join(workdir, f"part{i:02d}.mp4"), lang))
    with ProcessPoolExecutor(len(jobs)) as ex:
        parts = list(ex.map(_render_part, jobs))
    lst = os.path.join(workdir, "parts.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out_mp4], check=True)
