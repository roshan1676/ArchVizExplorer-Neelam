"""Rendered depth of the Google tiles for the grey massing (PIE, 30 Sep). The tiles' collision is a coarse parent tile
(traces return a smooth blanket, no buildings), so heights come from RENDERING: SceneCapture2D 'Neelam_DepthCap'
(scene depth, RT_NeelamDepth 1600x1600 R32F, show-only the map tilesets, FOV 90, nadir) next to the view-target camera
'Neelam_AlignCam' 450 m above each 500 m cell; Google tileset SSE 2 so roofs are real geometry.
Modes: prep / go (CELL) / shot (CELL) -> Saved/NeelamBridge/depth/d_<CELL>.bin (+ .json camera)."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
OUTD = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "depth")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CC = 50000.0; H = 45000.0
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
acts = lambda cls: unreal.GameplayStatics.get_all_actors_of_class(gw, cls)
cap = next(a for a in acts(unreal.SceneCapture2D) if a.get_actor_label() == "Neelam_DepthCap")
cam = next(a for a in acts(unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
if MODE == "prep":
    os.makedirs(OUTD, exist_ok=True)
    S = json.load(open(os.path.join(P, "Data", "massing_sel.json")))
    cells = sorted({(math.floor(b["c"][0] / CC), math.floor(b["c"][1] / CC)) for b in S})
    env["dp_cells"] = cells
    tiles = list(acts(unreal.Cesium3DTileset))
    for t in tiles:
        if t.get_actor_label().startswith("Google"): t.set_editor_property("maximum_screen_space_error", 2.0)
    sc = cap.capture_component2d
    sc.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
    sc.set_editor_property("show_only_actors", tiles)
    result = {"cells": len(cells)}
elif MODE == "go":
    cx, cy = env["dp_cells"][CELL]
    loc = unreal.Vector((cx + .5) * CC, (cy + .5) * CC, H); rot = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
    for a in (cam, cap): a.set_actor_location_and_rotation(loc, rot, False, True)
    cam.camera_component.set_editor_property("field_of_view", 90.0)
    unreal.GameplayStatics.get_player_controller(gw, 0).set_view_target_with_blend(cam, 0.0)
    result = CELL
elif MODE == "cap":                 # render now; read back in the NEXT job (same-frame readback returned stale data)
    cap.capture_component2d.capture_scene(); result = CELL
elif MODE == "shot":
    sc = cap.capture_component2d
    rt = sc.get_editor_property("texture_target")
    f = os.path.join(OUTD, "d_%d.bin" % CELL)
    err = unreal.NeelamToolsLibrary.export_render_target_raw_r(rt, f)
    l = cap.get_actor_location(); r = cap.get_actor_rotation()
    json.dump({"cell": env["dp_cells"][CELL], "loc": [l.x, l.y, l.z], "rot": [r.pitch, r.yaw, r.roll], "fov": 90.0, "w": rt.size_x, "h": rt.size_y},
              open(os.path.join(OUTD, "d_%d.json" % CELL), "w"))
    result = [CELL, err or "ok"]
