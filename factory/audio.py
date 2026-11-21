"""موسيقى خلفية ومؤثرات صوتية مولّدة بالكود (أصلية 100% بدون حقوق) + الميكس النهائي."""
import subprocess

import numpy as np

SR = 44100


def load(mp3):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def _note(f):
    return 440.0 * 2 ** ((f - 69) / 12)


def music_bed(seconds, seed=0):
    """باد هادئ + نبضات خفيفة، مفتاح وسرعة تتغير حسب الحلقة."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    root = 57 + int(rng.integers(-3, 4))
    progs = [[0, 7, 3, 10], [0, 5, 7, 3], [0, 8, 3, 10], [0, 3, 8, 7]]
    prog = progs[int(rng.integers(len(progs)))]
    bar = 60 / 104 * 4
    # الباد
    for i in range(int(seconds / bar) + 1):
        s, e = int(i * bar * SR), min(n, int((i + 1) * bar * SR) + SR // 2)
        if s >= n:
            break
        deg = prog[i % 4]
        minor = deg in (0, 5, 7)
        chord = [root + deg, root + deg + (3 if minor else 4), root + deg + 7, root + deg + 12]
        tt = t[s:e] - t[s]
        env = np.minimum(1, tt / 0.6) * np.exp(-tt * 0.25)
        seg = np.zeros(e - s, dtype=np.float32)
        for m in chord:
            f = _note(m - 12)
            seg += (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.003 * tt)) * 0.06
        out[s:e] += seg * env
        # أرپيجيو خفيف
        step = bar / 8
        for k in range(8):
            ps = s + int(k * step * SR)
            pe = min(n, ps + int(0.35 * SR))
            if ps >= n:
                break
            m = chord[[0, 2, 1, 3, 2, 1, 3, 2][k]] + 12
            pt = np.arange(pe - ps) / SR
            out[ps:pe] += np.sin(2 * np.pi * _note(m) * pt) * np.exp(-pt * 9) * 0.05
        # كيك ناعم
        for k in range(4):
            ks = s + int(k * bar / 4 * SR)
            ke = min(n, ks + int(0.25 * SR))
            if ks >= n:
                break
            kt = np.arange(ke - ks) / SR
            out[ks:ke] += np.sin(2 * np.pi * (50 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 14) * 0.18
    fade = int(1.5 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


def whoosh(seed=1):
    rng = np.random.default_rng(seed)
    n = int(0.45 * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    # فلتر بسيط متحرك
    k = np.linspace(0.02, 0.4, n)
    y = np.zeros(n, dtype=np.float32)
    acc = 0.0
    for i in range(n):
        acc += k[i] * (noise[i] - acc)
        y[i] = acc
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return y * env * 0.35


def pop():
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * (900 - 2500 * tt) * tt) * np.exp(-tt * 40) * 0.25).astype(np.float32)


def mix(voice_clips, total, sfx_times, pop_times, out_wav, seed=0):
    """voice_clips: [(start_sec, samples)]"""
    n = int(total * SR) + SR
    v = np.zeros(n, dtype=np.float32)
    for st, clip in voice_clips:
        s = int(st * SR)
        v[s:s + len(clip)] += clip[: n - s]
    # تخفيض الموسيقى أثناء الكلام (ducking)
    env = np.abs(v)
    win = int(0.25 * SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    duck = 1.0 - 0.55 * np.clip(env / (env.max() + 1e-6) * 4, 0, 1)
    m = music_bed(n / SR, seed)
    m = np.pad(m, (0, max(0, n - len(m))))[:n] * duck
    fx = np.zeros(n, dtype=np.float32)
    w = whoosh(seed)
    for st in sfx_times:
        s = int(max(0, st - 0.15) * SR)
        fx[s:s + len(w)] += w[: n - s]
    p = pop()
    for st in pop_times:
        s = int(st * SR)
        fx[s:s + len(p)] += p[: n - s]
    out = v * 1.0 + m * 0.55 + fx * 0.6
    out /= max(1.0, np.abs(out).max() / 0.95)
    pcm = (out * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1",
                    "-i", "-", out_wav], input=pcm.tobytes(), check=True)
