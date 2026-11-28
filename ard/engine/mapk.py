"""High-res paper map of the Korean peninsula + territorial-control overlay."""
import sys, json, math, functools, subprocess
sys.path.insert(0, '/home/claude/vox')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import SEA, INK, W, H

LON0, LON1, LAT0, LAT1 = 116.0, 136.0, 30.5, 46.0
K = 520.0
CL = math.cos(math.radians(38))
BW, BH = int((LON1 - LON0) * K * CL), int((LAT1 - LAT0) * K)
KOREA_LAND = (240, 233, 218)
OTHER_LAND = (222, 212, 190)


def P(lon, lat):
    return ((lon - LON0) * K * CL, (LAT1 - lat) * K)


def _load():
    js = subprocess.run(['node', '-e', r"""
const t=require('topojson-client');
const land=require('./node_modules/world-atlas/land-10m.json');
const c=require('./node_modules/world-atlas/countries-10m.json');
const L=t.feature(land,land.objects.land);
const C=t.feature(c,c.objects.countries);
const want=new Set(['North Korea','South Korea','China','Japan','Russia','Mongolia','Taiwan']);
process.stdout.write(JSON.stringify({land:L,countries:C.features.filter(f=>want.has(f.properties.name))}));
"""], capture_output=True, text=True, cwd='/home/claude/korea', check=True).stdout
    return json.loads(js)


def _polys(g):
    if g['type'] == 'Polygon':
        yield g['coordinates']
    elif g['type'] == 'MultiPolygon':
        yield from g['coordinates']


def _near(ring):
    return any(LON0 - 4 < x < LON1 + 4 and LAT0 - 4 < y < LAT1 + 4 for x, y in ring[::3] or ring)


def _clip_ring(ring):
    # avoid huge coordinates for giant polygons (Russia/China): clamp to a padded box
    return [P(min(max(x, LON0 - 6), LON1 + 6), min(max(y, LAT0 - 6), LAT1 + 6)) for x, y in ring]


@functools.lru_cache(None)
def big():
    data = _load()
    img = Image.new('RGB', (BW, BH), SEA)
    m_land = Image.new('L', (BW, BH), 0)
    d = ImageDraw.Draw(m_land)
    feats = data['land']['features']
    for f in feats:
        for poly in _polys(f['geometry']):
            if not _near(poly[0]):
                continue
            d.polygon(_clip_ring(poly[0]), fill=255)
            for hole in poly[1:]:
                d.polygon(_clip_ring(hole), fill=0)
    m_k = Image.new('L', (BW, BH), 0)
    dk = ImageDraw.Draw(m_k)
    for f in data['countries']:
        if f['properties']['name'] in ('North Korea', 'South Korea'):
            for poly in _polys(f['geometry']):
                dk.polygon(_clip_ring(poly[0]), fill=255)
    img = Image.composite(Image.new('RGB', (BW, BH), OTHER_LAND), img, m_land)
    img = Image.composite(Image.new('RGB', (BW, BH), KOREA_LAND), img, m_k)
    edge = m_land.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10))
    a = np.asarray(img).astype(np.float32)
    e = (np.asarray(edge).astype(np.float32) / 255) * (1 - np.asarray(m_land).astype(np.float32) / 255)
    a *= (1 - 0.22 * e)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for f in data['countries']:
        if f['properties']['name'] in ('North Korea', 'South Korea'):
            continue
        for poly in _polys(f['geometry']):
            if _near(poly[0]):
                pts = _clip_ring(poly[0])
                d.line(pts + [pts[0]], fill=(120, 110, 95), width=4)
    for f in feats:
        for poly in _polys(f['geometry']):
            if _near(poly[0]):
                pts = _clip_ring(poly[0])
                d.line(pts + [pts[0]], fill=INK, width=5)
    # outer outline of the whole peninsula only (no modern internal border)
    ring = np.asarray(m_k.filter(ImageFilter.MaxFilter(5))).astype(np.int16) - np.asarray(m_k.filter(ImageFilter.MinFilter(3))).astype(np.int16)
    ring = Image.fromarray((ring > 128).astype(np.uint8) * 255)
    img.paste(Image.new('RGB', (BW, BH), INK), (0, 0), ring)
    return img, m_k


