"""Dress amenity levels with props the same artist already modelled in OTHER amenity files (matching style/scale).
    import dress as D
    D.capture("Amenity_Senior", "Hedge_Flowering", "FlowerBush")     # with any level open: loads source, saves the prop's parts
    D.place("Amenity_JoggingTrack", "FlowerBush", 2.0, 2.5, yaw=90) # open target level: u, v = top-down grid cells (topdown_sheet.py)
    D.clear()                                                       # removes everything this module placed in the open level
Parts = every StaticMeshActor whose label matches the regex within `radius` cm of the first match, stored relative to it,
so multi-part meshes (trunk + leaves + flowers, pot + plant) come across together. Placed copies: tag "dress", folder Dress."""
import unreal, json, os, re, math
import scene_builder as SB

ACT = SB.ACT
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
SAVED = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
LIB = os.path.join(SAVED, "Dress"); os.makedirs(LIB, exist_ok=True)
TAG = "dress"

def _level(name): return "/Game/Neelam/%s/L_%s" % (name, name)

def capture(src, label_regex, prop, radius=400, index=0):
    """index = which match to use as the prop's anchor (0 = first)."""
    LES.load_level(_level(src))
    rx = re.compile(label_regex, re.I)
    hits = [a for a in ACT.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and rx.search(a.get_actor_label())]
    if not hits: return {"error": "no actor matches %s in %s" % (label_regex, src)}
    c = hits[min(index, len(hits) - 1)].get_actor_location()
    parts = []
    for a in hits:
        l = a.get_actor_location()
        if math.hypot(l.x - c.x, l.y - c.y) > radius: continue
        m = a.static_mesh_component.static_mesh
        r, s = a.get_actor_rotation(), a.get_actor_scale3d()
        mats = [x.get_path_name() if x else "" for x in a.static_mesh_component.get_materials()]
        parts.append({"mesh": m.get_path_name(), "off": [l.x - c.x, l.y - c.y, l.z - c.z], "rot": [r.roll, r.pitch, r.yaw],
                      "scale": [s.x, s.y, s.z], "mats": mats})
    zmin = min(p["off"][2] for p in parts)   # ponytail: lowest pivot = ground contact; fine for imported glTF (pivots at origin/base)
    for p in parts: p["off"][2] -= zmin
    json.dump(parts, open(os.path.join(LIB, prop + ".json"), "w"))
    return {"prop": prop, "parts": len(parts)}

def _floor(x, y, zlo, h0=250):
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    h = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, zlo + h0), unreal.Vector(x, y, zlo - 500),
                                               unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    return h.to_tuple()[4].z if h else zlo

def place(level, prop, u, v, yaw=0.0, scale=1.0, h0=250):
    """Place prop in the OPEN level at top-down grid cell coords (u, v in 0..10), standing on the floor below."""
    j = json.load(open(os.path.join(SAVED, "Pano", "_topdown", level.replace("Amenity_", "") + ".json")))
    x, y = j["cx"] + (u / 10 - 0.5) * j["w"], j["cy"] + (v / 10 - 0.5) * j["w"]
    z = _floor(x, y, j["zlo"], h0)
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    n = 0
    for p in json.load(open(os.path.join(LIB, prop + ".json"))):
        ox, oy, oz = (q * scale for q in p["off"])
        loc = unreal.Vector(x + ox * cy - oy * sy, y + ox * sy + oy * cy, z + oz)
        a = ACT.spawn_actor_from_object(unreal.load_asset(p["mesh"]), loc, unreal.Rotator(roll=p["rot"][0], pitch=p["rot"][1], yaw=p["rot"][2] + yaw))
        a.set_actor_scale3d(unreal.Vector(*(s * scale for s in p["scale"])))
        for i, mp in enumerate(p["mats"]):
            if mp: a.static_mesh_component.set_material(i, unreal.load_asset(mp))
        a.tags = [TAG]; a.set_folder_path("Dress"); a.set_actor_label("Dress_%s" % prop)
        n += 1
    return n

def clear():
    n = 0
    for a in ACT.get_all_level_actors():
        if TAG in [str(t) for t in a.tags]: ACT.destroy_actor(a); n += 1
    return n
