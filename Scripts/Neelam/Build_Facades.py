"""Neelam - realistic facades on the context buildings around the site (30 Sep, client). Re-run safe.
Pipeline:  select_textured.py (ids -> Data/massing_textured.json)
        -> Blender/build_facades.py (cloud bpy) -> Saved/NeelamBridge/facade_fbx/facade_<i>_<j>.fbx
        -> this script: materials + import + actors (folder Neelam/ContextFacades, tag Neelam_Facades)
        -> Import_Massing.py rebuilds the grey chunks WITHOUT those ids (Blender/build_massing.py 3rd arg).
M_Neelam_Facade (walls, procedural): per-building paint colour (8 Mumbai-typical tints), 5 facade styles
(punched windows, balconies with railings, ribbon windows, commercial glass, old chawl), slab bands, AC units,
stilt/shop ground floor, parapet top floor, curtains, window recess shadow, monsoon grime + streaks, stucco detail,
night: random lit windows (Emissive_MPC.Buildings, like the towers' glass). M_Neelam_Roof: weathered concrete.
Mesh data used by the shader: UV0 = bays x floors, UV1.x = floor count, vertex colour = tint / style / seed."""
import os, glob
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "facade_fbx")
DIR = "/Game/Neelam/Massing/Facades"
PH = "/Game/Neelam/Buildings/WindTunnel/Textures/PolyHaven/"
MPC = "/Game/ArchVizExplorer/Materials/MPC/Emissive_MPC"
FOLDER = "Neelam/ContextFacades"

FACADE = r"""
UV = float2(UV.x, 1.0 - UV.y);          // FBX -> UE flips V
float2 cell = floor(UV); float2 f = frac(UV);
float fl = max(INF.x, 1.0);
float sv = saturate(VC.y);   // Mumbai mix: punched 35 %, balconies 25 %, ribbon 15 %, commercial glass 8 %, old chawl 17 %
float style = sv < 0.35 ? 0.0 : (sv < 0.60 ? 1.0 : (sv < 0.75 ? 2.0 : (sv < 0.83 ? 3.0 : 4.0)));
if (style > 3.5 && fl > 9.0) style = 0.0;      // tall blocks are not chawls
float seed = VC.z * 91.7;
float3 pal[8] = { float3(0.80,0.75,0.64), float3(0.84,0.83,0.80), float3(0.62,0.62,0.61), float3(0.74,0.64,0.52),
                  float3(0.82,0.73,0.50), float3(0.60,0.66,0.70), float3(0.77,0.58,0.50), float3(0.70,0.72,0.64) };
float3 wall = pal[(int)floor(saturate(VC.x) * 7.999)];
float old = style > 3.5 ? 1.0 : 0.0;
wall *= 1.0 - 0.18 * old;
float4 W = style < 0.5 ? float4(0.22,0.78,0.30,0.80) : (style < 1.5 ? float4(0.10,0.90,0.24,0.84) :
          (style < 2.5 ? float4(-0.02,1.02,0.36,0.78) : (style < 3.5 ? float4(0.03,0.97,0.10,0.94) : float4(0.32,0.68,0.36,0.74))));
float2 aa = max(fwidth(UV), 1e-4);
float wm = smoothstep(W.x - aa.x, W.x + aa.x, f.x) * (1.0 - smoothstep(W.y - aa.x, W.y + aa.x, f.x))
         * smoothstep(W.z - aa.y, W.z + aa.y, f.y) * (1.0 - smoothstep(W.w - aa.y, W.w + aa.y, f.y));
float below = step(cell.y, -0.5);
float isG = step(-0.5, cell.y) * step(cell.y, 0.5);
float topR = step(floor(fl) - 0.5, cell.y);
float rowsOK = (1.0 - below) * (1.0 - isG) * (1.0 - topR);
wm *= rowsOK;
float h1 = frac(sin(dot(cell + seed, float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(sin(dot(cell + seed * 1.37, float2(39.346, 11.135))) * 24634.634);
// ground floor: stilt parking / shop openings between columns
float gm = isG * smoothstep(0.10, 0.13, f.x) * (1.0 - smoothstep(0.87, 0.90, f.x)) * (1.0 - smoothstep(0.80, 0.83, f.y));
// slab band + parapet cap
float band = (1.0 - smoothstep(0.05, 0.075, f.y)) * (1.0 - below);
float cap = step(fl - 0.12, UV.y);
// AC units beside punched windows
float acOn = step(0.70, h2) * ((style < 0.5 || old > 0.5) ? 1.0 : 0.0) * rowsOK;
float ac = acOn * step(0.81, f.x) * step(f.x, 0.95) * step(0.30, f.y) * step(f.y, 0.46);
// glass: dark residential glass, some curtains; commercial blue-green
float comm = (style > 2.5 && style < 3.5) ? 1.0 : 0.0;
float3 glass = lerp(float3(0.018, 0.022, 0.026), float3(0.04, 0.065, 0.085), comm);
float cur = step(0.55, h1) * (1.0 - comm);
glass = lerp(glass, float3(0.16, 0.13, 0.10) * (0.6 + 0.8 * h2), cur * 0.5);
float ex = min(f.x - W.x, W.y - f.x), ey = min(f.y - W.z, W.w - f.y);
float rec = saturate(1.0 - min(ex * 14.0, ey * 9.0)) * (1.0 - comm);
// weathering: big monsoon blotches, dirt near the ground, streaks under windows
float wc = 0.5 * (W.x + W.y), ww = 0.5 * (W.y - W.x);
float streak = (1.0 - smoothstep(ww * 0.55, ww * 0.95, abs(f.x - wc))) * saturate((W.z - f.y) / 0.28) * step(f.y, W.z) * rowsOK;
float dirt = saturate(GRM * 1.4 - 0.40);
float3 wallC = wall * DET * 0.70;
wallC *= 1.0 - (0.42 + 0.25 * old) * dirt - 0.22 * exp(-max(UV.y, 0.0) * 0.9) - streak * (0.20 + 0.15 * old);
wallC = lerp(wallC, wallC * 0.80, max(band, cap * 0.6));
float3 col = wallC;
col = lerp(col, float3(0.60, 0.61, 0.60), ac);
col = lerp(col, float3(0.045, 0.045, 0.045), gm);
col = lerp(col, glass * (1.0 - rec * 0.55), wm);
float rail = (style > 0.5 && style < 1.5) ? wm * (1.0 - smoothstep(W.z + 0.19, W.z + 0.215, f.y)) : 0.0;
col = lerp(col, wall * 0.92, rail * 0.9);
float g = wm * (1.0 - rail);
Rough = lerp(0.88, lerp(0.06, 0.04, comm), g);
Spec = lerp(0.35, 0.7, g);
Mask = g;
float lit = step(0.56, frac(h1 * 7.13 + h2)) * g;
float3 warm = lerp(float3(1.0, 0.72, 0.42), float3(0.95, 0.93, 0.86), step(0.72, h2));
Emis = (warm * lit * (0.5 + 0.9 * h2) + float3(1.0, 0.80, 0.55) * gm * step(0.5, h2) * 0.7) * NIGHT;
return col;
"""

