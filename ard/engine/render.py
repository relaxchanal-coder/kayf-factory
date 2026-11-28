"""Render all scenes to per-scene MP4s, build music+SFX, mux with narration."""
import json, os, subprocess, sys, math
import numpy as np
from multiprocessing import Pool

FPS = 30
SR = 44100
LEAD = 0.35      # silence before narration
TAIL = 3.2       # end card after last word


def timeline():
    seg = json.load(open('audio/segments_t.json'))       # [[start,end],...] in narration time
    starts = [0.0] + [LEAD + s[0] - 0.12 for s in seg[1:]]
    total = LEAD + seg[-1][1] + TAIL
    ends = starts[1:] + [total]
    # snap to frame grid
    fr = [round(x * FPS) for x in starts] + [round(total * FPS)]
    return [(fr[i], fr[i + 1]) for i in range(len(starts))], seg, total


def render_scene(i):
    from scenes import SCENES
    from engine import finish, W, H
    (f0, f1), seg, total = timeline()[0][i], timeline()[1], timeline()[2]
    n = f1 - f0
    dur = n / FPS
    tmp = f'build/scene{i:02d}.tmp.mp4'
    out = f'build/scene{i:02d}.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                          '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    f = SCENES[i]
    speech_end = (LEAD + seg[-1][1]) - f0 / FPS
    for k in range(n):
        t = k / FPS
        img = f(t, dur, speech_end) if i == len(SCENES) - 1 else f(t, dur)
        img = finish(img, t + f0 / FPS)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return i, n


# ----------------------------------------------------------------- audio
def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lowpass(x, fc):
    # one-pole
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def music(total):
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    # slow minor progression, 4 s per chord
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    span = 4.0
    for ci in range(int(total / span) + 1):
        notes = chords[ci % 4]
        s0 = int(ci * span * SR)
        ln = int((span + 1.5) * SR)
        s1 = min(n, s0 + ln)
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR
        e = env(s1 - s0, 1.2, 1.5)
        for m in notes:
            fq = 440 * 2 ** ((m - 69) / 12)
            out[s0:s1] += e * (0.5 * np.sin(2 * np.pi * fq * tt) + 0.18 * np.sin(2 * np.pi * fq * 2.003 * tt)) / 3
        bass = 440 * 2 ** ((notes[0] - 24 - 69) / 12)
        out[s0:s1] += e * 0.55 * np.sin(2 * np.pi * bass * tt)
    # soft pulse (ticks) at 96 bpm
    beat = 60 / 96
    k = 0
    while k * beat < total:
        s = int(k * beat * SR)
        ln = int(0.05 * SR)
        if s + ln < n:
            tt = np.arange(ln) / SR
            out[s:s + ln] += 0.12 * np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 90)
        k += 1
    out = out / (np.abs(out).max() + 1e-9)
    out *= env(n, 1.0, 2.5)
    return out


def sfx_pop(f=900):
    ln = int(0.09 * SR)
    t = np.arange(ln) / SR
    fr = f * np.exp(-t * 18)
    return 0.6 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 40)


def sfx_whoosh(d=0.45, seed=0):
    rng = np.random.default_rng(seed)
    ln = int(d * SR)
    x = rng.normal(0, 1, ln)
    x = lowpass(x, 1800)
    e = np.sin(np.linspace(0, np.pi, ln)) ** 2
    return 0.9 * x * e / (np.abs(x).max() + 1e-9)


def sfx_boom(seed=1):
    rng = np.random.default_rng(seed)
    ln = int(1.4 * SR)
    t = np.arange(ln) / SR
    x = np.sin(2 * np.pi * 48 * t * (1 - 0.3 * t)) * np.exp(-t * 3.2)
    nz = lowpass(rng.normal(0, 1, ln), 500) * np.exp(-t * 5)
    y = x + 2.5 * nz
    return 0.95 * y / np.abs(y).max()


def sfx_scribble(d=0.5, seed=2):
    rng = np.random.default_rng(seed)
    ln = int(d * SR)
    x = rng.normal(0, 1, ln)
    x = x - lowpass(x, 2500)
    am = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * np.arange(ln) / SR)
    return 0.25 * x * am * env(ln, 0.03, 0.12)


def add(track, clip, at, gain=1.0):
    s = int(at * SR)
    if s >= len(track) or s < 0:
        return
    e = min(len(track), s + len(clip))
    track[s:e] += clip[:e - s] * gain


