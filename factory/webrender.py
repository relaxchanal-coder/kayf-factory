"""محرك الموشن جرافيك الجديد (HTML + Chrome): يرسم كل إطار في صفحة web/player.html
ويصوّره، ثم يجمع الإطارات بـ FFmpeg. أنعم وأغنى من المحرك القديم (render.py):
خلفيات فضاء/شفق/شبكة متحركة، بطاقات زجاجية، أرقام تعدّ، صور حقيقية، أسهم تُرسم.

يُستدعى من make.py؛ وإذا فشل (لا يوجد Chrome مثلاً) يرجع المصنع للمحرك القديم تلقائياً.
"""
import asyncio
import json
import math
import os
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor

import gfx
import style as stylemod

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
CHANNELS = {"ar": os.environ.get("KAYF_CHANNEL") or "كيف يعمل؟",
            "en": os.environ.get("KAYF_CHANNEL_EN") or "How It Works?"}
STR = {"ar": {"didyou": "هل تعلم؟", "subscribe": "اشترك", "subscribed": "تم الاشتراك"},
       "en": {"didyou": "Did you know?", "subscribe": "Subscribe", "subscribed": "Subscribed"}}


def chrome_path():
    for p in (os.environ.get("KAYF_CHROME"), "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
              "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if p and os.path.exists(p):
            return p
    return None  # Chromium الخاص بـ Playwright


def _uri(p):
    return "file://" + os.path.abspath(p)


def _emo(e):
    return _uri(gfx._emoji_file(e or "❓"))


def build_data(W, H, st, timeline, total, lang):
    pal = stylemod.PALETTES[st["palette"]]
    pre = []
    scenes = []
    for s in timeline:
        d = {k: v for k, v in s.items() if not k.startswith("_")}
        d["emo"] = _emo(s.get("emoji"))
        pre.append(d["emo"])
        if s.get("image_file"):
            d["img"] = _uri(s["image_file"])
            pre.append(d["img"])
        items = []
        for it in s.get("items", []) or []:
            if isinstance(it, dict):
                it = dict(it, emo=_emo(it.get("emoji")))
                pre.append(it["emo"])
            items.append(it)
        if items:
            d["items"] = items
        for side in ("right", "left"):
            if isinstance(s.get(side), dict):
                d[side] = dict(s[side], emo=_emo(s[side].get("emoji")))
                pre.append(d[side]["emo"])
                if s[side].get("image_file"):
                    d[side]["img"] = _uri(s[side]["image_file"])
                    pre.append(d[side]["img"])
        scenes.append(d)
    avatar = os.path.join(ROOT, "assets", "brand", f"avatar-{lang}.jpg")
    data = {
        "W": W, "H": H, "lang": lang, "total": total, "scenes": scenes,
        "style": {k: st.get(k) for k in ("bg", "font", "transition", "subs", "progress", "radius")},
        "palette": {"bg1": pal[0], "bg2": pal[1], "acc": pal[2], "acc2": pal[3], "fg": pal[4],
                    "ink": pal[5], "light": pal[6]},
        "channel": CHANNELS[lang], "avatar": _uri(avatar), "bell": _emo("🔔"), "hand": _emo("👆"),
        "seed": sum(map(ord, st["palette"])) + W, **STR[lang],
    }
    data["preload"] = pre + [data["avatar"], data["bell"], data["hand"]]
    return data


def write_page(data, workdir):
    html = open(os.path.join(HERE, "web", "player.html"), encoding="utf-8").read()
    html = html.replace("../../fonts/", _uri(os.path.join(ROOT, "fonts")) + "/")
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    p = os.path.join(workdir, "player.html")
    open(p, "w", encoding="utf-8").write(html)
    return p


async def _shoot(page_path, W, H, f0, f1, out):
    from playwright.async_api import async_playwright
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS),
                           "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                           "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), out + ".tmp.mp4"],
                          stdin=subprocess.PIPE)
    async with async_playwright() as p:
        kw = {"args": ["--allow-file-access-from-files", "--no-sandbox", "--disable-gpu",
                       "--font-render-hinting=none", "--hide-scrollbars"]}
        if chrome_path():
            kw["executable_path"] = chrome_path()
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        await pg.goto(_uri(page_path))
        await pg.evaluate("window.ready")
        await pg.wait_for_timeout(300)
        for f in range(f0, f1):
            await pg.evaluate(f"frame({f / FPS:.5f})")
            ff.stdin.write(await pg.screenshot(type="jpeg", quality=92))
        await b.close()
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg فشل في " + out)
    os.replace(out + ".tmp.mp4", out)
    return out


def _job(a):
    return asyncio.run(_shoot(*a))


def render_video(W, H, st, timeline, total, wav, out_mp4, workdir, lang="ar", workers=None):
    gfx.LANG[0] = lang
    data = build_data(W, H, st, timeline, total, lang)
    page = write_page(data, workdir)
    workers = workers or max(1, os.cpu_count() or 2)
    nf = int(total * FPS)
    per = math.ceil(nf / workers)
    jobs = [(page, W, H, i * per, min(nf, (i + 1) * per), os.path.join(workdir, f"web{i:02d}.mp4"))
            for i in range(workers) if i * per < nf]
    with ProcessPoolExecutor(len(jobs)) as ex:
        parts = list(ex.map(_job, jobs))
    lst = os.path.join(workdir, "webparts.txt")
    with open(lst, "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_mp4],
                   check=True)


def still(W, H, st, timeline, total, lang, workdir, times, prefix):
    """لقطات ثابتة للمراجعة (بدون فيديو)."""
    data = build_data(W, H, st, timeline, total, lang)
    page = write_page(data, workdir)

    async def go():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            kw = {"args": ["--allow-file-access-from-files", "--no-sandbox"]}
            if chrome_path():
                kw["executable_path"] = chrome_path()
            b = await p.chromium.launch(**kw)
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.goto(_uri(page))
            await pg.evaluate("window.ready")
            out = []
            for t in times:
                await pg.evaluate(f"frame({t})")
                f = f"{prefix}_{t:.1f}.jpg"
                await pg.screenshot(path=f, type="jpeg", quality=85)
                out.append(f)
            await b.close()
            return out
    return asyncio.run(go())
