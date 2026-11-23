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


def pool(fmt, lang="ar"):
    files = sorted(glob.glob(os.path.join(QUEUE, "*.json")))
    out = []
    for f in files:
        j = json.load(open(f, encoding="utf-8"))
        if j.get("format", "short") == fmt and j.get("lang", "ar") == lang:
            out.append(f)
    return out


def twin(ar_id):
    """النسخة الإنجليزية لنفس الحلقة (تُنشر بنفس الموعد على القناة الإنجليزية)."""
    p = os.path.join(QUEUE, f"{ar_id}-en.json")
    return p if os.path.exists(p) else None


def rebuild(since):
    """إعادة صنع الفيديوهات المجدولة (من تاريخ since فما بعد) بالمحرك الحالي، بنفس النصوص.
    تُعلَّم replace=true حتى تحذف مهمة الرفع النسخة القديمة المجدولة وترفع الجديدة."""
    import urllib.request
    cfg = json.load(open(os.path.join(ROOT, "schedule.json"), encoding="utf-8"))
    en_cfg = cfg.get("en") or {}
    old = json.load(urllib.request.urlopen(os.environ["MANIFEST_URL"], timeout=30))
    report = []
    stamp = dt.datetime.now(TZ).isoformat(timespec="minutes")
    for m in old:
        if m.get("lang", "ar") != "ar":
            continue
        at = dt.datetime.fromisoformat(m["publish_at"])
        if at.date() < since:
            continue
        for path, lang in ((os.path.join(DONE, m["id"] + ".json"), "ar"),
                           (os.path.join(DONE, m["id"] + "-en.json"), "en")):
            if not os.path.exists(path):
                print("⚠️ لا يوجد سكربت:", path)
                continue
            when = at
            if lang == "en":
                nt = (en_cfg.get(m["format"]) or {}).get(at.strftime("%H:%M"))
                if nt:
                    hh, mm = map(int, nt.split(":"))
                    d = at.date() + (dt.timedelta(days=1) if en_cfg.get("next_day") else dt.timedelta())
                    when = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ)
            out, meta = make.build(path)
            meta.update(publish_at=when.isoformat(), replace=True, rebuilt_at=stamp)
            json.dump(meta, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            report.append(meta)
    return report


def write_manifest(report):
    json.dump(report, open(os.path.join(ROOT, "out", "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    manifest = [{"id": m["id"], "format": m["format"], "lang": m.get("lang", "ar"), "title": m["title"],
                 "description": m["description"], "tags": m["tags"], "publish_at": m["publish_at"],
                 "video": f"{m['id']}.mp4",
                 "thumb": f"{m['id']}-thumb.jpg" if m["format"] == "long" else None,
                 "status": "pending", **({"replace": True, "rebuilt_at": m["rebuilt_at"]} if m.get("replace") else {})}
                for m in report]
    json.dump(manifest, open(os.path.join(ROOT, "out", "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def main():
    if "--rebuild" in sys.argv:
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        report = rebuild(dt.date.fromisoformat(sys.argv[sys.argv.index("--rebuild") + 1]))
        write_manifest(report)
        print(f"✅ أُعيد صنع {len(report)} فيديو")
        return
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

    # المواعيد اللي عندها فيديو جاهز مسبقاً (من فرع videos)
    taken = {}  # (موعد+نوع+لغة) -> id
    try:
        import urllib.request
        url = os.environ.get("MANIFEST_URL")
        if url:
            for m in json.load(urllib.request.urlopen(url, timeout=30)):
                taken[m["publish_at"][:16] + m["format"] + m.get("lang", "ar")] = m["id"]
    except Exception as e:
        print("لا يوجد manifest سابق:", e)

    def _key(fmt, d, t):
        hh, mm = map(int, t.split(":"))
        return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ).isoformat()[:16] + fmt

    missing_ar = [x for x in slots if _key(x[0], x[1], x[2]) + "ar" not in taken]
    need = {f: sum(1 for s in missing_ar if s[0] == f) for f in ("short", "long")}
    # املأ الطابور إذا قلّ (يحتفظ دائماً بحلقات احتياطية)
    has_ai = os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    for fmt, reserve in (("short", 4), ("long", 1)):
        if has_ai and need[fmt] and len(pool(fmt)) < need[fmt] + reserve:
            writer.write(need[fmt] + reserve - len(pool(fmt)), fmt)

    cfg = json.load(open(os.path.join(ROOT, "schedule.json"), encoding="utf-8"))
    en_cfg = cfg.get("en") or {}

    def en_slot(fmt, d, t):
        """موعد القناة الإنجليزية: مساء أمريكا بدل نفس موعد العربي (من schedule.json)."""
        nt = (en_cfg.get(fmt) or {}).get(t)
        if not nt:
            return d, t
        return (d + dt.timedelta(days=1) if en_cfg.get("next_day") else d), nt

    def produce(path, d, t):
        if json.load(open(path, encoding="utf-8")).get("lang") == "en":
            d, t = en_slot(fmt_of(path), d, t)
        out, meta = make.build(path)
        hh, mm = map(int, t.split(":"))
        meta["publish_at"] = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=TZ).isoformat()
        json.dump(meta, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        shutil.move(path, os.path.join(DONE, os.path.basename(path)))
        report.append(meta)
        return meta

    def fmt_of(path):
        return json.load(open(path, encoding="utf-8")).get("format", "short")

    report = []
    for fmt, d, t, _ in slots:
        k = _key(fmt, d, t)
        ar_id = taken.get(k + "ar")
        if not ar_id:
            files = pool(fmt)
            if not files:
                print(f"⚠️ لا يوجد سكربت {fmt} لموعد {d} {t}")
                continue
            ar_id = produce(files[0], d, t)["id"]
        ed, et = en_slot(fmt, d, t)
        if (k + "en" not in taken and _key(fmt, ed, et) + "en" not in taken
                and ar_id + "-en" not in taken.values()):
            tw = twin(ar_id)
            if not tw and has_ai:
                try:
                    tw = writer.translate(os.path.join(DONE, ar_id + ".json"))
                except Exception as e:
                    print("تعذّرت الترجمة:", ar_id, str(e)[:150])
            if tw:
                produce(tw, d, t)
    json.dump(report, open(os.path.join(ROOT, "out", "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(state, open(state_p, "w"))
    # ملف التعليمات لـ Claude حتى يرفع ويجدول
    manifest = [{"id": m["id"], "format": m["format"], "lang": m.get("lang", "ar"), "title": m["title"],
                 "description": m["description"], "tags": m["tags"], "publish_at": m["publish_at"],
                 "video": f"{m['id']}.mp4",
                 "thumb": f"{m['id']}-thumb.jpg" if m["format"] == "long" else None,
                 "status": "pending"} for m in report]
    json.dump(manifest, open(os.path.join(ROOT, "out", "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(report)} فيديو جاهز ليوم {day}")


if __name__ == "__main__":
    main()
