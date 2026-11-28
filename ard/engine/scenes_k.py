"""Korean War — Vox-style scenes. Each scene f(t, dur) -> RGB."""
import sys, math, random
sys.path.insert(0, '/home/claude/vox')
import numpy as np
from PIL import Image, ImageDraw
from engine import *
from scenes import bg, T, pop, tag, pin, _along, text_img as _ti
import mapk
from mapk import NORTH, SOUTH

SEOUL = (126.98, 37.57)
BUSAN = (129.04, 35.18)
INCHEON = (126.63, 37.46)
PYONGYANG = (125.75, 39.03)
PANMUNJOM = (126.68, 37.956)
NK_COL = (196, 52, 40)
SK_COL = (40, 92, 160)


def lbl(base, text, pos, size=46, color=GREY, alpha=1.0, weight=700):
    if alpha <= 0:
        return
    paste(base, text_img(text, 'cairo', size, weight, color), pos[0], pos[1], alpha=alpha)


def dashed(d, pts, p, color=RED, width=7, n=80):
    if p <= 0:
        return
    for i in range(int(n * p)):
        if i % 2 == 0:
            a, b = _along(pts, i / n), _along(pts, (i + 1) / n)
            d.line([a, b], fill=color, width=width)


def arrow(base, pts, p, color, width=34, head=70):
    """Thick map arrow that grows along pts."""
    if p <= 0:
        return
    p = ease_out(p)
    d = ImageDraw.Draw(base, 'RGBA')
    n = 40
    path = [_along(pts, p * i / n) for i in range(n + 1)]
    tip = path[-1]
    prev = _along(pts, max(0, p - 0.02))
    ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    # shorten shaft so head sits on the tip
    shaft = [q for q in path if math.dist(q, tip) > head * 0.6] or path[:1]
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    for dx, dy, col in [(8, 10, (0, 0, 0, 70)), (0, 0, color + (255,))]:
        q = [(x + dx, y + dy) for x, y in shaft]
        if len(q) > 1:
            ds.line(q, fill=col, width=width, joint='curve')
        tx, ty = tip[0] + dx, tip[1] + dy
        hx = [(tx, ty), (tx - head * math.cos(ang) + head * 0.6 * math.sin(ang), ty - head * math.sin(ang) - head * 0.6 * math.cos(ang)),
              (tx - head * math.cos(ang) - head * 0.6 * math.sin(ang), ty - head * math.sin(ang) + head * 0.6 * math.cos(ang))]
        ds.polygon(hx, fill=col)
    base.alpha_composite(sh)


def korea_frame(t, center=(127.6, 37.9), span=9.0, front=None, alpha=0.55, neutral=False):
    fr, S, mask, inv = mapk.view(center[0], center[1], span)
    if front is not None and not neutral:
        fr = mapk.overlay(fr, mask, inv, front, alpha)
    return fr.convert('RGBA'), S


def side_labels(im, S, a=1.0, n_pos=(127.0, 40.3), s_pos=(128.0, 36.4)):
    lbl(im, 'كوريا الشمالية', S(*n_pos), 58, NK_COL, a, 900)
    lbl(im, 'كوريا الجنوبية', S(*s_pos), 58, SK_COL, a, 900)


def datetag(im, text, p, t, key='date', x=1640, y=120):
    tag(im, text, x, y, p, size=54, key=key, t=t, seed=77, bgc=YELLOW, fname='cairo', rot=-2)


