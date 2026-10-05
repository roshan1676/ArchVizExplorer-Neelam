# Central Railway corridor + stations in 3D (4 Oct 2026, client: "railway is just a flat photo").
# python build_railway.py <railway.json> <rail_heights.json> <out_dir>      (bpy module, cloud)
# UE cm in, Blender m out (x/100, -y/100, z/100), one mesh per 500 m chunk (rail_<i>_<j>.fbx), vertices absolute (actor at 0).
# Slots: Ballast (u = metres along, v = metres across: sleepers in the shader), Rail, Steel (OHE portals, roof columns),
#        Wire, Concrete (platforms, FOB deck), Edge (platform coping), Roof (sheds, FOB roofs: u = metres across the sheets).
import bpy, bmesh, json, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
R = json.load(open(a[0])); H = json.load(open(a[1])); OUT = a[2]; os.makedirs(OUT, exist_ok=True)
SITE = (944.0, 4429.0); RAD = 265000.0
SLOTS = ["Ballast", "Rail", "Steel", "Wire", "Concrete", "Edge", "Roof"]
SI = {s: i for i, s in enumerate(SLOTS)}

# ---------------- heights: 'low' ground samples on a 10 m grid
G = {}
for k, v in H.items():
    x, y = map(float, k.split(",")); G.setdefault((int(x // 2000), int(y // 2000)), []).append((x, y, v[1]))
def ground(x, y, r=2500.0):
    best = []
    gx, gy = int(x // 2000), int(y // 2000)
    for i in (-1, 0, 1, 2, -2):
        for j in (-1, 0, 1, 2, -2):
            for (px, py, z) in G.get((gx + i, gy + j), []):
                d = math.hypot(px - x, py - y)
                if d < r: best.append((d, z))
    if not best: return None
    best.sort(); zs = sorted(z for _, z in best[:6]); return zs[len(zs) // 3]

def dens(pts, step=500.0):
    out = []
    for p, q in zip(pts[:-1], pts[1:]):
        L = math.hypot(q[0] - p[0], q[1] - p[1]); n = max(1, int(math.ceil(L / step)))
        for k in range(n): out.append((p[0] + (q[0] - p[0]) * k / n, p[1] + (q[1] - p[1]) * k / n))
    out.append(tuple(pts[-1])); return out
inr = lambda p: math.hypot(p[0] - SITE[0], p[1] - SITE[1]) < RAD

def smooth_profile(P):
    z = [ground(x, y) for x, y in P]
    known = [i for i, v in enumerate(z) if v is not None]
    if not known: return None
    for i in range(len(z)):
        if z[i] is None:
            j = min(known, key=lambda k: abs(k - i)); z[i] = z[j]
    # rolling 30th percentile +-60 m (trains / canopies in the photogrammetry), then mean +-40 m, grade-limited
    w = 12; zp = []
    for i in range(len(z)):
        s = sorted(z[max(0, i - w):i + w + 1]); zp.append(s[int(len(s) * 0.3)])
    w2 = 8; zs = [sum(zp[max(0, i - w2):i + w2 + 1]) / len(zp[max(0, i - w2):i + w2 + 1]) for i in range(len(zp))]
    return zs

# ---------------- tracks
tracks = []
for w in R["rails"]:
    P = [p for p in dens(w["pts"]) if inr(p)]
    if len(P) < 2: continue
    # keep the longest in-radius run
    runs, cur = [], [P[0]]
    for p, q in zip(P[:-1], P[1:]):
        if math.hypot(q[0] - p[0], q[1] - p[1]) > 700: runs.append(cur); cur = [q]
        else: cur.append(q)
    runs.append(cur)
    for run in runs:
        if len(run) < 2: continue
        zs = smooth_profile(run)
        if zs: tracks.append({"id": w["id"], "pts": run, "z": zs})

def track_z_at(x, y, maxd=1500.0):
    best = (1e18, None)
    for t in tracks:
        for (px, py), z in zip(t["pts"], t["z"]):
            if abs(px - x) > maxd or abs(py - y) > maxd: continue
            d = math.hypot(px - x, py - y)
            if d < best[0]: best = (d, z)
    return best[1] if best[0] < maxd else None

# ---------------- mesh store per chunk
chunks = {}
def ck(x, y): return "%d_%d" % (math.floor(x / 50000.0), math.floor(y / 50000.0))
def C(key):
    if key not in chunks:
        bm = bmesh.new(); chunks[key] = (bm, bm.loops.layers.uv.new("UVMap"))
    return chunks[key]
def V(bm, x, y, z): return bm.verts.new((x / 100.0, -y / 100.0, z / 100.0))
def quad(key, pts, slot, uvs):
    bm, uvl = C(key); vs = [V(bm, *p) for p in pts]
    try: f = bm.faces.new(vs)
    except ValueError: return
    f.material_index = SI[slot]
    for l, uv in zip(f.loops, uvs): l[uvl].uv = uv

def offsets(P):
    """per-vertex unit normal (left) with miter"""
    N = []
    for i in range(len(P)):
        a = P[max(0, i - 1)]; b = P[min(len(P) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1.0
        N.append((-dy / L, dx / L))
    return N

def ribbon(key, P, Z, N, prof, slot, dist):
    """extrude a cross-section profile [(offset_cm, dz_cm), ...] along P (open strip, faces between consecutive profile pts)"""
    for i in range(len(P) - 1):
        k = ck(*P[i])
        for j in range(len(prof) - 1):
            o0, h0 = prof[j]; o1, h1 = prof[j + 1]
            pts = [(P[i][0] + N[i][0] * o0, P[i][1] + N[i][1] * o0, Z[i] + h0),
                   (P[i + 1][0] + N[i + 1][0] * o0, P[i + 1][1] + N[i + 1][1] * o0, Z[i + 1] + h0),
                   (P[i + 1][0] + N[i + 1][0] * o1, P[i + 1][1] + N[i + 1][1] * o1, Z[i + 1] + h1),
                   (P[i][0] + N[i][0] * o1, P[i][1] + N[i][1] * o1, Z[i] + h1)]
            uvs = [(dist[i] / 100.0, o0 / 100.0), (dist[i + 1] / 100.0, o0 / 100.0), (dist[i + 1] / 100.0, o1 / 100.0), (dist[i] / 100.0, o1 / 100.0)]
            quad(k, pts, slot, uvs)

GAUGE = 167.6
for t in tracks:
    P, Z = t["pts"], t["z"]; N = offsets(P)
    dist = [0.0]
    for p, q in zip(P[:-1], P[1:]): dist.append(dist[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    # ballast bed: 5.4 m base buried 30 cm, 3.4 m top at +35 cm
    ribbon(None, P, Z, N, [(270, -30), (170, 35), (-170, 35), (-270, -30)], "Ballast", dist)
    # two rails 7 cm x 15 cm on the sleepers (+35 .. +50), with a 15 cm foot
    for s in (1, -1):
        c = s * GAUGE / 2
        ribbon(None, P, Z, N, [(c + 7, 35), (c + 3.5, 49), (c - 3.5, 49), (c - 7, 35)], "Rail", dist)
    # contact wire 5.6 m above rail
    ribbon(None, P, Z, N, [(1.2, 610), (-1.2, 610), (-1.2, 607.5), (1.2, 607.5), (1.2, 610)], "Wire", dist)

# ---------------- OHE portals every 60 m across the whole bundle
def box(key, cx, cy, z0, z1, hw, hd, yaw_deg, slot):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    corners = [(cx + c * dx - s * dy, cy + s * dx + c * dy) for dx, dy in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]
    for i in range(4):
        p, q = corners[i], corners[(i + 1) % 4]
        L = math.hypot(q[0] - p[0], q[1] - p[1]) / 100.0
        quad(key, [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)], slot, [(0, 0), (L, 0), (L, (z1 - z0) / 100), (0, (z1 - z0) / 100)])
    quad(key, [(x, y, z1) for x, y in corners], slot, [(0, 0), (1, 0), (1, 1), (0, 1)])
def beam(key, p, q, z0, z1, hw, slot):
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1.0; nx, ny = -dy / L * hw, dx / L * hw
    A = [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]
    u = L / 100.0
    for zz, rev in ((z1, False), (z0, True)):
        pts = [(x, y, zz) for x, y in A]; quad(key, pts[::-1] if rev else pts, slot, [(0, 0), (u, 0), (u, 1), (0, 1)])
    for i in range(4):
        a_, b_ = A[i], A[(i + 1) % 4]
        quad(key, [(a_[0], a_[1], z0), (b_[0], b_[1], z0), (b_[0], b_[1], z1), (a_[0], a_[1], z1)], slot, [(0, 0), (u, 0), (u, 1), (0, 1)])

portals = []
def cross_offsets(px, py, nx, ny, span=3000.0):
    """signed offsets of every track crossing the perpendicular line through (px,py)"""
    out = []
    for t in tracks:
        P = t["pts"]
        for (a_, b_), za in zip(zip(P[:-1], P[1:]), t["z"]):
            if min(abs(a_[0] - px), abs(b_[0] - px)) > span + 600 or min(abs(a_[1] - py), abs(b_[1] - py)) > span + 600: continue
            # intersect segment a-b with line p + s*n
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]; den = dx * ny - dy * nx
            if abs(den) < 1e-6: continue
            u = ((px - a_[0]) * ny - (py - a_[1]) * nx) / den
            if 0 <= u <= 1:
                sx, sy = a_[0] + dx * u, a_[1] + dy * u; s = (sx - px) * nx + (sy - py) * ny
                if abs(s) < span: out.append((s, za))
    return sorted(out)
for t in tracks:
    P = t["pts"]; N = offsets(P); acc = 0.0
    for i in range(1, len(P)):
        acc += math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1])
        if acc < 6000: continue
        acc = 0.0
        px, py = P[i]
        if any(math.hypot(px - qx, py - qy) < 4500 for qx, qy in portals): continue
        offs = cross_offsets(px, py, N[i][0], N[i][1])
        if not offs: continue
        # contiguous group around this track (gaps < 9 m)
        grp = [o for o in offs]; s_min = min(o[0] for o in grp); s_max = max(o[0] for o in grp)
        lo = hi = 0.0
        srt = sorted(set(round(o[0]) for o in grp))
        idx = min(range(len(srt)), key=lambda k: abs(srt[k]))
        lo = hi = srt[idx]
        for k in range(idx - 1, -1, -1):
            if lo - srt[k] < 900: lo = srt[k]
            else: break
        for k in range(idx + 1, len(srt)):
            if srt[k] - hi < 900: hi = srt[k]
            else: break
        z = t["z"][i]; key = ck(px, py)
        nx, ny = N[i]
        m1 = (px + nx * (lo - 300), py + ny * (lo - 300)); m2 = (px + nx * (hi + 300), py + ny * (hi + 300))
        yaw = math.degrees(math.atan2(ny, nx))
        for m in (m1, m2):
            box(key, m[0], m[1], z - 30, z + 900, 15, 15, yaw, "Steel")          # H-mast 30 x 30 cm, 9 m
            box(key, m[0], m[1], z - 30, z + 40, 40, 40, yaw, "Concrete")         # foundation
        beam(key, m1, m2, z + 820, z + 870, 18, "Steel")                          # portal boom
        for s, _ in offs:
            if lo - 1 <= s <= hi + 1:                                            # droppers to each contact wire
                d = (px + nx * s, py + ny * s); box(key, d[0], d[1], z + 610, z + 820, 2, 2, yaw, "Steel")
        portals.append((px, py))

# ---------------- platforms (closed OSM areas): 84 cm above rail level, coping, umbrella sheds
def pca(poly):
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    sxx = sum((p[0] - cx) ** 2 for p in poly); syy = sum((p[1] - cy) ** 2 for p in poly); sxy = sum((p[0] - cx) * (p[1] - cy) for p in poly)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy); ux, uy = math.cos(ang), math.sin(ang)
    proj = [((p[0] - cx) * ux + (p[1] - cy) * uy, -(p[0] - cx) * uy + (p[1] - cy) * ux) for p in poly]
    return cx, cy, ux, uy, min(q[0] for q in proj), max(q[0] for q in proj), min(q[1] for q in proj), max(q[1] for q in proj)
def width_at(poly, cx, cy, ux, uy, s):
    """platform width across the main axis at station s"""
    vs = []
    n = len(poly)
    for i in range(n):
        a_, b_ = poly[i], poly[(i + 1) % n]
        sa = (a_[0] - cx) * ux + (a_[1] - cy) * uy; sb = (b_[0] - cx) * ux + (b_[1] - cy) * uy
        if (sa - s) * (sb - s) <= 0 and sa != sb:
            t_ = (s - sa) / (sb - sa); x = a_[0] + (b_[0] - a_[0]) * t_; y = a_[1] + (b_[1] - a_[1]) * t_
            vs.append(-(x - cx) * uy + (y - cy) * ux)
    return (min(vs), max(vs)) if len(vs) >= 2 else None
nplat = 0
for p in R["platforms"]:
    poly = p["pts"]
    if poly[0] != poly[-1] or not any(inr(q) for q in poly): continue
    poly = poly[:-1]
    area = sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly))) / 2
    if abs(area) < 2e6: continue                       # < 200 m2
    if area < 0: poly = poly[::-1]
    zr = [track_z_at(x, y) for x, y in poly]; zr = sorted(z for z in zr if z is not None)
    if not zr: continue
    zt = zr[len(zr) // 2] + 50 + 84                    # rail top + 84 cm
    cx, cy, ux, uy, s0, s1, w0, w1 = pca(poly); key = ck(cx, cy)
    # top (n-gon -> triangulated in Blender) + walls down 1.6 m
    bm, uvl = C(key); vt = [V(bm, x, y, zt) for x, y in poly]; vb = [V(bm, x, y, zt - 160) for x, y in poly]
    try:
        f = bm.faces.new(vt); f.material_index = SI["Concrete"]
        for l in f.loops: l[uvl].uv = (l.vert.co.x / 2.0, l.vert.co.y / 2.0)
    except ValueError: pass
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        try:
            f = bm.faces.new((vb[i], vb[j], vt[j], vt[i])); f.material_index = SI["Concrete"]
            L = math.hypot(poly[j][0] - poly[i][0], poly[j][1] - poly[i][1]) / 100
            for l, uv in zip(f.loops, ((0, 0), (L, 0), (L, 1.6), (0, 1.6))): l[uvl].uv = uv
        except ValueError: pass
    # coping strip (yellow / white) 45 cm wide along every long edge, 1 cm proud
    for i in range(len(poly)):
        a_, b_ = poly[i], poly[(i + 1) % len(poly)]
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        if L < 1500: continue
        dx, dy = (b_[0] - a_[0]) / L, (b_[1] - a_[1]) / L; nx, ny = -dy, dx      # inward for CCW
        pts = [(a_[0], a_[1], zt + 1), (b_[0], b_[1], zt + 1), (b_[0] + nx * 45, b_[1] + ny * 45, zt + 1), (a_[0] + nx * 45, a_[1] + ny * 45, zt + 1)]
        quad(key, pts, "Edge", [(0, 0), (L / 100, 0), (L / 100, 1), (0, 1)])
    # umbrella sheds over the middle 80 %: centre columns every 8 m, roof 5 m up, width = platform width - 1 m (max 10 m)
    s = s0 + (s1 - s0) * 0.1; end = s1 - (s1 - s0) * 0.1; prev = None
    while s <= end:
        wa = width_at(poly, cx, cy, ux, uy, s)
        if wa and wa[1] - wa[0] > 450:
            mid = (wa[0] + wa[1]) / 2; half = min(500, (wa[1] - wa[0]) / 2 - 50)
            x = cx + ux * s - uy * mid; y = cy + uy * s + ux * mid
            box(key, x, y, zt, zt + 500, 12, 12, math.degrees(math.atan2(uy, ux)), "Steel")
            if prev:
                (px_, py_, ph) = prev; h_ = min(half, ph)
                a1 = (px_ - (-uy) * h_, py_ - ux * h_); a2 = (x - (-uy) * h_, y - ux * h_); b2 = (x + (-uy) * h_, y + ux * h_); b1 = (px_ + (-uy) * h_, py_ + ux * h_)
                Lr = math.hypot(x - px_, y - py_) / 100
                # gently pitched butterfly roof: edges 30 cm higher than the centre gutter
                for (e1, e2) in ((a1, a2), (b1, b2)):
                    quad(key, [(px_, py_, zt + 500), (x, y, zt + 500), (e2[0], e2[1], zt + 530), (e1[0], e1[1], zt + 530)], "Roof",
                         [(0, 0), (0, Lr), (h_ / 100, Lr), (h_ / 100, 0)])
                    quad(key, [(e1[0], e1[1], zt + 518), (e2[0], e2[1], zt + 518), (x, y, zt + 488), (px_, py_, zt + 488)], "Roof",
                         [(h_ / 100, 0), (h_ / 100, Lr), (0, Lr), (0, 0)])
                beam(key, (px_, py_), (x, y), zt + 470, zt + 500, 10, "Steel")
            prev = (x, y, half)
        else: prev = None
        s += 800
    nplat += 1

# ---------------- foot over-bridges (OSM footway bridges near the tracks): deck 8.6 m over rail, 3.6 m wide, railings, covered roofs
nfob = 0
for b in R["bridges"]:
    P = b["pts"]
    if not all(inr(q) for q in P) or len(P) < 2: continue
    zs = [track_z_at(x, y, 2500) for x, y in dens(P, 300)]; zs = [z for z in zs if z is not None]
    if not zs: continue
    zd = max(zs) + 50 + 860; P = dens(P, 400); N = offsets(P); key = ck(*P[len(P) // 2])
    dist = [0.0]
    for p, q in zip(P[:-1], P[1:]): dist.append(dist[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    Z = [zd] * len(P)
    ribbon(key, P, Z, N, [(180, 0), (-180, 0), (-180, -60), (180, -60), (180, 0)], "Concrete", dist)
    for sgn in (1, -1):
        ribbon(key, P, Z, N, [(sgn * 180, 0), (sgn * 180, 110), (sgn * 172, 110), (sgn * 172, 0)], "Steel", dist)
    if b["tags"].get("covered") == "yes" or b["tags"].get("layer") == "2":
        ribbon(key, P, Z, N, [(-210, 330), (0, 360), (210, 330)], "Roof", dist)
        ribbon(key, P, Z, N, [(210, 322), (0, 352), (-210, 322)], "Roof", dist)
        acc = 0.0
        for i in range(len(P)):
            if i == 0 or acc >= 600:
                for sgn in (1, -1):
                    box(key, P[i][0] + N[i][0] * sgn * 176, P[i][1] + N[i][1] * sgn * 176, zd, zd + 335, 6, 6, 0, "Steel")
                acc = 0.0
            if i + 1 < len(P): acc += dist[i + 1] - dist[i]
    # piers at both ends
    for i in (0, len(P) - 1):
        zg = track_z_at(P[i][0], P[i][1], 3000) or zd - 900
        box(key, P[i][0], P[i][1], zg, zd - 60, 30, 30, 0, "Concrete")
    nfob += 1

# ---------------- write
mats = [bpy.data.materials.new(s) for s in SLOTS]
n = 0
for key, (bm, uvl) in sorted(chunks.items()):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = [bpy.data.materials.new(s) for s in SLOTS]
    me = bpy.data.meshes.new("rail_" + key); ob = bpy.data.objects.new("rail_" + key, me); bpy.context.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.normal_update(); bm.to_mesh(me); bm.free()
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "rail_%s.fbx" % key), use_selection=False, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y", axis_up="Z", object_types={"MESH"},
                             mesh_smooth_type="FACE", bake_space_transform=False)
    n += 1
print("RAIL_OK chunks", n, "tracks", len(tracks), "portals", len(portals), "platforms", nplat, "fobs", nfob)
