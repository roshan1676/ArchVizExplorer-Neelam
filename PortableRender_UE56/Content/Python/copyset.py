"""Copy furniture groups between levels.
    copyset.grab("bed_upholstered", box=(x0,x1,y0,y1), anchor=(x, y)) in the source level -> Saved/ClaudeBridge/sets/<name>.json
    copyset.drop("bed_upholstered", target=(x, y), yaw=0, tag="3BHK_BedA") in the target level
anchor = point of the set that lands on target (e.g. headboard-wall midpoint); yaw rotates the set about it."""
import unreal, json, os, re
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
DIR = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "ClaudeBridge", "sets")
SKIP = re.compile(r"carpet|rug|^Vert$|^Floor|Tv_wall|window|curtain|Plane_06|Cube_002|^LUX_|^BL_|Fitted|Wardrob", re.I)

def grab(name, box, anchor, max_top=160.0):
    x0, x1, y0, y1 = box; items = []
    for a in ACT.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor) or SKIP.search(a.get_actor_label()): continue
        o, e = a.get_actor_bounds(False)
        if not (x0 <= o.x <= x1 and y0 <= o.y <= y1 and o.z + e.z <= max_top): continue
        c = a.static_mesh_component
        if not c.static_mesh: continue
        t = a.get_actor_transform()
        items.append({"label": a.get_actor_label(), "mesh": c.static_mesh.get_path_name(),
                      "mats": [m.get_path_name() if m else None for m in c.get_materials()],
                      "loc": [t.translation.x - anchor[0], t.translation.y - anchor[1], t.translation.z],
                      "rot": [t.rotation.rotator().roll, t.rotation.rotator().pitch, t.rotation.rotator().yaw],
                      "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z]})
    os.makedirs(DIR, exist_ok=True)
    json.dump(items, open(os.path.join(DIR, name + ".json"), "w"), indent=1)
    return [i["label"] for i in items]

def drop(name, target, yaw=0.0, tag=None):
    import math
    tag = tag or name
    for a in ACT.get_all_level_actors():
        if ("set_" + tag) in [str(t) for t in a.tags]: ACT.destroy_actor(a)
    items = json.load(open(os.path.join(DIR, name + ".json")))
    c_, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); n = 0
    for it in items:
        dx, dy, z = it["loc"]
        x, y = target[0] + dx * c_ - dy * s_, target[1] + dx * s_ + dy * c_
        r = it["rot"]
        a = ACT.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(roll=r[0], pitch=r[1], yaw=r[2] + yaw))
        a.set_actor_scale3d(unreal.Vector(*it["scale"]))
        comp = a.static_mesh_component; comp.set_static_mesh(unreal.load_asset(it["mesh"]))
        for i, m in enumerate(it["mats"]):
            if m: comp.set_material(i, unreal.load_asset(m))
        a.set_actor_label("%s_%s" % (tag, it["label"])); a.tags = ["set_" + tag]; a.set_folder_path("Lux/Sets/" + tag); n += 1
    return n
