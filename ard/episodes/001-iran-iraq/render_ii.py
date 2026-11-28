"""Render «الحرب العراقية الإيرانية» long video + 2 Shorts."""
import json, os, subprocess, sys, math
sys.path.insert(0, '/home/claude/vox')
import numpy as np
from multiprocessing import Pool

ROOT = '/home/claude/iraniraq'
FPS, SR = 30, 44100
LEAD, GAP, TAIL = 0.45, 0.38, 4.2
os.chdir(ROOT)


def plan():
    import scenes_ii as S
    ta = json.load(open('audio/iraniraq/timings.json'))
    tb = json.load(open('audio/iraniraq2/timings.json'))
    items, cur = [], LEAD
    for src, i in S.ORDER:
        d = (ta if src == 'a' else tb)[i]['dur']
        f = f"audio/{'iraniraq' if src == 'a' else 'iraniraq2'}/seg_{i:02d}.mp3"
        items.append({'src': src, 'i': i, 'file': f, 'start': cur, 'dur': d})
        cur += d + GAP
    speech_end = items[-1]['start'] + items[-1]['dur']
    total = speech_end + TAIL
    starts = [0.0] + [it['start'] - 0.12 for it in items[1:]]
    fr = [round(x * FPS) for x in starts] + [round(total * FPS)]
    for k, it in enumerate(items):
        it['f0'], it['f1'] = fr[k], fr[k + 1]
    return items, speech_end, total


def render_scene(k):
    import engine
    engine.grains.cache_clear() if hasattr(engine.grains, 'cache_clear') else None
    rng = np.random.default_rng(77)
    G = [rng.normal(0, 0.9, (engine.H // 2, engine.W // 2)).astype(np.float32) for _ in range(4)]
    engine.grains = lambda: G
    import scenes_ii as S
    items, speech_end, total = plan()
    it = items[k]
    n = it['f1'] - it['f0']
    dur = n / FPS
    tmp, out = f'build/scene{k:02d}.tmp.mp4', f'build/scene{k:02d}.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '1300k',
                          '-bufsize', '2600k', '-g', '60', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    f = S.FINAL_SCENES[k]
    for j in range(n):
        t = j / FPS
        img = f(t, dur, speech_end - it['f0'] / FPS) if f is S.s41 else f(t, dur)
        p.stdin.write(engine.finish(img, t + it['f0'] / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return k, n


def build_audio():
    import render as VR   # music / sfx helpers from the first project
    items, speech_end, total = plan()
    n = int(total * SR)
    voice = np.zeros(n)
    for it in items:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', it['file'], '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                             capture_output=True).stdout
        VR.add(voice, np.frombuffer(raw, np.float32).astype(np.float64), it['start'])
    fx = np.zeros(n)
    for k, it in enumerate(items[1:], 1):
        VR.add(fx, VR.sfx_whoosh(0.4, k), it['f0'] / FPS - 0.2, 0.18)
    import scenes_ii as S
    names = [f.__name__ for f in S.FINAL_SCENES]
    for k, nm in enumerate(names):
        st = items[k]['f0'] / FPS
        du = (items[k]['f1'] - items[k]['f0']) / FPS
        if nm == 's15':
            VR.add(fx, VR.sfx_boom(1), st + 0.5, 0.45)
        if nm == 'x1':
            VR.add(fx, VR.sfx_boom(2), st + 0.5 + du * 0.35, 0.4)
        if nm in ('s14', 'x0'):
            VR.add(fx, VR.sfx_boom(3), st + du * (0.55 if nm == 's14' else 0.75), 0.25)
        if nm in ('s00', 's04', 's35', 's11'):
            VR.add(fx, VR.sfx_pop(800), st + 0.15, 0.3)
    mus = VR.music(total) * 0.08
    venv = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), mode='same')
    duck = 1 - 0.45 * np.clip(venv / (venv.max() * 0.25 + 1e-9), 0, 1)
    mix = voice / (np.abs(voice).max() + 1e-9) * 0.9 + fx + mus * duck
    mix = np.tanh(mix * 1.05) * 0.95
    np.stack([mix, mix], 1).astype(np.float32).tofile('build/mix.f32')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', 'build/mix.f32',
                    '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', str(SR), '-c:a', 'pcm_s16le', 'build/mix.wav'], check=True)


def mux():
    items, _, _ = plan()
    with open('build/list.txt', 'w') as f:
        for k in range(len(items)):
            f.write(f"file 'scene{k:02d}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/list.txt', '-c', 'copy',
                    'build/video_only.mp4'], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', 'build/video_only.mp4', '-i', 'build/mix.wav', '-map', '0:v',
                    '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart',
                    'build/final.tmp.mp4'], check=True)
    os.replace('build/final.tmp.mp4', 'build/iran_iraq_war.mp4')


if __name__ == '__main__':
    os.makedirs('build', exist_ok=True)
    what = sys.argv[1]
    if what == 'plan':
        items, se, tot = plan()
        print(len(items), 'scenes; speech end', round(se, 1), 'total', round(tot, 1))
    elif what == 'video':
        items, _, _ = plan()
        idx = [int(x) for x in sys.argv[2:]] or list(range(len(items)))
        idx.sort(key=lambda k: -(items[k]['f1'] - items[k]['f0']))
        with Pool(2) as pool:
            for k, n in pool.imap_unordered(render_scene, idx):
                print('scene', k, n, flush=True)
    elif what == 'audio':
        build_audio()
    elif what == 'mux':
        mux()