# ------------------------------------------------------------------ 0: invasion
def s0(t, dur):
    p38 = prog(t, 0.3, 1.4)
    split = prog(t, 1.6, 0.8)
    im, S = korea_frame(t, front=mapk.FRONT['p38'], alpha=0.55 * ease_out(split))
    d = ImageDraw.Draw(im)
    dashed(d, [S(124.0, 38.0), S(131.0, 38.0)], p38, INK, 8)
    tag(im, 'خط العرض 38', S(124.6, 38.0)[0] + 40, S(124.6, 38.0)[1] - 60, prog(t, 1.2, 0.35), size=44, key='l38', t=t, seed=3)
    side_labels(im, S, ease_out(split), (127.4, 39.62), (128.0, 36.4))
    for k, (a, b) in enumerate([((126.0, 38.75), (126.6, 37.2)), ((127.3, 38.85), (127.4, 37.3)), ((128.3, 38.85), (128.6, 37.5))]):
        pa = prog(t, dur * 0.55 + k * 0.25, 1.2)
        mid = ((a[0] + b[0]) / 2 + 0.15, (a[1] + b[1]) / 2)
        arrow(im, [S(*a), S(*mid), S(*b)], pa, NK_COL, 30, 62)
    datetag(im, '25 يونيو 1950', prog(t, 0.2, 0.35), t)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


# ------------------------------------------------------------------ 1: why two Koreas
def s1(t, dur):
    im = bg()
    q = T('لماذا كانت هناك', 110)
    paste(im, q, W / 2, 400, scale=pop(prog(t, 0.0, 0.3)))
    k = T('كوريّتان؟', 190)
    pk = prog(t, dur * 0.35, 0.3)
    if pk > 0:
        if pk < 1:
            paste(im, k, W / 2, 620, scale=pop(pk))
        else:
            highlight_text(im, k, W / 2, 620, prog(t, dur * 0.45, 0.5))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04)


# ------------------------------------------------------------------ 2: 1945 division
def s2(t, dur):
    split = prog(t, dur * 0.45, 0.8)
    center, span = (128.4, 38.3), 19.0
    im, S = korea_frame(t, center, span, mapk.FRONT['p38'], 0.45 * ease_out(split))
    d = ImageDraw.Draw(im)
    lbl(im, 'الصين', S(121.0, 41.5), 70, GREY, 1, 800)
    lbl(im, 'اليابان', S(134.6, 36.9), 64, GREY, 1, 800)
    lbl(im, 'الاتحاد السوفييتي', S(132.8, 44.6), 54, GREY, 1, 800)
    lbl(im, 'كوريا', S(127.6, 39.6), 64, INK, 1 - split, 900)
    datetag(im, '1945', prog(t, 0.1, 0.35), t)
    tag(im, 'هزيمة اليابان', S(133.5, 36.1)[0], S(134.4, 36.1)[1], prog(t, dur * 0.12, 0.35), size=42,
        key='jp', t=t, seed=5, fill=CARD, bgc=INK, fname='cairo', rot=2)
    dashed(d, [S(124.0, 38.0), S(130.6, 38.0)], prog(t, dur * 0.35, 1.0), INK, 7)
    tag(im, 'تقسيم «مؤقت»', S(124.3, 38.0)[0] - 150, S(124.3, 38.0)[1], prog(t, dur * 0.45, 0.35), size=46,
        key='tmp', t=t, seed=6, bgc=YELLOW, fname='cairo')
    arrow(im, [S(131.6, 43.4), S(130.0, 42.0), S(128.2, 40.4)], prog(t, dur * 0.55, 1.0), NK_COL, 26, 56)
    tag(im, 'السوفييت', S(130.2, 41.0)[0] + 150, S(130.2, 41.0)[1], prog(t, dur * 0.6, 0.3), size=44, key='sov', t=t, seed=7)
    arrow(im, [S(132.6, 37.6), S(130.6, 36.9), S(128.6, 36.7)], prog(t, dur * 0.72, 1.0), SK_COL, 26, 56)
    tag(im, 'الأمريكيون', S(131.6, 37.6)[0] + 40, S(131.6, 37.6)[1] - 70, prog(t, dur * 0.78, 0.3), size=44, key='us', t=t, seed=8)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 3: 1948 two states
def state_card(title, sub, date, col, w=640, seed=0):
    c = card(w, 300, seed=seed)
    dd = ImageDraw.Draw(c)
    dd.rectangle((0, 0, w, 16), fill=col)
    a = text_img(title, 'cairo', 56, 900, col)
    c.alpha_composite(a, (w - 36 - a.width, 40))
    b = text_img(sub, 'plexb', 36, None, INK)
    c.alpha_composite(b, (w - 36 - b.width, 140))
    e = text_img(date, 'plexb', 34, None, GREY)
    c.alpha_composite(e, (w - 36 - e.width, 215))
    return c


