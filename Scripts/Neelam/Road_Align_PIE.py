"""Nadir screenshots of the REAL roads (photogrammetry) to align the OSM carriageways laterally (29 Sep).
PIE only; needs a CameraActor labelled Neelam_AlignCam in the editor level (spawned before PIE, deleted after). prep: hide every non-map actor (roads, ribbons, poles, trees, labels) and remove the road cut polygons so the
imagery under the carriageways is visible; go(CELL): player camera 395 m straight above a 400 x 700 m cell, FOV 90;
shot(CELL): HighResShot 3200x1800 -> Saved/Screenshots/WindowsEditor/align_<CELL>.png + camera json.
Analysis (cloud, numpy): align_roads.py -> Data/road_offsets.json."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "prep"); env = globals()["env"]
CX, CY, H = 40000.0, 70000.0, 39500.0
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(gw, 0)
if MODE == "prep":
    R = json.load(open(os.path.join(P, "Data", "road_build_raw.json")))["roads"]
    cells = sorted({(math.floor(p[0] / CX), math.floor(p[1] / CY)) for r in R.values() for p in r["pts"]})
    env["al_cells"] = cells
    keep = ("Cesium", "Sky", "Light", "Fog", "Atmosphere", "Volume", "PostProcess", "Cloud", "World", "GameMode", "Controller", "HUD", "PlayerState", "GameState", "Camera")
    hid = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        cn = a.get_class().get_name()
        if any(k in cn for k in keep) or a.get_actor_label() == "Neelam_AlignCam": continue
        a.set_actor_hidden_in_game(True); hid += 1
    tiles = [t for t in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Cesium3DTileset)]
    for t in tiles:
        for c in t.get_components_by_class(unreal.ActorComponent):
            if c.get_class().get_name() == "CesiumPolygonRasterOverlay":
                c.set_editor_property("polygons", [])
        t.refresh_tileset()
    unreal.SystemLibrary.execute_console_command(gw, "fov 90")
    result = {"cells": len(cells), "hidden": hid, "tilesets": len(tiles)}
elif MODE == "go":
    # own CameraActor as view target (the template pawn eases its rotation -> never exactly nadir / static)
    cx, cy = env["al_cells"][CELL]
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.set_actor_location_and_rotation(unreal.Vector((cx + .5) * CX, (cy + .5) * CY, H), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cc = cam.camera_component; cc.set_editor_property("field_of_view", 90.0); cc.set_editor_property("constrain_aspect_ratio", False)
    pc.set_view_target_with_blend(cam, 0.0)
    result = CELL
elif MODE == "shot":
    cm = pc.player_camera_manager
    l = cm.get_camera_location(); r = cm.get_camera_rotation()
    cam = {"cell": env["al_cells"][CELL], "loc": [l.x, l.y, l.z], "rot": [r.pitch, r.yaw, r.roll], "fov": cm.get_fov_angle(), "w": 3200, "h": 1800}
    d = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Screenshots", "WindowsEditor")
    json.dump(cam, open(os.path.join(d, "align_%d.json" % CELL), "w"))
    unreal.SystemLibrary.execute_console_command(gw, "HighResShot 3200x1800 filename=align_%d" % CELL)
    result = cam
