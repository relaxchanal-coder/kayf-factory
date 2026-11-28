"""الحرب العراقية الإيرانية — Vox-style scenes (sand/amber/teal theme). f(t, dur) -> RGB."""
import sys, math, random, functools
sys.path.insert(0, '/home/claude/vox')
import numpy as np
from PIL import Image, ImageDraw
from engine import *
from scenes import T, pop, tag, pin, _along, stroke_path
import mapr
from mapr import IRAQ, IRAN

SAND = (236, 226, 204)
IQ_D = (176, 112, 30)     # dark amber for text
IR_D = (40, 108, 104)     # dark teal for text
PLACES = {
    'baghdad': (44.37, 33.31), 'tehran': (51.39, 35.69), 'basra': (47.82, 30.52), 'khorramshahr': (48.18, 30.44),
    'abadan': (48.30, 30.34), 'faw': (48.48, 29.97), 'halabja': (45.99, 35.18), 'kharg': (50.32, 29.26),
    'hormuz': (56.3, 26.55), 'majnoon': (47.55, 31.05), 'ahvaz': (48.67, 31.32), 'dezful': (48.40, 32.38),
    'qurna': (47.43, 31.0),
}


def bg():
    return Image.new('RGBA', (W, H), SAND + (255,))


@functools.lru_cache(maxsize=6)
def _view(lon, lat, span):
    return mapr.View(lon, lat, span)


def mapf(lon, lat, span, iq=0.0, ir=0.0, cache=True):
    v = _view(round(lon, 3), round(lat, 3), round(span, 3)) if cache else mapr.View(lon, lat, span)
    f = v.frame
    if iq > 0:
        f = mapr.tint(f, v.mask('Iraq'), IRAQ, iq)
    if ir > 0:
        f = mapr.tint(f, v.mask('Iran'), IRAN, ir)
    return f.convert('RGBA'), v


def cam(t, dur, a, b, t0=0.0, t1=None):
    """interpolate camera tuples a->b."""
    t1 = dur if t1 is None else t1
    f = ease_io(prog(t, t0, max(0.01, t1 - t0)))
    lon = a[0] + (b[0] - a[0]) * f
    lat = a[1] + (b[1] - a[1]) * f
    span = math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * f)
    return lon, lat, span, f


def lbl(im, text, xy, size=46, color=GREY, alpha=1.0, weight=800):
    if alpha > 0:
        paste(im, text_img(text, 'cairo', size, weight, color), xy[0], xy[1], alpha=alpha)


def country_labels(im, v, a=1.0, iq_pos=(43.2, 32.2), ir_pos=(53.0, 33.0), size=72):
    lbl(im, 'العراق', v.S(*iq_pos), size, IQ_D, a, 900)
    lbl(im, 'إيران', v.S(*ir_pos), size, IR_D, a, 900)


def arrow(base, pts, p, color, width=30, head=62):
    if p <= 0 or len(pts) < 2:
        return
    p = ease_out(p)
    n = 40
    path = [_along(pts, p * i / n) for i in range(n + 1)]
    tip = path[-1]
    prev = _along(pts, max(0, p - 0.03))
    ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    shaft = [q for q in path if math.dist(q, tip) > head * 0.6] or path[:1]
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    for dx, dy, col in [(7, 9, (0, 0, 0, 70)), (0, 0, tuple(color) + (255,))]:
        q = [(x + dx, y + dy) for x, y in shaft]
        if len(q) > 1:
            ds.line(q, fill=col, width=width, joint='curve')
        tx, ty = tip[0] + dx, tip[1] + dy
        ds.polygon([(tx, ty),
                    (tx - head * math.cos(ang) + head * 0.6 * math.sin(ang), ty - head * math.sin(ang) - head * 0.6 * math.cos(ang)),
                    (tx - head * math.cos(ang) - head * 0.6 * math.sin(ang), ty - head * math.sin(ang) + head * 0.6 * math.cos(ang))],
                   fill=col)
    base.alpha_composite(sh)


def dashed(d, pts, p, color=INK, width=6, n=60):
    for i in range(int(n * clamp(p))):
        if i % 2 == 0:
            d.line([_along(pts, i / n), _along(pts, (i + 1) / n)], fill=color, width=width)


def burst(d, cx, cy, r, q, color=RED, seed=0):
    if q <= 0:
        return
    rnd = random.Random(seed)
    pts = []
    for i in range(18):
        a = i / 18 * 2 * math.pi
        rad = r * q * (1.0 if i % 2 == 0 else 0.5) * rnd.uniform(0.9, 1.1)
        pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    d.polygon(pts, fill=color)


