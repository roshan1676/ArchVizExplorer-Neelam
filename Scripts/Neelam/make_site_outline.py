"""Builds Data/site_outline.json from the model's real site boundary (design_data.json).
Local frame = Neelam_WindTunnel_Root (cm): X = (x - 15.77) * 100, Y = -(y + 1.19) * 100."""
import json, os, shapely
from shapely.geometry import Polygon
SRC = os.path.expanduser("~/mnt/wind tunnel/wind tunnel/Working/Analysis/design_data.json")
PIV = (15.77, -1.19)
P = Polygon(json.load(open(SRC))["site_boundary"]).buffer(0)
def loc(pt): return [round((pt[0] - PIV[0]) * 100, 2), round(-(pt[1] - PIV[1]) * 100, 2)]
def ring(poly): return [loc(p) for p in list(poly.exterior.coords)[:-1]]
def tris(poly):
    out = []
    for t in shapely.constrained_delaunay_triangles(poly).geoms:
        c = list(t.exterior.coords)[:3]
        out.append([loc(p) for p in c])
    return out
cut = P.buffer(-0.12, join_style=2).simplify(0.03)      # inside the 0.23 m wall body -> seam hidden by wall
lawn = P.buffer(-0.05, join_style=2).simplify(0.03)
plat = P.buffer(0.10, join_style=2).simplify(0.03)      # 10 cm past the wall face
data = {"cut": ring(cut), "lawn_tris": tris(lawn), "platform_ring": ring(plat), "platform_tris": tris(plat),
        "area_m2": round(P.area, 1)}
json.dump(data, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "site_outline.json"), "w"))
print({k: (len(v) if isinstance(v, list) else v) for k, v in data.items()})
