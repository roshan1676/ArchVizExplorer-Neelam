"""Size the BP_POI hologram box (POI_Geometry, engine 1 m cube + MI_Holo) to the landmark's real footprint,
so the template's highlight / blink on selection is visible above the Google 3D Tiles.
Footprints: Data/footprints.json (make_footprints.py, OSM) + OVERRIDES below. Base = ground (lowest cached
height of nearby route points, which lie on roads), height per category."""
import json, math, os
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
HEIGHT_M = {"Healthcare": 35, "Retail": 28, "Education": 20, "Immediate": 20, "Transport": 12, "Neighbourhood": 40}
OVERRIDES = {  # OSM had no usable polygon (checked 29 Sep)
    "checknaka": {"cx_m": 0, "cy_m": 0, "w_m": 70, "d_m": 35, "yaw_deg": 60, "src": "manual (toll plaza on EEH)"},
    "apex":      {"cx_m": 0, "cy_m": 0, "w_m": 45, "d_m": 35, "yaw_deg": 0,  "src": "manual (hospital block)"},
}
try:
    FP = json.load(open(os.path.join(P, "Data", "footprints.json")))
except Exception:
    FP = {}
FP.update(OVERRIDES)


def ground_z(C, lm, route_pts):
    near = [C.to_ue(la, lo)[0].z for la, lo in (route_pts or []) if math.dist((la * 110540, lo * 104900), (lm["lat"] * 110540, lm["lon"] * 104900)) < 200]
    zs = sorted(near) or [C.to_ue(lm["lat"], lm["lon"])[0].z]
    return zs[max(0, len(zs) // 10)]           # ~10th percentile: road level, not roofs/flyovers


def apply(C, poi, lm, route_pts=None, sink_m=6.0):
    f = FP.get(lm["id"], {"cx_m": 0, "cy_m": 0, "w_m": 40, "d_m": 40, "yaw_deg": 0})
    geo = [c for c in poi.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == "POI_Geometry"][0]
    h = HEIGHT_M.get(lm["cat"], 25) + sink_m
    gz = ground_z(C, lm, route_pts) - sink_m * 100
    base = poi.get_actor_location()
    loc = unreal.Vector(base.x + f["cx_m"] * 100, base.y - f["cy_m"] * 100, gz + h * 50)   # UE: +X east, +Y south
    geo.set_world_location_and_rotation(loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=-f["yaw_deg"]), False, False)  # Rotator(roll, pitch, yaw)
    geo.set_world_scale3d(unreal.Vector(max(f["w_m"], 8), max(f["d_m"], 8), h))
    return [lm["id"], round(f["w_m"]), round(f["d_m"]), round(h), round((gz - C.RZ) / 100, 1)]
