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
    """Remove spikes (bridges, trees, flyovers caught by traces): median filter + clamp to ground-ish."""
    zs = [v.z for v in vs]
    out = []
    for i in range(len(zs)):
        w = sorted(zs[max(0, i - window): i + window + 1])
        out.append(w[len(w) // 2])
    return [unreal.Vector(v.x, v.y, z) for v, z in zip(vs, out)]
