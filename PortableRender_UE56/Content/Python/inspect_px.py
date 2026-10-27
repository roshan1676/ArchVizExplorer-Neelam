"""Debug helpers: what is under a pixel of a camera view, and how far it sits from walls/ceiling.
    import inspect_px as IP; IP.pick("LUX_Cam_Bed1", 150, 350)   # pixel in a 1920x1080 frame"""
import unreal, math
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def _world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def _trace(a, b, ignore=()):
    h = unreal.SystemLibrary.line_trace_single(_world(), a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
    return h.to_tuple() if h else None

def pick(cam_label, px, py, W=1920, H=1080):
    cam = next(a for a in ACT.get_all_level_actors() if a.get_actor_label() == cam_label)
    cc = cam.get_cine_camera_component()
    fov = 2 * math.atan(cc.get_editor_property("filmback").sensor_width / (2 * cc.get_editor_property("current_focal_length")))
    r = cam.get_actor_rotation(); t = math.tan(fov / 2)
    d = r.get_forward_vector() + r.get_right_vector() * ((px / W * 2 - 1) * t) + r.get_up_vector() * (-(py / H * 2 - 1) * t * H / W)
    o = cam.get_actor_location(); h = _trace(o, o + d * 5000)
    if not h: return None
    a, c, p = h[9], h[10], h[4]
    lo, ext = a.get_actor_bounds(False)
    return {"actor": a.get_actor_label(), "hit": [round(p.x), round(p.y), round(p.z)],
            "bounds": [[round(lo.x - ext.x), round(lo.y - ext.y), round(lo.z - ext.z)], [round(lo.x + ext.x), round(lo.y + ext.y), round(lo.z + ext.z)]],
            "mats": [m.get_name() for m in c.get_materials() if m]}

def gap_up(label):
    """Distance from the actor's top to the next surface above (ceiling)."""
    a = next(x for x in ACT.get_all_level_actors() if x.get_actor_label() == label)
    o, e = a.get_actor_bounds(False); top = o.z + e.z
    h = _trace(unreal.Vector(o.x, o.y, top + 0.5), unreal.Vector(o.x, o.y, top + 300), [a])
    return {"top": round(top, 1), "ceiling": round(h[4].z, 1) if h else None, "gap": round(h[4].z - top, 1) if h else None, "ceiling_actor": h[9].get_actor_label() if h else None}

def ceiling_fixtures(max_gap=40.0):
    """Small objects near the ceiling: report gap between their top and the ceiling surface above (traced from below at their centre)."""
    out = []
    for a in ACT.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor) or a.get_actor_label().startswith(("BL_Sky", "LUX_View")): continue
        o, e = a.get_actor_bounds(False)
        top, bot = o.z + e.z, o.z - e.z
        if not (200 < top < 300 and e.z < 60 and max(e.x, e.y) < 250): continue
        # ceiling = first hit going up from just below the fixture, ignoring the fixture itself
        h = _trace(unreal.Vector(o.x, o.y, bot - 1), unreal.Vector(o.x, o.y, bot + 200), [a])
        if not h: continue
        gap = h[4].z - top
        if 0.5 < gap < max_gap:
            out.append({"actor": a.get_actor_label(), "gap": round(gap, 1), "top": round(top, 1), "ceiling": round(h[4].z, 1), "above": h[9].get_actor_label()})
    return sorted(out, key=lambda r: -r["gap"])

def snap_ceiling_lights(prefixes=("Disc",), max_gap=15.0):
    """Raise ceiling light fittings flush to the ceiling; light actors just under each fitting move with it."""
    lights = [a for a in ACT.get_all_level_actors() if isinstance(a, (unreal.RectLight, unreal.PointLight, unreal.SpotLight))]
    moved = []
    for r in ceiling_fixtures(max_gap):
        if not r["actor"].startswith(prefixes): continue
        a = next(x for x in ACT.get_all_level_actors() if x.get_actor_label() == r["actor"])
        o, e = a.get_actor_bounds(False); dz = r["gap"]
        l = a.get_actor_location(); a.set_actor_location(unreal.Vector(l.x, l.y, l.z + dz), False, False)
        for L in lights:
            p = L.get_actor_location()
            if abs(p.x - o.x) < max(e.x, 25) and abs(p.y - o.y) < max(e.y, 25) and o.z - e.z - 20 < p.z < o.z + e.z + 1:
                L.set_actor_location(unreal.Vector(p.x, p.y, p.z + dz), False, False)
        moved.append((r["actor"], dz))
    return moved

def invisible_material():
    EAL = unreal.EditorAssetLibrary; p = "/Game/Neelam/Shared/M_Invisible"
    if not EAL.does_asset_exist(p):
        MEL = unreal.MaterialEditingLibrary
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Invisible", "/Game/Neelam/Shared", unreal.Material, unreal.MaterialFactoryNew())
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        z = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 0)
        MEL.connect_material_property(z, "", unreal.MaterialProperty.MP_OPACITY_MASK)
        MEL.recompile_material(m); EAL.save_loaded_asset(m)
    return EAL.load_asset(p)