ROOF = r"""
float lum = dot(DET, float3(0.333, 0.333, 0.333));
float3 base = lerp(float3(0.13, 0.13, 0.13), float3(0.20, 0.19, 0.175), VC.x) * (0.80 + 0.35 * lum);
float coat = smoothstep(0.58, 0.66, GRM) * step(0.5, VC.z);          // white waterproofing patches on some roofs
base = lerp(base, float3(0.30, 0.30, 0.29), coat * 0.8);
base *= 1.0 - 0.30 * (1.0 - smoothstep(0.22, 0.40, GRM));           // monsoon dirt
return base;
"""


def _mat(name):
    path = DIR + "/" + name
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path); MEL.delete_all_material_expressions(m); return m
    return AT.create_asset(name, DIR, unreal.Material, unreal.MaterialFactoryNew())


def _tex(m, path, uvscale, x, y, sampler=None, uvindex=0):
    tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, x - 250, y)
    tc.set_editor_property("coordinate_index", uvindex); tc.set_editor_property("u_tiling", uvscale); tc.set_editor_property("v_tiling", uvscale)
    t = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSample, x, y)
    t.set_editor_property("texture", unreal.load_asset(path))
    if sampler: t.set_editor_property("sampler_type", sampler)
    MEL.connect_material_expressions(tc, "", t, "UVs")
    return t


def _custom(m, code, inputs, outs, x, y, desc):
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property("code", code); c.set_editor_property("description", desc)
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for nm, _ in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    c.set_editor_property("inputs", ins)
    ao = []
    for nm, typ in outs:
        o = unreal.CustomOutput(); o.set_editor_property("output_name", nm); o.set_editor_property("output_type", typ); ao.append(o)
    c.set_editor_property("additional_outputs", ao)
    for nm, (node, pin) in inputs:
        MEL.connect_material_expressions(node, pin, c, nm)
    return c


