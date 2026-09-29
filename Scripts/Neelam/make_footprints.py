"""OSM footprints -> oriented boxes for the POI hologram highlight (BP_POI.POI_Geometry).
One Overpass query for all landmarks (runs inside UE: Windows has network). Writes Data/footprints.json:
{id: {cx_m, cy_m (offset east/north of the pin), w_m, d_m, yaw_deg (east=0, CCW), src}}"""
import json, math, os, urllib.request, urllib.parse, time
try:
    import unreal
    P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
except ImportError:
    P = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(P, "Data")
LMS = []
for ph in globals().get("PHASES", ["phase2", "phase3"]):
    LMS += json.load(open(os.path.join(D, "landmarks_%s.json" % ph), encoding="utf-8"))["landmarks"]
WANT = {"Immediate": ("college", "university", "school"), "Education": ("school", "college", "university", "kindergarten"),
        "Healthcare": ("hospital", "clinic"), "Retail": ("mall", "supermarket", "department_store", "retail", "commercial"),
        "Transport": ("train_station", "station", "railway", "platform", "toll_booth", "bus_station")}
around = "".join('way(around:180,%f,%f)[~"^(building|amenity|shop|landuse|railway|public_transport|barrier)$"~"."];' % (l["lat"], l["lon"]) for l in LMS)
q = "[out:json][timeout:60];(%s);out geom tags;" % around
MIRRORS = ["https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass-api.de/api/interpreter"]
errs = []
for url in MIRRORS:                                   # short timeouts: the editor is blocked while a bridge job runs
    try:
        data = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                          headers={"User-Agent": "neelam-archviz"}), timeout=40).read())
        break
    except Exception as e:
        errs.append("%s: %s" % (url, e))
else:
    raise RuntimeError(errs)
def xy(la, lo, la0, lo0): return ((lo - lo0) * 111320 * math.cos(math.radians(la0)), (la - la0) * 110540)
def inside(p, poly):
    c = False; j = len(poly) - 1
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[j]
        if (yi > p[1]) != (yj > p[1]) and p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def area(poly): return abs(sum(poly[j][0] * poly[i][1] - poly[i][0] * poly[j][1] for i, j in zip(range(len(poly)), [len(poly) - 1] + list(range(len(poly) - 1))))) / 2
def obb(pts):
    best = None
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if L < 0.5: continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        A = [p[0] * ux + p[1] * uy for p in pts]; B = [-p[0] * uy + p[1] * ux for p in pts]
        ar = (max(A) - min(A)) * (max(B) - min(B))
        if best is None or ar < best[0]:
            ca, cb = (max(A) + min(A)) / 2, (max(B) + min(B)) / 2
            best = (ar, ca * ux - cb * uy, ca * uy + cb * ux, max(A) - min(A), max(B) - min(B), math.degrees(math.atan2(uy, ux)))
    return best
out = {}
for l in LMS:
    want = WANT.get(l["cat"], ())
    cands = []
    for w in data["elements"]:
        g = w.get("geometry") or []
        if len(g) < 4: continue
        poly = [xy(n["lat"], n["lon"], l["lat"], l["lon"]) for n in g]
        if math.dist(poly[0], poly[-1]) > 1: continue
        t = w.get("tags", {}); kind = t.get("amenity") or t.get("shop") or t.get("railway") or t.get("public_transport") or t.get("building") or t.get("landuse") or t.get("barrier") or ""
        A = area(poly); inn = inside((0, 0), poly); d = min(math.hypot(*p) for p in poly)
        if A < 60 or A > 60000: continue
        named = bool(t.get("name")) and any(s in t.get("name", "").lower() for s in l["name"].lower().replace("-", " ").split()[:2] if len(s) > 2)
        score = (3 if named else 0) + (2 if kind in want else 0) + (2 if inn else 0) + (1 if "building" in t else 0) - d / 40.0
        cands.append((score, A, t.get("name", ""), kind, inn, d, obb(poly)))
    if not cands:
        out[l["id"]] = {"cx_m": 0, "cy_m": 0, "w_m": 40, "d_m": 40, "yaw_deg": 0, "src": "default"}; continue
    s, A, nm, kind, inn, d, o = max(cands, key=lambda c: c[0])
    out[l["id"]] = {"cx_m": round(o[1], 1), "cy_m": round(o[2], 1), "w_m": round(o[3], 1), "d_m": round(o[4], 1), "yaw_deg": round(o[5], 1),
                    "src": "osm %s '%s' area=%d inside=%s d=%d score=%.1f" % (kind, nm, A, inn, d, s)}
json.dump(out, open(os.path.join(D, "footprints.json"), "w"), indent=1)
result = {k: [v["w_m"], v["d_m"], v["src"]] for k, v in out.items()}