def s3(t, dur):
    im, S = korea_frame(t, (128.6, 38.3), 10.5, mapk.FRONT['p38'], 0.55)
    d = ImageDraw.Draw(im)
    dashed(d, [S(124.0, 38.0), S(131.0, 38.0)], 1.0, INK, 8)
    side_labels(im, S, 1.0, (126.9, 39.6), (127.4, 36.9))
    c1 = state_card('الشمال', 'جمهورية كوريا الديمقراطية الشعبية', 'سبتمبر 1948', NK_COL, seed=11)
    c2 = state_card('الجنوب', 'جمهورية كوريا', 'أغسطس 1948', SK_COL, seed=12)
    j1 = jitter('c1', t, 1.0)
    j2 = jitter('c2', t, 1.0)
    paste(im, shadowed(c1), 1500 + j1[0], 330 + j1[1], scale=pop(prog(t, dur * 0.2, 0.4)), rot=-2 + j1[2])
    paste(im, shadowed(c2), 1500 + j2[0], 740 + j2[1], scale=pop(prog(t, dur * 0.32, 0.4)), rot=1.5 + j2[2])
    tag(im, 'كلٌّ منهما: «أنا كوريا كلّها»', 520, 1000, prog(t, dur * 0.58, 0.4), size=50, key='claim', t=t,
        seed=13, bgc=YELLOW, fname='cairo', rot=-1.5)
    datetag(im, '1948', prog(t, 0.05, 0.3), t, x=300, y=120)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 4: to Pusan
def s4(t, dur):
    f = ease_io(prog(t, 0.4, dur * 0.8))
    front = mapk.front_mix('p38', 'pusan', f)
    im, S = korea_frame(t, (127.7, 36.5), 7.5, front, 0.58)
    x, y = S(*SEOUL)
    pin(im, x, y, prog(t, 0.3, 0.4), INK)
    tag(im, 'سقوط سيول خلال 3 أيام', x + 260, y - 60, prog(t, dur * 0.12, 0.35), size=46, key='seoul', t=t, seed=21,
        fill=CARD, bgc=NK_COL, fname='cairo')
    xb, yb = S(*BUSAN)
    pin(im, xb, yb, prog(t, dur * 0.62, 0.4), SK_COL)
    tag(im, 'بوسان', xb + 130, yb + 40, prog(t, dur * 0.66, 0.35), size=50, key='busan', t=t, seed=22, fname='cairo')
    tag(im, 'آخر جيب للجنوب', xb - 40, yb - 260, prog(t, dur * 0.82, 0.35), size=44, key='pocket', t=t, seed=23,
        bgc=YELLOW, fname='cairo', rot=2)
    datetag(im, 'صيف 1950', prog(t, 0.0, 0.3), t, x=300, y=120)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 5: Incheon
def s5(t, dur):
    f = ease_io(prog(t, dur * 0.55, dur * 0.42))
    front = mapk.front_mix('pusan', 'p38', f)
    im, S = korea_frame(t, (127.4, 37.1), 7.5, front, 0.58)
    tag(im, 'قوات الأمم المتحدة بقيادة أمريكية', 1400, 150, prog(t, 0.2, 0.4), size=46, key='un', t=t, seed=31,
        fill=CARD, bgc=SK_COL, fname='cairo')
    xi, yi = S(*INCHEON)
    arrow(im, [S(123.9, 35.9), S(124.9, 36.9), S(125.9, 37.35), (xi - 18, yi)], prog(t, dur * 0.28, 1.1), SK_COL, 34, 70)
    pin(im, xi, yi, prog(t, dur * 0.42, 0.3), SK_COL)
    tag(im, 'إنزال إنتشون', xi - 270, yi - 120, prog(t, dur * 0.4, 0.35), size=52, key='inch', t=t, seed=32,
        bgc=YELLOW, fname='cairo', rot=-2)
    datetag(im, '15 سبتمبر 1950', prog(t, dur * 0.4, 0.35), t, x=300, y=120)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.04, 0.45, 0.5)


