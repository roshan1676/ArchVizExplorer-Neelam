"""Landmark corrections after the client review (11 Oct 2026). Run AFTER Place_Landmarks.py (it re-places from OSM).
Ground: Data/landmark_ground.json (Landmark_PIE.py - photogrammetry traces on a ring 6-24 m around each model).
The old seating used road_build rings with tile holes -> several models were 4-17 m under the real ground
(Vaze "submerged", D-Mart "flat", Korum / Apex too low). Now base = ring p10 - 0.5 m, top = ring p50 + H.
Footprints read from PIE nadir shots of the real buildings (models + cut-outs hidden):
  vaze   real college block ~82 x 80 m, 21 m west / 8 m south of the old model -> moved + enlarged
  jbcn   school strip next to the CTS Cricket Academy turf (Google pin 19.15856, 72.94988) -> moved there
  fortis model already on the hospital (Google 19.16179, 72.94181); the PIN was 110 m north across the link road -> pin moved
  viviana / jupiter  both shrunk to the real footprints, Jupiter pushed off until there is a >= GAP_M lane between them
Also: map cut-out (LandmarkCut_*) + POI hologram box re-fitted to every model."""
import json, os, math
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
G = json.load(open(os.path.join(P, "Data", "landmark_ground.json")))
GAP_M = 14.0
# H = metres above the surrounding ground (p50). xy/yaw/w/d only where the footprint changes (w along the actor X, d along Y).
T = {
    "vaze":      dict(H=20, xy=(-16543, 10125), yaw=-180.0, w=82, d=80),
    "dmart":     dict(H=16),
    "korum":     dict(H=30),
    "fortis":    dict(H=40, pin=True),
    "apex":      dict(H=30),
    "jbcn":      dict(H=18, xy=(-92125, 58339), yaw=171.5, w=95, d=30),
    "billabong": dict(H=32),
    "viviana":   dict(H=30, shrink=0.94),
    "jupiter":   dict(H=55, xy=(141198, -510746), w=66, d=56),
}
A = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}

def zs(lid):
    z = sorted(v for _, _, v in G[lid]["ring"] if v is not None)
    return z[len(z) // 10], z[len(z) // 2]

def frame(a):
    """mesh-local bbox + world centre / axes / half sizes (cm)"""
    bb = a.static_mesh_component.static_mesh.get_bounding_box(); s = a.get_actor_scale3d()
    y = math.radians(a.get_actor_rotation().yaw); u, v = (math.cos(y), math.sin(y)), (-math.sin(y), math.cos(y))
    c = a.get_actor_transform().transform_location(unreal.Vector((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, 0))
    return bb, (c.x, c.y), u, v, (bb.max.x - bb.min.x) * abs(s.x) / 2, (bb.max.y - bb.min.y) * abs(s.y) / 2

def place(a, cx, cy, yaw, hw, hd, base, top):
    bb = a.static_mesh_component.static_mesh.get_bounding_box()
    sx, sy = hw * 2 / (bb.max.x - bb.min.x), hd * 2 / (bb.max.y - bb.min.y); sz = (top - base) / (bb.max.z - bb.min.z)
    lx, ly = (bb.min.x + bb.max.x) / 2 * sx, (bb.min.y + bb.max.y) / 2 * sy
    r = math.radians(yaw); ox, oy = lx * math.cos(r) - ly * math.sin(r), lx * math.sin(r) + ly * math.cos(r)
    a.set_actor_scale3d(unreal.Vector(sx, sy, sz))
    a.set_actor_location_and_rotation(unreal.Vector(cx - ox, cy - oy, base - bb.min.z * sz), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), False, False)

def corners(cx, cy, yaw, hw, hd):
    r = math.radians(yaw); u, v = (math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))
    return [(cx + s1 * hw * u[0] + s2 * hd * v[0], cy + s1 * hw * u[1] + s2 * hd * v[1]) for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

def sat_gap(p, q):
    """separating-axis distance between two convex quads (cm, <= 0 = overlap)"""
    best = -1e18
    for poly in (p, q):
        for i in range(4):
            ex, ey = poly[(i + 1) % 4][0] - poly[i][0], poly[(i + 1) % 4][1] - poly[i][1]; L = math.hypot(ex, ey); nx, ny = -ey / L, ex / L
            pa = [x * nx + y * ny for x, y in p]; qa = [x * nx + y * ny for x, y in q]
            best = max(best, max(min(qa) - max(pa), min(pa) - max(qa)))
    return best

out, boxes = {}, {}
for lid, t in T.items():
    a = A["Landmark_" + lid]; p10, p50 = zs(lid)
    bb, (cx, cy), u, v, hw, hd = frame(a); yaw = a.get_actor_rotation().yaw
    if "xy" in t: cx, cy = t["xy"]
    if "yaw" in t: yaw = t["yaw"]
    if "w" in t: hw, hd = t["w"] * 50, t["d"] * 50
    if "shrink" in t: hw, hd = hw * t["shrink"], hd * t["shrink"]
    boxes[lid] = [cx, cy, yaw, hw, hd, p10 - 50, p50 + t["H"] * 100]
# Viviana / Jupiter: push Jupiter straight away from Viviana until the lane is >= GAP_M
vb, jb = boxes["viviana"], boxes["jupiter"]
dx, dy = jb[0] - vb[0], jb[1] - vb[1]; L = math.hypot(dx, dy)
for _ in range(200):
    g = sat_gap(corners(*vb[:5]), corners(*jb[:5]))
    if g >= GAP_M * 100: break
    jb[0] += dx / L * 100; jb[1] += dy / L * 100
out["viviana_jupiter_gap_m"] = round(sat_gap(corners(*vb[:5]), corners(*jb[:5])) / 100, 1)

tiles = next(x for x in A.values() if x.get_actor_label() == "Google Photorealistic 3D Tiles")
for lid, (cx, cy, yaw, hw, hd, base, top) in boxes.items():
    a = A["Landmark_" + lid]
    place(a, cx, cy, yaw, hw, hd, base, top)
    # map cut-out 0.3 m inside the walls
    cp = A.get("LandmarkCut_" + lid)
    if cp:
        cp.set_actor_location(unreal.Vector(cx, cy, base), False, False)
        spl = cp.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
        for x, y in corners(cx, cy, yaw, hw - 30, hd - 30): spl.add_spline_point(unreal.Vector(x, y, base), unreal.SplineCoordinateSpace.WORLD, False)
        for q in range(4): spl.set_spline_point_type(q, unreal.SplinePointType.LINEAR, False)
        spl.set_closed_loop(True, True)
    # POI pin + hologram box (template blinks it on selection)
    poi = A.get("POI_" + lid)
    if poi:
        if T[lid].get("pin"):
            pl = poi.get_actor_location(); poi.set_actor_location(unreal.Vector(cx, cy, pl.z), False, False)
        geo = [c for c in poi.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == "POI_Geometry"]
        if geo:
            gb, gt = base - 600, top + 400
            geo[0].set_world_location_and_rotation(unreal.Vector(cx, cy, (gb + gt) / 2), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), False, False)
            geo[0].set_world_scale3d(unreal.Vector(hw / 50 + 8, hd / 50 + 8, (gt - gb) / 100))
    out[lid] = {"xy": [round(cx), round(cy)], "yaw": round(yaw, 1), "size_m": [round(hw / 50), round(hd / 50), round((top - base) / 100)],
                "base_m": round(base / 100, 1), "ground_p50_m": round(boxes[lid][6] / 100 - T[lid]["H"], 1)}
try: tiles.refresh_tileset()
except Exception: pass
result = out
