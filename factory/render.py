"""محرك الموشن جرافيك: يرسم كل مشهد إطاراً بإطار ويضخّه إلى FFmpeg."""
import math
import os
import random
import subprocess
from concurrent.futures import ProcessPoolExecutor

from PIL import Image, ImageDraw, ImageFilter

from gfx import (THEMES, WHITE, blit, circle, clamp, ease_in_out, ease_out_back,
                 ease_out_cubic, emoji_img, font, glow, prog, rounded, text_img,
                 text_width)

FPS = 30
CHANNEL = os.environ.get("KAYF_CHANNEL") or "كيف يعمل؟"


class Ctx:
    def __init__(self, W, H, theme):
        self.W, self.H = W, H
        self.portrait = H > W
        self.s = (W / 1080) if self.portrait else (H / 1080) * 1.0
        self.bg1, self.bg2, self.acc, self.acc2 = THEMES.get(theme, THEMES["cyan"])
        self.cy = H * (0.39 if self.portrait else 0.45)      # مركز المحتوى
        self.sub_y = H * (0.735 if self.portrait else 0.86)  # مكان الترجمة
        self.maxw = W * (0.84 if self.portrait else 0.62)


# ---------------- الخلفية ----------------
_BG = {}


def background(ctx):
    key = (ctx.W, ctx.H, ctx.bg1, ctx.acc)
    if key in _BG:
        return _BG[key]
    W, H = ctx.W, ctx.H
    grad = Image.new("RGB", (1, 256))
    for y in range(256):
        k = y / 255
        grad.putpixel((0, y), tuple(int(ctx.bg1[i] * (1 - k) + ctx.bg2[i] * k) for i in range(3)))
    bg = grad.resize((W, H), Image.BILINEAR).convert("RGBA")
    g = glow(int(max(W, H) * 1.1), ctx.acc, 0.16)
    bg.alpha_composite(g, (int(W / 2 - g.width / 2), int(ctx.cy - g.height / 2)))
    # شبكة خفيفة أكبر من الشاشة لتحريكها
    sp = int(90 * ctx.s)
    grid = Image.new("RGBA", (W + sp, H + sp), (0, 0, 0, 0))
    d = ImageDraw.Draw(grid)
    for x in range(0, W + sp, sp):
        d.line([(x, 0), (x, H + sp)], fill=ctx.acc + (14,), width=1)
    for y in range(0, H + sp, sp):
        d.line([(0, y), (W + sp, y)], fill=ctx.acc + (14,), width=1)
    rng = random.Random(7)
    parts = [(rng.random() * W, rng.random() * H, rng.uniform(2, 6) * ctx.s,
              rng.uniform(8, 30) * ctx.s, rng.random() * 6.28) for _ in range(34)]
    _BG[key] = (bg, grid, sp, parts)
    return _BG[key]


def draw_bg(ctx, T):
    bg, grid, sp, parts = background(ctx)
    frame = bg.copy()
    off = int((T * 18 * ctx.s) % sp)
    frame.alpha_composite(grid.crop((off, off, off + ctx.W, off + ctx.H)))
    d = ImageDraw.Draw(frame)
    for x, y, r, v, ph in parts:
        yy = (y - T * v) % ctx.H
        xx = x + math.sin(T * 0.6 + ph) * 20 * ctx.s
        a = int(60 + 60 * math.sin(T * 1.5 + ph))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=ctx.acc + (a,))
    return frame


def _rays(size, color):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(16):
        a0 = i * math.tau / 16
        a1 = a0 + math.tau / 40
        d.polygon([(c, c), (c + c * math.cos(a0), c + c * math.sin(a0)),
                   (c + c * math.cos(a1), c + c * math.sin(a1))], fill=color + (26,))
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


