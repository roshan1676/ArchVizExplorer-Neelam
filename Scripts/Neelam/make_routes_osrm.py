"""Drive routes site -> landmarks via OSRM (real roads) -> Data/connectivity_<phase>.json.
Pure stdlib, so it runs inside Unreal's Python (Windows has network; the Cowork VM does not).
Usage (bridge job): NEELAM_PHASE = "phase3"; exec(open(<this file>).read())"""
import json, math, os, urllib.request, time
try:
    import unreal
    P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
except ImportError:
    P = os.path.dirname(os.path.abspath(__file__))
PHASE = globals().get("NEELAM_PHASE", "phase3")
D = os.path.join(P, "Data")
L = json.load(open(os.path.join(D, "landmarks_%s.json" % PHASE), encoding="utf-8"))
SITE = (19.163933, 72.959038)                       # same start point as phase 2 (site gate on V B Phadke Rd)
LAT0 = 19.1634
def m(p): return ((p[1] - 72.959) * 111320 * math.cos(math.radians(LAT0)), (p[0] - LAT0) * 110540)
def ll(x, y): return [round(LAT0 + y / 110540, 7), round(72.959 + x / (111320 * math.cos(math.radians(LAT0))), 7)]
def length(pts): return sum(math.dist(m(a), m(b)) for a, b in zip(pts, pts[1:]))
def dp(xy, tol):                                     # Douglas-Peucker
    if len(xy) < 3: return xy
    (x0, y0), (x1, y1) = xy[0], xy[-1]; L2 = (x1-x0)**2 + (y1-y0)**2 or 1e-9
    def d(p):
        t = max(0, min(1, ((p[0]-x0)*(x1-x0) + (p[1]-y0)*(y1-y0)) / L2))
        return math.dist(p, (x0 + t*(x1-x0), y0 + t*(y1-y0)))
    i, dm = max(((i, d(p)) for i, p in enumerate(xy[1:-1], 1)), key=lambda t: t[1])
    return dp(xy[:i+1], tol)[:-1] + dp(xy[i:], tol) if dm > tol else [xy[0], xy[-1]]
def resample(xy, step):
    seg = [math.dist(a, b) for a, b in zip(xy, xy[1:])]; tot = sum(seg); n = max(2, int(tot // step) + 1)
    out, acc, j = [], 0.0, 0
    for k in range(n):
        s = tot * k / (n - 1)
        while j < len(seg) - 1 and acc + seg[j] < s: acc += seg[j]; j += 1
        t = 0 if seg[j] == 0 else (s - acc) / seg[j]; a, b = xy[j], xy[j+1]
        out.append((a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1])))
    return out
out = {"roads": {}, "routes": {}}
for lm in L["landmarks"]:
    url = "https://router.project-osrm.org/route/v1/driving/%f,%f;%f,%f?overview=full&geometries=geojson" % (SITE[1], SITE[0], lm["lon"], lm["lat"])
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "neelam-archviz"}), timeout=30).read())["routes"][0]
    pts = [(c[1], c[0]) for c in r["geometry"]["coordinates"]]
    d = (lm["lat"], lm["lon"]); i = min(range(len(pts)), key=lambda j: math.dist(m(pts[j]), m(d)))
    pts = pts[:i + 1] + [d]
    xy = resample(dp([m(p) for p in pts], 1.5), 15.0)
    out["routes"][lm["id"]] = {"km_route": round(length(pts) / 1000, 2), "min_osrm": round(r["duration"] / 60, 1),
                               "min": lm.get("drive_min", round(r["duration"] / 60 * 1.75)), "pts": [ll(*q) for q in xy]}
    time.sleep(0.4)
json.dump(out, open(os.path.join(D, "connectivity_%s.json" % PHASE), "w"), indent=0)
result = {k: (v["km_route"], v["min_osrm"], v["min"], len(v["pts"])) for k, v in out["routes"].items()}
print(result)
