import sys
sys.path.insert(0, '/home/claude/vox')
from PIL import Image, ImageDraw, ImageFilter
from engine import *
import mapr
v = mapr.View(47.6, 32.3, 13.0)
f = mapr.tint(v.frame, v.mask('Iraq'), mapr.IRAQ, 0.75)
f = mapr.tint(f, v.mask('Iran'), mapr.IRAN, 0.75).convert('RGBA')
# darken left for text
ov = Image.new('RGBA', f.size, (0, 0, 0, 0))
d = ImageDraw.Draw(ov)
for x in range(0, 1100, 4):
    a = int(170 * (1 - x / 1100))
    d.rectangle((x, 0, x + 4, 1080), fill=(20, 16, 10, a))
f.alpha_composite(ov)
# red X on border line area
d = ImageDraw.Draw(f)
bx, by = v.S(47.7, 31.4)
def big(text, size, col):
    return text_img(text, 'cairo', size, 900, col)
t1 = big('8 سنوات', 250, YELLOW)
t2 = big('حرب انتهت', 150, CARD)
t3 = big('حيث بدأت!', 150, CARD)
for im_, y in [(t1, 250), (t2, 560), (t3, 760)]:
    sh = Image.new('RGBA', (im_.width + 40, im_.height + 40), (0, 0, 0, 0))
    m = im_.getchannel('A').filter(ImageFilter.MaxFilter(9))
    sh.paste((0, 0, 0, 230), (20, 20), m)
    sh = sh.filter(ImageFilter.GaussianBlur(3))
    f.alpha_composite(sh, (int(540 - sh.width / 2), int(y - sh.height / 2)))
    f.alpha_composite(im_, (int(540 - im_.width / 2), int(y - im_.height / 2)))
lab = label('العراق × إيران', 60, fname='cairo', weight=900, fill=CARD, bg=RED, seed=3)
f.alpha_composite(shadowed(lab, (6, 8), 8, 0.4), (1380, 60))
out = finish(f.convert('RGB'), 0).resize((1280, 720), Image.LANCZOS)
out.save('build/thumb.jpg', quality=92)
print('ok')
