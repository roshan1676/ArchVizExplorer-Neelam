"""Neelam - premium hologram highlight materials (re-run safe).
  M_Neelam_HoloFX  (+ MI_Neelam_HoloFX)  - BP_POI highlight boxes (amenities / surroundings). Same parameter names the
                    template drives: Color, Blink (0 idle / 1 selected), Opacity_Total.
  M_Neelam_FloorBox - Floor View floor boxes, state from per-instance custom data 0: -1 hidden, 0 idle, 1 hover, 2 selected.
Look: screen-space crisp edge lines (fwidth), fresnel rim, bottom-heavy fill, world-space grid, rising scan lines,
selected (POI + floor box): pulsing edges, grid, scan lines and a light running around the box."""
import unreal
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
DIR = "/Game/Neelam/Materials/FX"

COMMON = r"""
float3 n = L / 50.0;
float3 d = 1.0 - abs(n);
float3 fw = max(fwidth(d), 1e-4);
float3 l = 1.0 - saturate(d / (fw * LW));
float e = max(max(min(l.x, l.y), min(l.y, l.z)), min(l.x, l.z));
float3 nn = normalize(N);
float fres = pow(1.0 - saturate(abs(dot(normalize(CV), nn))), 3.0);
float3 gd = abs(frac(W / GS + 0.5) - 0.5) * GS;
float3 gl = (1.0 - saturate(gd / (max(fwidth(W), 1e-3) * 1.2))) * (1.0 - abs(nn));
float grid = max(max(gl.x, gl.y), gl.z);
float scan = pow(frac(W.z / 45.0 - T * 0.9), 14.0) * (1.0 - abs(nn.z));
float pulse = 0.5 + 0.5 * sin(T * 4.0);
float h = saturate(n.z * 0.5 + 0.5);
"""

POI_EM = COMMON + r"""
float ang = atan2(n.y, n.x) / 6.2831853 + 0.5;
float run = exp(-pow((frac(ang - T * 0.25) - 0.5) / 0.035, 2.0)) * (1.0 - abs(nn.z));
float s = saturate(B);
float idle = e * 1.1 + fres * 0.20 + (0.015 + 0.05 * (1.0 - h)) + scan * 0.10;
float sel  = e * (3.0 + 2.0 * pulse) + fres * 0.6 + 0.05 + grid * (0.9 + 0.5 * pulse) + scan * 0.5 + run * 2.5;   // Floor View selected look (big boxes: less fill, more grid)
float3 col = lerp(C, float3(1, 1, 1), saturate((e * 0.5 + run * 0.4) * s));
return col * lerp(idle, sel, s);
"""
POI_OP = COMMON + r"""
float ang = atan2(n.y, n.x) / 6.2831853 + 0.5;
float run = exp(-pow((frac(ang - T * 0.25) - 0.5) / 0.035, 2.0)) * (1.0 - abs(nn.z));
float s = saturate(B);
float idle = e * 0.85 + fres * 0.10 + (0.015 + 0.04 * (1.0 - h)) + scan * 0.05;
float sel  = e + fres * 0.25 + 0.06 + grid * 0.55 + scan * 0.25 + run * 0.6;
return saturate(lerp(idle, sel, s)) * saturate(O);
"""

FLOOR_EM = COMMON + r"""
float hv = saturate(S);            // 1 on hover and selected
float sl = saturate(S - 1.0);      // 1 selected
float ang = atan2(n.y, n.x) / 6.2831853 + 0.5;
float run = exp(-pow((frac(ang - T * 0.25) - 0.5) / 0.035, 2.0)) * (1.0 - abs(nn.z));
float3 idleC = float3(0.95, 0.90, 0.80), hovC = float3(1.0, 0.93, 0.75), selC = float3(1.0, 0.66, 0.22);
float3 c = lerp(lerp(idleC, hovC, hv), selC, sl);
float idle = e * 0.35;
float hov  = e * 1.8 + fres * 0.35 + 0.10 + scan * 0.25;
float sel  = e * (3.0 + 2.0 * pulse) + fres * 0.8 + 0.22 + grid * 0.5 + scan * 0.5 + run * 2.5;
float I = lerp(lerp(idle, hov, hv), sel, sl);
c = lerp(c, float3(1, 1, 1), saturate(e * 0.5 * sl + run * 0.4));
return c * I;
"""
FLOOR_OP = COMMON + r"""
float hv = saturate(S), sl = saturate(S - 1.0);
float ang = atan2(n.y, n.x) / 6.2831853 + 0.5;
float run = exp(-pow((frac(ang - T * 0.25) - 0.5) / 0.035, 2.0)) * (1.0 - abs(nn.z));
float idle = e * 0.22;
float hov  = e * 0.85 + fres * 0.12 + 0.10 + scan * 0.12;
float sel  = e + fres * 0.30 + 0.20 + grid * 0.30 + scan * 0.25 + run * 0.6;
float mask = saturate((S + 0.5) * 10.0);
return saturate(lerp(lerp(idle, hov, hv), sel, sl)) * mask;
"""


