"""كاتب السكربتات: يأخذ موضوعاً من topics.txt ويكتب حلقة جديدة بصيغة JSON.

يعمل مع Gemini (مجاني: GEMINI_API_KEY) أو Claude (ANTHROPIC_API_KEY).
الاستخدام:  python factory/writer.py --count 7 [--format short|long]
"""
import json
import os
import re
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, "content", "queue")
DONE = os.path.join(ROOT, "content", "done")
TOPICS = os.path.join(ROOT, "topics.txt")
TYPES = {"hook", "icon", "steps", "stat", "compare", "flow", "fact", "outro"}
THEMES = ["cyan", "orange", "purple", "green", "red", "blue"]

GUIDE = """أنت كاتب محتوى لقناة يوتيوب عربية اسمها «كيف يعمل؟» تشرح العلوم والتكنولوجيا بموشن جرافيك.
اكتب حلقة عن الموضوع: «{topic}».
الصيغة: {fmt_desc}

القواعد:
- لغة عربية فصحى بسيطة وقريبة من الناس، جمل قصيرة وحماسية، بدون حشو.
- الدقة العلمية أهم شيء: لا تخترع أرقاماً. إذا لم تكن متأكداً من رقم فلا تستخدم مشهد stat.
- أول مشهد hook يشد الانتباه في أول 3 ثوانٍ بسؤال أو مفاجأة.
- كل مشهد فيه "say" (ما تقوله المعلقة، 12 إلى 35 كلمة) + عناصر الشاشة.
- الأرقام في "say" تُكتب بالحروف لتنطقها المعلقة صح، وفي حقول الشاشة بالأرقام.
- نصوص الشاشة قصيرة جداً (حتى 6 كلمات) وبدون إيموجي داخلها.
- آخر مشهد outro يدعو للاشتراك ويشوّق للحلقة الجاية.
- لا تكرر نفس نوع المشهد مرتين متتاليتين.

أنواع المشاهد المسموحة (type):
hook: {{emoji, text}}
icon: {{emoji, caption}}
steps: {{title, items: [2-4 نصوص قصيرة]}}
stat: {{emoji, number (رقم أو نص قصير مثل "95%"), unit, label}}
compare: {{right: {{emoji,label,sub}}, left: {{emoji,label,sub}}}}  (اليمين يظهر أولاً)
flow: {{items: [2-4 من {{emoji,label}}]}}  (سلسلة سبب ← نتيجة)
fact: {{emoji, text, badge اختياري}}
outro: {{text}}

أرجع JSON فقط بهذا الشكل:
{{"id":"{id}","format":"{fmt}","theme":"{theme}","title":"عنوان جذاب أقل من 70 حرفاً مع إيموجي واحد",
"description":"وصف من 2-3 جمل","tags":["كيف يعمل", "..."],
"thumb":{{"text":"سطر أول|سطر ثاني (كلمتان أو ثلاث لكل سطر)","emoji":"إيموجي"}},
"scenes":[...]}}

مثال كامل لحلقة جيدة:
{example}
"""


def slug(i, topic):
    base = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")[:20] or "ep"
    return f"{i:03d}-{base}" if base != "ep" else f"{i:03d}-ep"


def ask_llm(prompt):
    if os.environ.get("GEMINI_API_KEY"):
        model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": os.environ["GEMINI_API_KEY"]}, timeout=180,
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8}})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    if os.environ.get("ANTHROPIC_API_KEY"):
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=300, headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
            json={"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"), "max_tokens": 8000,
                  "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    raise SystemExit("ضع GEMINI_API_KEY أو ANTHROPIC_API_KEY")


def validate(d):
    assert d.get("title") and d.get("scenes"), "ناقص عنوان أو مشاهد"
    sc = [s for s in d["scenes"] if s.get("type") in TYPES and s.get("say")]
    assert len(sc) >= 4, "مشاهد قليلة"
    for s in sc:
        if s["type"] in ("steps", "flow"):
            s["items"] = s.get("items", [])[:4]
            assert len(s["items"]) >= 2
    d["scenes"] = sc
    d["tags"] = (["كيف يعمل"] + [t for t in d.get("tags", []) if t != "كيف يعمل"])[:12]
    return d


def next_number(long=False):
    nums = [int(f[:3]) for d in (QUEUE, DONE) if os.path.isdir(d)
            for f in os.listdir(d) if f[:3].isdigit()]
    nums = [n for n in nums if (n > 100) == long]
    return max(nums or [100 if long else 0]) + 1


def write(count=1, fmt="short"):
    os.makedirs(QUEUE, exist_ok=True)
    topics = [t.strip() for t in open(TOPICS, encoding="utf-8") if t.strip() and not t.startswith("#")]
    example = open(os.path.join(ROOT, "content", "example.json"), encoding="utf-8").read()
    made = 0
    while topics and made < count:
        topic = topics.pop(0)
        n = next_number(fmt == "long")
        vid = f"{n:03d}-{'long' if fmt == 'long' else 'short'}"
        fmt_desc = ("شورت عمودي مدته 35-50 ثانية: 6 أو 7 مشاهد." if fmt == "short" else
                    "فيديو أفقي طويل مدته 4-6 دقائق: من 16 إلى 24 مشهداً، مع قصة متسلسلة وخلاصة.")
        prompt = GUIDE.format(topic=topic, fmt_desc=fmt_desc, id=vid, fmt=fmt,
                              theme=THEMES[n % len(THEMES)], example=example)
        for attempt in range(3):
            try:
                raw = ask_llm(prompt)
                raw = raw[raw.find("{"): raw.rfind("}") + 1]
                d = validate(json.loads(raw))
                d.update(id=vid, format=fmt, topic=topic)
                path = os.path.join(QUEUE, vid + ".json")
                json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print("✍️ ", path, "—", d["title"])
                made += 1
                break
            except Exception as e:
                print("محاولة فاشلة:", topic, e)
        # احذف الموضوع من القائمة بعد استخدامه
        with open(TOPICS, encoding="utf-8") as fh:
            lines = fh.readlines()
        with open(TOPICS, "w", encoding="utf-8") as fh:
            fh.writelines(l for l in lines if l.strip() != topic)
    return made


if __name__ == "__main__":
    cnt = int(sys.argv[sys.argv.index("--count") + 1]) if "--count" in sys.argv else 1
    f = sys.argv[sys.argv.index("--format") + 1] if "--format" in sys.argv else "short"
    write(cnt, f)
