"""Pick the context buildings for the grey massing (30 Sep): OSM footprints (Data/massing_src.json, 2.5 km around the
site) -> Data/massing_sel.json. Sparse near the tower (client: 'just enough to identify the surroundings'):
< 500 m from the site only >= 500 m2, < 1.2 km >= 300 m2, beyond >= 250 m2. Site / landmark cut-outs excluded.
Footprints simplified (0.6 m) and closed. Pure python."""
import json, math, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
B = json.load(open(os.path.join(D, "massing_src.json"))); C = json.load(open(os.path.join(D, "cut_polys.json")))
S = (944.0, 4429.0)
def area(p): return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2 / 1e4
def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c
def dp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1e-9
    i, dm = 0, 0
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + b[0] * a[1] - b[1] * a[0]) / L
        if d > dm: i, dm = k, d
    return dp(pts[:i + 1], eps)[:-1] + dp(pts[i:], eps) if dm > eps else [a, b]
sel = []
for b in B:
    p = b["pts"][:-1] if b["pts"][0] == b["pts"][-1] else b["pts"]
    if len(p) < 3: continue
    a = area(p); cx = sum(q[0] for q in p) / len(p); cy = sum(q[1] for q in p) / len(p)
    d = math.hypot(cx - S[0], cy - S[1]) / 100
    if any(inside(cx, cy, poly) for poly in C.values()): continue
    if a < (500 if d < 500 else 300 if d < 1200 else 250): continue
    q = dp(p + [p[0]], 60.0)[:-1]
    if len(q) < 3: q = p
    lv = b.get("levels"); h = b.get("height")
    try: h = float(str(h).replace("m", "").strip()) if h else None
    except Exception: h = None
    try: lv = float(lv) if lv else None
    except Exception: lv = None
    sel.append({"id": b["id"], "pts": [[round(x, 1), round(y, 1)] for x, y in q], "area": round(a), "d": round(d), "c": [round(cx, 1), round(cy, 1)],
                "h_osm": h if h else (lv * 3.2 if lv else None)})
json.dump(sel, open(os.path.join(D, "massing_sel.json"), "w"))
print(len(sel), "buildings;", sum(1 for s in sel if s["h_osm"]), "with OSM height/levels;", sum(len(s["pts"]) for s in sel), "verts")