def _material(path):
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
        return m
    pkg, name = path.rsplit("/", 1)
    return AT.create_asset(name, pkg, unreal.Material, unreal.MaterialFactoryNew())


def _build(path, em_code, op_code, inputs, extra, instanced=False, after_dof=False):
    m = _material(path)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    if instanced:
        m.set_editor_property("used_with_instanced_static_meshes", True)
    if after_dof:
        m.set_editor_property("translucency_pass", unreal.MaterialTranslucencyPass.MTP_AFTER_DOF)
    src = {
        "L": MEL.create_material_expression(m, unreal.MaterialExpressionLocalPosition, -900, -300),
        "W": MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, -150),
        "T": MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 0),
        "CV": MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -900, 150),
        "N": MEL.create_material_expression(m, unreal.MaterialExpressionVertexNormalWS, -900, 300),
    }
    src.update(extra(m))
    consts = "static const float LW = 1.6; static const float GS = 250.0;\n"

    def custom(code, out_type, y, desc):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -400, y)
        c.set_editor_property("code", consts + code)
        c.set_editor_property("output_type", out_type)
        c.set_editor_property("description", desc)
        ins = []
        for nm in inputs:
            ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
        c.set_editor_property("inputs", ins)
        for nm in inputs:
            MEL.connect_material_expressions(src[nm], "", c, nm)
        return c
    em = custom(em_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, 0, "HoloEmissive")
    op = custom(op_code, unreal.CustomMaterialOutputType.CMOT_FLOAT1, 300, "HoloOpacity")
    gain = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, -250)
    gain.set_editor_property("parameter_name", "Brightness"); gain.set_editor_property("default_value", 180.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -120, 0)
    MEL.connect_material_expressions(em, "", mul, "A"); MEL.connect_material_expressions(gain, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_asset(path)
    return m


def step_poi_material():
    def extra(m):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -900, 450)
        c.set_editor_property("parameter_name", "Color"); c.set_editor_property("default_value", unreal.LinearColor(0.2, 0.8, 1.0, 1))
        b = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 600)
        b.set_editor_property("parameter_name", "Blink"); b.set_editor_property("default_value", 0.0)
        o = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 750)
        o.set_editor_property("parameter_name", "Opacity_Total"); o.set_editor_property("default_value", 1.0)
        return {"C": c, "B": b, "O": o}
    m = _build(DIR + "/M_Neelam_HoloFX", POI_EM, POI_OP, ["L", "W", "T", "CV", "N", "C", "B", "O"], extra)
    mi_path = DIR + "/MI_Neelam_HoloFX"
    mi = unreal.load_asset(mi_path) if EAL.does_asset_exist(mi_path) else AT.create_asset("MI_Neelam_HoloFX", DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, m)
    EAL.save_asset(mi_path)
    return mi_path


def step_floor_material():
    def extra(m):
        cd = MEL.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData, -900, 450)
        cd.set_editor_property("data_index", 0)
        return {"S": cd}
    _build("/Game/Neelam/FloorView/Materials/M_Neelam_FloorBox", FLOOR_EM, FLOOR_OP, ["L", "W", "T", "CV", "N", "S"], extra, instanced=True, after_dof=True)
    return "M_Neelam_FloorBox"


def step_apply_pois(only_amenities=False):
    """put MI_Neelam_HoloFX on every placed BP_POI highlight box (the BP builds its dynamic material from slot 0)"""
    mi = unreal.load_asset(DIR + "/MI_Neelam_HoloFX")
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_class().get_name() != "BP_POI_C":
            continue
        if only_amenities and not a.actor_has_tag("Amenities"):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name() == "POI_Geometry":
                c.set_material(0, mi); n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return n


def run():
    return [step_poi_material(), step_floor_material(), step_apply_pois()]
