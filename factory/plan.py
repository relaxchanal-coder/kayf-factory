"""خطة النشر الأسبوعية: تحسب مواعيد النشر حسب schedule.json وتوزّع الحلقات عليها.

الاستخدام:  python factory/plan.py 2026-11-23   (تاريخ أول يوم بالأسبوع)
"""
import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
AR = {"monday": "الاثنين", "tuesday": "الثلاثاء", "wednesday": "الأربعاء", "thursday": "الخميس",
      "friday": "الجمعة", "saturday": "السبت", "sunday": "الأحد"}


def slots(start, days=7):
    cfg = json.load(open(os.path.join(ROOT, "schedule.json"), encoding="utf-8"))
    out = []
    for i in range(days):
        d = start + dt.timedelta(days=i)
        name = DAYS[d.weekday()]
        for t in cfg["shorts"]["every_day"]:
            out.append(("short", d, t, name))
        if name in cfg["long"]["days"]:
            out.append(("long", d, cfg["long"]["time"], name))
    return sorted(out, key=lambda x: (x[1], x[2]))


def plan(start):
    queue = sorted(glob.glob(os.path.join(ROOT, "content", "queue", "*.json")))
    pools = {"short": [], "long": []}
    for f in queue:
        pools[json.load(open(f, encoding="utf-8")).get("format", "short")].append(f)
    rows = []
    for fmt, d, t, name in slots(start):
        f = pools[fmt].pop(0) if pools[fmt] else None
        rows.append({"format": fmt, "date": d.isoformat(), "time": t, "day": AR[name],
                     "script": os.path.basename(f) if f else None})
    return rows


if __name__ == "__main__":
    start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    rows = plan(start)
    for r in rows:
        print(f"{r['day']:<9} {r['date']} {r['time']}  {r['format']:<5}  {r['script'] or '— يحتاج سكربت'}")
    need = {k: sum(1 for r in rows if r["format"] == k and not r["script"]) for k in ("short", "long")}
    print("\nناقص:", need)
