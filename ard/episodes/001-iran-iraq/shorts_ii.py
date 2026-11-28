"""Two vertical teaser Shorts cut from the long video, with title, captions and an end card."""
import sys, json, subprocess, os
sys.path.insert(0, '/home/claude/vox')
sys.path.insert(0, '/home/claude/iraniraq')
import numpy as np
from PIL import Image, ImageDraw
from engine import *
os.chdir('/home/claude/iraniraq')
import render_ii as R

SW, SH = 1080, 1920
SAND = (236, 226, 204)
ITEMS, SPEECH_END, TOTAL = R.plan()
TA = json.load(open('segments.json'))
TB = json.load(open('segments2.json'))


def text_of(it):
    return (TA if it['src'] == 'a' else TB)[it['i']]


def strip_tashkeel(s):
    return ''.join(c for c in s if not ('ً' <= c <= 'ْ'))


def wrap(text, fname, size, maxw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if text_img(test, fname, size, None, INK).width > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def base_frame(title):
    im = Image.new('RGBA', (SW, SH), SAND + (255,))
    d = ImageDraw.Draw(im)
    lines = wrap(title, 'cairo', 84, 960)
    y = 230 - (len(lines) - 1) * 55
    for ln in lines:
        ti = text_img(ln, 'cairo', 84, 900, INK)
        multiply_rect(im, (SW / 2 - ti.width / 2 - 16, y + 10, SW / 2 + ti.width / 2 + 16, y + ti.height - 6), YELLOW)
        im.alpha_composite(ti, (int(SW / 2 - ti.width / 2), int(y)))
        y += 110
    br = text_img('معلومات الأرض', 'cairo', 44, 900, GREY)
    im.alpha_composite(br, (int(SW / 2 - br.width / 2), 70))
    return im


def end_card(t):
    im = Image.new('RGBA', (SW, SH), SAND + (255,))
    a = text_img('القصة كاملة', 'cairo', 120, 900, INK)
    b = text_img('في الفيديو المرتبط', 'cairo', 90, 900, INK)
    multiply_rect(im, (SW / 2 - a.width / 2 - 20, 720, SW / 2 + a.width / 2 + 20, 840), YELLOW)
    im.alpha_composite(a, (int(SW / 2 - a.width / 2), 700))
    im.alpha_composite(b, (int(SW / 2 - b.width / 2), 880))
    d = ImageDraw.Draw(im)
    bob = 18 * math.sin(t * 6)
    x, y = SW / 2, 1220 + bob
    d.rectangle((x - 26, y - 150, x + 26, y), fill=RED)
    d.polygon([(x - 90, y - 10), (x + 90, y - 10), (x, y + 110)], fill=RED)
    c = text_img('اضغط الرابط أسفل الشاشة', 'plexb', 52, None, GREY)
    im.alpha_composite(c, (int(SW / 2 - c.width / 2), 1440))
    return im


def make_short(name, k_from, k_to, title, end_len=2.8):
    t0 = ITEMS[k_from]['start'] - 0.3
    t1 = ITEMS[k_to]['start'] + ITEMS[k_to]['dur'] + 0.35
    clip = t1 - t0
    total = clip + end_len
    base = base_frame(title)
    caps = [(it['start'] - t0, it['start'] + it['dur'] - t0, strip_tashkeel(text_of(it))) for it in ITEMS[k_from:k_to + 1]]
    vin = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-t', f'{clip:.3f}', '-i', 'build/iran_iraq_war.mp4',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x608', '-r', '30', '-'], stdout=subprocess.PIPE)
    tmp = f'build/{name}.v.mp4'
    out = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{SW}x{SH}', '-r', '30',
                            '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', tmp],
                           stdin=subprocess.PIPE)
    n = int(round(total * 30))
    fsize = 1080 * 608 * 3
    cache = {}
    for j in range(n):
        t = j / 30
        if t < clip:
            raw = vin.stdout.read(fsize)
            if len(raw) < fsize:
                raw = last
            last = raw
            fr = Image.frombytes('RGB', (1080, 608), raw)
            im = base.copy()
            im.paste(fr, (0, 520))
            ImageDraw.Draw(im).rectangle((0, 516, SW, 520), fill=INK)
            ImageDraw.Draw(im).rectangle((0, 1128, SW, 1132), fill=INK)
            cap = next((c for c in caps if c[0] - 0.1 <= t <= c[1] + 0.25), None)
            if cap:
                key = cap[2]
                if key not in cache:
                    lines = wrap(key, 'plexb', 54, 960)
                    layer = Image.new('RGBA', (SW, 520), (0, 0, 0, 0))
                    y = 30
                    for ln in lines[:5]:
                        ti = text_img(ln, 'plexb', 54, None, INK)
                        layer.alpha_composite(ti, (int(SW / 2 - ti.width / 2), y))
                        y += 86
                    cache[key] = layer
                im.alpha_composite(cache[key], (0, 1190))
            frame = finish_short(im)
        else:
            frame = finish_short(end_card(t - clip))
        out.stdin.write(frame.tobytes())
    out.stdin.close()
    out.wait()
    vin.stdout.close()
    vin.kill()
    vin.wait()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', tmp, '-ss', f'{t0:.3f}', '-t', f'{clip:.3f}', '-i', 'build/mix.wav',
                    '-filter_complex', f'[1:a]afade=t=out:st={clip - 0.4:.2f}:d=0.4,apad=whole_dur={total:.2f}[a]',
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest',
                    '-movflags', '+faststart', f'build/{name}.mp4'], check=True)
    os.remove(tmp)
    print(name, round(total, 1), 's')


@functools.lru_cache(None)
def _lum():
    rng = np.random.default_rng(9)
    return (1 + 0.012 * rng.normal(0, 1, (SH, SW)).astype(np.float32))[..., None]


def finish_short(im):
    a = np.asarray(im.convert('RGB')).astype(np.float32) * _lum()
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


if __name__ == '__main__':
    import scenes_ii as S
    pos = {v: k for k, v in enumerate(S.ORDER)}
    make_short('short1', pos[('a', 0)], pos[('a', 3)], 'حرب 8 سنوات... انتهت حيث بدأت!')
    make_short('short2', pos[('a', 20)], pos[('a', 22)], 'لماذا لم تتوقّف الحرب عام 1982؟')
