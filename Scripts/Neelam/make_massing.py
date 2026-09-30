"""Grey context massing (30 Sep): Data/massing_sel.json + Data/massing_heights.json -> Data/massing_build.json.
Height: OSM height / levels x 3.2 m when tagged; otherwise by type and footprint (Mulund: G+3 chawls to G+10 blocks),
with a stable per-building variation (+-20 %) so the skyline is not flat. The photogrammetry roofs cannot be measured:
the Google tiles' collision and captured depth are a coarse blanket (see Massing_PIE.py / Depth_PIE.py notes).
Base = map ground - 3 m (never floats). Chunks: 500 m grid -> one mesh each (Blender/build_massing.py)."""
import json, os, math, random
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
S = json.load(open(os.path.join(D, "massing_sel.json")))
H = json.load(open(os.path.join(D, "massing_heights.json")))
SRC = {b["id"]: b for b in json.load(open(os.path.join(D, "massing_src.json")))}
def guess(b, typ, a):
    r = random.Random(b["id"]).uniform(0.8, 1.2)
    if typ in ("industrial", "warehouse", "roof", "shed", "garage", "construction", "stadium"): return 9.0 * r
    if typ in ("school", "hospital", "public", "temple", "commercial", "retail", "mall"): return 15.0 * r
    if a < 400: return 13.0 * r
    if a < 800: return 19.0 * r
    if a < 1500: return 26.0 * r
    return 30.0 * r
# no block may stand on a built carriageway (OSM building polygons sometimes overlap flyovers / the highway)
RB = json.load(open(os.path.join(D, "road_build.json")))["roads"]
def _inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c
def _segd(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy or 1e-9
    t = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / L)); return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)
def on_road(P):
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    for r in RB.values():
        hw = r["width_m"] * 50
        for q in r["pts"]:
            if not (min(xs) - hw <= q[0] <= max(xs) + hw and min(ys) - hw <= q[1] <= max(ys) + hw): continue
            d = 0 if _inside(q[0], q[1], P) else min(_segd(q[0], q[1], P[i], P[i - 1]) for i in range(len(P)))
            if d < hw - 100: return True
    return False
EXF = os.path.join(D, "massing_exclude.json")          # ids removed on request (Mark_Massing_Removals.py)
EXCL = set(json.load(open(EXF))) if os.path.exists(EXF) else set()
out = []; used = {"osm": 0, "guess": 0, "on_road_removed": 0, "excluded": 0}
for b in S:
    if b["id"] in EXCL: used["excluded"] += 1; continue
    if on_road(b["pts"]): used["on_road_removed"] += 1; continue
    typ = SRC[b["id"]].get("b") or "yes"
    if b["h_osm"] and 3 <= b["h_osm"] <= 250: h = b["h_osm"]; used["osm"] += 1
    else: h = guess(b, typ, b["area"]); used["guess"] += 1
    g = H.get(str(b["id"]))
    ground = g[0] if g else None
    if ground is None: continue
    out.append({"id": b["id"], "pts": b["pts"], "base": round(ground - 300, 1), "top": round(ground + h * 100, 1),
                "chunk": "%d_%d" % (math.floor(b["c"][0] / 50000), math.floor(b["c"][1] / 50000))})
json.dump(out, open(os.path.join(D, "massing_build.json"), "w"))
print(len(out), used, len({o["chunk"] for o in out}), "chunks")
