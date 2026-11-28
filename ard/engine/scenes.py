"""Scenes for the Derna Vox-style sample. Each scene: f(t, dur) -> RGB Image."""
import math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import *
import mapdata


def bg():
    return paper_bg().copy().convert('RGBA')


def T(text, size, fname='cairo', weight=900, fill=INK):
    return text_img(text, fname, size, weight, fill)


def pop(p):
    """scale for a pop-in"""
    return back_out(clamp(p)) if p > 0 else 0


def tag(base, text, cx, cy, p, size=40, fill=INK, bgc=CARD, seed=0, rot=-1.5, key='t', t=0, fname='plexb'):
    if p <= 0:
        return
    im = shadowed(label(text, size, fname=fname, fill=fill, bg=bgc, seed=seed), off=(6, 9), blur=9, opacity=0.33)
    jx, jy, jr = jitter(key, t, 1.0)
    paste(base, im, cx + jx, cy + jy, scale=pop(p), rot=rot + jr)


def rain(base, t, n=60, seed=1, color=(47, 104, 168), alpha=110, area=(0, 0, W, H)):
    d = ImageDraw.Draw(base, 'RGBA')
    r = random.Random(seed)
    x0, y0, x1, y1 = area
    for i in range(n):
        sx, sy, sp = r.uniform(x0, x1), r.uniform(0, 1), r.uniform(0.9, 1.4)
        y = y0 + ((sy + t * sp * 0.9) % 1.0) * (y1 - y0 + 80) - 40
        x = sx - (y - y0) * 0.18
        d.line([(x, y), (x - 9, y + 46)], fill=color + (alpha,), width=4)


