"""التشغيل اليومي: يصنع فيديوهات «الغد» حسب schedule.json، ويسجّل موعد نشر كل واحد.

الاستخدام:  python factory/daily.py [--date 2026-11-23]
(بدون --date يصنع حلقات يوم الغد بتوقيت بغداد)
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
    slots = plan.slots(day, days=1)
    need = {f: sum(1 for s in slots if s[0] == f) for f in ("short", "long")}
    os.makedirs(DONE, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)

    # املأ الطابور إذا قلّ (يحتفظ دائماً بحلقات احتياطية)
    has_ai = os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    for fmt, reserve in (("short", 4), ("long", 1)):
        if has_ai and need[fmt] and len(pool(fmt)) < need[fmt] + reserve:
            writer.write(need[fmt] + reserve - len(pool(fmt)), fmt)

    report = []
    for fmt, d, t, _ in slots:
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
    print(f"✅ {len(report)} فيديو جاهز ليوم {day}")


if __name__ == "__main__":
    main()
