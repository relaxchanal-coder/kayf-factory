"""الصورة المصغّرة 1280x720 (للفيديو الطويل) + غلاف عمودي (للشورتس)."""
import math
from PIL import Image, ImageDraw, ImageFilter

import gfx
import style as stylemod
from gfx import blit, emoji_img, glow, rounded, text_img
from render import Ctx, channel, draw_bg


def _outline(t, px):
    """إطار أسود سميك حول النص (أسلوب صور يوتيوب الملفتة)."""
    pad = px + 4
    base = Image.new("RGBA", (t.width + pad * 2, t.height + pad * 2), (0, 0, 0, 0))
    base.paste(t, (pad, pad), t)
    a = base.getchannel("A").point(lambda v: 255 if v > 60 else 0).filter(ImageFilter.MaxFilter(px * 2 + 1))
    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 0), a)
    return Image.alpha_composite(out, base)


def _rays(im, cx, cy, c1, c2, n=26):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    R = max(im.size) * 1.6
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + .5) / n
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=(c1 if i % 2 else c2) + (70,))
    im.alpha_composite(ov)


def thumbnail(script, out_path, W=1280, H=720, style=None):
    th = script.get("thumb", {})
    style = style or stylemod.pick(script.get("id", "000"), script)
    ctx = Ctx(W, H, style)
    im = draw_bg(ctx, 0.0)
    s = H / 720 if W > H else W / 720
    acc, acc2 = ctx.acc, ctx.acc2
    portrait = H > W
    rtl = gfx.is_rtl()
    ex, ey = (W * 0.5, H * 0.34) if portrait else ((W * 0.25 if rtl else W * 0.76), H * 0.52)
    _rays(im, ex, ey, acc, acc2)
    blit(im, glow(int(760 * s), acc, 0.75), ex, ey)
    ring = Image.new("RGBA", (int(620 * s), int(620 * s)), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([6, 6, ring.width - 6, ring.height - 6], outline=(255, 255, 255, 230), width=int(9 * s))
    blit(im, ring, ex, ey)
    blit(im, emoji_img(th.get("emoji", "❓"), int(380 * s)), ex, ey, rot=-8 if rtl else 8)
    lines = th.get("text", script["title"]).split("|")
    tx_c = W * 0.5 if portrait else (W * 0.69 if rtl else W * 0.31)
    y = H * 0.60 if portrait else H * 0.22
    maxw = W * (0.9 if portrait else 0.52)
    for i, ln in enumerate(lines[:3]):
        col = ctx.fg if i % 2 == 0 else acc2
        fam = "Lalezar" if ctx.hf == "Cairo" else ctx.hf
        size = 124
        t = text_img(ln.strip(), int(size * s), col, family=fam, shadow=True)
        while t.width > maxw and size > 60:  # سطر واحد دائماً: نصغّر الخط بدل الالتفاف
            size -= 6
            t = text_img(ln.strip(), int(size * s), col, family=fam, shadow=True)
        t = _outline(t, max(4, int(9 * s)))
        blit(im, t, tx_c, y + t.height / 2)
        y += t.height + 30 * s
    if script.get("format") == "long" and not portrait:
        lab = text_img("شرح كامل" if rtl else "FULL STORY", int(46 * s), (255, 255, 255), family="Lalezar", shadow=False)
        bd = rounded(lab.width + int(44 * s), lab.height + int(12 * s), int(14 * s), (232, 17, 45, 255))
        bx = tx_c; by = H * 0.1
        blit(im, bd, bx, by, rot=-3); blit(im, lab, bx, by, rot=-3)
    tag = text_img(channel(), int(44 * s), ctx.ink, family="Lalezar", shadow=False)
    pill = rounded(tag.width + int(30 * s), tag.height + int(6 * s), max(ctx.r(24), 4), acc + (255,))
    px, py = (W / 2, H * 0.9) if portrait else ((W - pill.width / 2 - 30 * s) if rtl else (pill.width / 2 + 30 * s), H - pill.height / 2 - 30 * s)
    blit(im, pill, px, py)
    blit(im, tag, px, py)
    ImageDraw.Draw(im).rectangle([0, 0, W - 1, H - 1], outline=acc + (255,), width=int(10 * s))
    im.convert("RGB").save(out_path, quality=92)
