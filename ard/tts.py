"""معلومات الأرض: يولّد صوت مايكروسوفت (edge-tts) لكل مقطع في ard/tts/<id>.json
ويحفظ out/<id>/seg_XX.mp3 و timings.json (مدة كل مقطع + توقيت الكلمات)."""
import asyncio, json, os, subprocess, sys, glob

VOICE = os.environ.get("ARD_VOICE", "ar-SA-HamedNeural")
RATE = os.environ.get("ARD_RATE", "+6%")
PITCH = os.environ.get("ARD_PITCH", "-4Hz")
FX = ("highpass=f=55,equalizer=f=130:t=q:w=1.1:g=3,equalizer=f=320:t=q:w=1.4:g=-1.5,"
      "equalizer=f=3800:t=q:w=1.6:g=1.5,acompressor=threshold=-21dB:ratio=2.6:attack=6:release=90:makeup=1.5")


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "default=nw=1:nk=1", p], capture_output=True, text=True).stdout.strip())


async def one(text, mp3):
    import edge_tts
    for attempt in range(5):
        try:
            com = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
            words = []
            with open(mp3, "wb") as fh:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        fh.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append({"w": ch["text"], "t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7})
            if os.path.getsize(mp3) > 1000:
                return words
        except Exception as e:
            print("retry", attempt, e)
            await asyncio.sleep(3 + attempt * 3)
    raise SystemExit("tts failed: " + text[:40])


def main():
    for req in sorted(glob.glob("ard/tts/*.json")):
        vid = os.path.splitext(os.path.basename(req))[0]
        out = f"out/{vid}"
        if os.path.exists(f"{out}/timings.json"):
            continue
        os.makedirs(out, exist_ok=True)
        segs = json.load(open(req))
        tim = []
        for i, text in enumerate(segs):
            raw = f"{out}/raw_{i:02d}.mp3"
            words = asyncio.run(one(text, raw))
            mp3 = f"{out}/seg_{i:02d}.mp3"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", FX, "-ar", "44100", "-b:a", "160k", mp3], check=True)
            os.remove(raw)
            tim.append({"i": i, "dur": round(dur(mp3), 3), "words": words})
            print(vid, i, tim[-1]["dur"])
        json.dump(tim, open(f"{out}/timings.json", "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
