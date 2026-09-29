"""Landmark buildings from the client's Blender files (exported by Blender/export_landmark.py: bottom-centre pivot).
Each is imported, scaled to the real OSM building outline (Data/building_footprints.json + OVERRIDES), turned so its
front (-Y in Blender = +Y in UE) faces the road its drive route arrives on, seated on the measured ground ring
(road_build.json rings, 15th percentile) and the Google tiles are cut out under the footprint (like the Neelam site).
Heights: HEIGHT_M (typical floor counts) - the Blender boxes are not to scale."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
import sys; sys.path.insert(0, P)
import importlib, connectivity_lib as C; importlib.reload(C)
EAS = C.EAS; EAL = unreal.EditorAssetLibrary
SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "landmarks")
HEIGHT_M = {"apex": 20, "billabong": 32, "dmart": 13, "fortis": 30, "hiramongi": 20, "jbcn": 18, "jupiter": 55, "korum": 28, "rmall": 24,
            "singhania": 20, "vaze": 16, "viviana": 30}
BF = json.load(open(os.path.join(P, "Data", "building_footprints.json")))
PLOT = json.load(open(os.path.join(P, "Data", "footprints.json")))
OVERRIDES = {   # no usable OSM building (29 Sep): building-sized box on the plot
    "apex": {"cx_m": 0, "cy_m": 0, "w_m": 45, "d_m": 35, "yaw_deg": 0},
    "jbcn": dict(PLOT["jbcn"], w_m=60, d_m=35), "vaze": dict(PLOT["vaze"], w_m=70, d_m=30)}
RINGS = json.load(open(os.path.join(P, "Data", "road_build.json")))["rings"]
LMS = {}; ROUTES = {}
for ph in ("phase2", "phase3"):
    for l in json.load(open(os.path.join(P, "Data", "landmarks_%s.json" % ph), encoding="utf-8"))["landmarks"]: LMS[l["id"]] = l
    ROUTES.update(json.load(open(os.path.join(P, "Data", "connectivity_%s.json" % ph), encoding="utf-8"))["routes"])
FOLDER, CUTF = "Neelam/Landmarks", "Neelam/Landmarks/Cutouts"
for a in [a for a in EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]: EAS.destroy_actor(a)
tiles = next(t for t in EAS.get_all_level_actors() if t.get_actor_label() == "Google Photorealistic 3D Tiles")
ov = next(c for c in tiles.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "CesiumPolygonRasterOverlay")
polys = [p for p in ov.get_editor_property("polygons") if p and not str(p.get_actor_label()).startswith("LandmarkCut_")]
report = {}
for lid, H in HEIGHT_M.items():
    fbx = os.path.join(SRC, "LM_%s.fbx" % lid)
    if not os.path.exists(fbx): continue
    dest = "/Game/Neelam/Landmarks/" + lid
    t = unreal.AssetImportTask(); t.filename = fbx; t.destination_path = dest; t.destination_name = "SM_Landmark_" + lid
    t.automated = True; t.replace_existing = True; t.save = True
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = True; ui.import_textures = True
    ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False
    t.options = ui; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    sm = unreal.load_asset(dest + "/SM_Landmark_" + lid)
    bb = sm.get_bounding_box(); bx, by, bz = bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z
    f = OVERRIDES.get(lid) or BF[lid]
    l = LMS[lid]; pin = C.to_xy(l["lat"], l["lon"])
    cx, cy = pin.x + f["cx_m"] * 100, pin.y - f["cy_m"] * 100
    # road direction: route point ~60 m before the landmark
    rp = ROUTES[lid]["pts"]; tgt = C.to_xy(*rp[max(0, len(rp) - 5)]); want = math.atan2(tgt.y - cy, tgt.x - cx)
    best = None
    for k in range(4):
        yaw = -f["yaw_deg"] + 90 * k
        along_w = k % 2 == 0
        sx = (f["w_m"] if along_w else f["d_m"]) * 100 / bx; sy = (f["d_m"] if along_w else f["w_m"]) * 100 / by
        distort = abs(math.log(sx / sy))
        fy = math.radians(yaw + 90)                       # local +Y after yaw (UE yaw rotates X toward Y)
        face = math.cos(fy - want)
        score = -distort * 2 + face
        if best is None or score > best[0]: best = (score, yaw, sx, sy, face)
    _, yaw, sx, sy, face = best
    sz = H * 100 / bz
    ring = RINGS.get(lid) or {}
    gz = (ring.get("ground_p15") if ring.get("ground_p15") is not None else C.to_ue(l["lat"], l["lon"])[0].z) - 30
    a = EAS.spawn_actor_from_object(sm, unreal.Vector(cx, cy, gz - bb.min.z * sz), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    a.set_actor_scale3d(unreal.Vector(sx, sy, sz)); a.set_actor_label("Landmark_" + lid); a.set_folder_path(FOLDER)
    a.static_mesh_component.set_collision_profile_name("NoCollision")
    # cut the map under the building (0.3 m inside the walls)
    ang = math.radians(-f["yaw_deg"]); ux, uy = math.cos(ang), math.sin(ang); vx, vy = -uy, ux
    hw, hd = f["w_m"] * 50 - 30, f["d_m"] * 50 - 30
    cp = EAS.spawn_actor_from_class(unreal.CesiumCartographicPolygon, unreal.Vector(cx, cy, gz))
    cp.set_actor_label("LandmarkCut_" + lid); cp.set_folder_path(CUTF)
    spl = cp.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
    for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        spl.add_spline_point(unreal.Vector(cx + s1 * hw * ux + s2 * hd * vx, cy + s1 * hw * uy + s2 * hd * vy, gz), unreal.SplineCoordinateSpace.WORLD, False)
    for q in range(4): spl.set_spline_point_type(q, unreal.SplinePointType.LINEAR, False)
    spl.set_closed_loop(True, True); polys.append(cp)
    report[lid] = {"size_m": [round(f["w_m"]), round(f["d_m"]), H], "yaw": round(yaw), "faces_road": round(face, 2), "ground_m": round((gz - C.RZ) / 100, 1)}
ov.set_editor_property("polygons", polys)
try: tiles.refresh_tileset()
except Exception: pass
result = report
