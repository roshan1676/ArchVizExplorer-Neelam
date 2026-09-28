"""OSM ways + OSRM routes -> clean lat/lon polylines for the Phase 2 connectivity layer."""
import json, math, os
from shapely.geometry import LineString
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
ways = json.load(open(os.path.join(D, "osm", "roads_ways.json")))["elements"]
routes = json.load(open(os.path.join(D, "osm", "routes_phase2.json")))
LAT0 = 19.1634
def m(p):  # lat,lon -> local metres (for simplify/length)
    return ((p[1] - 72.959) * 111320 * math.cos(math.radians(LAT0)), (p[0] - LAT0) * 110540)
def length(pts): return sum(math.dist(m(a), m(b)) for a, b in zip(pts, pts[1:]))
def group(name):
    if "Phadke" in name: return "vb"
    if "Airoli" in name: return "mar"
    return "eeh"
chains = {}
for g in ("vb", "eeh", "mar"):
    segs = [[(n["lat"], n["lon"]) for n in w["geometry"]] for w in ways if group(w["tags"]["name"]) == g]
    best = []
    for start in range(len(segs)):                      # greedy chain from each segment, keep the longest
        used = {start}; ch = list(segs[start])
        while True:
            def ok(s):
                if len(ch) < 2 or len(s) < 2: return True
                a0, a1, b0, b1 = m(ch[-2]), m(ch[-1]), m(s[0]), m(s[1])
                u = (a1[0]-a0[0], a1[1]-a0[1]); v = (b1[0]-b0[0], b1[1]-b0[1])
                nu, nv = math.hypot(*u) or 1, math.hypot(*v) or 1
                return (u[0]*v[0] + u[1]*v[1]) / (nu*nv) > -0.3      # no U-turn onto the other carriageway
            nxt = next((i for i, s in enumerate(segs) if i not in used and math.dist(m(s[0]), m(ch[-1])) < 3 and ok(s)), None)
            if nxt is None: break
            used.add(nxt); ch += segs[nxt][1:]
        if length(ch) > length(best): best = ch
    chains[g] = best
def simplify(pts, tol_m=2.0, step_m=25.0):
    xy = [m(p) for p in pts]
    ls = LineString(xy).simplify(tol_m)
    L = ls.length; n = max(2, int(L // step_m) + 1)
    out = [ls.interpolate(L * i / (n - 1)) for i in range(n)]
    return [[round(LAT0 + q.y / 110540, 7), round(72.959 + q.x / (111320 * math.cos(math.radians(LAT0))), 7)] for q in out]
DEST = {"vaze": (19.16294, 72.95744), "station": (19.17164, 72.95627), "checknaka": (19.17610, 72.96824)}
out = {"roads": {}, "routes": {}}
NAMES = {"vb": "V B Phadke Road", "eeh": "Mumbai–Thane East / Eastern Express Highway", "mar": "Mulund–Airoli Link Road"}
for g, ch in chains.items():
    out["roads"][g] = {"name": NAMES[g], "km": round(length(ch) / 1000, 2), "pts": simplify(ch, 2.0, 30.0)}
for k, r in routes.items():
    pts = [(c[1], c[0]) for c in r["coords"]]
    d = DEST[k]; i = min(range(len(pts)), key=lambda j: math.dist(m(pts[j]), m(d)))
    pts = pts[:i + 1] + [d]                              # stop at the landmark (no U-turn tail)
    out["routes"][k] = {"km_route": round(length(pts) / 1000, 2), "min": round(r["min"], 1), "pts": simplify(pts, 1.5, 15.0)}
json.dump(out, open(os.path.join(D, "connectivity_phase2.json"), "w"), indent=0)
print({k: (v["km"], len(v["pts"])) for k, v in out["roads"].items()}, {k: (v["km_route"], v["min"], len(v["pts"])) for k, v in out["routes"].items()})
