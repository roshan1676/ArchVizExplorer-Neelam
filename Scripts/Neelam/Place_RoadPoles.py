"""Street lights along the OUTER kerb of every built carriageway (BP_RoadTool, poles only), on the deck height.
India drives on the left: the outer edge is the LEFT side of the OSM way direction. Folder Neelam/Roads/Poles."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ROAD = unreal.EditorAssetLibrary.load_blueprint_class("/Game/ArchVizExplorer/Blueprints/BP_RoadTool")
RB = json.load(open(os.path.join(P, "Data", "road_build.json")))["roads"]
FOLDER = "Neelam/Roads/Poles"; SIGN = globals().get("POLE_SIGN", 1.0)
SPACING = {"vb": 3500.0, "eeh": 4500.0, "mar": 4500.0}
for a in [a for a in EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER) or a.get_actor_label().startswith("Poles_")]:
    EAS.destroy_actor(a)
rep = []
for k, r in RB.items():
    pts = r["pts"]
    L = sum(math.dist(a[:2], b[:2]) for a, b in zip(pts, pts[1:]))
    if L < 20000: continue
    t = EAS.spawn_actor_from_class(ROAD, unreal.Vector(*pts[0]))
    t.set_actor_label("Poles_%s_%s" % (r["group"], k[3:])); t.set_folder_path(FOLDER)
    spl = t.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
    for x, y, z in pts[::3] + [pts[-1]]:
        spl.add_spline_point(unreal.Vector(x, y, z + 12.0), unreal.SplineCoordinateSpace.WORLD, False)
    for q in range(spl.get_number_of_spline_points()): spl.set_spline_point_type(q, unreal.SplinePointType.CURVE_CLAMPED, False)
    spl.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: spl.set_editor_property(pr, True)
        except Exception: pass
    for kk, val in (("DrawSplinePointNumbers?", False), ("Collision_Road?", False), ("Width_Road", 0.01),
                    ("CenterOffset_LightPoles", SIGN * (r["width_m"] * 50 + 60.0)), ("Spacing_LightPoles", SPACING[r["group"]])):
        t.set_editor_property(kk, val)
    t.set_editor_property("Build_LightPoles?", True)
    poles = [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == "BP_Pole_C" and a.get_attach_parent_actor() == t]
    side = None
    if poles and len(pts) > 2:           # which side did they land on? (+ = left of travel)
        pl = poles[0].get_actor_location(); a, b = pts[0], pts[2]; dx, dy = b[0] - a[0], b[1] - a[1]
        side = (dx * (pl.y - a[1]) - dy * (pl.x - a[0]))    # UE is left-handed: <0 means left of travel when looking down Z
    rep.append([k, len(poles), None if side is None else round(side)])
result = {"tools": len(rep), "poles": sum(r[1] for r in rep), "sample": rep[:6]}
