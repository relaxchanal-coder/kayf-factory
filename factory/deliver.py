"""التسليم: يرسل الفيديو الجاهز إلى تيليجرام، ويرفعه على يوتيوب (اختياري)."""
import json
import os

import requests


# ---------------- تيليجرام ----------------
def telegram(out_dir, meta, release_url=None):
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        print("تيليجرام غير مفعّل")
        return
    api = f"https://api.telegram.org/bot{tok}"
    vid = meta["id"]
    mp4 = os.path.join(out_dir, f"{vid}.mp4")
    kind = "شورت" if meta["format"] == "short" else "فيديو طويل"
    head = f"🎬 {kind} جديد جاهز للنشر ({meta['duration']:.0f} ثانية)\n\n{meta['title']}"
    if os.path.getsize(mp4) < 49 * 1024 * 1024:
        with open(mp4, "rb") as fh:
            r = requests.post(f"{api}/sendVideo", data={
                "chat_id": chat, "caption": head[:1000], "supports_streaming": "true",
                "width": 1080 if meta["format"] == "short" else 1920,
                "height": 1920 if meta["format"] == "short" else 1080}, files={"video": fh}, timeout=600)
        print("telegram video:", r.status_code, r.text[:200])
    else:
        requests.post(f"{api}/sendMessage", data={
            "chat_id": chat, "text": f"{head}\n\nالملف أكبر من 50MB، حمّله من هنا:\n{release_url}"}, timeout=60)
    # الصورة المصغّرة كملف (بجودة كاملة)
    for name in (f"{vid}-thumb.jpg", f"{vid}-cover.jpg"):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            with open(p, "rb") as fh:
                requests.post(f"{api}/sendDocument", data={"chat_id": chat}, files={"document": fh}, timeout=120)
    # النصوص جاهزة للنسخ، كل واحد برسالة منفصلة
    for label, text in (("العنوان", meta["title"]), ("الوصف", meta["description"]),
                        ("الوسوم", ", ".join(meta["tags"]))):
        requests.post(f"{api}/sendMessage", data={"chat_id": chat, "text": f"📋 {label}:"}, timeout=60)
        requests.post(f"{api}/sendMessage", data={"chat_id": chat, "text": text[:4000]}, timeout=60)


def notify(out_dir, meta, sent_to_youtube=True):
    """رسالة قصيرة + الفيديو للمعاينة."""
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        return
    if not sent_to_youtube:
        return telegram(out_dir, meta)
    api = f"https://api.telegram.org/bot{tok}"
    when = meta["publish_at"].replace("T", " ")[:16]
    kind = "شورت" if meta["format"] == "short" else "فيديو طويل"
    cap = f"✅ {kind} مجدول على يوتيوب\n🕕 {when} بتوقيت بغداد\n\n{meta['title']}"
    mp4 = os.path.join(out_dir, f"{meta['id']}.mp4")
    if os.path.getsize(mp4) < 49 * 1024 * 1024:
        with open(mp4, "rb") as fh:
            requests.post(f"{api}/sendVideo", data={"chat_id": chat, "caption": cap,
                                                    "supports_streaming": "true"},
                          files={"video": fh}, timeout=600)
    else:
        requests.post(f"{api}/sendMessage", data={"chat_id": chat, "text": cap}, timeout=60)


# ---------------- يوتيوب (اختياري) ----------------
def _yt_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def youtube(out_dir, meta):
    if os.environ.get("YT_UPLOAD") != "1" or not os.environ.get("YT_REFRESH_TOKEN"):
        print("رفع يوتيوب التلقائي غير مفعّل")
        return None
    tok = _yt_token()
    body = {"snippet": {"title": meta["title"], "description": meta["description"],
                        "tags": meta["tags"], "categoryId": "28", "defaultLanguage": "ar",
                        "defaultAudioLanguage": "ar"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"),
                       "selfDeclaredMadeForKids": False}}
    mp4 = os.path.join(out_dir, f"{meta['id']}.mp4")
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
                 "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(os.path.getsize(mp4))},
        data=json.dumps(body), timeout=60)
    init.raise_for_status()
    with open(mp4, "rb") as fh:
        up = requests.put(init.headers["Location"], data=fh, timeout=1800,
                          headers={"Content-Type": "video/mp4"})
    up.raise_for_status()
    vid_id = up.json()["id"]
    print("YouTube:", f"https://youtu.be/{vid_id}")
    thumbp = os.path.join(out_dir, f"{meta['id']}-thumb.jpg")
    if meta["format"] == "long" and os.path.exists(thumbp):
        with open(thumbp, "rb") as fh:
            t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid_id}",
                              headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"},
                              data=fh, timeout=120)
        print("thumbnail:", t.status_code)
    return vid_id
