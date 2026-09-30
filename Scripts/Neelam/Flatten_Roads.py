"""Data/road_build.json: remove the bogus dips from the carriageway profiles (29 Sep).
The Google tiles had holes / creek-level geometry under parts of EEH and Mulund-Airoli, so the traced deck dropped
up to 19 m in 50 m (road plunging into a trench and back). Real highways never do that, so each profile becomes its
closing over 300 m (dips shorter than that are filled, long real slopes kept) followed by a 6 % grade cap, computed
on the road NETWORK (along carriageways and across junctions: endpoints within 8 m of another carriageway), then a 27 m mean.
The traced value is kept as "ground" per point -> build_roads.py drops the side walls down to it (embankment look).
Pure python; keeps a backup in road_build_raw.json. Idempotent (always starts from the raw file)."""
import json, os, math, heapq
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
RAW = os.path.join(D, "road_build_raw.json"); OUT = os.path.join(D, "road_build.json")
if not os.path.exists(RAW): json.dump(json.load(open(OUT)), open(RAW, "w"))
ALN = os.path.join(D, "road_build_aligned_raw.json")      # centrelines snapped onto the real carriageways (Align/)
if os.path.exists(ALN): RAW = ALN
data = json.load(open(RAW)); R = data["roads"]
G, W, PIT = 0.08, 30000.0, 250.0          # max grade 8 %, dips shorter than 300 m are filled
nodes = []; idx = {}
for k, r in R.items():
    idx[k] = []
    for i, p in enumerate(r["pts"]): idx[k].append(len(nodes)); nodes.append(p)
adj = [[] for _ in nodes]
def link(a, b):
    d = math.dist(nodes[a][:2], nodes[b][:2]); adj[a].append((b, d)); adj[b].append((a, d))
for k in R:
    for a, b in zip(idx[k], idx[k][1:]): link(a, b)
