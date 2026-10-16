"""Real ground + roof heights around each landmark from the photogrammetry, plus a nadir review shot (PIE, 11 Oct).
Needs CameraActor Neelam_AlignCam in the level. Per landmark: go(LID) -> wait >= 40 s (tiles stream) -> trace(LID) -> shot(LID).
trace: ground = traces on a ring 6 / 14 / 24 m outside the model's footprint (32 directions), roof = 3x3 grid inside
(the cut-out only hides the tiles, their collision stays = the real building). -> env["lmp"][LID]; save -> Data/landmark_ground.json"""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "go"); env = globals()["env"]; LID = globals().get("LID")
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(gw, 0)
def actor(label): return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if a.get_actor_label() == label)
def frame(a):
    """centre, unit axes, half sizes (cm) of the landmark mesh footprint"""
    sm = a.static_mesh_component.static_mesh; bb = sm.get_bounding_box(); s = a.get_actor_scale3d()
    yaw = math.radians(a.get_actor_rotation().yaw); ux, uy = math.cos(yaw), math.sin(yaw)
    c = a.get_actor_transform().transform_location(unreal.Vector((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, 0))
    return c, (ux, uy), (-uy, ux), (bb.max.x - bb.min.x) * s.x / 2, (bb.max.y - bb.min.y) * s.y / 2
if MODE == "prep":
    # show the REAL buildings: hide our landmark models and drop their map cut-outs
    n = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        if a.get_actor_label().startswith(("Landmark_", "Label_", "POI_")) or a.get_class().get_name() in ("BP_POI_C",):
            a.set_actor_hidden_in_game(True); n += 1
    for t in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Cesium3DTileset):
        for c in t.get_components_by_class(unreal.ActorComponent):
            if c.get_class().get_name() == "CesiumPolygonRasterOverlay":
                c.set_editor_property("polygons", [p for p in c.get_editor_property("polygons") if p and not str(p.get_actor_label()).startswith("LandmarkCut_")])
        t.refresh_tileset()
    result = n
elif MODE == "go":
    a = actor("Landmark_" + LID); c, _, _, hx, hy = frame(a)
    cam = actor("Neelam_AlignCam")
    h = max(40000.0, max(hx, hy) * 4.0)
    env["lmp_cam_" + LID] = [c.x, c.y, a.get_actor_location().z + h]
    cam.set_actor_location_and_rotation(unreal.Vector(c.x, c.y, a.get_actor_location().z + h), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cc = cam.camera_component; cc.set_editor_property("field_of_view", 70.0); cc.set_editor_property("constrain_aspect_ratio", False)
    pc.set_view_target_with_blend(cam, 0.0)
    result = [LID, round(h), round(c.x), round(c.y)]
elif MODE == "trace":
    if env.get("lmp_world") != gw.get_path_name():
        env["lmp_ignore"] = [x for x in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(x, unreal.Cesium3DTileset)]
        env["lmp_world"] = gw.get_path_name()
    def z_at(x, y):
        hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x, y, 90000), unreal.Vector(x, y, -60000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                   env["lmp_ignore"], unreal.DrawDebugTrace.NONE, True)
        for h in hs or []:
            t = h.to_tuple()
            if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset): return round(float(t[4].z))
        return None
    a = actor("Landmark_" + LID); c, u, v, hx, hy = frame(a)
    ring = []
    for off in (600, 1400, 2400):
        for k in range(32):
            ang = 2 * math.pi * k / 32; du, dv = math.cos(ang), math.sin(ang)
            s = 1.0 / max(abs(du) / hx, abs(dv) / hy)               # ray to the box edge
            pu, pv = du * (s + off), dv * (s + off)
            z = z_at(c.x + pu * u[0] + pv * v[0], c.y + pu * u[1] + pv * v[1])
            ring.append([off, k, z])
    roof = [z_at(c.x + i * hx * 0.6 * u[0] + j * hy * 0.6 * v[0], c.y + i * hx * 0.6 * u[1] + j * hy * 0.6 * v[1]) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    env.setdefault("lmp", {})[LID] = {"ring": ring, "roof": roof, "c": [c.x, c.y], "half": [hx, hy], "cam": env.get("lmp_cam_" + LID)}
    zs = sorted(z for _, _, z in ring if z is not None); rf = sorted(z for z in roof if z is not None)
    result = {"lid": LID, "n": len(zs), "p10": zs[len(zs) // 10] if zs else None, "p50": zs[len(zs) // 2] if zs else None,
              "roof_med": rf[len(rf) // 2] if rf else None, "base_now": round(a.get_actor_location().z)}
elif MODE == "shot":
    unreal.SystemLibrary.execute_console_command(gw, "HighResShot 1600x900 filename=lm2_%s" % LID)
    result = LID
elif MODE == "save":
    json.dump(env.get("lmp", {}), open(os.path.join(P, "Data", "landmark_ground.json"), "w"), indent=0)
    result = sorted(env.get("lmp", {}))
