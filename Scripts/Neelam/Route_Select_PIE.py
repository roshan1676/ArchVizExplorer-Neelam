"""PIE check of the Surroundings landmark selection (27 Oct, client: "click a landmark -> the map shows just that path").
Bridge job, PIE running, globals MODE / LID:
  MODE "list"   -> landmark ids (BP_POI pins with an LM_<id> tag)
  MODE "select" -> as the user does: press the real Surroundings button (ui_press.py), then the pin's Select_POI. Reports which route / glow /
                   traffic actors are visible: PASS = every visible one carries LM_<LID>, and its own Route_/Road_ is on.
  MODE "amenity"-> select an amenity pin (no LM tag): PASS = no route / glow visible
  MODE "showall"-> ShowAllSurroundingsRoutes: PASS = all visible
  MODE "frame"  -> CameraActor Neelam_AlignCam straight down over the whole visible route (fits its bounds), as view
                   target; then wait for tiles (Cesium3DTileset.load_progress == 100) and take "HighResShot".
"""
import unreal
MODE = globals().get("MODE", "list"); LID = globals().get("LID")
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
ALL = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
TAGS = lambda a: [str(t) for t in a.tags]
RIB = [a for a in ALL if {"Neelam_Route", "Neelam_RoadGlow"} & set(TAGS(a))]
PINS = {next(t[3:] for t in TAGS(a) if t.startswith("LM_")): a for a in ALL
        if a.get_class().get_name() == "BP_POI_C" and any(t.startswith("LM_") for t in TAGS(a))}
vis = lambda: sorted(a.get_actor_label() for a in RIB if not a.get_editor_property("hidden"))
SL = unreal.NeelamSurroundingsLibrary

if MODE == "list":
    result = {"landmarks": sorted(PINS), "ribbons": len(RIB)}
elif MODE == "select":
    BUTTON = "Button_Surroundings"
    exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/ui_press.py").read())
    PINS[LID].call_method("Select_POI")
    v = vis(); own = sorted(a.get_actor_label() for a in RIB if "LM_" + LID in TAGS(a))
    wrong = [l for l in v if l not in own]
    main = [a for a in RIB if "LM_" + LID in TAGS(a) and a.get_actor_label().startswith(("Route_", "Road_"))]
    # visible also needs the reveal mask open (Show_Route animates the material's Mask_Radius; 0 = fully masked)
    mask = {a.get_actor_label(): round(a.get_components_by_class(unreal.SplineMeshComponent)[0].get_material(0).get_scalar_parameter_value("Mask_Radius"))
            for a in main if a.get_components_by_class(unreal.SplineMeshComponent)}
    result = {"lid": LID, "visible": v, "own": own, "wrong_visible": wrong, "own_hidden": [l for l in own if l not in v], "mask_radius": mask,
              "PASS": not wrong and bool(main) and all(a.get_actor_label() in v for a in main) and all(r > 0 for r in mask.values())}
elif MODE == "amenity":   # Amenities button, then an amenity pin: no route may stay on from Surroundings
    am = next(a for a in ALL if a.get_actor_label() == (LID or "Amenity_pool"))
    BUTTON = "Button_Surroundings"
    exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/ui_press.py").read())
    BUTTON = "Button_Amenities"
    exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/ui_press.py").read())
    am.call_method("Select_POI")
    v = vis(); result = {"amenity": am.get_actor_label(), "visible": v, "PASS": not v}
elif MODE == "showall":
    BUTTON = "Button_Surroundings"
    exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/ui_press.py").read())
    v = vis(); result = {"visible": len(v), "of": len(RIB), "PASS": len(v) == len(RIB)}
elif MODE == "frame":
    own = [a for a in RIB if "LM_" + LID in TAGS(a) and not a.get_editor_property("hidden")] + [PINS[LID]]
    lo = [1e12, 1e12]; hi = [-1e12, -1e12]
    for a in own:
        o, e = a.get_actor_bounds(False)
        lo = [min(lo[0], o.x - e.x), min(lo[1], o.y - e.y)]; hi = [max(hi[0], o.x + e.x), max(hi[1], o.y + e.y)]
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    span = max(hi[0] - lo[0], (hi[1] - lo[1]) * 16 / 9) * 1.15 + 20000
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.camera_component.set_editor_property("field_of_view", 60.0)
    h = span / 2 / 0.5774   # tan(30)
    cam.set_actor_location_and_rotation(unreal.Vector(cx, cy, h), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    unreal.GameplayStatics.get_player_controller(gw, 0).set_view_target_with_blend(cam, 0.0)
    result = {"lid": LID, "centre": [round(cx), round(cy)], "height_m": round(h / 100)}
elif MODE == "progress":
    result = min(t.load_progress for t in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Cesium3DTileset))
elif MODE == "oblique":   # AlignCam 45 deg down, ~350 m from the point at fraction FRAC of the landmark's main ribbon
    rt = next(a for a in RIB if "LM_" + LID in TAGS(a) and a.get_actor_label().startswith(("Route_", "Road_")))
    sp = rt.get_component_by_class(unreal.SplineComponent); m = sp.get_location_at_distance_along_spline(sp.get_spline_length() * FRAC, unreal.SplineCoordinateSpace.WORLD)
    t = sp.get_direction_at_distance_along_spline(sp.get_spline_length() * FRAC, unreal.SplineCoordinateSpace.WORLD)
    loc = unreal.Vector(m.x - t.y * 24000 - t.x * 6000, m.y + t.x * 24000 - t.y * 6000, m.z + 25000)   # off to the side: road reads along the frame
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.camera_component.set_editor_property("field_of_view", 60.0)
    cam.set_actor_location_and_rotation(loc, unreal.MathLibrary.find_look_at_rotation(loc, m), False, True)
    unreal.GameplayStatics.get_player_controller(gw, 0).set_view_target_with_blend(cam, 0.0)
    result = {"lid": LID, "frac": FRAC, "at": [round(m.x), round(m.y), round(m.z)]}
elif MODE == "shot":
    unreal.SystemLibrary.execute_console_command(gw, "HighResShot 1600x900 filename=route_%s" % LID)
    result = "route_%s" % LID