# ------------------------------------------------------------------ 6: north, then China
def s6(t, dur):
    f1 = ease_io(prog(t, 0.2, dur * 0.4))
    f2 = ease_io(prog(t, dur * 0.58, dur * 0.4))
    front = mapk.front_mix('p38', 'yalu', f1) if f2 <= 0 else mapk.front_mix('yalu', 'jan51', f2)
    im, S = korea_frame(t, (127.5, 39.0), 10.5, front, 0.58)
    lbl(im, 'الصين', S(123.9, 41.0), 70, GREY, 1, 800)
    for k, (a, b) in enumerate([((124.9, 41.6), (126.0, 38.6)), ((126.8, 42.0), (127.3, 38.6)), ((128.4, 42.3), (128.6, 38.9))]):
        arrow(im, [S(*a), S((a[0] + b[0]) / 2 + 0.2, (a[1] + b[1]) / 2), S(*b)], prog(t, dur * 0.56 + k * 0.2, 1.4),
              (170, 30, 30), 34, 70)
    tag(im, 'نهر يالو: الحدود مع الصين', 520, 330, prog(t, dur * 0.3, 0.35),
        size=40, key='yalu', t=t, seed=41, rot=-2)
    tag(im, 'الصين تدخل الحرب', 1450, 320, prog(t, dur * 0.5, 0.35), size=60, key='cn', t=t, seed=42,
        fill=CARD, bgc=(170, 30, 30), fname='cairo', rot=-2)
    tag(im, 'مئات الآلاف من الجنود', 1450, 440, prog(t, dur * 0.62, 0.35), size=44, key='cn2', t=t, seed=43, rot=1.5)
    datetag(im, 'أكتوبر 1950', prog(t, dur * 0.5, 0.3), t, x=1660, y=150)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 7: stalemate
def s7(t, dur):
    f1 = ease_io(prog(t, 0.1, dur * 0.3))
    f2 = ease_io(prog(t, dur * 0.4, dur * 0.4))
    front = mapk.front_mix('jan51', 'mid51', f1) if f2 <= 0 else mapk.front_mix('mid51', 'dmz', f2)
    wob = 0.05 * math.sin(t * 5) * (1 - prog(t, dur * 0.45, dur * 0.3))
    im, S = korea_frame(t, (127.6, 37.9), 7.0, front + wob, 0.58)
    d = ImageDraw.Draw(im)
    dashed(d, [S(124.0, 38.0), S(131.0, 38.0)], 1.0, (90, 80, 70), 4)
    lbl(im, 'خط 38', (S(124.4, 38.0)[0] + 60, S(124.4, 38.0)[1] - 30), 36, GREY, 1, 700)
    yr = 1951 + int(2 * ease_io(prog(t, dur * 0.3, dur * 0.6)))
    datetag(im, f'{yr}', 1.0, t, x=300, y=120)
    tag(im, 'مفاوضات لمدة عامين', 1500, 160, prog(t, dur * 0.55, 0.35), size=54, key='neg', t=t, seed=51,
        bgc=YELLOW, fname='cairo')
    side_labels(im, S, 1.0, (127.2, 39.05), (128.2, 36.6))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 8: armistice
