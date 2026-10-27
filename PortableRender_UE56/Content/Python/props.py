"""Decor props from BlenderKit (converted by Tools/bk_import.sh -> SourceArt/Props/<Name>).
    import props as PR
    PR.import_prop("Console")                                    # once: assets + materials (glass/emissive/bakes)
    PR.place("Console", "LUX_Console", (380, -1050, 0), yaw=0)    # spawn/move a copy in the open level
Tagged "lux_prop"; placed copies live in the outliner folder Lux/Props."""
import unreal, math
import scene_builder as SB

ACT, EAL = SB.ACT, SB.EAL

def _mesh(name):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=["/Game/Neelam/Props/%s/Assets" % name], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])
    a = reg.get_assets(f)
    return a[0].get_asset() if a else None

def import_prop(name):
    """Interchange-import SourceArt/Props/<name>/scene.gltf as assets, then glass/emissive + baked materials onto the mesh."""
    unit = "Props/" + name
    if _mesh(name) is None:
        before = set(a.get_name() for a in ACT.get_all_level_actors())
        SB.import_meshes(unit)
        for a in ACT.get_all_level_actors():        # import_scene also drops an actor at the origin -> remove it
            if a.get_name() not in before and isinstance(a, unreal.StaticMeshActor): ACT.destroy_actor(a)
    r = SB.fix_materials(unit)
    try: r.update(SB.apply_bakes(unit))
    except FileNotFoundError: pass
    m = _mesh(name)
    # mesh slots carry the final materials; placed copies just use them
    return {"mesh": m.get_path_name() if m else None, **r}

def place(name, label, loc, yaw=0.0, rot=None, scale=1.0):
    """rot: optional unreal.Rotator overriding yaw. Re-running with the same label moves the existing copy."""
    a = next((x for x in ACT.get_all_level_actors() if x.get_actor_label() == label), None)
    if a is None:
        a = ACT.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc))
        a.static_mesh_component.set_static_mesh(_mesh(name))
        a.set_actor_label(label); a.tags = ["lux_prop"]; a.set_folder_path("Lux/Props")
    a.set_actor_location(unreal.Vector(*loc), False, False)
    a.set_actor_rotation(rot or unreal.Rotator(roll=0, pitch=0, yaw=yaw), False)
    sc = scale if isinstance(scale, (tuple, list)) else (scale, scale, scale)
    a.set_actor_scale3d(unreal.Vector(*sc))
    return a

def picture_light(label, loc, length_cm=100.0, aim=unreal.Vector(-0.35, 0, -1), kelvin=3000.0, nits=4000.0):
    """Linear wall-wash light (rect light) grazing down a wall/artwork."""
    a = next((x for x in ACT.get_all_level_actors() if x.get_actor_label() == label), None) or \
        ACT.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*loc))
    a.set_actor_location(unreal.Vector(*loc), False, False)
    a.set_actor_rotation(unreal.MathLibrary.make_rot_from_x(aim), False)
    c = a.light_component
    c.set_editor_property("intensity_units", unreal.LightUnits.NITS); c.set_intensity(nits)
    c.set_editor_property("source_width", length_cm); c.set_editor_property("source_height", 3.0)
    c.set_editor_property("barn_door_angle", 35.0); c.set_editor_property("barn_door_length", 8.0)
    c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", kelvin)
    c.set_editor_property("attenuation_radius", 400.0)
    a.set_actor_label(label); a.tags = ["lux_prop"]; a.set_folder_path("Lux/Props")
    return a
