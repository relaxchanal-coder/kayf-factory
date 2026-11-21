"""المصنع: سكربت JSON ← صوت ← موسيقى ← رسوم ← فيديو + صورة مصغّرة + نص الوصف.

الاستخدام:
    python factory/make.py content/queue/001-microwave.json [--silent]
"""
import json
import zlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio  # noqa: E402
import render  # noqa: E402
import thumb  # noqa: E402
import voice  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = 0.3  # صمت بين المشاهد
CREDIT = "الرموز: Twemoji (CC BY 4.0) — الموسيقى والرسوم من إنتاج القناة."


def build(script_path, silent=False, out_root=None):
    sc = json.load(open(script_path, encoding="utf-8"))
    vid = sc["id"]
    out = os.path.join(out_root or os.path.join(ROOT, "out"), vid)
    work = os.path.join(out, "_work")
    os.makedirs(work, exist_ok=True)
    fmt = sc.get("format", "short")
    W, H = (1080, 1920) if fmt == "short" else (1920, 1080)

    # 1) الصوت لكل مشهد
    timeline, clips, t = [], [], 0.4
    whooshes, pops = [], []
    for i, s in enumerate(sc["scenes"]):
        mp3 = os.path.join(work, f"v{i:02d}.mp3")
        dur, words = voice.speak(s["say"], mp3, silent=silent)
        s = dict(s)
        s["start"] = t if i else 0.0
        s["words"] = [dict(w, t=w["t"] + (0.4 if i == 0 else 0)) for w in words] if i == 0 else words
        if i == 0:
            s["dur"] = dur + 0.4 + GAP
            clips.append((0.4, audio.load(mp3)))
        else:
            s["dur"] = dur + GAP
            clips.append((t, audio.load(mp3)))
        whooshes.append(s["start"])
        if s["type"] in ("steps", "flow"):
            n = len(s.get("items", []))
            pops += [s["start"] + x for x in render._reveal_times(n, s["dur"])]
        elif s["type"] in ("stat", "compare", "fact", "outro"):
            pops.append(s["start"] + 0.15)
        timeline.append(s)
        t = s["start"] + s["dur"]
    timeline[-1]["dur"] += 1.2  # نهاية مريحة
    total = timeline[-1]["start"] + timeline[-1]["dur"]
    print(f"[{vid}] المدة: {total:.1f} ثانية، {len(timeline)} مشاهد")

    # 2) الميكس
    wav = os.path.join(work, "mix.wav")
    audio.mix(clips, total, whooshes, pops, wav, seed=zlib.crc32(vid.encode()) % 1000)

    # 3) الرسوم والفيديو
    mp4 = os.path.join(out, f"{vid}.mp4")
    render.render_video(W, H, sc.get("theme", "cyan"), timeline, total, wav, mp4, work)

    # 4) الصورة المصغّرة
    thumb.thumbnail(sc, os.path.join(out, f"{vid}-thumb.jpg"))
    if fmt == "short":
        thumb.thumbnail(sc, os.path.join(out, f"{vid}-cover.jpg"), 1080, 1920)

    # 5) العنوان والوصف والوسوم
    tags = sc.get("tags", [])
    title = sc["title"] + (" #shorts" if fmt == "short" and "#" not in sc["title"] else "")
    desc = sc.get("description", "").strip()
    hashtags = " ".join("#" + x.replace(" ", "_") for x in tags[:5])
    desc = f"{desc}\n\n{hashtags}\n\n{CREDIT}"
    meta = {"id": vid, "title": title[:100], "description": desc, "tags": tags,
            "format": fmt, "duration": round(total, 1)}
    json.dump(meta, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(out, "انسخ-للنشر.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"العنوان:\n{meta['title']}\n\nالوصف:\n{desc}\n\nالوسوم:\n{', '.join(tags)}\n")
    shutil.rmtree(work, ignore_errors=True)
    print(f"[{vid}] جاهز ← {mp4}")
    return out, meta


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for p in args:
        build(p, silent="--silent" in sys.argv)
