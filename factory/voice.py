"""التعليق الصوتي: صوت رجالي فخم (Microsoft Neural عبر edge-tts) مع توقيت كل كلمة،
ثم معالجة خفيفة (دفء بالترددات المنخفضة + ضغط ناعم) حتى يقترب من صوت معلّق حقيقي."""
import asyncio
import json
import os
import subprocess

VOICES = {"ar": os.environ.get("KAYF_VOICE") or "ar-SA-HamedNeural",
          "en": os.environ.get("KAYF_VOICE_EN") or "en-US-AndrewMultilingualNeural"}
VOICE = VOICES["ar"]
LANG = ["ar"]
RATE = os.environ.get("KAYF_RATE") or "+6%"    # إيقاع طبيعي مريح (كان +14%)
PITCH = os.environ.get("KAYF_PITCH") or "-2Hz"  # أعمق قليلاً للعربي
PITCH_EN = os.environ.get("KAYF_PITCH_EN") or "+0Hz"  # الأصوات متعددة اللغات لا تقبل تغيير الطبقة
# دفء خفيف + وضوح + ضغط ناعم (مثل ميكروفون استوديو) — KAYF_VOICE_FX=0 لإيقافه
VOICE_FX = ("highpass=f=55,equalizer=f=130:t=q:w=1.1:g=3,equalizer=f=320:t=q:w=1.4:g=-1.5,"
            "equalizer=f=3800:t=q:w=1.6:g=1.5,"
            "acompressor=threshold=-21dB:ratio=2.6:attack=6:release=90:makeup=1.5")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(out.stdout.strip())


# صوت احتياطي ثابت إذا تعثّر الصوت الأساسي (الأصوات متعددة اللغات تفشل أحياناً)
BACKUP = {"ar": "ar-SA-HamedNeural", "en": "en-US-ChristopherNeural"}


async def _tts(text, mp3, voice_name=None):
    import edge_tts
    voice_name = voice_name or VOICES[LANG[0]]
    rate = RATE if LANG[0] == "ar" else (os.environ.get("KAYF_RATE_EN") or "+4%")
    pitch = PITCH if LANG[0] == "ar" else PITCH_EN
    if "Multilingual" in voice_name:
        pitch = "+0Hz"
    elif voice_name == BACKUP["en"] and LANG[0] == "en":
        pitch = "-2Hz"
    com = edge_tts.Communicate(text, voice_name, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as fh:
        async for ch in com.stream():
            if ch["type"] == "audio":
                fh.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "t": ch["offset"] / 1e7,
                              "d": ch["duration"] / 1e7})
    return words


def polish(mp3):
    """معالجة صوتية خفيفة لصوت أدفأ وأقرب للتسجيل الحقيقي (لا تغيّر المدة)."""
    if os.environ.get("KAYF_VOICE_FX", "1") != "1":
        return
    tmp = mp3 + ".fx.mp3"
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-af", VOICE_FX,
                        "-ar", "24000", "-b:a", "128k", tmp])
    if r.returncode == 0 and os.path.getsize(tmp) > 1000:
        os.replace(tmp, mp3)


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
        import time
        main = VOICES[LANG[0]]
        plan = [main] * 10 + ([BACKUP[LANG[0]]] * 3 if BACKUP[LANG[0]] != main else [])
        for attempt, vname in enumerate(plan):
            try:
                words = asyncio.run(_tts(text, mp3, vname))
                if os.path.getsize(mp3) > 1000:
                    if vname != main:
                        print("TTS: استُخدم الصوت الاحتياطي", vname)
                    polish(mp3)
                    dur = duration(mp3)
                    if len(words) < len(text.split()) * 0.5:
                        words = _even_words(text, dur)
                    return dur, words
            except Exception as e:  # شبكة متقطعة أو تعثّر الخدمة: نعيد المحاولة
                print("TTS retry", attempt, vname, str(e)[:100])
                if "certificate" in str(e).lower():
                    break
                time.sleep(1.5)
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