def date_card(day, month_year, sub=None, head=RED, w=600, seed=1):
    c = card(w, 500 if sub else 430, seed=seed)
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, w, 96), fill=head)
    hd = text_img(month_year, 'cairo', 56, 800, CARD)
    c.alpha_composite(hd, (w // 2 - hd.width // 2, 48 - hd.height // 2))
    big = text_img(day, 'oswald', 230, 700, INK)
    c.alpha_composite(big, (w // 2 - big.width // 2, 105))
    if sub:
        s = text_img(sub, 'cairo', 46, 800, GREY)
        c.alpha_composite(s, (w // 2 - s.width // 2, 400))
    return c


def stat_card(num, label_, col=INK, w=520, seed=0):
    c = card(w, 300, seed=seed)
    sz = 104
    n = text_img(num, 'cairo', sz, 900, col)
    while n.width > w - 50 and sz > 50:
        sz -= 6
        n = text_img(num, 'cairo', sz, 900, col)
    c.alpha_composite(n, (w // 2 - n.width // 2, 40 + (104 - sz) // 2))
    l_ = text_img(label_ or ' ', 'plexb', 38, None, GREY)
    c.alpha_composite(l_, (w // 2 - l_.width // 2, 200))
    return c


def put(im, c, x, y, p, key, t, rot=0.0, shadow=True):
    if p <= 0:
        return
    j = jitter(key, t, 1.0)
    paste(im, shadowed(c) if shadow else c, x + j[0], y + j[1], scale=pop(p), rot=rot + j[2])


def headline(im, text, y, p, size=110, hp=0.0, x=W / 2, color=INK):
    if p <= 0:
        return
    ti = T(text, size, fill=color)
    if p < 1:
        paste(im, ti, x, y, scale=pop(p))
    else:
        highlight_text(im, ti, x, y, hp)


def zone(im, v, poly, alpha, color=IRAQ, outline=True):
    if alpha <= 0:
        return
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    pts = [v.S(*q) for q in poly]
    d.polygon(pts, fill=tuple(color) + (int(200 * alpha),))
    # hatch
    hatch = Image.new('RGBA', im.size, (0, 0, 0, 0))
    dh = ImageDraw.Draw(hatch)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for k in range(int(min(xs) - (max(ys) - min(ys))), int(max(xs)), 18):
        dh.line([(k, max(ys)), (k + (max(ys) - min(ys)), min(ys))], fill=(90, 60, 20, int(120 * alpha)), width=3)
    m = Image.new('L', im.size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    ov.alpha_composite(Image.composite(hatch, Image.new('RGBA', im.size, (0, 0, 0, 0)), m))
    if outline:
        ImageDraw.Draw(ov).line(pts + [pts[0]], fill=tuple(INK) + (int(255 * alpha),), width=5)
    im.alpha_composite(ov)


def shrink(poly, f, anchor):
    return [(anchor[0] + (x - anchor[0]) * f, anchor[1] + (y - anchor[1]) * f) for x, y in poly]


OCCUPIED = [(46.2, 33.1), (46.9, 32.8), (47.6, 32.55), (48.25, 32.35), (48.55, 31.8), (48.85, 31.3), (48.75, 30.75),
            (48.45, 30.35), (48.1, 30.42), (47.85, 30.95), (47.65, 31.5), (47.4, 31.9), (46.6, 32.5)]
FAW = [(48.0, 30.05), (48.35, 30.25), (48.6, 30.0), (48.55, 29.85), (48.2, 29.9)]


# ---------------------------------------------------------------- icons
def icon_tanker(w=150):
    im = Image.new('RGBA', (w, int(w * 0.45)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    h = im.height
    d.polygon([(4, h * 0.35), (w - 4, h * 0.35), (w - 18, h - 4), (18, h - 4)], fill=(60, 58, 54))
    d.rectangle((w * 0.68, h * 0.05, w * 0.88, h * 0.36), fill=(80, 78, 72))
    d.rectangle((w * 0.12, h * 0.22, w * 0.62, h * 0.36), fill=RED)
    return im


def icon_warship(w=150):
    im = Image.new('RGBA', (w, int(w * 0.5)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    h = im.height
    d.polygon([(2, h * 0.5), (w - 2, h * 0.5), (w - 26, h - 4), (14, h - 4)], fill=(96, 104, 112))
    d.polygon([(w * 0.35, h * 0.5), (w * 0.42, h * 0.12), (w * 0.6, h * 0.12), (w * 0.68, h * 0.5)], fill=(120, 128, 136))
    d.line((w * 0.5, h * 0.12, w * 0.5, 0), fill=(96, 104, 112), width=4)
    return im


def icon_plane(w=90, ang=0):
    im = Image.new('RGBA', (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = w / 2
    d.polygon([(c, 4), (c + 8, c), (c + 8, w - 10), (c, w - 4), (c - 8, w - 10), (c - 8, c)], fill=INK)
    d.polygon([(c - w * 0.45, c + 6), (c + w * 0.45, c + 6), (c + 8, c - 10), (c - 8, c - 10)], fill=INK)
    d.polygon([(c - 18, w - 12), (c + 18, w - 12), (c + 4, w - 24), (c - 4, w - 24)], fill=INK)
    return im.rotate(ang, resample=Image.BICUBIC)


def icon_hazard(s=300):
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(s / 2, 10), (s - 10, s - 20), (10, s - 20)], fill=YELLOW, outline=INK)
    d.line([(s / 2, 10), (s - 10, s - 20), (10, s - 20), (s / 2, 10)], fill=INK, width=12, joint='curve')
    d.rounded_rectangle((s / 2 - 12, s * 0.33, s / 2 + 12, s * 0.66), 8, fill=INK)
    d.ellipse((s / 2 - 14, s * 0.72, s / 2 + 14, s * 0.72 + 28), fill=INK)
    return im


def icon_barrel(s=220, col=(70, 70, 70)):
    im = Image.new('RGBA', (int(s * 0.75), s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rounded_rectangle((4, 10, w - 4, h - 10), 26, fill=col)
    for y in (h * 0.3, h * 0.7):
        d.line((4, y, w - 4, y), fill=(40, 40, 40), width=8)
    d.ellipse((8, 2, w - 8, 30), fill=(95, 95, 95))
    return im


def icon_refinery(s=120):
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((10, s * 0.55, s - 10, s - 6), fill=(70, 66, 60))
    for x in (s * 0.25, s * 0.5, s * 0.72):
        d.rectangle((x - 7, s * 0.15, x + 7, s * 0.55), fill=(90, 86, 80))
    d.ellipse((s * 0.2, 0, s * 0.42, s * 0.18), fill=(150, 150, 150, 200))
    return im


# ================================================================== scenes
def s00(t, dur):  # ceasefire date
    im = bg()
    put(im, date_card('20', 'أغسطس 1988', 'وقف إطلاق النار', RED, seed=3), 1300, 540, prog(t, 0.1, 0.45), 'dc', t, -3)
    pa = prog(t, dur * 0.45, 0.4)
    if pa > 0:
        lbl(im, 'العراق', (420, 380), 110, IQ_D, clamp(pa * 2), 900)
        lbl(im, '×', (420, 520), 120, GREY, clamp(pa * 2), 700)
        lbl(im, 'إيران', (420, 670), 110, IR_D, clamp(pa * 2), 900)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


def s01(t, dur):  # border same place
    im, v = mapf(46.5, 32.5, 15.0, 0.55, 0.55)
    d = ImageDraw.Draw(im)
    country_labels(im, v, 1, (43.2, 32.2), (51.0, 32.6))
    tag(im, 'حدود 1980', 520, 220, prog(t, dur * 0.25, 0.35), size=48, key='b80', t=t, seed=3, fname='cairo', rot=-2)
    tag(im, 'حدود 1988', 520, 330, prog(t, dur * 0.55, 0.35), size=48, key='b88', t=t, seed=4, bgc=YELLOW, fname='cairo', rot=1.5)
    tag(im, '= نفس الخط تقريبًا', 520, 450, prog(t, dur * 0.75, 0.35), size=44, key='same', t=t, seed=5, fill=CARD, bgc=INK, rot=-1)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04, 0.55, 0.5)


def s02(t, dur):  # cost counters
    im = bg()
    put(im, stat_card('8', 'سنوات من القتال', INK, w=460, seed=1), 1560, 330, prog(t, 0.0, 0.35), 'c1', t, -2)
    put(im, stat_card('1 – 2 مليون', 'ضحية بين قتيل وجريح', RED, w=600, seed=2), 960, 330, prog(t, dur * 0.2, 0.35), 'c2', t, 1.5)
    put(im, stat_card('≈ 500 ألف', 'قتيل', INK, w=460, seed=3), 360, 330, prog(t, dur * 0.42, 0.35), 'c3', t, -1.5)
    headline(im, 'والخط لم يتغيّر تقريبًا', 760, prog(t, dur * 0.72, 0.3), 96, prog(t, dur * 0.8, 0.5))
    src = text_img('المصدر: الموسوعة البريطانية', 'plex', 28, None, GREY)
    paste(im, src, W - 60 - src.width / 2, H - 50)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s03(t, dur):  # three questions
    im = bg()
    for i, (q, at) in enumerate([('كيف بدأت؟', 0.0), ('لماذا استمرّت 8 سنوات؟', 0.3), ('لماذا انتهت حيث بدأت؟', 0.62)]):
        p = prog(t, dur * at, 0.3)
        if p > 0:
            ti = T(q, 96)
            if i == 2 and p >= 1:
                highlight_text(im, ti, W / 2, 300 + i * 230, prog(t, dur * at + 0.3, 0.5))
            else:
                paste(im, ti, W / 2, 300 + i * 230, scale=pop(p))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


def s04(t, dur):  # title
    im, v = mapf(47.5, 32.0, 18.0, 0.45, 0.45)
    ov = Image.new('RGBA', im.size, SAND + (150,))
    im.alpha_composite(ov)
    headline(im, 'الحرب العراقية الإيرانية', 430, prog(t, 0.0, 0.35), 130, prog(t, 0.4, 0.6))
    lbl(im, '1980 — 1988', (W / 2, 590), 90, RED, prog(t, 0.5, 0.4), 900)
    tag(im, 'حرب الخليج الأولى', W / 2, 740, prog(t, dur * 0.55, 0.35), size=54, key='gw1', t=t, seed=7, fill=CARD, bgc=INK, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s05(t, dur):  # rivers to Shatt
    lon, lat, span, f = cam(t, dur, (44.5, 33.0, 14.0), (47.7, 30.9, 5.2), 0.2, dur * 0.85)
    im, v = mapf(lon, lat, span, cache=False)
    d = ImageDraw.Draw(im)
    for name, at in [('tigris', 0.0), ('euphrates', 0.08), ('shatt', 0.45)]:
        pts = [v.S(*q) for q in mapr.RIVERS[name]]
        stroke_path(d, pts, ease_out(prog(t, dur * at, dur * 0.4)), (40, 110, 190), 12 if name == 'shatt' else 9)
    lbl(im, 'دجلة', v.S(44.9, 33.4), 46, (40, 90, 150), clamp(1 - f * 1.5), 800)
    lbl(im, 'الفرات', v.S(43.3, 32.4), 46, (40, 90, 150), clamp(1 - f * 1.5), 800)
    tag(im, 'شطّ العرب', v.S(*PLACES['basra'])[0] - 230, v.S(*PLACES['basra'])[1] + 60, prog(t, dur * 0.55, 0.35),
        size=56, key='shatt', t=t, seed=8, bgc=YELLOW, fname='cairo')
    lbl(im, 'الخليج', v.S(49.6, 29.2), 60, (60, 100, 110), prog(t, dur * 0.7, 0.5), 800)
    return im.convert('RGB')


def s06(t, dur):  # Iraq's short coastline
    im, v = mapf(48.0, 30.0, 5.2, 0.5 * prog(t, 0, 0.6), 0.0)
    d = ImageDraw.Draw(im)
    # highlight Iraq coast between Kuwait border and Faw
    coast = [v.S(47.95, 29.98), v.S(48.2, 29.95), v.S(48.45, 29.98), v.S(48.55, 29.96)]
    stroke_path(d, coast, ease_out(prog(t, dur * 0.25, 0.8)), RED, 14)
    tag(im, 'ساحل العراق: قصير جدًّا', v.S(48.2, 29.95)[0] + 330, v.S(48.2, 29.95)[1] + 110, prog(t, dur * 0.3, 0.35),
        size=48, key='coast', t=t, seed=9, fill=CARD, bgc=RED, fname='cairo')
    x, y = v.S(*PLACES['basra'])
    pin(im, x, y, prog(t, dur * 0.5, 0.4), INK)
    tag(im, 'ميناء البصرة', x - 210, y - 60, prog(t, dur * 0.55, 0.3), size=46, key='basra', t=t, seed=10, fname='cairo')
    lbl(im, 'الكويت', v.S(47.6, 29.4), 52, GREY, 1, 800)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04, 0.5, 0.45)


def s07(t, dur):  # Khorramshahr & Abadan
    im, v = mapf(48.15, 30.35, 3.0, 0.45, 0.5 * prog(t, 0, 0.6))
    for k, (key, name, dx, dy, at) in enumerate([('khorramshahr', 'خرّمشهر (المحمّرة)', 300, -70, 0.15),
                                                 ('abadan', 'عبّادان', 220, 70, 0.45)]):
        x, y = v.S(*PLACES[key])
        pin(im, x, y, prog(t, dur * at, 0.4), IR_D)
        tag(im, name, x + dx, y + dy, prog(t, dur * at + 0.15, 0.3), size=48, key=key, t=t, seed=11 + k, fname='cairo')
    pr = prog(t, dur * 0.6, 0.4)
    if pr > 0:
        x, y = v.S(*PLACES['abadan'])
        paste(im, shadowed(icon_refinery(130), (4, 6), 6, 0.3), x + 130, y + 190, scale=pop(pr))
        tag(im, 'مصفاة نفط ضخمة', x + 320, y + 190, prog(t, dur * 0.65, 0.3), size=40, key='ref', t=t, seed=13, bgc=YELLOW)
    x, y = v.S(*PLACES['basra'])
    lbl(im, 'البصرة', (x, y - 40), 46, IQ_D, 1, 900)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def river_diagram(im, t, border_mode, pb, label_text=None, key='rd'):
    """Top view of a river: Iraq bank (left) / Iran bank (right)."""
    d = ImageDraw.Draw(im)
    d.rectangle((0, 160, 640, 920), fill=IRAQ + (255,))
    d.rectangle((1280, 160, W, 920), fill=IRAN + (255,))
    d.rectangle((640, 160, 1280, 920), fill=(120, 170, 205, 255))
    for k in range(7):
        y = 230 + k * 100
        d.line([(x, y + 10 * math.sin(x / 50 + t * 2 + k)) for x in range(660, 1270, 15)], fill=(170, 205, 228), width=4)
    lbl(im, 'العراق', (320, 540), 90, (90, 55, 10), 1, 900)
    lbl(im, 'إيران', (1600, 540), 90, (20, 70, 66), 1, 900)
    lbl(im, 'شطّ العرب', (960, 120), 64, INK, 1, 900)
    if pb > 0:
        x = 1262 if border_mode == 'bank' else 960
        dashed(d, [(x, 170), (x, 910)], pb, RED, 12, 40)
        if label_text:
            tag(im, label_text, x, 980, pb, size=44, key=key, t=t, seed=21, bgc=YELLOW, fname='cairo')


def s08(t, dur):  # where is the border? two options
    im = bg()
    mode = 'bank' if t < dur * 0.55 else 'mid'
    pb = prog(t, dur * 0.25, 0.6) if mode == 'bank' else prog(t, dur * 0.6, 0.6)
    river_diagram(im, t, mode, pb, 'على الضفة الإيرانية؟' if mode == 'bank' else 'أم في منتصف المجرى؟',
                  key='rd' + mode)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def doc_card(title, lines, year, w=760, seed=31, head=INK):
    h = 170 + 80 * len(lines) + 40
    c = card(w, h, seed=seed)
    d = ImageDraw.Draw(c)
    yi = text_img(year, 'oswald', 96, 700, RED)
    c.alpha_composite(yi, (40, 24))
    ti = text_img(title, 'cairo', 52, 900, head)
    c.alpha_composite(ti, (w - 40 - ti.width, 44))
    d.line((40, 150, w - 40, 150), fill=INK, width=3)
    y = 172
    for ln in lines:
        li = text_img(ln, 'plexb', 40, None, INK)
        c.alpha_composite(li, (w - 44 - li.width, y))
        y += 80
    return c


def s09(t, dur):  # Algiers agreement 1975
    im = bg()
    c = doc_card('اتفاقية الجزائر', ['بين العراق وإيران', 'حول الحدود وشطّ العرب'], '1975', seed=32)
    put(im, c, W / 2, 540, prog(t, 0.05, 0.45), 'alg', t, -2)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.05)


def s10(t, dur):  # the trade
    im = bg()
    pb = 1.0
    river_diagram(im, t, 'mid', prog(t, 0.0, 0.6), 'الحدود: منتصف المجرى', key='rdm')
    pc = prog(t, dur * 0.45, 0.4)
    if pc > 0:
        ov = Image.new('RGBA', im.size, SAND + (int(200 * clamp(pc * 2)),))
        im.alpha_composite(ov)
        put(im, stat_card('نصف المجرى', 'تنازل عنه العراق', IQ_D, w=560, seed=41), 1400, 520, pc, 'tr1', t, -2)
        put(im, stat_card('وقف الدعم', 'للتمرّد الكردي من إيران', IR_D, w=600, seed=42), 520, 520, prog(t, dur * 0.62, 0.4), 'tr2', t, 2)
        ex = text_img('⇄', 'plexb', 140, None, INK) if False else text_img('مقابل', 'cairo', 70, 900, RED)
        paste(im, ex, 960, 520, scale=pop(prog(t, dur * 0.58, 0.3)))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s11(t, dur):  # 1979
    im = bg()
    big = text_img('1979', 'oswald', 380, 700, INK)
    paste(im, big, W / 2, 430, scale=pop(prog(t, 0.0, 0.4)))
    tag(im, 'سقوط الشاه', 640, 790, prog(t, dur * 0.35, 0.35), size=64, key='shah', t=t, seed=51, fname='cairo', rot=-2)
    tag(im, 'جمهورية إسلامية في إيران', 1300, 790, prog(t, dur * 0.6, 0.35), size=60, key='ir', t=t, seed=52,
        fill=CARD, bgc=IR_D, fname='cairo', rot=1.5)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


BORDER_PTS = [(45.0, 35.9), (45.55, 34.6), (45.8, 33.6), (46.4, 33.0), (47.2, 32.6), (47.7, 31.9), (47.7, 31.0),
              (48.0, 30.47)]


def s12(t, dur):  # chaos & clashes
    im, v = mapf(46.8, 33.0, 9.0, 0.45, 0.45)
    d = ImageDraw.Draw(im)
    country_labels(im, v, 1, (43.8, 32.4), (49.6, 33.6), 70)
    for k, q in enumerate(BORDER_PTS):
        x, y = v.S(*q)
        burst(d, x, y, 38, pop(prog(t, dur * (0.2 + 0.07 * k), 0.25)), RED if k % 2 else (230, 120, 40), seed=k + int(t * 6))
    tag(im, 'فوضى بعد الثورة', 1480, 170, prog(t, 0.2, 0.35), size=50, key='chaos', t=t, seed=61, fill=CARD, bgc=IR_D, fname='cairo')
    tag(im, 'اشتباكات حدودية متكرّرة', 520, 960, prog(t, dur * 0.5, 0.35), size=50, key='clash', t=t, seed=62, bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


def s13(t, dur):  # Baghdad sees an opportunity
    im, v = mapf(46.6, 32.0, 9.5, 0.5, 0.35)
    xb, yb = v.S(*PLACES['baghdad'])
    pin(im, xb, yb, prog(t, 0.1, 0.4), IQ_D)
    tag(im, 'بغداد', xb - 120, yb - 60, prog(t, 0.3, 0.3), size=50, key='bg', t=t, seed=71, fname='cairo')
    d = ImageDraw.Draw(im)
    dashed(d, [(xb, yb), v.S(46.5, 31.6), v.S(*PLACES['khorramshahr'])], prog(t, dur * 0.3, 1.0), IQ_D, 8)
    x, y = v.S(*PLACES['khorramshahr'])
    tag(im, 'شطّ العرب كاملًا', x + 30, y + 90, prog(t, dur * 0.5, 0.35), size=48, key='opp1', t=t, seed=72, bgc=YELLOW, fname='cairo')
    tag(im, 'وربّما أكثر؟', v.S(49.2, 31.6)[0], v.S(49.2, 31.6)[1], prog(t, dur * 0.72, 0.35), size=48, key='opp2', t=t, seed=73,
        fill=CARD, bgc=INK, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


def s14(t, dur):  # 17 Sept 1980 cancellation
    im = bg()
    put(im, date_card('17', 'سبتمبر 1980', None, IQ_D, seed=81), 1400, 520, prog(t, 0.05, 0.4), 'd17', t, -2)
    c = doc_card('اتفاقية الجزائر', ['بين العراق وإيران', 'حول الحدود وشطّ العرب'], '1975', w=700, seed=82)
    put(im, c, 640, 520, prog(t, dur * 0.25, 0.4), 'alg2', t, 2)
    pa = prog(t, dur * 0.55, 0.3)
    if pa > 0:
        st = text_img('مُلغاة', 'cairo', 150, 900, RED)
        stamp = Image.new('RGBA', (st.width + 80, st.height + 60), (0, 0, 0, 0))
        ds = ImageDraw.Draw(stamp)
        ds.rounded_rectangle((6, 6, stamp.width - 6, stamp.height - 6), 18, outline=RED, width=12)
        stamp.alpha_composite(st, (40, 30))
        paste(im, stamp, 640, 520, scale=1.6 - 0.6 * ease_out(pa), rot=-12, alpha=clamp(pa * 2))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s15(t, dur):  # 22 Sept: air strikes + ground invasion
    im, v = mapf(48.2, 33.3, 11.0, 0.45, 0.45)
    d = ImageDraw.Draw(im)
    tgts = [(51.31, 35.69), (48.39, 32.43), (46.24, 38.13), (48.53, 34.87), (47.1, 34.35), (48.7, 31.34)]
    for k, q in enumerate(tgts):
        x, y = v.S(*q)
        q_ = pop(prog(t, 0.4 + k * 0.35, 0.3))
        burst(d, x, y, 34, q_, RED, seed=k + int(t * 8))
        if q_ > 0 and k < 3:
            paste(im, icon_plane(70, -60), x - 70, y + 50, alpha=clamp(1 - prog(t, 0.4 + k * 0.35 + 0.6, 0.5)))
    pa = prog(t, dur * 0.45, 1.4)
    for k, (a, b) in enumerate([((47.3, 31.3), (48.4, 30.6)), ((47.5, 32.3), (48.4, 31.6)), ((46.6, 33.0), (47.6, 32.6))]):
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.15)
        arrow(im, [v.S(*a), v.S(*mid), v.S(*b)], prog(t, dur * 0.45 + k * 0.3, 1.2), IQ_D, 28, 56)
    tag(im, 'خوزستان: محافظة النفط', v.S(49.6, 31.2)[0] + 60, v.S(49.6, 31.2)[1], prog(t, dur * 0.65, 0.35), size=48,
        key='khz', t=t, seed=91, bgc=YELLOW, fname='cairo')
    tag(im, '22 سبتمبر 1980', 330, 120, prog(t, 0.0, 0.3), size=54, key='d22', t=t, seed=92, fill=CARD, bgc=RED, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s16(t, dur):  # occupied areas
    im, v = mapf(47.8, 31.6, 6.0, 0.45, 0.45)
    zone(im, v, shrink(OCCUPIED, 0.3 + 0.7 * ease_out(prog(t, 0.1, dur * 0.6)), (47.6, 31.9)), 1.0)
    x, y = v.S(*PLACES['khorramshahr'])
    pin(im, x, y, prog(t, dur * 0.45, 0.4), IQ_D)
    tag(im, 'سقوط خرّمشهر', x + 230, y + 40, prog(t, dur * 0.5, 0.35), size=48, key='kfall', t=t, seed=101, fill=CARD, bgc=IQ_D, fname='cairo')
    tag(im, 'مناطق سيطرة العراق (تقريبي)', 1500, 140, prog(t, dur * 0.2, 0.35), size=42, key='occ', t=t, seed=102)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s17(t, dur):  # Abadan holds
    im, v = mapf(48.0, 30.9, 4.0, 0.45, 0.45)
    zone(im, v, OCCUPIED, 1.0)
    x, y = v.S(*PLACES['abadan'])
    d = ImageDraw.Draw(im)
    r = 110
    pr = prog(t, dur * 0.25, 0.8)
    pts = [(x + math.cos(a) * r, y + math.sin(a) * r) for a in np.linspace(0, 2 * math.pi, 50)]
    dashed(d, pts, pr, RED, 7, 50)
    pin(im, x, y, 1.0, IR_D)
    tag(im, 'عبّادان: حوصرت ولم تسقط', x + 60, y - 210, prog(t, dur * 0.55, 0.35), size=48, key='abd', t=t, seed=111,
        fill=CARD, bgc=IR_D, fname='cairo')
    tag(im, 'لا حرب سريعة', 400, 140, prog(t, 0.2, 0.35), size=56, key='nofast', t=t, seed=112, bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04, 0.6, 0.6)


def s18(t, dur):  # Iran retakes
    im, v = mapf(47.8, 31.6, 6.0, 0.45, 0.45)
    f = 1 - 0.85 * ease_io(prog(t, 0.2, dur * 0.7))
    zone(im, v, shrink(OCCUPIED, f, (47.4, 31.6)), clamp(f * 1.5))
    for k, (a, b) in enumerate([((49.4, 31.0), (48.4, 30.6)), ((49.6, 31.9), (48.6, 31.6)), ((49.0, 32.7), (48.0, 32.4))]):
        arrow(im, [v.S(*a), v.S(*b)], prog(t, 0.4 + k * 0.4, 1.4), IR_D, 26, 52)
    x, y = v.S(*PLACES['khorramshahr'])
    tag(im, 'مايو 1982: استعادة خرّمشهر', x + 160, y - 170, prog(t, dur * 0.65, 0.35), size=46, key='krec', t=t, seed=121,
        fill=CARD, bgc=IR_D, fname='cairo')
    tag(im, '1981', 300, 120, prog(t, 0.0, 0.3), size=56, key='y81', t=t, seed=122, bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s19(t, dur):  # Iraq withdraws, offers peace
    im, v = mapf(47.0, 32.3, 9.0, 0.45, 0.45)
    for k, (a, b) in enumerate([((48.3, 31.5), (47.0, 31.4)), ((47.9, 32.6), (46.6, 32.7)), ((46.9, 33.4), (45.7, 33.6))]):
        arrow(im, [v.S(*a), v.S(*b)], prog(t, 0.2 + k * 0.25, 1.1), IQ_D, 26, 52)
    tag(im, 'العودة إلى الحدود', 1450, 170, prog(t, dur * 0.35, 0.35), size=52, key='back', t=t, seed=131, fname='cairo')
    tag(im, 'العراق: نريد السلام', 1450, 290, prog(t, dur * 0.6, 0.35), size=52, key='peace', t=t, seed=132,
        bgc=YELLOW, fname='cairo')
    country_labels(im, v, 1, (44.2, 31.8), (49.3, 31.6), 70)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def timeline(im, t, years, segs, y=560):
    """years: (y0,y1). segs: list of (a,b,color,label,p)."""
    x0, x1 = 260, 1660
    d = ImageDraw.Draw(im)
    d.line((x0, y, x1, y), fill=INK, width=6)
    Y0, Y1 = years
    for yr in range(Y0, Y1 + 1):
        x = x1 - (yr - Y0) / (Y1 - Y0) * (x1 - x0)          # RTL: earlier on the right
        d.line((x, y - 18, x, y + 18), fill=INK, width=4)
        ti = text_img(str(yr), 'oswald', 40, 600, GREY)
        paste(im, ti, x, y + 60)
    for (a, b, col, lab, p) in segs:
        if p <= 0:
            continue
        xa = x1 - (a - Y0) / (Y1 - Y0) * (x1 - x0)
        xb = x1 - (b - Y0) / (Y1 - Y0) * (x1 - x0)
        xe = xa + (xb - xa) * ease_out(p)
        d.rounded_rectangle((min(xa, xe), y - 60, max(xa, xe), y - 22), 8, fill=col)
        if p >= 0.6:
            li = text_img(lab, 'cairo', 52, 900, col)
            paste(im, li, (xa + xb) / 2, y - 120, alpha=clamp((p - 0.6) * 3))


def s20(t, dur):  # if it ended in 1982
    im = bg()
    headline(im, 'لو انتهت هنا...', 220, prog(t, 0.0, 0.3), 100, prog(t, 0.4, 0.5))
    timeline(im, t, (1980, 1988), [(1980, 1982, IQ_D, 'عامان فقط', prog(t, dur * 0.35, 0.9))])
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s21(t, dur):  # Iran takes the war into Iraq
    im, v = mapf(47.2, 31.3, 6.5, 0.45, 0.45)
    for k, (a, b) in enumerate([((48.6, 31.2), (47.5, 30.8)), ((48.4, 30.5), (47.4, 30.4)), ((48.3, 32.0), (47.0, 31.8))]):
        arrow(im, [v.S(*a), v.S(*b)], prog(t, dur * 0.3 + k * 0.3, 1.2), IR_D, 28, 56)
    x, y = v.S(*PLACES['basra'])
    pin(im, x, y, prog(t, dur * 0.25, 0.4), IQ_D)
    tag(im, 'البصرة', x - 140, y - 50, prog(t, dur * 0.3, 0.3), size=48, key='bsr', t=t, seed=141, fname='cairo')
    tag(im, 'رفض وقف إطلاق النار', 1450, 160, prog(t, 0.1, 0.35), size=52, key='rej', t=t, seed=142, fill=CARD, bgc=IR_D, fname='cairo')
    tag(im, 'الهدف المعلن: إسقاط النظام في بغداد', 900, 980, prog(t, dur * 0.65, 0.35), size=46, key='goal', t=t, seed=143,
        bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s22(t, dur):  # 2 years became 8
    im = bg()
    timeline(im, t, (1980, 1988), [(1980, 1982, IQ_D, 'عامان', 1.0),
                                    (1982, 1988, RED, '6 سنوات أخرى', prog(t, 0.3, dur * 0.6))])
    headline(im, '8 سنوات', 230, prog(t, dur * 0.7, 0.3), 140, prog(t, dur * 0.78, 0.5))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s23(t, dur):  # WW1-like trenches near Basra
    im, v = mapf(47.6, 30.9, 3.6, 0.45, 0.45)
    d = ImageDraw.Draw(im)
    front = [v.S(47.75, 32.0), v.S(47.85, 31.6), v.S(47.95, 31.2), v.S(48.0, 30.9), v.S(48.0, 30.6)]
    # zig-zag trench line
    zz = []
    for i in range(len(front) - 1):
        a, b = front[i], front[i + 1]
        for k in range(10):
            f = k / 10
            x = a[0] + (b[0] - a[0]) * f + (12 if k % 2 else -12)
            y = a[1] + (b[1] - a[1]) * f
            zz.append((x, y))
    stroke_path(d, zz, ease_out(prog(t, 0.1, 1.0)), INK, 8)
    for w_ in range(4):
        tt = (t - 0.8 - w_ * 0.9)
        if tt > 0:
            pw = (tt % 3.0) / 3.0
            for k in range(4):
                y = front[0][1] + (front[-1][1] - front[0][1]) * (0.15 + 0.22 * k)
                x = front[0][0] + 360 - 320 * ease_out(pw)
                arrow(im, [(x + 120, y), (x, y)], 1.0, IR_D, 16, 34) if pw < 0.95 else None
    tag(im, 'مثل الحرب العالمية الأولى', 520, 150, prog(t, dur * 0.2, 0.35), size=52, key='ww1', t=t, seed=151,
        bgc=YELLOW, fname='cairo')
    tag(im, 'خنادق وموجات بشرية', 520, 270, prog(t, dur * 0.4, 0.35), size=46, key='tr', t=t, seed=152)
    x, y = v.S(*PLACES['basra'])
    lbl(im, 'البصرة', (x - 60, y - 30), 50, IQ_D, 1, 900)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s24(t, dur):  # small gains: Majnoon 1984, Faw 1986
    im, v = mapf(48.0, 30.6, 3.6, 0.45, 0.45)
    x, y = v.S(*PLACES['majnoon'])
    pin(im, x, y, prog(t, dur * 0.1, 0.4), IR_D)
    tag(im, 'جزر مجنون — 1984', x - 230, y - 60, prog(t, dur * 0.15, 0.35), size=46, key='maj', t=t, seed=161, fname='cairo')
    zone(im, v, FAW, prog(t, dur * 0.5, 0.6), IRAN)
    x, y = v.S(*PLACES['faw'])
    tag(im, 'الفاو — 1986', x + 200, y + 80, prog(t, dur * 0.55, 0.35), size=46, key='faw', t=t, seed=162, fill=CARD,
        bgc=IR_D, fname='cairo')
    tag(im, 'مكاسب صغيرة... بثمن هائل', 960, 980, prog(t, dur * 0.75, 0.35), size=50, key='small', t=t, seed=163,
        bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s25(t, dur):  # chemical weapons, Halabja (non-graphic)
    if t < dur * 0.55:
        im = bg()
        paste(im, shadowed(icon_hazard(320)), 1380, 470, scale=pop(prog(t, 0.05, 0.4)))
        headline(im, 'أسلحة كيميائية', 470, prog(t, 0.3, 0.3), 110, prog(t, 0.6, 0.5), x=640)
        lbl(im, 'ضد القوات الإيرانية، ثم ضد المدنيين', (640, 640), 50, GREY, prog(t, dur * 0.25, 0.4), 800)
        return camera(im.convert('RGB'), t, dur, 1.0, 1.03)
    tt = t - dur * 0.55
    im, v = mapf(45.6, 34.6, 6.0, 0.45, 0.45)
    x, y = v.S(*PLACES['halabja'])
    pin(im, x, y, prog(tt, 0.05, 0.4), INK)
    tag(im, 'حلبجة — مارس 1988', x - 260, y + 60, prog(tt, 0.2, 0.35), size=50, key='hal', t=t, seed=171, fill=CARD,
        bgc=INK, fname='cairo')
    return im.convert('RGB')


def missile_arc(d, a, b, p, color, h=160, width=6):
    if p <= 0:
        return
    pts = []
    for i in range(41):
        f = i / 40 * p
        x = a[0] + (b[0] - a[0]) * f
        y = a[1] + (b[1] - a[1]) * f - math.sin(math.pi * f) * h
        pts.append((x, y))
    for i in range(0, len(pts) - 1, 2):
        d.line([pts[i], pts[i + 1]], fill=color, width=width)
    if p < 1:
        d.ellipse((pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10), fill=color)


def s26(t, dur):  # war of the cities
    im, v = mapf(48.0, 34.0, 12.0, 0.45, 0.45)
    d = ImageDraw.Draw(im)
    b, te = v.S(*PLACES['baghdad']), v.S(*PLACES['tehran'])
    for k in range(5):
        p = prog(t, 0.4 + k * 0.6, 1.2)
        if k % 2 == 0:
            missile_arc(d, b, (te[0] + random.Random(k).uniform(-40, 40), te[1]), p, IQ_D, 220)
        else:
            missile_arc(d, te, (b[0] + random.Random(k).uniform(-40, 40), b[1]), p, IR_D, 200)
    for key, name, dx in [('baghdad', 'بغداد', -110), ('tehran', 'طهران', 110)]:
        x, y = v.S(*PLACES[key])
        pin(im, x, y, 1.0, INK)
        tag(im, name, x + dx, y + 50, 1.0, size=50, key=key, t=t, seed=181, fname='cairo')
    tag(im, 'حرب المدن', 960, 140, prog(t, dur * 0.4, 0.35), size=64, key='cities', t=t, seed=182, fill=CARD, bgc=RED, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


LANE = [(48.9, 29.6), (50.3, 28.9), (51.8, 27.5), (53.5, 26.6), (55.3, 26.3), (56.4, 26.5), (57.5, 25.6)]


def s27(t, dur):  # tanker war
    im, v = mapf(52.0, 27.6, 11.0, 0.4, 0.4)
    d = ImageDraw.Draw(im)
    pts = [v.S(*q) for q in LANE]
    dashed(d, pts, 1.0, (90, 120, 130), 4, 70)
    for k in range(5):
        f = ((t * 0.05 + k * 0.2) % 1.0)
        x, y = _along(pts, f)
        paste(im, icon_tanker(120), x, y - 10)
        if k in (1, 3) and t > dur * 0.4 + k * 0.3:
            burst(d, x + 20, y - 30, 40, pop(prog(t, dur * 0.4 + k * 0.3, 0.3)), (240, 120, 30), seed=k + int(t * 8))
    x, y = v.S(*PLACES['kharg'])
    pin(im, x, y, prog(t, dur * 0.3, 0.3), IR_D)
    tag(im, 'جزيرة خرج', x + 140, y - 60, prog(t, dur * 0.35, 0.3), size=42, key='khg', t=t, seed=191, fname='cairo')
    x, y = v.S(*PLACES['hormuz'])
    tag(im, 'مضيق هرمز', x - 40, y + 110, prog(t, dur * 0.5, 0.3), size=42, key='hmz', t=t, seed=192, fname='cairo')
    tag(im, 'حرب الناقلات', 1450, 140, prog(t, 0.1, 0.35), size=64, key='tank', t=t, seed=193, fill=CARD, bgc=RED, fname='cairo')
    tag(im, 'النفط = مموّل الحرب', 1450, 260, prog(t, dur * 0.65, 0.35), size=46, key='oil', t=t, seed=194, bgc=YELLOW, fname='cairo')
    return im.convert('RGB')


def s28(t, dur):  # foreign navies
    im, v = mapf(53.5, 26.8, 10.0, 0.4, 0.4)
    pts = [v.S(*q) for q in reversed(LANE)]
    for k in range(3):
        f = clamp((t - k * 0.8) * 0.07)
        x, y = _along(pts, f)
        paste(im, icon_warship(140), x, y - 30, alpha=clamp((t - k * 0.8) * 2))
    tag(im, 'سفن حربية أجنبية لحماية الناقلات', 960, 140, prog(t, dur * 0.2, 0.35), size=50, key='nav', t=t, seed=201,
        fill=CARD, bgc=INK, fname='cairo')
    tag(im, 'من حرب إقليمية... إلى قضية دولية', 960, 980, prog(t, dur * 0.6, 0.35), size=50, key='intl', t=t, seed=202,
        bgc=YELLOW, fname='cairo')
    return im.convert('RGB')


def s29(t, dur):  # why so long? 3 reasons
    im = bg()
    headline(im, 'لماذا استمرّت كلّ هذا الوقت؟', 420, prog(t, 0.0, 0.3), 104, prog(t, 0.5, 0.5))
    p = prog(t, dur * 0.55, 0.35)
    if p > 0:
        for k in range(3):
            c = text_img(str(k + 1), 'oswald', 120, 700, CARD)
            badge = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
            ImageDraw.Draw(badge).ellipse((10, 10, 190, 190), fill=[RED, IQ_D, IR_D][k])
            badge.alpha_composite(c, (100 - c.width // 2, 100 - c.height // 2))
            paste(im, shadowed(badge, (5, 7), 6, 0.3), 1260 - k * 300, 700, scale=pop(prog(t, dur * 0.55 + k * 0.2, 0.35)))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def reason_head(im, n, title, t, col):
    badge = Image.new('RGBA', (170, 170), (0, 0, 0, 0))
    ImageDraw.Draw(badge).ellipse((5, 5, 165, 165), fill=col)
    c = text_img(str(n), 'oswald', 100, 700, CARD)
    badge.alpha_composite(c, (85 - c.width // 2, 85 - c.height // 2))
    paste(im, shadowed(badge, (5, 7), 6, 0.3), 1700, 150, scale=pop(prog(t, 0.0, 0.3)))
    ti = T(title, 100)
    paste(im, ti, 1580 - ti.width / 2, 150, scale=pop(prog(t, 0.1, 0.3)))


def s30(t, dur):  # reason 1: goals
    im = bg()
    reason_head(im, 1, 'الأهداف', t, RED)
    tag(im, 'قبل 1982: نزاع على نهر', 1300, 450, prog(t, dur * 0.12, 0.35), size=54, key='g1', t=t, seed=211, fname='cairo')
    arrow(im, [(1040, 450), (880, 450)], prog(t, dur * 0.3, 0.5), INK, 20, 44)
    tag(im, 'بعدها: بقاء الأنظمة نفسها', 560, 450, prog(t, dur * 0.38, 0.35), size=54, key='g2', t=t, seed=212,
        fill=CARD, bgc=RED, fname='cairo')
    headline(im, 'ومن الصعب التفاوض حين يكون الهدف إسقاط الطرف الآخر', 760, prog(t, dur * 0.65, 0.3), 56, prog(t, dur * 0.72, 0.6))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def scale_img(tilt):
    im = Image.new('RGBA', (1200, 620), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, top = 600, 120
    d.polygon([(cx - 80, 600), (cx + 80, 600), (cx + 14, top), (cx - 14, top)], fill=INK)
    a = math.radians(tilt)
    L = 430
    lx, ly = cx - L * math.cos(a), top + L * math.sin(a)
    rx, ry = cx + L * math.cos(a), top - L * math.sin(a)
    d.line((lx, ly, rx, ry), fill=INK, width=14)
    for (x, y, col) in [(lx, ly, IR_D), (rx, ry, IQ_D)]:
        d.line((x, y, x - 90, y + 170), fill=INK, width=4)
        d.line((x, y, x + 90, y + 170), fill=INK, width=4)
        d.pieslice((x - 150, y + 90, x + 150, y + 250), 0, 180, fill=col)
    d.ellipse((cx - 26, top - 26, cx + 26, top + 26), fill=RED)
    return im, (lx, ly), (rx, ry)


def s31(t, dur):  # reason 2: balance
    im = bg()
    reason_head(im, 2, 'التوازن', t, IQ_D)
    tilt = 8 * math.sin(t * 1.3) * (1 - prog(t, dur * 0.6, dur * 0.3))
    sc, l, r = scale_img(tilt)
    ox, oy = W / 2 - 600, 330
    im.alpha_composite(sc, (int(ox), int(oy)))
    tag(im, 'إيران: سكان أكثر بكثير', ox + l[0], oy + l[1] + 330, prog(t, dur * 0.15, 0.35), size=46, key='b1', t=t,
        seed=221, fill=CARD, bgc=IR_D, fname='cairo')
    tag(im, 'العراق: سلاح ودعم خارجي أكثر', ox + r[0], oy + r[1] + 330, prog(t, dur * 0.35, 0.35), size=46, key='b2',
        t=t, seed=222, fill=CARD, bgc=IQ_D, fname='cairo')
    tag(im, 'لا أحد يحسم', 420, 300, prog(t, dur * 0.7, 0.35), size=60, key='nod', t=t, seed=223, bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.02)


def s32(t, dur):  # reason 3: oil
    im = bg()
    reason_head(im, 3, 'النفط', t, IR_D)
    paste(im, shadowed(icon_barrel(260)), 1350, 600, scale=pop(prog(t, dur * 0.1, 0.35)))
    arrow(im, [(1180, 600), (1020, 600)], prog(t, dur * 0.25, 0.5), INK, 20, 44)
    tag(im, 'أموال', 900, 600, prog(t, dur * 0.3, 0.35), size=70, key='money', t=t, seed=231, bgc=YELLOW, fname='cairo')
    arrow(im, [(780, 600), (620, 600)], prog(t, dur * 0.45, 0.5), INK, 20, 44)
    tag(im, 'عام آخر من الحرب', 430, 600, prog(t, dur * 0.5, 0.35), size=60, key='war', t=t, seed=232, fill=CARD, bgc=RED, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s33(t, dur):  # 1988 balance shifts
    im, v = mapf(47.8, 30.8, 4.2, 0.45, 0.45)
    zone(im, v, FAW, 1 - prog(t, dur * 0.25, 0.6), IRAN)
    for k, (a, b) in enumerate([((47.6, 30.3), (48.3, 30.0)), ((47.4, 31.0), (47.9, 31.0)), ((47.3, 31.5), (47.8, 31.6))]):
        arrow(im, [v.S(*a), v.S(*b)], prog(t, dur * 0.15 + k * 0.3, 1.0), IQ_D, 26, 52)
    x, y = v.S(*PLACES['faw'])
    tag(im, 'استعادة الفاو', x + 150, y + 120, prog(t, dur * 0.4, 0.35), size=48, key='faw2', t=t, seed=241, fill=CARD,
        bgc=IQ_D, fname='cairo')
    tag(im, '1988: الميزان يتغيّر', 400, 140, prog(t, 0.0, 0.3), size=58, key='y88', t=t, seed=242, bgc=YELLOW, fname='cairo')
    tag(im, 'إيران منهكة اقتصاديًّا', 1450, 140, prog(t, dur * 0.65, 0.35), size=48, key='tired', t=t, seed=243,
        fill=CARD, bgc=IR_D, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s34(t, dur):  # Resolution 598
    im = bg()
    c = doc_card('مجلس الأمن الدولي', ['القرار رقم 598', 'وقف إطلاق النار والعودة', 'إلى الحدود الدولية'], '1987', seed=251)
    put(im, c, 1150, 520, prog(t, 0.05, 0.4), 'res', t, -2)
    tag(im, 'يوليو 1988: إيران تقبل القرار', 560, 820, prog(t, dur * 0.45, 0.35), size=52, key='acc', t=t, seed=252,
        fill=CARD, bgc=IR_D, fname='cairo', rot=2)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s35(t, dur):
    im = bg()
    put(im, date_card('20', 'أغسطس 1988', 'وقف إطلاق النار', RED, seed=3), W / 2, 540, prog(t, 0.05, 0.4), 'dc2', t, 2)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.06)


def s36(t, dur):  # back to the border; 1990 Algiers again
    if t < dur * 0.55:
        im, v = mapf(46.5, 32.5, 15.0, 0.55, 0.55)
        country_labels(im, v)
        tag(im, 'العودة إلى الحدود الدولية', 1450, 150, prog(t, 0.1, 0.35), size=52, key='bd', t=t, seed=261, fname='cairo')
        tag(im, 'لا أرض جديدة لأحد', 520, 960, prog(t, dur * 0.25, 0.35), size=60, key='noland', t=t, seed=262,
            bgc=YELLOW, fname='cairo')
        return im.convert('RGB')
    tt = t - dur * 0.55
    im = bg()
    c = doc_card('اتفاقية الجزائر', ['بين العراق وإيران', 'حول الحدود وشطّ العرب'], '1975', w=700, seed=82)
    put(im, c, 1200, 520, prog(tt, 0.05, 0.4), 'alg3', t, 2)
    tag(im, '1990: العراق يقبل الاتفاقية نفسها مجددًا', 620, 860, prog(tt, 0.4, 0.35), size=46, key='alg90', t=t,
        seed=263, fill=CARD, bgc=INK, fname='cairo', rot=-1.5)
    return camera(im.convert('RGB'), tt, dur - dur * 0.55, 1.0, 1.04)


def s37(t, dur):  # toll
    im = bg()
    cols, total = 20, 100
    gx0, gy0, step = 160, 260, 44
    pf = ease_io(prog(t, 0.2, dur * 0.55))
    d = ImageDraw.Draw(im)
    for k in range(total):
        r, c = divmod(k, cols)
        x, y = gx0 + c * step, gy0 + r * step
        if k < int(total * pf):
            d.ellipse((x - 15, y - 15, x + 15, y + 15), fill=INK)
        else:
            d.ellipse((x - 15, y - 15, x + 15, y + 15), outline=(185, 172, 150), width=2)
    leg = text_img('كل نقطة = 5 آلاف قتيل', 'plex', 32, None, GREY)
    paste(im, leg, gx0 + leg.width / 2 - 10, gy0 + 5 * step + 30)
    put(im, stat_card('≈ 500 ألف', 'قتيل', INK, seed=271), 1500, 330, prog(t, dur * 0.3, 0.35), 'k1', t, -2)
    put(im, stat_card('1 – 2 مليون', 'ضحية بين قتيل وجريح', RED, w=600, seed=272), 1480, 660, prog(t, dur * 0.5, 0.35), 'k2', t, 1.5)
    tag(im, '+ ملايين النازحين', 600, 860, prog(t, dur * 0.72, 0.35), size=56, key='disp', t=t, seed=273, fill=CARD, bgc=RED, fname='cairo')
    src = text_img('المصادر: الموسوعة البريطانية، GlobalSecurity', 'plex', 28, None, GREY)
    paste(im, src, W - 60 - src.width / 2, H - 50)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s38(t, dur):  # POWs until 2003
    im = bg()
    x0, x1, y = 260, 1660, 600
    d = ImageDraw.Draw(im)
    d.line((x0, y, x1, y), fill=INK, width=6)
    for yr, lab in [(1988, '1988'), (2003, '2003')]:
        x = x1 - (yr - 1988) / 15 * (x1 - x0)
        d.line((x, y - 20, x, y + 20), fill=INK, width=5)
        paste(im, text_img(lab, 'oswald', 64, 700, INK), x, y + 70)
    p = ease_out(prog(t, 0.3, dur * 0.6))
    d.rounded_rectangle((x1 - (x1 - x0) * p, y - 60, x1, y - 22), 8, fill=RED)
    headline(im, 'ملفّ الأسرى', 260, prog(t, 0.0, 0.3), 110, prog(t, 0.4, 0.5))
    tag(im, 'آخر تبادل للأسرى: 2003', x0 + 120, y + 200, prog(t, dur * 0.7, 0.35), size=50, key='pow', t=t, seed=281,
        bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s39(t, dur):  # started & ended at the Shatt
    lon, lat, span, f = cam(t, dur, (46.5, 32.5, 14.0), (48.1, 30.35, 3.0), 0.1, dur * 0.8)
    im, v = mapf(lon, lat, span, 0.45, 0.45, cache=False)
    d = ImageDraw.Draw(im)
    stroke_path(d, [v.S(*q) for q in mapr.RIVERS['shatt']], 1.0, (40, 110, 190), 14)
    tag(im, 'بدأت هنا...', 520, 200, prog(t, dur * 0.3, 0.35), size=60, key='st', t=t, seed=291, fname='cairo')
    tag(im, '...وانتهت هنا', 1400, 880, prog(t, dur * 0.65, 0.35), size=60, key='en', t=t, seed=292, bgc=YELLOW, fname='cairo')
    return im.convert('RGB')


def s40(t, dur):
    im = bg()
    headline(im, '8 سنوات غيّرت جيلًا كاملًا...', 400, prog(t, 0.0, 0.3), 96, 0.0)
    headline(im, 'من دون أن تغيّر الخريطة', 620, prog(t, dur * 0.45, 0.3), 120, prog(t, dur * 0.55, 0.6))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def s41(t, dur, speech_end=4.0):  # end card
    im = bg()
    lbl(im, 'الفيديو القادم', (W / 2, 220), 70, GREY, prog(t, 0.0, 0.3), 800)
    headline(im, 'حرب توقّف فيها إطلاق النار... ولم تنتهِ', 400, prog(t, 0.3, 0.3), 84, prog(t, 0.8, 0.6))
    pb = prog(t, speech_end * 0.55, 0.35)
    if pb > 0:
        btn = Image.new('RGBA', (560, 150), (0, 0, 0, 0))
        ImageDraw.Draw(btn).rounded_rectangle((0, 0, 560, 150), 75, fill=RED)
        tx = text_img('اشترك', 'cairo', 76, 900, CARD)
        btn.alpha_composite(tx, (280 - tx.width // 2, 75 - tx.height // 2))
        paste(im, shadowed(btn, (6, 8), 8, 0.3), W / 2, 640, scale=pop(pb))
        lbl(im, 'معلومات الأرض', (W / 2, 800), 64, INK, clamp(pb * 2), 900)
    ps = prog(t, speech_end + 0.3, 0.8)
    if ps > 0:
        s = text_img('المصادر: الموسوعة البريطانية · HISTORY · GlobalSecurity · Encyclopaedia Iranica · قرار مجلس الأمن 598',
                     'plex', 28, None, GREY)
        paste(im, s, W / 2, H - 110, alpha=ps)
    out = camera(im.convert('RGB'), t, dur, 1.0, 1.03)
    fo = prog(t, dur - 0.8, 0.8)
    if fo > 0:
        out = Image.blend(out, Image.new('RGB', (W, H), SAND), fo)
    return out


SCENES = [s00, s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15, s16, s17, s18, s19, s20,
          s21, s22, s23, s24, s25, s26, s27, s28, s29, s30, s31, s32, s33, s34, s35, s36, s37, s38, s39, s40, s41]


# ---------------------------------------------------------------- extra segments
def x0(t, dur):  # mediation attempts
    im = bg()
    headline(im, 'وساطات دولية', 220, prog(t, 0.0, 0.3), 110, prog(t, 0.4, 0.5))
    put(im, stat_card('الأمم المتحدة', 'قرارات ونداءات لوقف القتال', INK, w=600, seed=301), 1350, 560, prog(t, dur * 0.15, 0.35), 'm1', t, -2)
    put(im, stat_card('أولوف بالمه', 'مبعوث أممي — زيارات عدّة للبلدين', INK, w=640, seed=302), 600, 560, prog(t, dur * 0.35, 0.35), 'm2', t, 2)
    pa = prog(t, dur * 0.75, 0.3)
    if pa > 0:
        st = text_img('بلا نتيجة', 'cairo', 120, 900, RED)
        stamp = Image.new('RGBA', (st.width + 80, st.height + 60), (0, 0, 0, 0))
        ImageDraw.Draw(stamp).rounded_rectangle((6, 6, stamp.width - 6, stamp.height - 6), 18, outline=RED, width=12)
        stamp.alpha_composite(st, (40, 30))
        paste(im, stamp, W / 2, 860, scale=1.5 - 0.5 * ease_out(pa), rot=-8, alpha=clamp(pa * 2))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def x1(t, dur):  # Iran Air 655 (non-graphic)
    im, v = mapf(56.0, 26.8, 4.5, 0.0, 0.45)
    d = ImageDraw.Draw(im)
    ba = v.S(56.37, 27.22)     # Bandar Abbas
    sp = v.S(56.05, 26.67)     # approx. location
    dubai = v.S(55.3, 25.25)
    dashed(d, [ba, dubai], prog(t, 0.2, 1.0), (90, 90, 90), 5, 40)
    p = clamp(prog(t, 0.5, dur * 0.35))
    x, y = _along([ba, sp], p)
    if p < 1:
        paste(im, icon_plane(80, 150), x, y)
    else:
        burst(d, sp[0], sp[1], 46, pop(prog(t, 0.5 + dur * 0.35, 0.3)), RED, seed=int(t * 8))
    paste(im, shadowed(icon_warship(170), (4, 6), 6, 0.3), sp[0] - 240, sp[1] + 170)
    tag(im, '3 يوليو 1988', 330, 130, prog(t, 0.0, 0.3), size=54, key='d3j', t=t, seed=311, fill=CARD, bgc=RED, fname='cairo')
    tag(im, 'رحلة إيران إير 655 — 290 قتيلًا', 1400, 130, prog(t, dur * 0.4, 0.35), size=48, key='ir655', t=t, seed=312,
        fill=CARD, bgc=INK, fname='cairo')
    tag(im, 'واشنطن: ظنّتها طائرة حربية', 1400, 960, prog(t, dur * 0.75, 0.35), size=46, key='us', t=t, seed=313,
        bgc=YELLOW, fname='cairo')
    lbl(im, 'بندر عباس', (ba[0] + 120, ba[1] - 30), 40, IR_D, 1, 800)
    lbl(im, 'دبي', (dubai[0] - 60, dubai[1] + 40), 40, GREY, 1, 800)
    return im.convert('RGB')


def x2(t, dur):  # arms to both sides; Iran-Contra
    im = bg()
    put(im, stat_card('إيران', '', IR_D, w=420, seed=321), 1500, 640, prog(t, 0.05, 0.3), 'si', t, -2)
    put(im, stat_card('العراق', '', IQ_D, w=420, seed=322), 420, 640, prog(t, 0.1, 0.3), 'sq', t, 2)
    tag(im, 'دول تبيع السلاح', W / 2, 260, prog(t, dur * 0.1, 0.35), size=62, key='sell', t=t, seed=323, fill=CARD, bgc=INK, fname='cairo')
    arrow(im, [(1080, 320), (1400, 520)], prog(t, dur * 0.2, 0.6), INK, 18, 40)
    arrow(im, [(840, 320), (520, 520)], prog(t, dur * 0.25, 0.6), INK, 18, 40)
    tag(im, 'فضيحة إيران كونترا', W / 2, 900, prog(t, dur * 0.6, 0.35), size=60, key='ic', t=t, seed=324, bgc=YELLOW, fname='cairo')
    lbl(im, 'أسلحة أمريكية لإيران سرًّا', (W / 2, 1000), 40, GREY, prog(t, dur * 0.7, 0.4), 800)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def x3(t, dur):  # Faw retaken in ~36h
    im = bg()
    put(im, date_card('17', 'أبريل 1988', 'معركة الفاو الثانية', IQ_D, seed=331), 1350, 520, prog(t, 0.05, 0.4), 'd17a', t, -2)
    put(im, stat_card('≈ 36 ساعة', 'لاستعادة الفاو', IQ_D, w=520, seed=332), 560, 420, prog(t, dur * 0.35, 0.35), 'h36', t, 2)
    tag(im, 'بعد أكثر من عامين بيد إيران', 560, 720, prog(t, dur * 0.6, 0.35), size=46, key='2y', t=t, seed=333, bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


def x4(t, dur):  # Aug 1990, Kuwait
    im, v = mapf(47.5, 30.0, 5.0, 0.45, 0.45)
    tag(im, 'أغسطس 1990', 330, 130, prog(t, 0.0, 0.3), size=56, key='a90', t=t, seed=341, fill=CARD, bgc=RED, fname='cairo')
    x, y = v.S(47.7, 29.3)
    arrow(im, [v.S(47.3, 30.3), (x, y)], prog(t, dur * 0.3, 0.8), IQ_D, 26, 52)
    lbl(im, 'الكويت', (x + 40, y + 70), 60, INK, 1, 900)
    tag(im, '...لكنّ تلك قصّة أخرى', 1450, 160, prog(t, dur * 0.6, 0.35), size=54, key='other', t=t, seed=342, bgc=YELLOW, fname='cairo')
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# (source, index) in final order: 'a' = main narration, 'b' = extra narration
ORDER = ([('a', i) for i in range(0, 20)] + [('b', 0)] + [('a', i) for i in range(20, 29)] + [('b', 1)] +
         [('a', i) for i in range(29, 32)] + [('b', 2)] + [('a', i) for i in range(32, 34)] + [('b', 3)] +
         [('a', i) for i in range(34, 37)] + [('b', 4)] + [('a', i) for i in range(37, 42)])
EXTRA = [x0, x1, x2, x3, x4]
FINAL_SCENES = [SCENES[i] if s == 'a' else EXTRA[i] for s, i in ORDER]
