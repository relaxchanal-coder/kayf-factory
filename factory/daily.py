"""التشغيل اليومي: يصنع فيديوهات «الغد» حسب schedule.json، ويسجّل موعد نشر كل واحد.

الاستخدام:  python factory/daily.py [--date 2026-11-23]
(بدون --date يبدأ من الغد بتوقيت بغداد؛ --days 7 لأسبوع كامل)
"""
import datetime as dt
import glob
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import make  # noqa: E402
import plan  # noqa: E402
import writer  # noqa: E402

ROOT = make.ROOT
QUEUE = os.path.join(ROOT, "content", "queue")
DONE = os.path.join(ROOT, "content", "done")
TZ = dt.timezone(dt.timedelta(hours=3))  # بغداد


def pool(fmt):
    files = sorted(glob.glob(os.path.join(QUEUE, "*.json")))
    return [f for f in files if json.load(open(f, encoding="utf-8")).get("format", "short") == fmt]


def main():
    if "--date" in sys.argv:
        day = dt.date.fromisoformat(sys.argv[sys.argv.index("--date") + 1])
    else:
        day = (dt.datetime.now(TZ) + dt.timedelta(days=1)).date()
    ndays = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 1
    # لا نعيد صنع أيام سبق صنعها (حماية من التكرار)
    state_p = os.path.join(ROOT, "content", "state.json")
    state = json.load(open(state_p)) if os.path.exists(state_p) else {}
    last = dt.date.fromisoformat(state["last_day"]) if state.get("last_day") else None
    if last and "--date" not in sys.argv and day <= last:
        ndays -= (last - day).days + 1
        day = last + dt.timedelta(days=1)
        if ndays <= 0:
            print("هذه الأيام مصنوعة مسبقاً")
            return
    slots = plan.slots(day, days=ndays)
    state["last_day"] = (day + dt.timedelta(days=ndays - 1)).isoformat()
    need = {f: sum(1 for s in slots if s[0] == f) for f in ("short", "long")}
    os.makedirs(DONE, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)

    # املأ الطابور إذا قلّ (يحتفظ دائماً بحلقات احتياطية)
    has_ai = os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    for fmt, reserve in (("short", 4), ("long", 1)):
        if has_ai and need[fmt] and len(pool(fmt)) < need[fmt] + reserve:
            writer.write(need[fmt] + reserve - len(pool(fmt)), fmt)

    # المواعيد اللي عندها فيديو جاهز مسبقاً (من فرع videos)
    taken = set()
    try:
        import urllib.request
        url = os.environ.get("MANIFEST_URL")
        if url:
            for m in json.load(urllib.request.urlopen(url, timeout=30)):
                taken.add(m["publish_at"][:16] + m["format"])
    except Exception as e:
        print("لا يوجد manifest سابق:", e)
    report = []
    for fmt, d, t, _ in slots:
        hh, mm = map(int, t.split(":"))
        key = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ).isoformat()[:16] + fmt
        if key in taken:
            continue
        files = pool(fmt)
        if not files:
            print(f"⚠️ لا يوجد سكربت {fmt} لموعد {d} {t}")
            continue
        path = files[0]
        out, meta = make.build(path)
        hh, mm = map(int, t.split(":"))
        meta["publish_at"] = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ).isoformat()
        json.dump(meta, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        shutil.move(path, os.path.join(DONE, os.path.basename(path)))
        report.append(meta)
    json.dump(report, open(os.path.join(ROOT, "out", "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(state, open(state_p, "w"))
    # ملف التعليمات لـ Claude حتى يرفع ويجدول
    manifest = [{"id": m["id"], "format": m["format"], "title": m["title"],
                 "description": m["description"], "tags": m["tags"], "publish_at": m["publish_at"],
                 "video": f"{m['id']}.mp4",
                 "thumb": f"{m['id']}-thumb.jpg" if m["format"] == "long" else None,
                 "status": "pending"} for m in report]
    json.dump(manifest, open(os.path.join(ROOT, "out", "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(report)} فيديو جاهز ليوم {day}")


if __name__ == "__main__":
    main()
