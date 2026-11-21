"""يدمج فيديوهات هذا التشغيل مع الموجود في فرع videos، ويحذف ما مضى عليه أكثر من 3 أيام."""
import datetime as dt
import glob
import json
import os
import shutil
import sys

dest, out = sys.argv[1], sys.argv[2]
old = json.load(open(os.path.join(dest, "manifest.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(dest, "manifest.json")) else []
new = json.load(open(os.path.join(out, "manifest.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(out, "manifest.json")) else []
ids = {m["id"] for m in new}
merged = [m for m in old if m["id"] not in ids] + new
cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=3)
keep = []
for m in merged:
    if dt.datetime.fromisoformat(m["publish_at"]) < cutoff:
        for f in (m.get("video"), m.get("thumb")):
            if f and os.path.exists(os.path.join(dest, f)):
                os.remove(os.path.join(dest, f))
    else:
        keep.append(m)
keep.sort(key=lambda m: m["publish_at"])
for f in glob.glob(os.path.join(out, "*", "*.mp4")) + glob.glob(os.path.join(out, "*", "*-thumb.jpg")):
    shutil.copy(f, dest)
json.dump(keep, open(os.path.join(dest, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"manifest: {len(keep)} فيديو")
