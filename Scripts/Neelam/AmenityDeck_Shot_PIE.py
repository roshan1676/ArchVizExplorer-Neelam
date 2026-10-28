"""Amenity deck review shots in PIE (bridge job). Nothing is saved; PIE copies only.
MODE "start": throttle off + begin PIE.
MODE "shot":  globals VIEW (name in VIEWS), NAME (file name). Hides the old SM_Amenity_* blockouts in the PIE copy,
              puts Neelam_AlignCam at the view and HighResShots 1600x900 into Saved/Screenshots/WindowsEditor.
              Returns the map tile load progress (wait for 100 before trusting the shot).
MODE "end":   end PIE + throttle back on.
Views are in deck model metres (x east along the deck, y north, z up from deck FFL); see SourceArt/AmenityDeck."""
import math
import unreal

MODE = globals().get("MODE", "shot")
ROOT, YAW, Z0 = (950.0, 4430.0), 40.0, 2477.5
# name: (eye x, y, z, look-at x, y, z, fov or ortho width m)
VIEWS = {
    "top":       (28, 34, 160, 28, 34, 0, -125),          # negative = orthographic width in metres
    "reference": (24, 95, 55, 30, 33, 0, 50),             # from the street side (north), high, like the client render
    "pool":      (-14, 49, 6, 8, 40, 0.5, 70),
    "courts":    (40, 50, 9, 58, 30, 0, 70),
    "central":   (24, 47, 4, 36, 34, 0, 75),
    "pergola":   (-2, 28, 2.2, 12, 34, 1.8, 80),
    "lineup":    (-2, 19.0, 3.2, -2, 26.5, 0.5, 80),
    "lineup2":   (14, 19.0, 3.2, 14, 26.5, 0.5, 80),
}


def world(x, y, z):
    c, s = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
    lx, ly = x * 100.0, -y * 100.0
    return unreal.Vector(ROOT[0] + lx * c - ly * s, ROOT[1] + lx * s + ly * c, Z0 + z * 100.0)


perf = unreal.get_default_object(unreal.load_class(None, "/Script/UnrealEd.EditorPerformanceSettings"))
if MODE == "start":
    perf.set_editor_property("bThrottleCPUWhenNotForeground", False)
    if not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
    result = "started"
elif MODE == "end":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
    perf.set_editor_property("bThrottleCPUWhenNotForeground", True)
    result = "ended"
elif MODE == "lineup":
    # PIE-only test row of the kit meshes on the party lawn (x from -11 m), nothing saved
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    import os   # asset-registry listing returns nothing during PIE -> take the kit names from SourceArt
    kd = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt", "AmenityDeck", "kit")
    kits = ["/Game/Neelam/AmenityDeck/Kit/%s/%s" % (k, k) for k in sorted(os.listdir(kd)) if k.startswith("KIT_")]
    # Python can't spawn into the PIE world here: borrow the (hidden) old bollard fixtures' PIE copies instead
    donors = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.StaticMeshActor) if a.get_actor_label().startswith("AmenLt_Bollard")]
    x = -11.0; placed = []
    for p, a in zip(kits, donors):
        sm = unreal.load_asset(p)
        if sm is None:
            continue
        b = sm.get_bounding_box(); w = (b.max.x - b.min.x) / 100.0
        x += w / 2 + 0.4
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE); c.set_static_mesh(sm)
        a.set_actor_hidden_in_game(False); a.tags = [unreal.Name('kitlineup')]
        a.set_actor_location_and_rotation(world(x, 25.8, -0.1), unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW), False, True)
        a.set_actor_scale3d(unreal.Vector(1, 1, 1))
        placed.append((sm.get_name(), round(x, 1)))
        x += w / 2
    result = placed
else:
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):   # old blockout deck, its lights + trees
        l = a.get_actor_label()
        if unreal.Name('kitlineup') in a.tags:
            continue
        if (l.startswith("SM_Amenity_") and l != "SM_Amenity_ABDeck_Lawn") or l.startswith(("AmenLt_", "AmenityTree_")) or l in globals().get("HIDE", ("SM_Podium_Deck_CDE_v2",)):
            a.set_actor_hidden_in_game(True)
            for c in a.get_components_by_class(unreal.LightComponent):
                c.set_visibility(False)
    ex, ey, ez, tx, ty, tz, f = VIEWS[globals().get("VIEW", "top")]
    eye, tgt = world(ex, ey, ez), world(tx, ty, tz)
    rot = unreal.MathLibrary.find_look_at_rotation(eye, tgt)
    if f < 0:
        rot = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=YAW - 90.0)
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cc = cam.camera_component
    cc.set_editor_property("constrain_aspect_ratio", False)
    if f < 0:
        cc.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        cc.set_editor_property("ortho_width", -f * 100.0)
    else:
        cc.set_editor_property("projection_mode", unreal.CameraProjectionMode.PERSPECTIVE)
        cc.set_editor_property("field_of_view", float(f))
    cam.set_actor_location_and_rotation(eye, rot, False, True)
    unreal.GameplayStatics.get_player_controller(gw, 0).set_view_target_with_blend(cam, 0.0)
    prog = [round(t.get_editor_property("load_progress")) for t in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Cesium3DTileset)]
    if globals().get("NAME"):
        unreal.SystemLibrary.execute_console_command(gw, "HighResShot 1600x900 filename=%s" % NAME)
    result = prog