def s8(t, dur):
    im = bg()
    c = card(620, 520, seed=61)
    dd = ImageDraw.Draw(c)
    dd.rectangle((0, 0, 620, 100), fill=INK)
    hd = T('يوليو 1953', 58, 'cairo', 800, CARD)
    c.alpha_composite(hd, (310 - hd.width // 2, 50 - hd.height // 2))
    big = text_img('27', 'oswald', 260, 700, INK)
    c.alpha_composite(big, (310 - big.width // 2, 110))
    sub = T('بانمونجوم', 52, 'cairo', 800, GREY)
    c.alpha_composite(sub, (310 - sub.width // 2, 415))
    j = jitter('cal', t, 1.0)
    paste(im, shadowed(c), 1360 + j[0], 520 + j[1], scale=pop(prog(t, 0.1, 0.45)), rot=-3 + j[2])
    pa = prog(t, dur * 0.55, 0.3)
    if pa > 0:
        st = text_img('هدنة', 'cairo', 170, 900, RED)
        stamp = Image.new('RGBA', (st.width + 80, st.height + 60), (0, 0, 0, 0))
        ds = ImageDraw.Draw(stamp)
        ds.rounded_rectangle((6, 6, stamp.width - 6, stamp.height - 6), 18, outline=RED, width=12)
        stamp.alpha_composite(st, (40, 30))
        s = 1.6 - 0.6 * ease_out(pa)
        paste(im, stamp, 640, 380, scale=s, rot=8, alpha=clamp(pa * 2))
    pb = prog(t, dur * 0.72, 0.3)
    if pb > 0:
        tx = T('معاهدة سلام', 110, weight=900, fill=GREY)
        paste(im, tx, 640, 720, scale=pop(pb))
        d = ImageDraw.Draw(im)
        ps = prog(t, dur * 0.8, 0.4)
        stroke_path(d, [(640 + tx.width / 2 + 20, 740), (640 - tx.width / 2 - 20, 712)], ease_out(ps), RED, 16)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 9: toll
def s9(t, dur):
    im = bg()
    cols, rows, total = 30, 10, 300
    gx0, gy0, step = 120, 260, 34
    pf = ease_io(prog(t, 0.2, dur * 0.6))
    d = ImageDraw.Draw(im)
    nfill = int(total * pf)
    for k in range(total):
        r, c = divmod(k, cols)
        x, y = gx0 + c * step, gy0 + r * step
        if k < nfill:
            d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=INK)
        else:
            d.ellipse((x - 12, y - 12, x + 12, y + 12), outline=(190, 180, 162), width=2)
    leg = text_img('كل نقطة = 10 آلاف إنسان', 'plex', 32, None, GREY)
    paste(im, leg, gx0 + leg.width / 2 - 10, gy0 + rows * step + 40)
    num = text_img('≈ 3', 'oswald', 230, 700, INK)
    paste(im, num, 1560, 420, alpha=clamp(pf * 3))
    sub = T('ملايين قتيل', 80)
    paste(im, sub, 1560, 600, alpha=clamp(pf * 3))
    tag(im, 'أغلبهم من المدنيين', 1560, 760, prog(t, dur * 0.55, 0.35), size=58, key='civ', t=t, seed=71,
        fill=CARD, bgc=RED, fname='cairo', rot=-2)
    src = text_img('تقديرات المؤرخين ومعهد أبحاث السلام في أوسلو', 'plex', 28, None, GREY)
    paste(im, src, W - 60 - src.width / 2, H - 50)
    return camera(im.convert('RGB'), t, dur, 1.0, 1.03)


# ------------------------------------------------------------------ 10: DMZ today
def s10(t, dur):
    z = ease_io(prog(t, 0, dur * 0.5))
    span = 9.0 + (4.6 - 9.0) * z
    cen = (127.6 + (127.35 - 127.6) * z, 37.9 + (38.1 - 37.9) * z)
    im, S = korea_frame(t, cen, span, mapk.FRONT['dmz'], 0.5)
    d = ImageDraw.Draw(im)
    pts = [S(*q) for q in mapk.MDL]
    s_px = abs(S(127, 38)[1] - S(127, 38.018)[1])           # ~2 km in px
    band = max(10, int(4 * s_px * 2))
    pb = prog(t, dur * 0.2, 1.4)
    stroke_path(d, pts, ease_out(pb), (250, 245, 232), band)
    stroke_path(d, pts, ease_out(pb), RED, 5)
    xp, yp = S(*PANMUNJOM)
    pin(im, xp, yp, prog(t, dur * 0.5, 0.4), INK)
    tag(im, 'بانمونجوم', xp - 30, yp + 90, prog(t, dur * 0.52, 0.3), size=40, key='pmj', t=t, seed=81)
    tag(im, 'المنطقة منزوعة السلاح', 1450, 170, prog(t, dur * 0.3, 0.35), size=56, key='dmz', t=t, seed=82,
        bgc=YELLOW, fname='cairo')
    tag(im, '≈ 250 كم طولًا · ≈ 4 كم عرضًا', 1450, 290, prog(t, dur * 0.45, 0.35), size=42, key='dmz2', t=t, seed=83)
    tag(im, 'أكثر من 70 عامًا بلا معاهدة سلام', 960, 960, prog(t, dur * 0.1, 0.35), size=52, key='70', t=t,
        seed=84, fill=CARD, bgc=INK, fname='cairo', rot=-1)
    side_labels(im, S, 1 - z * 0.3, (126.7, 39.3), (128.0, 36.9))
    return camera(im.convert('RGB'), t, dur, 1.0, 1.02)


# ------------------------------------------------------------------ 11: ending
def s11(t, dur, speech_end=3.0):
    im = bg()
    l1 = T('حربٌ توقّف فيها إطلاق النار...', 96)
    paste(im, l1, W / 2, 380, scale=pop(prog(t, 0.0, 0.35)))
    l2 = T('لكنّها لم تنتهِ أبدًا', 140)
    p2 = prog(t, speech_end * 0.55, 0.3)
    if p2 > 0:
        if p2 < 1:
            paste(im, l2, W / 2, 600, scale=pop(p2))
        else:
            highlight_text(im, l2, W / 2, 600, prog(t, speech_end * 0.7, 0.6))
    ps = prog(t, speech_end + 0.3, 0.8)
    if ps > 0:
        s1_ = text_img('المصادر: الموسوعة البريطانية · مركز التاريخ العسكري الأمريكي · اتفاقية الهدنة 1953 · معهد أبحاث السلام في أوسلو',
                       'plex', 28, None, GREY)
        paste(im, s1_, W / 2, H - 120, alpha=ps)
    out = camera(im.convert('RGB'), t, dur, 1.0, 1.03)
    fo = prog(t, dur - 0.8, 0.8)
    if fo > 0:
        out = Image.blend(out, paper_bg(), fo)
    return out


SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11]

# (scene, fraction of scene, offset seconds, kind)
EVENTS = [(0, 0, 0.2, 'pop'), (0, 0, 0.3, 'scr'), (0, 0, 1.2, 'pop'), (0, 0.55, 0, 'boom'),
          (1, 0, 0, 'pop'), (1, 0.35, 0, 'pop'), (1, 0.45, 0, 'scr'),
          (2, 0, 0.1, 'pop'), (2, 0.12, 0, 'pop'), (2, 0.35, 0, 'scr'), (2, 0.45, 0, 'pop'), (2, 0.6, 0, 'pop'), (2, 0.78, 0, 'pop'),
          (3, 0.2, 0, 'pop'), (3, 0.32, 0, 'pop'), (3, 0.58, 0, 'pop'),
          (4, 0.12, 0, 'pop'), (4, 0.62, 0, 'pop'), (4, 0.82, 0, 'pop'),
          (5, 0, 0.2, 'pop'), (5, 0.28, 0, 'scr'), (5, 0.4, 0, 'boom'),
          (6, 0.3, 0, 'pop'), (6, 0.5, 0, 'boom'), (6, 0.62, 0, 'pop'),
          (7, 0.55, 0, 'pop'),
          (8, 0, 0.1, 'pop'), (8, 0.55, 0, 'boom'), (8, 0.72, 0, 'pop'), (8, 0.8, 0, 'scr'),
          (9, 0.55, 0, 'pop'),
          (10, 0.1, 0, 'pop'), (10, 0.2, 0, 'scr'), (10, 0.3, 0, 'pop'), (10, 0.45, 0, 'pop'),
          (11, 0, 0, 'pop')]