def step_materials():
    F1 = unreal.CustomMaterialOutputType.CMOT_FLOAT1; F3 = unreal.CustomMaterialOutputType.CMOT_FLOAT3
    # ---- walls
    m = _mat("M_Neelam_Facade")
    uv0 = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1200, -300)
    uv1 = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1200, -150); uv1.set_editor_property("coordinate_index", 1)
    vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -1200, 0)
    det = _tex(m, PH + "white_stucco/T_WhiteStucco_D", 0.8, -1200, 150)
    grm = _tex(m, PH + "painted_concrete/T_PaintedConcrete_D", 0.11, -1200, 400)
    mpc = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -1200, 650)
    mpc.set_editor_property("collection", unreal.load_asset(MPC)); mpc.set_editor_property("parameter_name", "Buildings")
    c = _custom(m, FACADE, [("UV", (uv0, "")), ("INF", (uv1, "")), ("VC", (vc, "")), ("DET", (det, "RGB")), ("GRM", (grm, "R")), ("NIGHT", (mpc, ""))],
                [("Rough", F1), ("Spec", F1), ("Emis", F3), ("Mask", F1)], -700, 0, "NeelamFacade")
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(c, "Rough", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(c, "Spec", unreal.MaterialProperty.MP_SPECULAR)
    ints = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 350)
    ints.set_editor_property("parameter_name", "Window_Intensity"); ints.set_editor_property("default_value", 12.0)
    em = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -400, 300)
    MEL.connect_material_expressions(c, "Emis", em, "A"); MEL.connect_material_expressions(ints, "", em, "B")
    MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    nrm = _tex(m, PH + "white_stucco/T_WhiteStucco_N", 0.8, -700, 550, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    flat = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, 750); flat.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 0))
    lp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, 600)
    MEL.connect_material_expressions(nrm, "RGB", lp, "A"); MEL.connect_material_expressions(flat, "", lp, "B"); MEL.connect_material_expressions(c, "Mask", lp, "Alpha")
    MEL.connect_material_property(lp, "", unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(m); EAL.save_asset(m.get_path_name())
    # ---- roofs
    r = _mat("M_Neelam_Roof")
    vc = MEL.create_material_expression(r, unreal.MaterialExpressionVertexColor, -1200, 0)
    det = _tex(r, PH + "white_stucco/T_WhiteStucco_D", 2.0, -1200, 150)
    grm = _tex(r, PH + "painted_concrete/T_PaintedConcrete_D", 0.3, -1200, 400)
    c = _custom(r, ROOF, [("VC", (vc, "")), ("DET", (det, "RGB")), ("GRM", (grm, "R"))], [], -700, 0, "NeelamRoof")
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rr = MEL.create_material_expression(r, unreal.MaterialExpressionConstant, -700, 250); rr.set_editor_property("r", 0.9)
    MEL.connect_material_property(rr, "", unreal.MaterialProperty.MP_ROUGHNESS)
    rn = _tex(r, PH + "white_stucco/T_WhiteStucco_N", 2.0, -700, 450, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    MEL.connect_material_property(rn, "RGB", unreal.MaterialProperty.MP_NORMAL)
    MEL.recompile_material(r); EAL.save_asset(r.get_path_name())
    return [m.get_path_name(), r.get_path_name()]


def step_import():
    mf = unreal.load_asset(DIR + "/M_Neelam_Facade"); mr = unreal.load_asset(DIR + "/M_Neelam_Roof")
    for a in [a for a in EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]:
        EAS.destroy_actor(a)
    tasks = []
    for f in sorted(glob.glob(os.path.join(SRC, "facade_*.fbx"))):
        t = unreal.AssetImportTask(); t.filename = f; t.destination_path = DIR + "/Meshes"; t.destination_name = os.path.splitext(os.path.basename(f))[0]
        t.automated = True; t.replace_existing = True; t.save = True
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
        sd = ui.static_mesh_import_data
        sd.combine_meshes = True; sd.auto_generate_collision = False; sd.generate_lightmap_u_vs = False
        sd.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE
        t.options = ui; tasks.append(t)
    AT.import_asset_tasks(tasks)
    n = tris = 0
    for t in tasks:
        sm = unreal.load_asset(DIR + "/Meshes/" + t.destination_name)
        if sm is None: continue
        for i, s in enumerate(sm.static_materials):
            sm.set_material(i, mr if "Roof" in str(s.material_slot_name) else mf)
        EAL.save_asset(sm.get_path_name()); tris += sm.get_num_triangles(0)
        a = EAS.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_label("Facade_" + t.destination_name[7:]); a.set_folder_path(FOLDER); a.tags = [unreal.Name("Neelam_Facades")]
        c = a.static_mesh_component; c.set_collision_profile_name("NoCollision"); c.set_editor_property("cast_shadow", True); n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {"chunks": n, "triangles": tris}


def run():
    return {"materials": step_materials(), "import": step_import()}