def view(lon, lat, span):
    bm, mk = big()
    cx, cy = P(lon, lat)
    w = span * K * CL
    h = w * H / W
    x0 = min(max(cx - w / 2, 0.0), BW - w)
    y0 = min(max(cy - h / 2, 0.0), BH - h)
    box = (x0, y0, x0 + w, y0 + h)
    fr = bm.resize((W, H), Image.LANCZOS, box=box, reducing_gap=2.0)
    mask = mk.resize((W, H), Image.BILINEAR, box=box, reducing_gap=2.0)
    s = W / w

    def S(lo, la):
        x, y = P(lo, la)
        return ((x - box[0]) * s, (y - box[1]) * s)

    def inv():
        xs = (np.arange(W) / s + box[0]) / (K * CL) + LON0
        ys = LAT1 - (np.arange(H) / s + box[1]) / K
        return xs, ys
    return fr, S, mask, inv


# ----------------------------------------------------------------- front lines
LONS = np.linspace(123.5, 131.5, 81)


def _interp(pts):
    xs, ys = zip(*pts)
    return np.interp(LONS, xs, ys)


FRONT = {
    'p38': _interp([(123.5, 38.0), (131.5, 38.0)]),
    'pusan': np.where(LONS < 128.25, 33.0, np.where(LONS < 128.45, 33.0 + (LONS - 128.25) / 0.2 * 3.3, 36.3)),
    'yalu': _interp([(123.5, 39.9), (124.5, 40.1), (125.5, 40.5), (126.5, 40.9), (127.5, 41.2), (128.5, 41.5),
                     (129.5, 41.9), (130.5, 42.3), (131.5, 42.6)]),
    'jan51': _interp([(123.5, 37.0), (126.9, 37.0), (128.0, 37.2), (129.2, 37.4), (131.5, 37.4)]),
    'mid51': _interp([(123.5, 37.8), (126.9, 37.7), (127.8, 38.1), (128.6, 38.6), (131.5, 38.6)]),
    'dmz': _interp([(123.5, 37.7), (126.1, 37.7), (126.68, 37.78), (127.0, 38.0), (127.3, 38.27), (127.75, 38.32),
                    (128.1, 38.35), (128.37, 38.61), (131.5, 38.61)]),
}
MDL = [(126.1, 37.7), (126.68, 37.78), (127.0, 38.0), (127.3, 38.27), (127.75, 38.32), (128.1, 38.35), (128.37, 38.61)]


def front_mix(a, b, f):
    return FRONT[a] + (FRONT[b] - FRONT[a]) * f


NORTH = (214, 74, 60)
SOUTH = (58, 112, 178)


def overlay(fr, mask, inv, front, alpha=0.55, neutral=False, north=NORTH, south=SOUTH):
    """Tint Korea land north/south of the given front (array over LONS)."""
    xs, ys = inv()
    fl = np.interp(xs, LONS, front)                 # per column
    north_m = ys[:, None] > fl[None, :]
    a = np.asarray(fr).astype(np.float32)
    m = np.asarray(mask).astype(np.float32)[..., None] / 255 * alpha
    if neutral:
        return fr
    col = np.where(north_m[..., None], np.array(north, np.float32), np.array(south, np.float32))
    out = a * (1 - m) + (a * col / 255) * m
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def front_pts(S, front, lon_min=124.2, lon_max=130.0):
    sel = (LONS >= lon_min) & (LONS <= lon_max)
    return [S(lo, la) for lo, la in zip(LONS[sel], front[sel])]
