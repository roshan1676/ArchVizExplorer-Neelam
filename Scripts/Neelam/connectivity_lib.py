"""Shared helpers: lat/lon -> Unreal (CesiumGeoreference) + ground height from the map."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
WORLD = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
GEO = next(a for a in EAS.get_all_level_actors() if isinstance(a, unreal.CesiumGeoreference))
ROOT = next(a for a in EAS.get_all_level_actors() if a.get_actor_label() == "Neelam_WindTunnel_Root")
RZ = ROOT.get_actor_location().z
TILESETS = [a for a in EAS.get_all_level_actors() if isinstance(a, unreal.Cesium3DTileset)]
IGNORE = [a for a in EAS.get_all_level_actors() if a not in TILESETS and a.get_class().get_name() not in ("CesiumGeoreference",)]


import json as _json, os as _os
HCACHE_PATH = _os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam", "Data", "height_cache.json")
try:
    HCACHE = _json.load(open(HCACHE_PATH))          # "lat,lon" (6 dp) -> ground Z (cm); filled by Sample_Heights.py
except Exception:
    HCACHE = {}


def hkey(lat, lon):
    return "%.6f,%.6f" % (lat, lon)


def to_xy(lat, lon):
    return GEO.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lon, lat, GEO.get_editor_property("origin_height")))


def to_ue(lat, lon, h=None):
    """lat/lon -> Unreal XY; Z from the height cache (Sample_Heights.py), else a downward trace onto the map
    (Google 3D Tiles, only works where tiles are streamed in), else root height."""
    geo_h = GEO.get_editor_property("origin_height") if h is None else h
    w = GEO.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lon, lat, geo_h))
    k = hkey(lat, lon)
    if k in HCACHE:
        return unreal.Vector(w.x, w.y, HCACHE[k]), True
    hit = unreal.SystemLibrary.line_trace_single(WORLD, unreal.Vector(w.x, w.y, RZ + 60000), unreal.Vector(w.x, w.y, RZ - 20000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, IGNORE, unreal.DrawDebugTrace.NONE, True)
    z = None
    if hit is not None:
        t = hit.to_tuple()
        if t[0]:
            z = float(t[4].z)
    return unreal.Vector(w.x, w.y, z if z is not None else RZ), z is not None


def smooth_z(vs, max_step=400.0, window=3):
    """Median filter (kills single spikes: trees, lamp posts, vehicles caught by traces), then a running max over
    +-1 point so the ribbon never sags below a real bump between samples (flyover ramps, road camber)."""
    zs = [v.z for v in vs]
    med = []
    for i in range(len(zs)):
        w = sorted(zs[max(0, i - window): i + window + 1])
        med.append(w[len(w) // 2])
    out = [max(med[max(0, i - 1): i + 2]) for i in range(len(med))]
    return [unreal.Vector(v.x, v.y, z) for v, z in zip(vs, out)]


try:
    SURF = _json.load(open(_os.path.join(_os.path.dirname(HCACHE_PATH), "surface_dense.json")))   # Surface_Align.py
except Exception:
    SURF = {}


def poly_s(pts):
    """cumulative distance (cm, UE XY) along a lat/lon polyline"""
    xy = [to_xy(la, lo) for la, lo in pts]; s = [0.0]
    for a, b in zip(xy, xy[1:]): s.append(s[-1] + ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5)
    return xy, s


ROAD_LIFT = 30.0


def envelope_z(pid, full_pts, idx, lift):
    """UE points for full_pts[idx...] (idx = ordered indices into the full polyline) sitting ON TOP of the dense surface:
    each point gets the highest sampled surface over both neighbouring segments (so no segment can dip under a bump),
    + lift. Falls back to the height cache + smooth_z where no dense samples exist."""
    xy, s = poly_s(full_pts)
    d = SURF.get(pid)
    if not d or not any(z is not None for z in d["z"]):
        vs = smooth_z([to_ue(*full_pts[i])[0] for i in idx])
        return [unreal.Vector(v.x, v.y, v.z + lift) for v in vs], False
    ds, dz = d["s"], d["z"]
    out = []
    for k, i in enumerate(idx):
        lo = s[idx[k - 1]] if k > 0 else s[i] - 300.0
        hi = s[idx[k + 1]] if k < len(idx) - 1 else s[i] + 300.0
        zs = [z for t, z in zip(ds, dz) if lo - 1 <= t <= hi + 1 and z is not None]
        if not zs:
            zs = [dz[min(range(len(ds)), key=lambda q: abs(ds[q] - s[i]))]]
        dk = road_deck(xy[i].x, xy[i].y, -100.0)       # only well inside a built carriageway (edges have barriers/trees)
        if dk is not None and max(zs) - dk > 150.0: dk = None   # something stands on it here (bridge/structure): stay on top
        z = (dk + ROAD_LIFT) if dk is not None else (max(zs) + lift)   # on a built road: sit on the deck
        out.append(unreal.Vector(xy[i].x, xy[i].y, z))
    return smooth_above(out), True


def smooth_above(vs, passes=3, win=3):
    """smooth the Z profile (running max then moving average) but never below the input -> clean ribbons, still on top"""
    base = [v.z for v in vs]; z = base[:]
    for _ in range(passes):
        mx = [max(z[max(0, i - 1): i + 2]) for i in range(len(z))]
        z = [max(base[i], sum(mx[max(0, i - win): i + win + 1]) / len(mx[max(0, i - win): i + win + 1])) for i in range(len(z))]
    return [unreal.Vector(v.x, v.y, zz) for v, zz in zip(vs, z)]


# ---- 3D road decks (Blender-built, Place_Roads.py): points on a carriageway ride the deck, not the photogrammetry
try:
    _RB = _json.load(open(_os.path.join(_os.path.dirname(HCACHE_PATH), "road_build.json")))["roads"]
except Exception:
    _RB = {}
DECK_TOP = 12.0                                   # cm, asphalt above the sampled surface (build_roads.py DECK)
_RG = {}
for _k, _r in _RB.items():
    for _x, _y, _z in _r["pts"]:
        _RG.setdefault((int(_x // 1000), int(_y // 1000)), []).append((_x, _y, _z, _r["width_m"] * 50.0, _k))


def road_deck(x, y, margin=100.0):
    """deck Z (cm) if (x,y) lies on a built carriageway (within half width + margin), else None"""
    best = None
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for (rx, ry, rz, hw, k) in _RG.get((int(x // 1000) + i, int(y // 1000) + j), []):
                d = ((rx - x) ** 2 + (ry - y) ** 2) ** 0.5
                if d <= hw + margin and (best is None or d < best[0]): best = (d, rz + DECK_TOP)
    return None if best is None else best[1]
