"""التعليق الصوتي: صوت نسائي عربي (Microsoft Neural عبر edge-tts) مع توقيت كل كلمة."""
import asyncio
import json
import os
import subprocess

VOICES = {"ar": os.environ.get("KAYF_VOICE") or "ar-SA-ZariyahNeural",
          "en": os.environ.get("KAYF_VOICE_EN") or "en-US-AvaNeural"}
VOICE = VOICES["ar"]
LANG = ["ar"]
RATE = os.environ.get("KAYF_RATE") or "+14%"   # أسرع قليلاً من الطبيعي
PITCH = os.environ.get("KAYF_PITCH") or "+0Hz"


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(out.stdout.strip())


async def _tts(text, mp3):
    import edge_tts
    rate = RATE if LANG[0] == "ar" else (os.environ.get("KAYF_RATE_EN") or "+6%")
    com = edge_tts.Communicate(text, VOICES[LANG[0]], rate=rate, pitch=PITCH, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as fh:
        async for ch in com.stream():
            if ch["type"] == "audio":
                fh.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "t": ch["offset"] / 1e7,
                              "d": ch["duration"] / 1e7})
    return words


def _even_words(text, dur):
    ws = text.split()
    total = sum(len(w) + 2 for w in ws)
    t, out = 0.0, []
    for w in ws:
        d = dur * (len(w) + 2) / total
        out.append({"w": w, "t": t, "d": d})
        t += d
    return out


def _gtts(text, mp3):
    """بديل احتياطي (Google Translate TTS) إذا تعذّر edge-tts — جودة أقل."""
    import re
    import tempfile
    import urllib.parse
    import urllib.request
    parts, cur = [], ""
    for w in re.split(r"(?<=[،,.؟?!])\s+|\s+", text):
        if len(cur) + len(w) + 1 > 180 and cur:
            parts.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        parts.append(cur)
    tmp = tempfile.mkdtemp()
    files = []
    for i, p in enumerate(parts):
        url = (f"https://translate.google.com/translate_tts?ie=UTF-8&tl={LANG[0]}&client=tw-ob&q="
               + urllib.parse.quote(p))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        f = os.path.join(tmp, f"{i}.mp3")
        open(f, "wb").write(urllib.request.urlopen(req, timeout=30).read())
        files.append(f)
    lst = os.path.join(tmp, "l.txt")
    open(lst, "w").writelines(f"file '{f}'\n" for f in files)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-af", "atempo=1.45,silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.25:stop_threshold=-45dB",
                    mp3], check=True)


def speak(text, mp3, silent=False):
    """يرجع (المدة بالثواني، قائمة الكلمات بتوقيتها). silent=True للتجربة بدون إنترنت."""
    if not silent:
        for attempt in range(3):
            try:
                words = asyncio.run(_tts(text, mp3))
                if os.path.getsize(mp3) > 1000:
                    dur = duration(mp3)
                    if len(words) < len(text.split()) * 0.5:
                        words = _even_words(text, dur)
                    return dur, words
            except Exception as e:  # شبكة متقطعة: نعيد المحاولة
                print("TTS retry", attempt, str(e)[:120])
                if "certificate" in str(e).lower() or "websocket" in str(e).lower():
                    break
        if os.environ.get("KAYF_TTS_FALLBACK", "1") == "1":
            _gtts(text, mp3)
            dur = duration(mp3)
            return dur, _even_words(text, dur)
        raise RuntimeError("فشل توليد الصوت")
    dur = max(1.6, len(text.split()) * 0.36)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    "anullsrc=r=24000:cl=mono", "-t", f"{dur:.2f}", mp3], check=True)
    return dur, _even_words(text, dur)


if __name__ == "__main__":
    import sys
    d, w = speak(sys.argv[1], "test.mp3")
    print(d, json.dumps(w, ensure_ascii=False)[:300])