# ---------------- المشاهد ----------------
def sc_hook(L, ctx, sc, t, dur):
    s = ctx.s
    p = ease_out_back(prog(t, 0, 0.55))
    es = 330 if ctx.portrait else 250
    ey = ctx.cy - (170 if ctx.portrait else 190) * s + math.sin(t * 2.4) * 14 * s
    blit(L, rays(int(900 * s), ctx.acc), ctx.W / 2, ey, 1, 0.9 * p, rot=t * 12)
    blit(L, glow(int(560 * s), ctx.acc, 0.5), ctx.W / 2, ey, 1, p)
    blit(L, emoji_img(sc.get("emoji", "❓"), int(es * s)), ctx.W / 2, ey, p)
    q = ease_out_cubic(prog(t, 0.2, 0.5))
    mw = int(ctx.maxw if ctx.portrait else ctx.W * 0.85)
    top = ey + es * s * 0.62
    size = 92
    tx = text_img(sc.get("text", ""), int(size * s), WHITE, 900, mw)
    while top + tx.height + 30 * s > ctx.sub_y - 70 * s and size > 50:  # لا يغطي الترجمة
        size -= 6
        tx = text_img(sc.get("text", ""), int(size * s), WHITE, 900, mw)
    ty = top + tx.height / 2
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
    for k in range(3):  # حلقات تموج
        ph = (t * 0.7 + k / 3) % 1
        blit(L, circle(int(420 * s), None, ctx.acc + (255,), max(2, int(5 * s))),
             ctx.W / 2, ey, 0.8 + ph * 0.9, (1 - ph) * 0.5 * p)
    blit(L, glow(int(620 * s), ctx.acc, 0.45), ctx.W / 2, ey, pulse, p)
    blit(L, emoji_img(sc.get("emoji", "💡"), int(340 * s)), ctx.W / 2, ey, p * pulse)
    cap = sc.get("caption") or sc.get("text")
    if cap:
        q = ease_out_cubic(prog(t, 0.25, 0.45))
        tx = text_img(cap, int(68 * s), WHITE, 800, int(ctx.maxw - 80 * s))
        box = rounded(tx.width + int(50 * s), tx.height + int(10 * s), int(40 * s),
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
        tt = text_img(sc["title"], int(70 * s), ctx.acc, 900, int(ctx.maxw))
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
        card = rounded(cw, ch, int(30 * s), (255, 255, 255, 34 if active else 20),
                       ctx.acc + (255 if active else 90,), max(2, int(3 * s)))
        blit(L, card, cx, cy, 1, q)
        right = cx + cw / 2
        d = int(ch * 0.66)
        blit(L, circle(d, ctx.acc + (255,)), right - d / 2 - 20 * s, cy, 1, q)
        num = text_img(str(i + 1), int(d * 0.62), ctx.bg1, 900, shadow=False)
        blit(L, num, right - d / 2 - 20 * s, cy + 2 * s, 1, q)
        tx = text_img(it, int((54 if len(it) < 26 else 44) * s), WHITE, 800,
                      int(cw - d - 70 * s), shadow=False)
        tr = right - d - 40 * s
        blit(L, tx, tr - tx.width / 2 + 16 * s, cy, 1, q)


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
    num = text_img(shown, int((180 if len(shown) < 8 else 130) * s), ctx.acc, 900)
    blit(L, glow(int(700 * s), ctx.acc, 0.25), ctx.W / 2, ctx.cy - 30 * s, 1, p)
    blit(L, num, ctx.W / 2, ctx.cy - 40 * s, 0.85 + 0.15 * p, clamp(p))
    q = ease_out_cubic(prog(t, 0.35, 0.4))
    if sc.get("unit"):
        u = text_img(sc["unit"], int(66 * s), WHITE, 800, int(ctx.maxw))
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
    for side, it, st in ((1, a, 0.0), (-1, b, max(0.6, dur * 0.42))):
        q = ease_out_back(prog(t, st, 0.5))
        if q <= 0:
            continue
        cx = ctx.W / 2 + side * gapx
        col = ctx.acc if side == 1 else ctx.acc2
        blit(L, rounded(cw, chh, int(40 * s), (255, 255, 255, 22), col + (255,),
                        max(3, int(4 * s))), cx, ctx.cy, q, clamp(q))
        blit(L, emoji_img(it.get("emoji", "❓"), int(200 * s)), cx, ctx.cy - 120 * s, q)
        lb = text_img(it.get("label", ""), int(56 * s), col, 900, int(cw - 40 * s))
        blit(L, lb, cx, ctx.cy + 50 * s, q, clamp(q))
        if it.get("sub"):
            sb = text_img(it["sub"], int(46 * s), WHITE, 700, int(cw - 50 * s))
            blit(L, sb, cx, ctx.cy + 150 * s + sb.height / 4, q, clamp(q))
    q = ease_out_back(prog(t, 0.3, 0.5))
    blit(L, circle(int(130 * s), (255, 255, 255, 255)), ctx.W / 2, ctx.cy, q)
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
        x0 = ctx.W / 2 + (n - 1) * step / 2
        pos = [(x0 - i * step, ctx.cy - 40 * s) for i in range(n)]
    for i, it in enumerate(items):
        q = ease_out_back(prog(t, times[i], 0.45))
        x, y = pos[i]
        if i > 0:
            fr = ease_in_out(prog(t, times[i] - 0.35, 0.35))
            px, py = pos[i - 1]
            if ctx.portrait:
                _arrow(L, x, py + node * 0.62, x, y - node * 0.62, ctx.acc2, 9 * s, fr)
            else:
                _arrow(L, px - node * 0.62, y, x + node * 0.62, y, ctx.acc2, 9 * s, fr)
        if q <= 0:
            continue
        blit(L, circle(int(node * 1.12), (255, 255, 255, 26), ctx.acc + (255,),
                       max(3, int(5 * s))), x, y, q, clamp(q))
        blit(L, emoji_img(it.get("emoji", "❓"), int(node * 0.7)), x, y, q)
        lb = text_img(it.get("label", ""), int((56 if ctx.portrait else 46) * s), WHITE, 800,
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
    badge = text_img(sc.get("badge", "هل تعلم؟"), int(58 * s), ctx.bg1, 900, shadow=False)
    pill = rounded(badge.width + int(40 * s), badge.height, int(badge.height / 2), ctx.acc2 + (255,))
    by = ctx.cy - 380 * s
    blit(L, pill, ctx.W / 2, by, q, clamp(q), rot=math.sin(t * 3) * 2)
    blit(L, badge, ctx.W / 2, by, q, clamp(q), rot=math.sin(t * 3) * 2)
    p = ease_out_back(prog(t, 0.15, 0.5))
    blit(L, glow(int(500 * s), ctx.acc2, 0.4), ctx.W / 2, ctx.cy - 150 * s, 1, p)
    blit(L, emoji_img(sc.get("emoji", "🤯"), int(250 * s)), ctx.W / 2,
         ctx.cy - 150 * s + math.sin(t * 2) * 10 * s, p)
    if sc.get("text"):
        r = ease_out_cubic(prog(t, 0.35, 0.45))
        tx = text_img(sc["text"], int(60 * s), WHITE, 800, int(ctx.maxw - 60 * s))
        box = rounded(int(ctx.maxw + 20 * s), tx.height + int(40 * s), int(34 * s),
                      (0, 0, 0, 90), ctx.acc2 + (200,), max(2, int(3 * s)))
        cy = ctx.cy + 120 * s + tx.height / 2
        blit(L, box, ctx.W / 2, cy + (1 - r) * 40 * s, 1, r)
        blit(L, tx, ctx.W / 2, cy + (1 - r) * 40 * s, 1, r)


def sc_outro(L, ctx, sc, t, dur):
    s = ctx.s
    p = ease_out_back(prog(t, 0, 0.6))
    blit(L, rays(int(1000 * s), ctx.acc), ctx.W / 2, ctx.cy - 160 * s, 1, p, rot=t * 15)
    name = text_img(CHANNEL, int(150 * s), ctx.acc, 900, family="Lalezar")
    blit(L, name, ctx.W / 2, ctx.cy - 160 * s, p, clamp(p))
    if sc.get("text"):
        tx = text_img(sc["text"], int(58 * s), WHITE, 800, int(ctx.maxw))
        blit(L, tx, ctx.W / 2, ctx.cy + 10 * s, 1, ease_out_cubic(prog(t, 0.3, 0.4)))
    q = ease_out_back(prog(t, 0.6, 0.5))
    pulse = 1 + 0.05 * math.sin(t * 6)
    btn_t = text_img("اشترك", int(70 * s), WHITE, 900, shadow=False)
    bw, bh = btn_t.width + int(200 * s), int(130 * s)
    by = ctx.cy + 190 * s
    blit(L, rounded(bw, bh, bh // 2, (230, 20, 40, 255)), ctx.W / 2, by, q * pulse)
    blit(L, btn_t, ctx.W / 2 + 40 * s, by + 4 * s, q * pulse)
    bell = emoji_img("🔔", int(80 * s))
    blit(L, bell, ctx.W / 2 - bw / 2 + 80 * s, by, q * pulse, rot=math.sin(t * 14) * 18)


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
    key = (id(chunk), active)
    if key in _SUB:
        return _SUB[key]
    f = font(size, 800)
    space = f.getlength(" ")
    ws = [text_width(w["w"], f) for w in chunk]
    padx, pady = 22 * ctx.s, 10 * ctx.s
    total = sum(ws) + space * (len(ws) - 1) + 2 * padx * len(ws) * 0.5
    asc, desc = f.getmetrics()
    h = int(asc + desc + pady * 2)
    im = Image.new("RGBA", (int(total + 60 * ctx.s), h + int(24 * ctx.s)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], int(26 * ctx.s), fill=(0, 0, 0, 140))
    x = im.width - 30 * ctx.s
    y = (im.height - (asc + desc)) / 2 - 2 * ctx.s
    for i, w in enumerate(chunk):
        x -= ws[i] + padx * 0.5
        if i == active:
            d.rounded_rectangle([x - padx * 0.5, y + 4 * ctx.s, x + ws[i] + padx * 0.5,
                                 y + asc + desc + 2 * ctx.s], int(16 * ctx.s), fill=ctx.acc + (255,))
            col = ctx.bg1
        else:
            col = WHITE
        d.text((x, y), w["w"], font=f, fill=col, direction="rtl", language="ar")
        x -= space + padx * 0.5
    _SUB[key] = im
    return im


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
    fade_out = clamp((dur - t) / 0.22) if idx < len(timeline) - 1 else 1
    fade_in = ease_out_cubic(prog(t, 0, 0.18))
    a = min(fade_in, fade_out)
    if a < 0.99:
        L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))
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
    # العلامة واسم القناة وشريط التقدم
    s = ctx.s
    tag = text_img(CHANNEL, int(40 * s), WHITE, 900, family="Lalezar", shadow=False)
    pill = rounded(tag.width + int(30 * s), tag.height + int(4 * s), int(30 * s), (0, 0, 0, 110),
                   ctx.acc + (200,), max(2, int(2 * s)))
    ty = ctx.H * (0.075 if ctx.portrait else 0.07)
    tx = ctx.W / 2 if ctx.portrait else ctx.W - pill.width / 2 - 40 * s
    frame.alpha_composite(pill, (int(tx - pill.width / 2), int(ty - pill.height / 2)))
    frame.alpha_composite(tag, (int(tx - tag.width / 2), int(ty - tag.height / 2)))
    d = ImageDraw.Draw(frame)
    bh = max(6, int(8 * s))
    d.rectangle([0, 0, ctx.W, bh], fill=(255, 255, 255, 40))
    d.rectangle([ctx.W - ctx.W * clamp(T / total), 0, ctx.W, bh], fill=ctx.acc + (255,))
    return frame.convert("RGB")


def _render_part(args):
    W, H, theme, timeline, start_f, end_f, total, path = args
    ctx = Ctx(W, H, theme)
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


def render_video(W, H, theme, timeline, total, wav, out_mp4, workdir, workers=None):
    workers = workers or max(1, (os.cpu_count() or 2))
    nf = int(total * FPS)
    per = math.ceil(nf / workers)
    jobs = []
    for i in range(workers):
        a, b = i * per, min(nf, (i + 1) * per)
        if a < b:
            jobs.append((W, H, theme, timeline, a, b, total, os.path.join(workdir, f"part{i:02d}.mp4")))
    with ProcessPoolExecutor(len(jobs)) as ex:
        parts = list(ex.map(_render_part, jobs))
    lst = os.path.join(workdir, "parts.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out_mp4], check=True)
