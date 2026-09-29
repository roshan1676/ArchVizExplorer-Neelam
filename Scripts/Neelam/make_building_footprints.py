"""For each landmark: the largest OSM *building* polygon on its plot (inside the footprint from make_footprints.py,
else nearest to the pin) -> oriented box. Writes Data/building_footprints.json. Runs inside UE (Windows network)."""
import json, math, os, urllib.request, urllib.parse
try:
    import unreal; P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
except ImportError:
    P = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(P, "Data")
LMS = []
for ph in ("phase2", "phase3"): LMS += json.load(open(os.path.join(D, "landmarks_%s.json" % ph), encoding="utf-8"))["landmarks"]
FP = json.load(open(os.path.join(D, "footprints.json")))
q = "[out:json][timeout:60];(%s);out geom tags;" % "".join('way(around:250,%f,%f)["building"];' % (l["lat"], l["lon"]) for l in LMS)
data = None
for url in ("https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass-api.de/api/interpreter"):
    try:
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "neelam-archviz"}), timeout=40).read()); break
    except Exception as e: err = e
if data is None: raise RuntimeError(err)
def xy(la, lo, la0, lo0): return ((lo - lo0) * 111320 * math.cos(math.radians(la0)), (la - la0) * 110540)
def area(p): return abs(sum(p[j][0] * p[i][1] - p[i][0] * p[j][1] for i, j in zip(range(len(p)), [len(p) - 1] + list(range(len(p) - 1))))) / 2
def obb(pts):
    best = None
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if L < 0.5: continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        A = [p[0] * ux + p[1] * uy for p in pts]; B = [-p[0] * uy + p[1] * ux for p in pts]; ar = (max(A) - min(A)) * (max(B) - min(B))
        if best is None or ar < best[0]:
            ca, cb = (max(A) + min(A)) / 2, (max(B) + min(B)) / 2
            best = (ar, ca * ux - cb * uy, ca * uy + cb * ux, max(A) - min(A), max(B) - min(B), math.degrees(math.atan2(uy, ux)))
    return best
def inbox(p, f):   # point (east,north m rel. pin) inside the plot box f
    a = math.radians(f["yaw_deg"]); dx, dy = p[0] - f["cx_m"], p[1] - f["cy_m"]
    u = dx * math.cos(a) + dy * math.sin(a); v = -dx * math.sin(a) + dy * math.cos(a)
    return abs(u) <= f["w_m"] / 2 + 5 and abs(v) <= f["d_m"] / 2 + 5
out = {}
for l in LMS:
    f = FP.get(l["id"]); cands = []
    for w in data["elements"]:
        g = w.get("geometry") or []
        if len(g) < 4: continue
        poly = [xy(n["lat"], n["lon"], l["lat"], l["lon"]) for n in g]
        if math.dist(poly[0], poly[-1]) > 1: continue
        A = area(poly); c = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
        if A < 150: continue
        cands.append((inbox(c, f) if f else False, A, math.hypot(*c), poly, w.get("tags", {}).get("name", "")))
    inside = [c for c in cands if c[0]]
    pick = max(inside, key=lambda c: c[1]) if inside else (min(cands, key=lambda c: c[2]) if cands else None)
    if not pick: continue
    o = obb(pick[3])
    out[l["id"]] = {"cx_m": round(o[1], 1), "cy_m": round(o[2], 1), "w_m": round(o[3], 1), "d_m": round(o[4], 1), "yaw_deg": round(o[5], 1),
                    "src": "osm building '%s' area=%d in_plot=%s" % (pick[4], pick[1], pick[0])}
json.dump(out, open(os.path.join(D, "building_footprints.json"), "w"), indent=1)
result = {k: [v["w_m"], v["d_m"], v["src"]] for k, v in out.items()}
