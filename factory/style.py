"""هوية بصرية مختلفة لكل حلقة حتى لا تبدو الفيديوهات نسخة من قالب واحد.

كل حلقة تأخذ تركيبة ثابتة (نفس الحلقة = نفس الشكل دائماً، والتوأم العربي/الإنجليزي
يتشاركان الشكل) من: لوحة ألوان، نمط خلفية، جزيئات، خط العناوين، حركة الانتقال،
شكل الترجمة، شكل إطار الأيقونة، تخطيط المقدمة، مكان شريط التقدم، استدارة البطاقات.

اللوحة تدور بخطوة ثابتة مع رقم الحلقة، فلا تتكرر لوحة في حلقتين متتاليتين.
تقدر تفرض أي خيار يدوياً من JSON الحلقة:  "style": {"palette": "paper", "bg": "dots"}
"""
import math
import re
import zlib

# (خلفية 1، خلفية 2، لون مميز، لون ثانوي، لون النص، لون النص فوق المميز، فاتحة؟)
PALETTES = {
    "cyan":     ((6, 14, 38), (12, 40, 78), (0, 220, 255), (255, 214, 0), (255, 255, 255), (6, 14, 38), False),
    "paper":    ((248, 242, 230), (232, 220, 198), (226, 84, 36), (24, 104, 196), (30, 28, 36), (255, 255, 255), True),
    "purple":   ((16, 6, 36), (52, 18, 92), (190, 110, 255), (0, 230, 200), (255, 255, 255), (16, 6, 36), False),
    "gold":     ((10, 10, 14), (34, 28, 20), (255, 196, 60), (255, 110, 80), (255, 248, 235), (20, 16, 10), False),
    "sky":      ((234, 245, 255), (198, 224, 250), (18, 104, 226), (255, 140, 0), (14, 28, 58), (255, 255, 255), True),
    "green":    ((4, 24, 18), (10, 62, 46), (40, 240, 140), (255, 220, 80), (255, 255, 255), (4, 24, 18), False),
    "magenta":  ((24, 4, 28), (66, 10, 72), (255, 64, 172), (120, 220, 255), (255, 255, 255), (24, 4, 28), False),
    "mint":     ((236, 250, 242), (204, 238, 222), (0, 146, 108), (236, 72, 88), (16, 40, 34), (255, 255, 255), True),
    "orange":   ((28, 10, 6), (70, 26, 10), (255, 140, 0), (255, 230, 120), (255, 255, 255), (28, 10, 6), False),
    "teal":     ((4, 28, 32), (8, 62, 68), (0, 214, 192), (255, 122, 100), (255, 255, 255), (4, 28, 32), False),
    "slate":    ((18, 22, 28), (42, 50, 62), (186, 255, 72), (92, 200, 255), (255, 255, 255), (18, 22, 28), False),
    "red":      ((30, 4, 10), (84, 12, 28), (255, 70, 90), (255, 210, 120), (255, 255, 255), (30, 4, 10), False),
    "blue":     ((4, 10, 30), (16, 36, 96), (70, 150, 255), (255, 190, 60), (255, 255, 255), (4, 10, 30), False),
}
PALETTE_ORDER = list(PALETTES)

OPTIONS = {
    "bg": ["grid", "dots", "diag", "rings", "waves", "plain"],     # نمط الخلفية
    "gradient": ["vertical", "diagonal", "radial"],               # اتجاه التدرّج
    "particles": ["float", "bokeh", "stars", "none"],             # الجزيئات المتحركة
    "font": ["Cairo", "Tajawal", "Lalezar"],                      # خط العناوين
    "transition": ["fade", "slide", "zoom", "rise", "wipe"],      # الانتقال بين المشاهد
    "subs": ["box", "band", "pop"],                               # شكل الترجمة
    "frame": ["rings", "tile", "orbit"],                          # إطار الأيقونة
    "hook": ["emoji_top", "text_top"],                            # تخطيط المقدمة
    "progress": ["top", "bottom", "segments"],                    # شريط التقدم
    "tag": ["center", "corner"],                                  # مكان اسم القناة
    "radius": [0.3, 0.7, 1.0, 1.4],                               # استدارة البطاقات
}


STRIDES = {"bg": 5, "gradient": 2, "particles": 3, "font": 1, "transition": 2, "subs": 2,
           "frame": 1, "hook": 1, "progress": 2, "tag": 1, "radius": 3}
OFFSETS = {"bg": 0, "gradient": 1, "particles": 2, "font": 0, "transition": 3, "subs": 1,
           "frame": 2, "hook": 0, "progress": 1, "tag": 1, "radius": 2}


def base_id(vid):
    return re.sub(r"-(en|ar)$", "", vid)


def _num(vid):
    m = re.match(r"(\d+)", vid)
    return int(m.group(1)) if m else zlib.crc32(vid.encode()) % 997


def pick(vid, script=None):
    """يرجع قاموس الستايل لهذه الحلقة."""
    bid = base_id(vid)
    n = _num(bid)
    # كل خاصية تدور بخطوة أولية مع طولها: حلقتان متتاليتان تختلفان في كل الخصائص،
    # وإزاحات مختلفة لكل خاصية حتى لا تتحرك الخصائص المتساوية الطول معاً.
    st = {}
    for j, (k, v) in enumerate(OPTIONS.items()):
        L = len(v)
        step = next(x for x in (STRIDES.get(k, 1), 1) if x % L and math.gcd(x, L) == 1)
        st[k] = v[(n * step + OFFSETS.get(k, j)) % L]
    # خطوة 5 أولية مع 13 لوحة: كل الحلقات المتتالية بلوحات مختلفة
    st["palette"] = PALETTE_ORDER[(n * 5) % len(PALETTE_ORDER)]
    if PALETTES[st["palette"]][6] and st["subs"] == "pop":
        st["subs"] = "box"  # النص المحدّد على خلفية فاتحة أوضح داخل صندوق
    st.update((script or {}).get("style") or {})
    if st["palette"] not in PALETTES:
        st["palette"] = "cyan"
    return st


def describe(st):
    keys = ["palette", "bg", "gradient", "particles", "font", "transition", "subs", "frame",
            "hook", "progress", "tag", "radius"]
    return ", ".join(f"{k}={st[k]}" for k in keys)


if __name__ == "__main__":
    for i in range(1, 21):
        print(f"{i:03d}", describe(pick(f"{i:03d}-x")))
