"""Candidate tree/bush spots from the real site boundary (local cm of Neelam_WindTunnel_Root).
Validated later inside Unreal (ground type + clearance)."""
import json, os, random, shapely
from shapely.geometry import Polygon, Point
SRC = os.path.expanduser("~/mnt/wind tunnel/wind tunnel/Working/Analysis/design_data.json")
PIV = (15.77, -1.19)
P = Polygon(json.load(open(SRC))["site_boundary"]).buffer(0)
loc = lambda x, y: [round((x - PIV[0]) * 100, 1), round(-(y - PIV[1]) * 100, 1)]
rnd = random.Random(7)
def along(poly, step, jitter):
    ring = poly.exterior; L = ring.length; pts = []; d = rnd.uniform(0, step)
    while d < L:
        p = ring.interpolate(d); pts.append(loc(p.x, p.y)); d += step * rnd.uniform(1 - jitter, 1 + jitter)
    return pts
out = {
  "street_trees": along(P.buffer(5.0, join_style=2), 11.0, 0.15),     # outside the wall, verge
  "edge_trees":   along(P.buffer(-3.5, join_style=2), 10.0, 0.2),     # inside the wall
  "edge_bushes":  along(P.buffer(-1.4, join_style=2), 4.5, 0.3),
}
inner = P.buffer(-7.0); minx, miny, maxx, maxy = inner.bounds; sc = []
for _ in range(4000):                                                 # poisson-ish scatter, >=13 m apart
    x, y = rnd.uniform(minx, maxx), rnd.uniform(miny, maxy)
    if inner.contains(Point(x, y)) and all((x - a) ** 2 + (y - b) ** 2 > 13 ** 2 for a, b in sc):
        sc.append((x, y))
out["lawn_trees"] = [loc(x, y) for x, y in sc]
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "tree_candidates.json"), "w"))
print({k: len(v) for k, v in out.items()})
