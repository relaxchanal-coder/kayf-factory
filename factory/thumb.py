"""الصورة المصغّرة 1280x720 (للفيديو الطويل) + غلاف عمودي (للشورتس)."""
from PIL import ImageDraw

import gfx
import style as stylemod
from gfx import blit, emoji_img, glow, rounded, text_img
from render import Ctx, channel, draw_bg


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
    blit(im, glow(int(700 * s), acc, 0.6), ex, ey)
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
        if i % 2 == 1:
            box = rounded(t.width + int(40 * s), t.height + int(10 * s), int(20 * s), (0, 0, 0, 150))
            blit(im, box, tx_c, y + t.height / 2)
        blit(im, t, tx_c, y + t.height / 2)
        y += t.height + 30 * s
    tag = text_img(channel(), int(44 * s), ctx.ink, family="Lalezar", shadow=False)
    pill = rounded(tag.width + int(30 * s), tag.height + int(6 * s), max(ctx.r(24), 4), acc + (255,))
    px, py = (W / 2, H * 0.9) if portrait else ((W - pill.width / 2 - 30 * s) if rtl else (pill.width / 2 + 30 * s), H - pill.height / 2 - 30 * s)
    blit(im, pill, px, py)
    blit(im, tag, px, py)
    ImageDraw.Draw(im).rectangle([0, 0, W - 1, H - 1], outline=acc + (255,), width=int(10 * s))
    im.convert("RGB").save(out_path, quality=92)