def build_audio():
    scenes, seg, total = timeline()
    st = [a / FPS for a, b in scenes]
    du = [(b - a) / FPS for a, b in scenes]
    n = int(total * SR)
    # narration
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'audio/narration.wav', '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True).stdout
    v = np.frombuffer(raw, np.float32).astype(np.float64)
    voice = np.zeros(n)
    add(voice, v, LEAD)
    fx = np.zeros(n)
    for i, s in enumerate(st[1:], 1):
        add(fx, sfx_whoosh(0.4, i), s - 0.2, 0.22)
    # scene-specific events (relative times mirror scenes.py)
    A, B, C, D, E, F, G, Hh, I, J, K, L, M = range(13)
    ev = [(A, 0.15, 'pop'), (A, 0.9, 'pop'), (A, du[A] * 0.62, 'boom'), (B, 0.0, 'pop'), (B, du[B] * 0.22, 'scr'),
          (B, du[B] * 0.45, 'pop'), (C, du[C] * 0.45, 'pop'), (C, du[C] * 0.5, 'pop'), (C, du[C] * 0.62, 'pop'),
          (C, du[C] * 0.76, 'scr'), (D, 0.3, 'pop'), (E, 0.0, 'pop'), (E, du[E] * 0.18, 'scr'), (E, du[E] * 0.62, 'scr'),
          (F, du[F] * 0.12, 'pop'), (F, du[F] * 0.2, 'pop'), (F, du[F] * 0.3, 'pop'), (F, du[F] * 0.48, 'pop'),
          (F, du[F] * 0.62, 'pop'), (F, du[F] * 0.75, 'scr'), (G, du[G] * 0.06, 'boom'), (G, du[G] * 0.34, 'boom'),
          (G, du[G] * 0.5, 'pop'), (Hh, 0.05, 'pop'), (Hh, 0.3, 'pop'), (Hh, du[Hh] * 0.62, 'scr'), (I, 0.1, 'pop'),
          (I, du[I] * 0.45, 'scr'), (J, du[J] * 0.72, 'pop'), (K, 0.0, 'pop'), (K, du[K] * 0.35, 'pop'),
          (K, du[K] * 0.6, 'scr'), (L, 0.0, 'pop'), (L, du[L] * 0.22, 'pop'), (L, du[L] * 0.38, 'pop'),
          (L, du[L] * 0.7, 'pop'), (L, du[L] * 0.74, 'pop'), (M, 0.0, 'pop')]
    for k, (sc, rt, kind) in enumerate(ev):
        at = st[sc] + rt
        if kind == 'pop':
            add(fx, sfx_pop(700 + (k * 97) % 500), at, 0.35)
        elif kind == 'boom':
            add(fx, sfx_boom(k), at, 0.55)
        else:
            add(fx, sfx_scribble(0.5, k), at, 0.9)
    mus = music(total) * 0.085
    # duck music under voice
    venv = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')
    duck = 1 - 0.45 * np.clip(venv / (venv.max() * 0.25 + 1e-9), 0, 1)
    mix = voice / (np.abs(voice).max() + 1e-9) * 0.9 + fx + mus * duck
    mix = np.tanh(mix * 1.05) * 0.95
    st2 = np.stack([mix, mix], 1).astype(np.float32)
    st2.tofile('build/mix.f32')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', 'build/mix.f32',
                    '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11', '-ar', str(SR), '-c:a', 'pcm_s16le', 'build/mix.wav'], check=True)


def mux():
    scenes, seg, total = timeline()
    with open('build/list.txt', 'w') as f:
        for i in range(len(scenes)):
            f.write(f"file 'scene{i:02d}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/list.txt', '-c', 'copy',
                    'build/video_only.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', 'build/video_only.mp4', '-i', 'build/mix.wav', '-map', '0:v',
                    '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
                    'build/final.tmp.mp4'], check=True)
    os.replace('build/final.tmp.mp4', 'build/derna_vox_sample.mp4')


if __name__ == '__main__':
    os.makedirs('build', exist_ok=True)
    what = sys.argv[1]
    if what == 'video':
        idx = [int(x) for x in sys.argv[2:]] or list(range(13))
        with Pool(2) as pool:
            for i, n in pool.imap_unordered(render_scene, idx):
                print('scene', i, 'frames', n, flush=True)
    elif what == 'audio':
        build_audio()
    elif what == 'mux':
        mux()
