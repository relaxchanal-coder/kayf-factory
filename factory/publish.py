"""يرسل فيديوهات الغد إلى Make (ويب هوك) حتى يرفعها على يوتيوب ويجدولها، ويبلغك على تيليجرام.

يحتاج: MAKE_WEBHOOK_URL و ASSETS_BASE (رابط ملفات الـ Release).
"""
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deliver  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    report = json.load(open(os.path.join(ROOT, "out", "report.json"), encoding="utf-8"))
    hook, base = os.environ.get("MAKE_WEBHOOK_URL"), os.environ.get("ASSETS_BASE", "")
    ok = 0
    for m in report:
        vid = m["id"]
        payload = {
            "id": vid, "format": m["format"], "title": m["title"], "description": m["description"],
            "tags": ",".join(m["tags"]), "category_id": "28", "publish_at": m["publish_at"],
            "video_url": f"{base}/{vid}.mp4", "video_name": f"{vid}.mp4",
            "thumb_url": f"{base}/{vid}-thumb.jpg" if m["format"] == "long" else "",
            "has_thumb": m["format"] == "long",
        }
        if hook:
            r = requests.post(hook, json=payload, timeout=120)
            print("Make:", vid, r.status_code, r.text[:100])
            ok += r.ok
        out = os.path.join(ROOT, "out", vid)
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            deliver.notify(out, m, sent_to_youtube=bool(hook))
    if hook and ok < len(report):
        sys.exit("بعض الفيديوهات ما انرسلت لـ Make")


if __name__ == "__main__":
    main()
