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
out = []; used = {"osm": 0, "guess": 0}
for b in S:
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
