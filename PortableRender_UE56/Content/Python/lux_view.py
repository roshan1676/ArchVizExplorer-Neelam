"""Real Mulund view outside the windows: client drone photo (ArchVizExplorer-Neelam SourceArt/FloorView/FloorGallery,
prepared into SourceArt/View/view_floor20.png) on a curved arc mesh (Tools/view_arc.py, 120 deg wide).
    import lux_view as LV; LV.setup(); LV.place("LUX_View_Living", center_xy=(x, y), facing_yaw=180)
facing_yaw = world yaw the photo's centre should be seen in (camera yaw of the window view)."""
import unreal, os
import scene_builder as SB

ACT, EAL, AT, MEL = SB.ACT, SB.EAL, SB.AT, SB.MEL
DIR = "/Game/Neelam/Shared/View"
SRC = os.path.join(SB.PROJ, "SourceArt", "View")

def _import(filename, name):
    if not EAL.does_asset_exist(DIR + "/" + name):
        t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, filename); t.destination_path = DIR
        t.destination_name = name; t.automated = True; t.save = True
        AT.import_asset_tasks([t])
    return EAL.load_asset(DIR + "/" + name)

def _arc_mesh():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=[DIR], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])
    a = reg.get_assets(f)
    if not a:
        t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, "view_arc.gltf"); t.destination_path = DIR + "/Arc"
        t.automated = True; t.save = True
        AT.import_asset_tasks([t]); a = reg.get_assets(f)
    return a[0].get_asset()

def setup(photo="view_floor20.png", strength=1.0):
    tex = _import(photo, "T_View_" + os.path.splitext(photo)[0])
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    path = DIR + "/M_ViewBackdrop"
    if not EAL.does_asset_exist(path):
        m = AT.create_asset("M_ViewBackdrop", DIR, unreal.Material, unreal.MaterialFactoryNew())
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("two_sided", True)
        t = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
        t.set_editor_property("parameter_name", "Photo"); t.set_editor_property("texture", tex)
        s = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 250)
        s.set_editor_property("parameter_name", "Strength"); s.set_editor_property("default_value", strength)
        mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, 0)
        MEL.connect_material_expressions(t, "RGB", mul, "A"); MEL.connect_material_expressions(s, "", mul, "B")
        MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.connect_material_property(t, "A", unreal.MaterialProperty.MP_OPACITY)
        MEL.recompile_material(m); EAL.save_loaded_asset(m)
    m = EAL.load_asset(path)
    MEL.set_material_instance_texture_parameter_value if False else None
    return {"material": m.get_path_name(), "texture": tex.get_path_name(), "mesh": _arc_mesh().get_path_name()}

def place(label, center_xy, facing_yaw, radius_m=300.0, eye_z=150.0, strength=1.0):
    """Arc centre faces +Y at yaw 0, so actor yaw = facing_yaw - 90."""
    a = next((x for x in ACT.get_all_level_actors() if x.get_actor_label() == label), None)
    if a is None:
        a = ACT.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(center_xy[0], center_xy[1], eye_z))
        a.static_mesh_component.set_static_mesh(_arc_mesh())
        a.set_actor_label(label); a.tags = ["lux_view"]; a.set_folder_path("Lux/View")
    a.set_actor_location(unreal.Vector(center_xy[0], center_xy[1], eye_z), False, False)
    a.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=facing_yaw - 90.0), False)
    a.set_actor_scale3d(unreal.Vector(radius_m, radius_m, radius_m))   # mesh is 1 m radius = 100 cm after import
    c = a.static_mesh_component
    c.set_material(0, EAL.load_asset(DIR + "/MI_ViewBackdrop") or EAL.load_asset(DIR + "/M_ViewBackdrop"))   # MI: Strength 3
    c.set_editor_property("cast_shadow", False)
    c.set_editor_property("affect_dynamic_indirect_lighting", False)
    return a
