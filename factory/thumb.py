"""الصورة المصغّرة 1280x720 (للفيديو الطويل) + غلاف عمودي (للشورتس)."""
from PIL import ImageDraw

from gfx import THEMES, blit, emoji_img, glow, rounded, text_img
from render import CHANNEL, Ctx, background


def thumbnail(script, out_path, W=1280, H=720):
    th = script.get("thumb", {})
    theme = script.get("theme", "cyan")
    ctx = Ctx(W, H, theme)
    bg, grid, sp, _ = background(ctx)
    im = bg.copy()
    im.alpha_composite(grid.crop((0, 0, W, H)))
    s = H / 720 if W > H else W / 720
    acc, acc2 = THEMES[theme][2], THEMES[theme][3]
    portrait = H > W
    ex, ey = (W * 0.5, H * 0.34) if portrait else (W * 0.27, H * 0.52)
    blit(im, glow(int(700 * s), acc, 0.6), ex, ey)
    blit(im, emoji_img(th.get("emoji", "❓"), int(380 * s)), ex, ey, rot=-8)
    lines = th.get("text", script["title"]).split("|")
    tx_c = W * 0.5 if portrait else W * 0.69
    y = H * 0.60 if portrait else H * 0.22
    maxw = W * (0.9 if portrait else 0.56)
    for i, ln in enumerate(lines[:3]):
        col = (255, 255, 255) if i % 2 == 0 else acc2
        t = text_img(ln.strip(), int(124 * s), col, family="Lalezar", max_w=int(maxw))
        if i % 2 == 1:
            box = rounded(t.width + int(40 * s), t.height + int(10 * s), int(20 * s), (0, 0, 0, 150))
            blit(im, box, tx_c, y + t.height / 2)
        blit(im, t, tx_c, y + t.height / 2)
        y += t.height + 30 * s
    tag = text_img(CHANNEL, int(44 * s), (20, 20, 20), family="Lalezar", shadow=False)
    pill = rounded(tag.width + int(30 * s), tag.height + int(6 * s), int(24 * s), acc + (255,))
    px, py = (W / 2, H * 0.9) if portrait else (W - pill.width / 2 - 30 * s, H - pill.height / 2 - 30 * s)
    blit(im, pill, px, py)
    blit(im, tag, px, py)
    ImageDraw.Draw(im).rectangle([0, 0, W - 1, H - 1], outline=acc + (255,), width=int(10 * s))
    im.convert("RGB").save(out_path, quality=92)
