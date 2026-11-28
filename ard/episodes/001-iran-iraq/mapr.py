"""Generic high-res paper map for a region, with per-country masks and rivers."""
import sys, json, math, functools, subprocess
sys.path.insert(0, '/home/claude/vox')
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from engine import INK, W, H

LON0, LON1, LAT0, LAT1 = 34.0, 64.0, 21.0, 42.5
K = 300.0
CL = math.cos(math.radians(32))
BW, BH = int((LON1 - LON0) * K * CL), int((LAT1 - LAT0) * K)

SEA = (176, 203, 206)
LAND = (226, 214, 188)
IRAQ = (226, 164, 76)
IRAN = (82, 150, 146)
RIVER = (70, 120, 160)
COUNTRIES = ['Iraq', 'Iran', 'Kuwait', 'Saudi Arabia', 'Syria', 'Turkey', 'Jordan', 'Qatar', 'Bahrain',
             'United Arab Emirates', 'Oman', 'Afghanistan', 'Pakistan', 'Turkmenistan', 'Azerbaijan', 'Armenia',
             'Israel', 'Lebanon', 'Egypt', 'Palestine', 'Georgia', 'Cyprus', 'Yemen']

RIVERS = {
    'tigris': [(42.2, 37.4), (42.7, 36.9), (43.13, 36.34), (43.3, 35.5), (43.68, 34.6), (44.2, 33.9), (44.37, 33.31),
               (44.9, 33.0), (45.8, 32.5), (46.4, 32.2), (47.15, 31.84), (47.43, 31.0)],
    'euphrates': [(38.3, 37.1), (38.5, 36.4), (39.0, 35.95), (40.14, 35.33), (41.0, 34.4), (42.4, 34.13),
                  (43.3, 33.42), (43.78, 33.35), (44.43, 32.48), (45.28, 31.31), (46.26, 31.05), (47.43, 31.0)],
    'shatt': [(47.43, 31.0), (47.65, 30.75), (47.82, 30.52), (48.008, 30.468), (48.146, 30.439), (48.192, 30.342),
              (48.295, 30.322), (48.398, 30.225), (48.387, 30.147), (48.444, 30.011), (48.547, 29.963)]
}


def P(lon, lat):
    return ((lon - LON0) * K * CL, (LAT1 - lat) * K)


def _load():
    js = subprocess.run(['node', '-e', r"""
const t=require('topojson-client');
const land=require('./node_modules/world-atlas/land-10m.json');
const c=require('./node_modules/world-atlas/countries-10m.json');
const want=new Set(process.argv[1].split('|'));
process.stdout.write(JSON.stringify({land:t.feature(land,land.objects.land),
 countries:t.feature(c,c.objects.countries).features.filter(f=>want.has(f.properties.name))}));
""", '|'.join(COUNTRIES)], capture_output=True, text=True, cwd='/home/claude/vox', check=True).stdout
    return json.loads(js)


def _polys(g):
    if g['type'] == 'Polygon':
        yield g['coordinates']
    elif g['type'] == 'MultiPolygon':
        yield from g['coordinates']


def _near(ring):
    return any(LON0 - 5 < x < LON1 + 5 and LAT0 - 5 < y < LAT1 + 5 for x, y in ring[::3] or ring)


def _clip(ring):
    return [P(min(max(x, LON0 - 8), LON1 + 8), min(max(y, LAT0 - 8), LAT1 + 8)) for x, y in ring]


@functools.lru_cache(None)
def big():
    data = _load()
    img = Image.new('RGB', (BW, BH), SEA)
    m_land = Image.new('L', (BW, BH), 0)
    d = ImageDraw.Draw(m_land)
    for f in data['land']['features']:
        for poly in _polys(f['geometry']):
            if _near(poly[0]):
                d.polygon(_clip(poly[0]), fill=255)
                for h in poly[1:]:
                    d.polygon(_clip(h), fill=0)
    masks = {}
    for name in ('Iraq', 'Iran'):
        m = Image.new('L', (BW, BH), 0)
        dm = ImageDraw.Draw(m)
        for f in data['countries']:
            if f['properties']['name'] == name:
                for poly in _polys(f['geometry']):
                    dm.polygon(_clip(poly[0]), fill=255)
        masks[name] = m
    img = Image.composite(Image.new('RGB', (BW, BH), LAND), img, m_land)
    edge = m_land.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10))
    a = np.asarray(img).astype(np.float32)
    e = (np.asarray(edge).astype(np.float32) / 255) * (1 - np.asarray(m_land).astype(np.float32) / 255)
    a *= (1 - 0.22 * e)[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for f in data['countries']:
        for poly in _polys(f['geometry']):
            if _near(poly[0]):
                pts = _clip(poly[0])
                d.line(pts + [pts[0]], fill=(125, 112, 92), width=3)
    for f in data['land']['features']:
        for poly in _polys(f['geometry']):
            if _near(poly[0]):
                pts = _clip(poly[0])
                d.line(pts + [pts[0]], fill=INK, width=4)
    # Iran-Iraq border emphasised
    both = np.asarray(masks['Iraq'].filter(ImageFilter.MaxFilter(5))) & np.asarray(masks['Iran'].filter(ImageFilter.MaxFilter(5)))
    bm = Image.fromarray(((both > 128) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    img.paste(Image.new('RGB', (BW, BH), INK), (0, 0), bm)
    d = ImageDraw.Draw(img)
    for name, pts in RIVERS.items():
        q = [P(*p) for p in pts]
        d.line(q, fill=RIVER, width=10 if name == 'shatt' else 6, joint='curve')
    return img, masks['Iraq'], masks['Iran']


class View:
    def __init__(self, lon, lat, span):
        bm, mi, mn = big()
        cx, cy = P(lon, lat)
        w = span * K * CL
        h = w * H / W
        x0 = min(max(cx - w / 2, 0.0), BW - w)
        y0 = min(max(cy - h / 2, 0.0), BH - h)
        self.box = (x0, y0, x0 + w, y0 + h)
        self.s = W / w
        self.frame = bm.resize((W, H), Image.LANCZOS, box=self.box, reducing_gap=2.0)
        self._mi, self._mn = mi, mn

    def S(self, lon, lat):
        x, y = P(lon, lat)
        return ((x - self.box[0]) * self.s, (y - self.box[1]) * self.s)

    def mask(self, which):
        m = self._mi if which == 'Iraq' else self._mn
        return m.resize((W, H), Image.BILINEAR, box=self.box, reducing_gap=2.0)

    def km(self, k):
        """pixels for k km (approx, N-S)."""
        return k / 111.0 * K * self.s


def tint(img, mask, color, alpha):
    if alpha <= 0:
        return img
    a = np.asarray(img).astype(np.float32)
    m = np.asarray(mask).astype(np.float32)[..., None] / 255 * alpha
    c = np.array(color, np.float32)
    out = a * (1 - m) + (a * c / 255) * m
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), img.mode if img.mode == 'RGB' else 'RGB')