# ------------------------------------------------------------------ A: dateline
def scene_A(t, dur):
    im = bg()
    # date card
    p = prog(t, 0.15, 0.5)
    c = card(560, 470, seed=4)
    dd = ImageDraw.Draw(c)
    dd.rectangle((0, 0, 560, 92), fill=RED)
    hd = T('سبتمبر 2023', 54, 'cairo', 800, CARD)
    c.alpha_composite(hd, (280 - hd.width // 2, 46 - hd.height // 2))
    big = text_img('11', 'oswald', 250, 700, INK)
    c.alpha_composite(big, (280 - big.width // 2, 105))
    sub = T('الساعات الأولى من الفجر', 40, 'plexb', None, GREY)
    c.alpha_composite(sub, (280 - sub.width // 2, 385))
    jx, jy, jr = jitter('date', t, 1.2)
    paste(im, shadowed(c), 1180 + jx, 520 + jy, scale=pop(p), rot=-3 + jr)
    tag(im, 'درنة، ليبيا', 560, 330, prog(t, 0.9, 0.4), size=58, key='loc', t=t, rot=2, seed=3)
    # explosions
    pe = prog(t, dur * 0.62, 0.35)
    if pe > 0:
        d = ImageDraw.Draw(im)
        for k, (cx, cy, rr, col) in enumerate([(520, 650, 150, RED), (700, 760, 95, INK), (380, 800, 80, YELLOW)]):
            q = pop(prog(t, dur * 0.62 + k * 0.12, 0.3))
            if q <= 0:
                continue
            rnd = random.Random(k * 7 + int(t * 12))
            pts = []
            for i in range(26):
                a = i / 26 * 2 * math.pi
                rad = rr * q * (1.0 if i % 2 == 0 else 0.55) * rnd.uniform(0.9, 1.1)
                pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
            d.polygon(pts, fill=col)
        tag(im, 'دويّ انفجارات', 560, 690, pe, size=64, key='boom', t=t, rot=-4, fill=INK, bgc=YELLOW, seed=5)
    shake = 6 * (1 - pe) if 0 < pe < 1 else 0
    out = camera(im.convert('RGB'), t, dur, 1.0, 1.05)
    if shake:
        out = out.transform(out.size, Image.AFFINE, (1, 0, random.uniform(-shake, shake), 0, 1, random.uniform(-shake, shake)))
    return out


# ------------------------------------------------------------------ B: not bombs
def scene_B(t, dur):
    im = bg()
    l1 = T('لم تكن قنابل', 150)
    p1 = prog(t, 0.0, 0.25)
    jx, jy, jr = jitter('b1', t, 1.0)
    paste(im, l1, W / 2 + jx, 380 + jy, scale=pop(p1))
    # strike-through
    ps = prog(t, dur * 0.22, 0.35)
    if ps > 0:
        d = ImageDraw.Draw(im)
        x0, x1 = W / 2 + l1.width / 2 + 20, W / 2 - l1.width / 2 - 20
        stroke_path(d, [(x0, 400), (W / 2, 392), (x1, 384)], ease_out(ps), RED, 16)
    p2 = prog(t, dur * 0.45, 0.25)
    if p2 > 0:
        l2 = T('كانت سدودًا تنهار', 150)
        sc = pop(p2)
        tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        highlight_text(im, l2, W / 2, 660, prog(t, dur * 0.55, 0.45)) if sc >= 0.999 else paste(im, l2, W / 2, 660, scale=sc)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ C: map zoom to Derna
DERNA = (22.637, 32.767)
BAYDA = (21.741, 32.762)
BENGHAZI = (20.07, 32.12)


def _maplabel(base, text, pos, size=46, color=GREY, alpha=1.0, weight=700):
    if alpha <= 0:
        return
    ti = text_img(text, 'cairo', size, weight, color)
    paste(base, ti, pos[0], pos[1], alpha=alpha)


def pin(base, x, y, p, color=RED):
    if p <= 0:
        return
    q = ease_out(p)
    y0 = y - 120 * (1 - q)
    d = ImageDraw.Draw(base)
    r = 20
    d.ellipse((x - 14, y - 5, x + 14, y + 5), fill=(0, 0, 0, 60))
    d.polygon([(x, y), (x - r * 0.9, y0 - r * 1.6), (x + r * 0.9, y0 - r * 1.6)], fill=color)
    d.ellipse((x - r, y0 - r * 2.6, x + r, y0 - r * 0.6), fill=color)
    d.ellipse((x - 7, y0 - r * 1.6 - 7, x + 7, y0 - r * 1.6 + 7), fill=CARD)


def scene_C(t, dur):
    z = ease_io(prog(t, 0.2, dur * 0.62))
    lon = 18.0 + (DERNA[0] - 0.15 - 18.0) * z
    lat = 31.0 + (DERNA[1] - 0.6 - 31.0) * z
    span = math.exp(math.log(21) + (math.log(4.2) - math.log(21)) * z)
    fr, S, s = mapdata.view(lon, lat, span)
    im = fr.convert('RGBA')
    a_big = 1 - clamp(z * 2.2)
    _maplabel(im, 'ليبيا', S(17.5, 27.6), 130, INK, a_big, 900)
    _maplabel(im, 'مصر', S(28.5, 27.5), 70, GREY, a_big)
    _maplabel(im, 'تونس', S(9.6, 33.6), 60, GREY, a_big)
    _maplabel(im, 'البحر المتوسط', S(18.5, 35.0), 64 if z < 0.5 else 56, (70, 100, 110), 1.0)
    x, y = S(*DERNA)
    pin(im, x, y, prog(t, dur * 0.45, 0.4))
    if t > dur * 0.5:
        tag(im, 'درنة', x + 150, y - 70, prog(t, dur * 0.5, 0.3), size=60, key='dn', t=t, seed=2, fname='cairo')
    tag(im, '≈ 90 ألف نسمة', x + 190, y + 40, prog(t, dur * 0.62, 0.3), size=40, key='pop', t=t, seed=6, rot=1.5)
    # wadi inland from the city
    pw = prog(t, dur * 0.76, 0.6)
    if pw > 0:
        d = ImageDraw.Draw(im)
        path = [(22.637, 32.765), (22.630, 32.745), (22.615, 32.725), (22.600, 32.700), (22.585, 32.672),
                (22.575, 32.650), (22.560, 32.625), (22.548, 32.595)]
        stroke_path(d, [S(*q) for q in path], ease_out(pw), BLUE, 9)
        xb, yb = S(22.56, 32.62)
        tag(im, 'وادي درنة', xb - 170, yb + 10, prog(t, dur * 0.82, 0.3), size=38, key='wd', t=t, seed=8, fill=BLUE)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.02)


# ------------------------------------------------------------------ D: storm track
TRACK = [(21.8, 39.2), (20.9, 37.6), (19.6, 35.8), (19.4, 34.0), (20.0, 32.5), (21.3, 32.5),
         (22.6, 32.5), (24.0, 31.6), (25.5, 30.8)]


def spiral(size, rot):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for arm in range(3):
        pts = []
        for i in range(60):
            f = i / 59
            a = rot + arm * 2 * math.pi / 3 + f * 4.2
            r = c * (0.12 + 0.85 * f)
            pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
        d.line(pts, fill=(60, 70, 80, 230), width=max(4, size // 24), joint='curve')
    d.ellipse((c - size * 0.09, c - size * 0.09, c + size * 0.09, c + size * 0.09), fill=CARD + (255,))
    return im


def _along(path, p):
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    tgt, acc = sum(seg) * p, 0
    for i, s in enumerate(seg):
        if acc + s >= tgt:
            f = (tgt - acc) / s
            return (path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f)
        acc += s
    return path[-1]


def scene_D(t, dur):
    fr, S, s = mapdata.view(21.0, 35.0, 17.5 - 1.0 * prog(t, 0, dur))
    im = fr.convert('RGBA')
    _maplabel(im, 'اليونان', S(22.3, 39.9), 52, GREY)
    _maplabel(im, 'ليبيا', S(19.0, 30.2), 90, INK, 1.0, 900)
    _maplabel(im, 'البحر المتوسط', S(17.2, 36.3), 54, (70, 100, 110))
    pts = [S(*q) for q in TRACK]
    p = ease_io(prog(t, 0.2, dur * 0.85))
    d = ImageDraw.Draw(im)
    # dashed trail
    n = 70
    for i in range(int(n * p)):
        if i % 2 == 0:
            a, b = _along(pts, i / n), _along(pts, (i + 1) / n)
            d.line([a, b], fill=RED, width=8)
    x, y = _along(pts, p)
    paste(im, shadowed(spiral(190, -t * 3.5), off=(5, 7), blur=8, opacity=0.3), x, y)
    tag(im, 'العاصفة دانيال', x - 290, y - 110, prog(t, 0.3, 0.35), size=48, key='dan', t=t, seed=9, fname='cairo')
    xd, yd = S(*DERNA)
    pin(im, xd, yd, 1.0)
    cap = text_img('المسار تقريبي', 'plex', 30, None, GREY)
    paste(im, cap, 140, H - 70, alpha=0.9)
    return im.convert('RGB')


# ------------------------------------------------------------------ E: rainfall bars
def scene_E(t, dur):
    im = bg()
    rain(im, t, 70, area=(0, 0, W, H), alpha=70)
    title = T('مدينة البيضاء، شرق ليبيا', 66)
    paste(im, title, W - 140 - title.width / 2, 120, scale=pop(prog(t, 0.0, 0.3)))
    base_y, x_a, x_b, bw = 900, 1180, 700, 260
    unit = 560 / 414
    d = ImageDraw.Draw(im)
    d.line((300, base_y, 1620, base_y), fill=INK, width=5)
    pa = ease_out(prog(t, dur * 0.18, 1.1))
    pb = ease_out(prog(t, dur * 0.62, 1.0))
    for (x, val, p, col, lab1, lab2, key) in [
            (x_a, 414.1, pa, BLUE, '414 ملم', 'خلال 24 ساعة فقط', 'ba'),
            (x_b, 300, pb, (150, 140, 124), '≈ 300 ملم', 'المعدّل السنوي المعتاد', 'bb')]:
        if p <= 0:
            continue
        h = val * unit * p
        bar = card(bw, max(2, int(h)), seed=hash(key) % 50)
        tint = Image.new('RGBA', bar.size, col + (255,))
        bar = Image.alpha_composite(bar, Image.new('RGBA', bar.size, (0, 0, 0, 0)))
        bar = Image.composite(tint, bar, bar.getchannel('A'))
        jx, jy, jr = jitter(key, t, 0.8)
        im.alpha_composite(shadowed(bar, (8, 10), 10, 0.3), (int(x - bw / 2 - 46 + jx), int(base_y - h - 46)))
        num = text_img(lab1, 'cairo', 76, 900, INK)
        paste(im, num, x + jx, base_y - h - 60, alpha=clamp(p * 3 - 1.2))
        sub = text_img(lab2, 'plexb', 36, None, GREY)
        paste(im, sub, x, base_y + 45, alpha=clamp(p * 3 - 0.5))
    src = text_img('المصادر: المنظمة العالمية للأرصاد الجوية، Copernicus', 'plex', 26, None, GREY)
    paste(im, src, 160 + src.width / 2, H - 50)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ F/G: valley & dams schematic
WADI = [(1180, -20), (1150, 90), (1210, 190), (1120, 290), (1040, 360), (1060, 450), (990, 540),
        (930, 610), (960, 700), (920, 790), (900, 900), (905, 1100)]
DAM1_P, DAM2_P = 0.33, 0.74   # positions along wadi
CITY_Y = (800, 960)


def _poly_pt(p):
    return _along(WADI, p)


def _tangent(p):
    a, b = _along(WADI, max(0, p - 0.01)), _along(WADI, min(1, p + 0.01))
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    return ang


@functools.lru_cache(None)
def valley_base():
    im = Image.new('RGBA', (W, H), (228, 218, 196, 255))
    d = ImageDraw.Draw(im)
    r = random.Random(4)
    # hills (hatched triangles)
    for _ in range(46):
        x, y = r.uniform(0, W), r.uniform(-20, 720)
        if abs(x - _along(WADI, clamp((y + 20) / 1120))[0]) < 150:
            continue
        s = r.uniform(50, 110)
        col = (192, 178, 146)
        d.polygon([(x - s, y + s * 0.6), (x, y - s * 0.5), (x + s, y + s * 0.6)], fill=col)
        for k in range(4):
            xx = x + s * (0.1 + 0.2 * k)
            d.line([(xx, y - s * 0.4 + s * 0.2 * k), (xx - s * 0.15, y + s * 0.55)], fill=(160, 146, 116), width=3)
    # sea band
    d.rectangle((0, 965, W, H), fill=SEA + (255,))
    for k in range(6):
        y = 995 + k * 16
        d.line([(x, y + 5 * math.sin(x / 40 + k)) for x in range(0, W, 20)], fill=(150, 175, 175), width=3)
    d.line((0, 965, W, 965), fill=INK, width=5)
    # wadi bed
    d.line(WADI, fill=(170, 150, 112), width=36, joint='curve')
    d.line(WADI, fill=(150, 128, 92), width=6, joint='curve')
    return im


def city_blocks():
    r = random.Random(12)
    blocks = []
    for _ in range(95):
        x = r.uniform(560, 1360)
        y = r.uniform(CITY_Y[0], CITY_Y[1] - 10)
        wx = _along(WADI, clamp((y + 20) / 1120))[0]
        if abs(x - wx) < 34:
            continue
        w, h = r.uniform(26, 52), r.uniform(20, 40)
        blocks.append((x, y, w, h, abs(x - wx)))
    return blocks


BLOCKS = city_blocks()


def dam_img(width=150, broken=0.0):
    im = Image.new('RGBA', (width + 40, 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if broken <= 0:
        d.rectangle((20, 14, 20 + width, 46), fill=(70, 66, 60))
        d.rectangle((20, 14, 20 + width, 22), fill=(110, 104, 96))
    else:
        g = 30 * broken
        d.rectangle((20, 14, 20 + width / 2 - g, 46), fill=(70, 66, 60))
        d.rectangle((20 + width / 2 + g, 14, 20 + width, 46), fill=(70, 66, 60))
    return im


def scene_valley(t, dur, collapse=False):
    im = valley_base().copy()
    d = ImageDraw.Draw(im)
    if not collapse:
        pw = 1.0
        pc = prog(t, 0.2, 1.2)
        pd1, pd2 = prog(t, dur * 0.12, 0.4), prog(t, dur * 0.3, 0.4)
        res = ease_out(prog(t, dur * 0.2, 1.2))
        flood = 0.0
        br1 = br2 = 0.0
    else:
        pc = pd1 = pd2 = res = 1.0
        br1 = ease_out(prog(t, dur * 0.06, 0.5))
        br2 = ease_out(prog(t, dur * 0.34, 0.5))
        flood = ease_io(prog(t, dur * 0.08, dur * 0.55))
    # reservoirs behind dams (upstream)
    for (dp, size, rp) in [(DAM1_P, 95, res * (1 - 0.8 * br1)), (DAM2_P, 45, res * (1 - 0.8 * br2))]:
        if rp <= 0:
            continue
        pts = [_along(WADI, dp - k * 0.004) for k in range(1, 30)]
        for i, q in enumerate(pts):
            rad = size * rp * (1 - i / 34)
            d.ellipse((q[0] - rad, q[1] - rad * 0.7, q[0] + rad, q[1] + rad * 0.7), fill=BLUE)
    # flood water down the valley
    if flood > 0:
        start = DAM1_P
        end = start + (1.0 - start) * flood
        steps = 80
        for i in range(steps + 1):
            p = start + (end - start) * i / steps
            q = _along(WADI, p)
            wdt = 34 + 60 * clamp((p - 0.62) / 0.3)
            d.ellipse((q[0] - wdt, q[1] - wdt * 0.6, q[0] + wdt, q[1] + wdt * 0.6), fill=BLUE)
    # city
    sweep_y = _along(WADI, DAM1_P + (1 - DAM1_P) * flood)[1] if flood > 0 else -1
    for i, (x, y, w, h, dist) in enumerate(BLOCKS):
        q = prog(pc, i / len(BLOCKS) * 0.7, 0.3)
        if q <= 0:
            continue
        gone = flood > 0 and y < sweep_y + 40 and dist < 70 + 120 * clamp((flood - 0.75) / 0.25)
        if gone:
            d.rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), outline=(90, 120, 150), width=2)
            continue
        s = pop(q)
        d.rectangle((x - w / 2 * s, y - h / 2 * s, x + w / 2 * s, y + h / 2 * s), fill=(245, 240, 228), outline=INK, width=3)
    # dams
    for (dp, pdm, br, wd) in [(DAM1_P, pd1, br1, 170), (DAM2_P, pd2, br2, 120)]:
        if pdm <= 0:
            continue
        x, y = _along(WADI, dp)
        ang = math.degrees(_tangent(dp))
        di = dam_img(wd, br)
        jx, jy, jr = jitter(('dam', dp), t, 0.8)
        paste(im, di, x + jx, y + jy, scale=pop(pdm), rot=-(ang + 90) + jr)
        if br > 0:
            stroke_path(d, [(x - 40, y - 30), (x - 10, y - 5), (x - 25, y + 10), (x + 15, y + 35)], br, RED, 7)
    # labels
    x1, y1 = _along(WADI, DAM1_P)
    x2, y2 = _along(WADI, DAM2_P)
    if not collapse:
        tag(im, 'السدّ الأكبر: ≈ 22.5 مليون م³', x1 + 380, y1 - 10, prog(t, dur * 0.48, 0.35), size=40, key='l1', t=t, seed=21, fname='plexb')
        tag(im, 'السدّ الأصغر: ≈ 1.5 مليون م³', x2 + 390, y2 - 30, prog(t, dur * 0.62, 0.35), size=36, key='l2', t=t, seed=22, rot=1.2)
        tag(im, 'بُنيا في السبعينيات', x1 - 340, y1 + 40, prog(t, dur * 0.2, 0.35), size=40, key='l3', t=t, seed=23, bgc=YELLOW, rot=2.5)
        # distance bracket
        pb = prog(t, dur * 0.75, 0.4)
        if pb > 0:
            bx = 420
            stroke_path(d, [(bx, y1), (bx, y1 + (CITY_Y[0] - y1) * ease_out(pb))], pb, INK, 4)
            d.line((bx - 18, y1, bx + 18, y1), fill=INK, width=4)
            if pb >= 1:
                d.line((bx - 18, CITY_Y[0], bx + 18, CITY_Y[0]), fill=INK, width=4)
            tag(im, '≈ 13 كم', bx - 115, (y1 + CITY_Y[0]) / 2, pb, size=40, key='km', t=t, seed=24, rot=0)
    else:
        tag(im, '≈ 30 مليون م³ من الماء', 520, 520, prog(t, dur * 0.5, 0.4), size=52, key='vol', t=t,
            seed=25, bgc=(205, 222, 240), fname='cairo', rot=-2)
    tag(im, 'درنة', 1500, 880, 1.0, size=50, key='city', t=t, seed=26, fname='cairo')
    cap = text_img('رسم توضيحي، ليس بمقياس رسم', 'plex', 28, None, GREY)
    paste(im, cap, 90 + cap.width / 2, 95)
    out = im.convert('RGB')
    if collapse:
        sh = 0
        for b0 in (dur * 0.06, dur * 0.34):
            if b0 < t < b0 + 0.4:
                sh = 9 * (1 - (t - b0) / 0.4)
        out = camera(out, t, dur, 1.03, 1.08, 0.55, 0.6)
        if sh:
            out = out.transform(out.size, Image.AFFINE, (1, 0, random.uniform(-sh, sh), 0, 1, random.uniform(-sh, sh)))
        return out
    return camera(out, t, dur, 1.0, 1.03, 0.55, 0.55)


def scene_F(t, dur):
    return scene_valley(t, dur, False)


def scene_G(t, dur):
    return scene_valley(t, dur, True)


# ------------------------------------------------------------------ H/I: warnings
def doc_card(year, lines, hl_idx, w=760, seed=31):
    """Returns (card RGBA, highlight box of line hl_idx in card coords)."""
    h = 150 + 92 * len(lines) + 40
    c = card(w, h, seed=seed)
    d = ImageDraw.Draw(c)
    yi = text_img(year, 'oswald', 96, 700, RED)
    c.alpha_composite(yi, (w - yi.width - 40, 20))
    d.line((40, 140, w - 40, 140), fill=INK, width=3)
    boxes = []
    y = 165
    for i, ln in enumerate(lines):
        ti = text_img(ln, 'plexb', 44, None, INK)
        boxes.append((w - 46 - ti.width, y, w - 46, y + ti.height))
        c.alpha_composite(ti, (w - 46 - ti.width, y))
        y += 92
    return c, boxes


def scene_H(t, dur, with_second=False, t2=0.0, dur2=1.0):
    im = bg()
    c1, b1 = doc_card('2022', ['دراسة هندسية تحذّر:', 'أيّ فيضان كبير', 'ستكون عواقبه كارثية', 'على الوادي والمدينة'], 2)
    p1 = 1.0 if with_second else prog(t, 0.05, 0.45)
    hp = 1.0 if with_second else prog(t, dur * 0.62, 0.6)
    # highlight drawn into the card
    cc = c1.copy()
    if hp > 0:
        x0, y0, x1, y1 = b1[2]
        ww = (x1 - x0 + 20) * ease_out(hp)
        multiply_rect(cc, (x1 + 10 - ww, y0 + 8, x1 + 10, y1 - 4), YELLOW)
        cc.alpha_composite(text_img('ستكون عواقبه كارثية', 'plexb', 44, None, INK), (x1 - text_img('ستكون عواقبه كارثية', 'plexb', 44, None, INK).width, y0))
    cx = 1230 if not with_second else 1230 + 60 * ease_out(prog(t2, 0, 0.5))
    jx, jy, jr = jitter('d1', t + t2, 1.0)
    paste(im, shadowed(cc), cx + jx, 520 + jy, scale=pop(p1), rot=2.5 + jr,
          alpha=1.0 if not with_second else 1 - 0.35 * prog(t2, 0, 0.5))
    if with_second:
        c2, b2 = doc_card('1998', ['دراسة حكومية تكشف:', 'تشقّقات في السدّين'], 1, w=700, seed=33)
        p2 = prog(t2, 0.1, 0.45)
        jx, jy, jr = jitter('d2', t2, 1.0)
        c2s = c2.copy()
        pm = prog(t2, dur2 * 0.45, 0.7)
        if pm > 0:
            dd = ImageDraw.Draw(c2s)
            x0, y0, x1, y1 = b2[1]
            seg_w = text_img('تشقّقات', 'plexb', 44, None, INK).width
            cx2 = x1 - seg_w / 2 + 8
            stroke_path(dd, marker_ellipse(cx2, (y0 + y1) / 2 + 4, seg_w / 2 + 22, 40), pm, RED, 7)
        paste(im, shadowed(c2s), 620 + jx, 560 + jy, scale=pop(p2), rot=-3 + jr)
    tag(im, 'تحذيرات سابقة', 300 if not with_second else 330, 170, prog(t + t2, 0.3, 0.35), size=56,
        key='warn', t=t + t2, seed=34, bgc=YELLOW, fname='cairo', rot=-2)
    return camera(im.convert('RGB'), t + t2, dur + dur2, 1.0, 1.04)


def scene_I(t, dur):
    return scene_H(99, 99, True, t, dur)


# ------------------------------------------------------------------ J: toll
def scene_J(t, dur):
    im = bg()
    cols, rows = 33, 12
    total = 396
    gx0, gy0, step = 110, 250, 30
    pf = ease_io(prog(t, 0.3, dur * 0.55))
    d = ImageDraw.Draw(im)
    nfill = int(total * pf)
    k = 0
    for r in range(rows):
        for c in range(cols):
            if k >= total:
                break
            x = gx0 + c * step
            y = gy0 + r * step
            if k < nfill:
                d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=INK)
            else:
                d.ellipse((x - 10, y - 10, x + 10, y + 10), outline=(190, 180, 162), width=2)
            k += 1
    leg = text_img('كل نقطة = 10 أشخاص', 'plex', 32, None, GREY)
    paste(im, leg, gx0 + leg.width / 2 - 10, gy0 + rows * step + 40)
    num = int(3958 * pf)
    nt = text_img(f'{num:,}', 'oswald', 210, 700, INK)
    paste(im, nt, 1490, 400)
    sub = T('وفاة موثّقة', 70)
    paste(im, sub, 1490, 560, alpha=clamp(pf * 4))
    src = text_img('بحسب منظمة الصحة العالمية', 'plexb', 36, None, GREY)
    paste(im, src, 1490, 640, alpha=clamp(pf * 4))
    tag(im, '+ آلاف المفقودين', 1490, 800, prog(t, dur * 0.72, 0.35), size=60, key='miss', t=t,
        seed=41, fill=CARD, bgc=RED, fname='cairo', rot=-2)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ K: x50
def scene_K(t, dur):
    im = bg()
    rain(im, t, 50, seed=3, alpha=60)
    top = T('التغيّر المناخي جعل أمطارًا كهذه', 64)
    paste(im, top, W / 2, 230, scale=pop(prog(t, 0.0, 0.35)))
    p = prog(t, dur * 0.35, 0.4)
    if p > 0:
        x = text_img('×50', 'oswald', 330, 700, RED)
        pre = T('حتى', 80, weight=800)
        jx, jy, jr = jitter('x50', t, 1.2)
        paste(im, x, W / 2 - 60 + jx, 560 + jy, scale=pop(p), rot=-3 + jr)
        paste(im, pre, W / 2 + 250, 560, alpha=clamp(p * 2))
    bot = T('أكثر احتمالًا', 72, weight=800)
    pb = prog(t, dur * 0.55, 0.3)
    if pb > 0:
        highlight_text(im, bot, W / 2, 830, prog(t, dur * 0.6, 0.5))
    src = text_img('المصدر: World Weather Attribution (2023)', 'plex', 28, None, GREY)
    paste(im, src, W - 60 - src.width / 2, H - 50)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


# ------------------------------------------------------------------ L: equation
def scene_L(t, dur):
    im = bg()
    items = [('العاصفة', CARD, INK, 0.0), ('الصراع', CARD, INK, 0.22), ('إهمال صيانة السدود', CARD, INK, 0.38)]
    xs = [1620, 1180, 640]
    d = ImageDraw.Draw(im)
    for i, ((txt, bgc, fg, at), x) in enumerate(zip(items, xs)):
        p = prog(t, dur * at, 0.35)
        tag(im, txt, x, 430, p, size=62, key=('eq', i), t=t, seed=50 + i, fill=fg, bgc=bgc, fname='cairo',
            rot=[-2, 1.5, -1][i])
        if i < 2 and prog(t, dur * items[i + 1][3], 0.2) > 0:
            plus = text_img('+', 'oswald', 120, 700, RED)
            paste(im, plus, (x + xs[i + 1]) / 2 + (40 if i == 1 else 0), 430, scale=pop(prog(t, dur * items[i + 1][3], 0.25)))
    pe = prog(t, dur * 0.7, 0.4)
    if pe > 0:
        eq = text_img('=', 'oswald', 140, 700, INK)
        paste(im, eq, W / 2, 640, scale=pop(pe))
        tag(im, 'كارثة إنسانية', W / 2, 820, prog(t, dur * 0.74, 0.4), size=92, key='res', t=t, seed=60,
            fill=CARD, bgc=RED, fname='cairo', rot=-1.5)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ M: ending
def scene_M(t, dur, speech_end=3.0):
    im = bg()
    l1 = T('المطر...', 120, weight=900)
    l2 = T('لم يقتل درنة وحده', 140, weight=900)
    paste(im, l1, W / 2 + 330, 360, scale=pop(prog(t, 0.0, 0.3)))
    p2 = prog(t, speech_end * 0.35, 0.3)
    if p2 > 0:
        if p2 < 1:
            paste(im, l2, W / 2, 560, scale=pop(p2))
        else:
            highlight_text(im, l2, W / 2, 560, prog(t, speech_end * 0.55, 0.6))
    ps = prog(t, speech_end + 0.3, 0.8)
    if ps > 0:
        s1 = text_img('المصادر: المنظمة العالمية للأرصاد الجوية · منظمة الصحة العالمية / أوتشا · World Weather Attribution · أسوشيتد برس',
                      'plex', 30, None, GREY)
        paste(im, s1, W / 2, H - 120, alpha=ps)
    out = camera(im.convert('RGB'), t, dur, 1.0, 1.03)
    fo = prog(t, dur - 0.8, 0.8)
    if fo > 0:
        out = Image.blend(out, paper_bg(), fo)
    return out


SCENES = [scene_A, scene_B, scene_C, scene_D, scene_E, scene_F, scene_G, scene_H, scene_I, scene_J, scene_K,
          scene_L, scene_M]
