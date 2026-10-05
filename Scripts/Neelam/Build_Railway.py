"""Railway corridor in the level (4 Oct, client 'railway is a flat photo'). Pipeline:
make_railway.py fetch() (UE, Overpass) -> Data/railway.json; Rail_Heights_PIE.py (PIE, prep/go/trace/save) -> Data/rail_heights.json;
Blender/build_railway.py (cloud bpy) -> Saved/NeelamBridge/rail_fbx/rail_<i>_<j>.fbx; this script: materials + import + actors
(folder Neelam/Railway, tag Neelam_Railway, no collision). Grey platform-shed blocks removed via Data/massing_exclude.json."""
import glob, os
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "rail_fbx")
DIR = "/Game/Neelam/Railway"; FOLDER = "Neelam/Railway"
HLSL = r"""
float n  = frac(sin(dot(floor(WP.xy / 4.0),  float2(12.9898, 78.233))) * 43758.5453);
float n2 = frac(sin(dot(floor(WP.xy / 37.0), float2(39.3468, 11.135))) * 24634.6345);
float3 c;
if (K < 0.5) {            // ballast + concrete sleepers (u = m along, v = m across)
  float sl = step(frac(UV.x / 0.6), 0.42) * step(abs(UV.y), 1.375);
  float3 g = lerp(float3(0.17, 0.16, 0.145), float3(0.31, 0.29, 0.26), n) * lerp(0.82, 1.1, n2);
  g = lerp(g, float3(0.22, 0.13, 0.07), step(abs(UV.y), 0.95) * 0.45 * n);
  c = lerp(g, float3(0.43, 0.42, 0.40) * lerp(0.88, 1.05, n), sl);
} else if (K < 1.5) c = float3(0.30, 0.27, 0.25);
else if (K < 2.5) c = float3(0.28, 0.30, 0.31);
else if (K < 3.5) c = float3(0.10, 0.07, 0.05);
else if (K < 4.5) {       // platform pavers 1 m
  float2 t = frac(UV * 2.0); float l = saturate(step(t.x, 0.03) + step(t.y, 0.03));
  c = float3(0.42, 0.40, 0.37) * lerp(0.86, 1.06, n) * lerp(0.9, 1.05, n2) * (1.0 - 0.3 * l);
} else if (K < 5.5) {     // coping: white edge line, yellow tactile strip
  c = UV.y < 0.33 ? float3(0.85, 0.85, 0.82) : float3(0.78, 0.58, 0.05) * lerp(0.85, 1.0, n);
} else {                  // corrugated roof sheets (u = m across)
  float r = frac(UV.x / 0.2); c = float3(0.30, 0.32, 0.34) * (0.82 + 0.18 * sin(r * 6.2832)) * lerp(0.9, 1.03, n2);
}
return c;"""
KINDS = {"Ballast": (0, 0.0, 0.95), "Rail": (1, 1.0, 0.35), "Steel": (2, 0.7, 0.5), "Wire": (3, 1.0, 0.4),
         "Concrete": (4, 0.0, 0.85), "Edge": (5, 0.0, 0.7), "Roof": (6, 0.3, 0.6)}

def step_materials():
    path = DIR + "/Materials/M_Neelam_Rail"
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset("M_Neelam_Rail", DIR + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, 120)
    k = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 240); k.set_editor_property("parameter_name", "Kind")
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -500, 0)
    c.set_editor_property("code", HLSL); c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for nm in ("UV", "WP", "K"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    c.set_editor_property("inputs", ins)
    MEL.connect_material_expressions(uv, "", c, "UV"); MEL.connect_material_expressions(wp, "", c, "WP"); MEL.connect_material_expressions(k, "", c, "K")
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for i, (nm, mp) in enumerate((("Metallic", unreal.MaterialProperty.MP_METALLIC), ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS))):
        p = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 250 + 120 * i); p.set_editor_property("parameter_name", nm)
        MEL.connect_material_property(p, "", mp)
    m.set_editor_property("two_sided", True)
    MEL.recompile_material(m); EAL.save_asset(path)
    for nm, (kind, met, rough) in KINDS.items():
        ip = DIR + "/Materials/MI_Rail_" + nm
        mi = unreal.load_asset(ip) if EAL.does_asset_exist(ip) else AT.create_asset("MI_Rail_" + nm, DIR + "/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, m)
        MEL.set_material_instance_scalar_parameter_value(mi, "Kind", float(kind))
        MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", met)
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
        EAL.save_asset(ip)
    return "ok"

def step_import():
    for a in EAS.get_all_level_actors():
        if "Neelam_Railway" in [str(t) for t in a.tags]: EAS.destroy_actor(a)
    tasks = []
    for f in sorted(glob.glob(os.path.join(SRC, "rail_*.fbx"))):
        t = unreal.AssetImportTask(); t.filename = f; t.destination_path = DIR + "/Meshes"; t.destination_name = os.path.splitext(os.path.basename(f))[0]
        t.automated = True; t.replace_existing = True; t.save = True
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
        sd = ui.static_mesh_import_data; sd.combine_meshes = True; sd.auto_generate_collision = False; sd.generate_lightmap_u_vs = False
        t.options = ui; tasks.append(t)
    AT.import_asset_tasks(tasks); n = tris = 0
    for t in tasks:
        sm = unreal.load_asset(DIR + "/Meshes/" + t.destination_name)
        if sm is None: continue
        for i, s in enumerate(sm.static_materials):
            nm = str(s.material_slot_name).split("_")[0]
            if nm in KINDS: sm.set_material(i, unreal.load_asset(DIR + "/Materials/MI_Rail_" + nm))
        EAL.save_asset(sm.get_path_name()); tris += sm.get_num_triangles(0)
        a = EAS.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_label("Railway_" + t.destination_name[5:]); a.set_folder_path(FOLDER); a.tags = [unreal.Name("Neelam_Railway")]
        c = a.static_mesh_component; c.set_collision_profile_name("NoCollision"); c.set_editor_property("cast_shadow", True); n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {"chunks": n, "triangles": tris}

def run():
    return {"materials": step_materials(), "import": step_import()}