grid = {}
for n, p in enumerate(nodes): grid.setdefault((int(p[0] // 1000), int(p[1] // 1000)), []).append(n)
for k in R:
    for e in (idx[k][0], idx[k][-1]):
        x, y = nodes[e][:2]; best = {}
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for n in grid.get((int(x // 1000) + i, int(y // 1000) + j), []):
                    if n in idx[k]: continue
                    d = math.hypot(nodes[n][0] - x, nodes[n][1] - y)
                    if d < 800: best[n] = d
        best = {n: d for n, d in best.items() if abs(nodes[n][2] - nodes[e][2]) < 250}      # same level only (not a flyover crossing)
        if best: link(e, min(best, key=best.get))
def within(n, rad):
    """nodes within geodesic distance rad of n (along carriageways + junction links)"""
    seen = {n: 0.0}; pq = [(0.0, n)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > seen.get(u, 1e18): continue
        for m, w in adj[u]:
            c = d + w
            if c <= rad and c < seen.get(m, 1e18): seen[m] = c; heapq.heappush(pq, (c, m))
    return seen
# 1) where the precise PIE surface (Surface_Align -> Data/surface_xy.json, full-detail tiles) has a sample within 12 m,
#    trust it over the carriageway trace (the traces fell into tile holes: -10 m where the real road is at +2..6 m)
SXY = os.path.join(D, "surface_xy.json"); sg = {}
if os.path.exists(SXY):
    for x, y, zz in json.load(open(SXY)): sg.setdefault((x // 1000, y // 1000), []).append((x, y, zz))
def precise(x, y, rad=1200.0):
    b = None
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for (a, c, zz) in sg.get((int(x // 1000) + i, int(y // 1000) + j), []):
                d = math.hypot(a - x, c - y)
                if d < rad and (b is None or d < b[0]): b = (d, zz)
    return None if b is None else b[1]
# every trace source randomly fell into tile holes in different places, but none of them ever reads too HIGH except
# under an overpass -> take the max of all sources (raw pass, Road_Surface_PIE.py pass, precise ribbon surface) ...
PIE = json.load(open(os.path.join(D, "road_surface_pie.json"))) if os.path.exists(os.path.join(D, "road_surface_pie.json")) else {}
pie = [None] * len(nodes)
for k, v in PIE.items():
    if k not in idx: continue
    good = [(i, q) for i, q in enumerate(v) if q is not None and i < len(idx[k])]
    if len(good) < max(2, len(idx[k]) // 6): continue
    gi = 0
    for i in range(len(idx[k])):        # linear interpolation between traced points (traced every 2nd point)
        while gi < len(good) - 2 and good[gi + 1][0] < i: gi += 1
        (i0, z0), (i1, z1) = good[gi], good[min(gi + 1, len(good) - 1)]
        if i <= i0: q = z0
        elif i >= i1: q = z1
        else: q = z0 + (z1 - z0) * (i - i0) / (i1 - i0)
        if abs(i - i0) <= 6 or abs(i - i1) <= 6: pie[idx[k][i]] = q
# the PIE re-trace ON the aligned carriageways (Road_Surface_PIE.py, 5 traces across, median) is the truth; the first
# pass (other positions) only fills the few points the re-trace missed
z = []; used = 0
for n, p in enumerate(nodes):
    if pie[n] is not None: used += 1; z.append(pie[n])
    else: z.append(p[2])
# ... then an opening over 60 m removes narrow high spikes (overpass decks, trucks) > 1.5 m
nb6 = [list(within(n, 3000.0)) for n in range(len(nodes))]
ero = [min(z[m] for m in nb6[n]) for n in range(len(nodes))]
opn = [max(ero[m] for m in nb6[n]) for n in range(len(nodes))]
z = [o if v - o > 150 else v for v, o in zip(z, opn)]
HALF = W / 2
nb = [list(within(n, HALF)) for n in range(len(nodes))]
dil = [max(z[m] for m in nb[n]) for n in range(len(nodes))]          # closing = dilation then erosion:
clo = [min(dil[m] for m in nb[n]) for n in range(len(nodes))]        # fills every dip narrower than W, keeps long slopes
steep = [0.0] * len(nodes)                                            # max |grade| to the neighbours
for n in range(len(nodes)):
    for m, d in adj[n]:
        if d > 1: steep[n] = max(steep[n], abs(z[m] - z[n]) / d)
pitmask = [c - v > PIT for c, v in zip(clo, z)]
# a pit is filled only if a >12 % wall lies within 30 m of it (geodesic) -> tile holes, bridges melted into the water
near_wall = [any(steep[m] > 0.12 for m in within(n, 3000.0)) if pitmask[n] else False for n in range(len(nodes))]
wall = [False] * len(nodes); seen = [False] * len(nodes)
for n0 in range(len(nodes)):              # whole connected pit region is filled if any of it touches a steep wall
    if not pitmask[n0] or seen[n0]: continue
    comp = [n0]; seen[n0] = True; q = [n0]
    while q:
        u = q.pop()
        for m, d in adj[u]:
            if pitmask[m] and not seen[m]: seen[m] = True; comp.append(m); q.append(m)
    if any(near_wall[c] for c in comp):
        for c in comp: wall[c] = True
env = [c if (pm and w) else v for c, v, pm, w in zip(clo, z, pitmask, wall)]
# then cap the grade (steep bogus steps -> ramps)
pq = [(-v, n) for n, v in enumerate(env)]; heapq.heapify(pq)
while pq:
    v, n = heapq.heappop(pq); v = -v
    if v < env[n]: continue
    for m, d in adj[n]:
        c = v - G * d
        if c > env[m] + 0.5: env[m] = c; heapq.heappush(pq, (-c, m))
env0 = env[:]
rep = {}
for k, r in R.items():
    ids = idx[k]; e = [env[n] for n in ids]
    sm = [sum(e[max(0, i - 4): i + 5]) / len(e[max(0, i - 4): i + 5]) for i in range(len(e))]
    if len(ids) > 1:  # keep the joints exact
        sm[0], sm[-1] = e[0], e[-1]
    r["ground"] = [round(z[n], 1) for n in ids]
    r["pts"] = [[p[0], p[1], round(max(v, g - 30), 1)] for p, v, g in zip(r["pts"], sm, r["ground"])]
    lift = [p[2] - g for p, g in zip(r["pts"], r["ground"])]
    rep[k] = round(max(lift) / 100, 1)
json.dump(data, open(OUT, "w"))
print("PIE-traced points:", used, "/", len(nodes)); print("max lift per carriageway (m):", {k: v for k, v in sorted(rep.items(), key=lambda t: -t[1]) if v > 0.5})
