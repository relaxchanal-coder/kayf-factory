"""صور حقيقية مجانية للمشاهد: من ويكيميديا كومنز (برخص حرة) أو مكتبة ناسا (ملكية عامة).

في JSON الحلقة، أي مشهد (أو right/left في compare) يقبل الحقل "image":
  - اسم ملف دقيق من كومنز:  "File:Microwave oven interior.jpg"
  - أو كلمات بحث إنجليزية:   "microwave oven magnetron"
إذا لم توجد صورة مناسبة يبقى الرمز (الإيموجي) كما هو، فلا يفشل الفيديو أبداً.
نسب كل صورة (المصوّر + الرخصة) تُضاف تلقائياً لوصف الفيديو.
"""
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "KayfFactory/1.0 (https://github.com/relaxchanal-coder/kayf-factory; educational videos)"}
OK_LIC = ("public domain", "pd", "cc0", "cc by", "cc-by")
BAD = re.compile(r"(logo|icon|flag|map of|diagram|chart|svg|coat of arms|signature|nude|corpse|dead|blood|wound|"
                 r"victim|weapon|gun|portrait of|selfie)", re.I)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "out", "_img")


def _get(url, tries=4):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()
        except Exception as e:  # 429/مهلة: انتظار ثم إعادة
            if i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


def _strip(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h or "")).strip()


def _commons(query):
    p = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
         "iiurlwidth": 1600}
    if query.startswith("File:"):
        p["titles"] = query
    else:
        p.update(generator="search", gsrsearch=f"{query} filetype:bitmap", gsrnamespace=6, gsrlimit=12)
    d = json.loads(_get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)))
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0))
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        title = pg.get("title", "")
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 900:
            continue
        if not any(x in lic.lower() for x in OK_LIC):
            continue
        if not query.startswith("File:") and BAD.search(title + " " + _strip(m.get("ImageDescription", {}).get("value"))[:200]):
            continue
        if ii.get("width", 1) / max(1, ii.get("height", 1)) < 0.6:  # صور طويلة جداً لا تناسب الإطار
            continue
        return {"url": ii.get("thumburl") or ii["url"], "title": title[5:],
                "artist": _strip(m.get("Artist", {}).get("value"))[:80] or "Wikimedia Commons",
                "license": lic, "source": "Wikimedia Commons"}
    return None


def _nasa(query):
    d = json.loads(_get("https://images-api.nasa.gov/search?" + urllib.parse.urlencode(
        {"q": query, "media_type": "image"})))
    for it in d["collection"]["items"][:8]:
        nid = it["data"][0]["nasa_id"]
        h = [x["href"] for x in json.loads(_get(f"https://images-api.nasa.gov/asset/{urllib.parse.quote(nid)}"))
             ["collection"]["items"]]
        c = [x for x in h if x.lower().endswith(("~large.jpg", "~medium.jpg", "~orig.jpg"))]
        if c:
            c.sort(key=lambda x: (0 if "~large" in x else 1 if "~medium" in x else 2))
            return {"url": c[0].replace("http://", "https://"), "title": it["data"][0]["title"],
                    "artist": "NASA", "license": "Public domain", "source": "NASA"}
    return None


def fetch(query):
    """يرجع (مسار الملف المحلي، معلومات النسب) أو (None, None)."""
    if not query or os.environ.get("KAYF_IMAGES", "1") != "1":
        return None, None
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(query.encode()).hexdigest()[:12]
    meta_p = os.path.join(CACHE, key + ".json")
    if os.path.exists(meta_p):
        info = json.load(open(meta_p, encoding="utf-8"))
        return (info.get("file"), info) if info.get("file") and os.path.exists(info["file"]) else (None, None)
    info = None
    # ناسا فقط عند طلبها صراحة ("nasa ...")؛ غير ذلك ويكيميديا كومنز
    for fn in ((_nasa,) if query.lower().startswith("nasa ") else (_commons,)):
        try:
            q = query[5:] if query.lower().startswith("nasa ") else query
            info = fn(q)
            if info:
                break
        except Exception as e:
            print("صورة:", fn.__name__, query, str(e)[:80])
    if not info:
        json.dump({}, open(meta_p, "w"))
        print("⚠️ لا صورة لـ:", query)
        return None, None
    try:
        raw = _get(info["url"])
        ext = ".png" if info["url"].lower().endswith(".png") else ".jpg"
        f = os.path.join(CACHE, key + ext)
        open(f, "wb").write(raw)
        from PIL import Image
        Image.open(f).verify()
        info["file"] = f
        json.dump(info, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False)
        print("🖼️", query, "←", info["title"][:60], f"({info['license']})")
        return f, info
    except Exception as e:
        print("صورة: فشل التحميل", query, str(e)[:80])
        return None, None


def attach(scenes):
    """يضيف image_file لكل مشهد فيه image، ويرجع قائمة النسب (بدون تكرار)."""
    credits = []
    for s in scenes:
        for obj in [s] + [s[k] for k in ("right", "left") if isinstance(s.get(k), dict)]:
            q = obj.get("image")
            if not q:
                continue
            f, info = fetch(q)
            if f:
                obj["image_file"] = f
                c = f"{info['artist']} — {info['license']} ({info['source']})"
                if c not in credits:
                    credits.append(c)
            time.sleep(0.5)
    return credits


def credit_line(credits, lang):
    if not credits:
        return ""
    head = "الصور:" if lang == "ar" else "Photos:"
    return head + " " + "؛ ".join(credits[:12]) if lang == "ar" else head + " " + "; ".join(credits[:12])
