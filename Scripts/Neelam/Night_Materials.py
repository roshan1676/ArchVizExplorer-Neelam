"""Night lighting, all driven by the template's day/night Emissive_MPC (BP_Time_Widget writes it):
  Effects   = 0 by day -> 1 at night   (traffic streams, street lamps)
  Buildings = 0 by day -> 1 late night (window lights)
1. M_Road_Lighting (traffic head/tail-light streams): emissive x Effects -> streams only at dusk/night.
2. MF_Neelam_NightLight (light-function material = Effects) on BP_Lamp's spot + point light, lights made Movable
   (they were Static = needed a lighting build that this Cesium level never has -> they never lit).
3. M_Neelam_Glass: static switch 'Window_Lights' -> per-window random warm glow (world-space 3.6 m x 3.15 m cells),
   x Buildings; switched on for MI_Glass_Residential + MI_Glass_Retail only (not railings).
Idempotent: nodes are tagged with desc 'NEELAM_NIGHT' and skipped when present."""
import unreal
mel = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
MPC = unreal.load_asset("/Game/ArchVizExplorer/Materials/MPC/Emissive_MPC")
TAG = "NEELAM_NIGHT"
MP = unreal.MaterialProperty
log = []

def tagged(mat):
    return any(e.get_editor_property("desc") == TAG for e in unreal.ObjectIterator(unreal.MaterialExpression) if e.get_outer() == mat)

def mpc_node(mat, name, x, y):
    n = mel.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, x, y)
    n.set_editor_property("collection", MPC); n.set_editor_property("parameter_name", name); n.set_editor_property("desc", TAG)
    return n

# 1 ---- traffic streams: night only
m = unreal.load_asset("/Game/ArchVizExplorer/Materials/Effects/M_Road_Lighting")
if not tagged(m):
    src = mel.get_material_property_input_node(m, MP.MP_EMISSIVE_COLOR)
    out = mel.get_material_property_input_node_output_name(m, MP.MP_EMISSIVE_COLOR)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, 400, 0); mul.set_editor_property("desc", TAG)
    mel.connect_material_expressions(src, out, mul, "A")
    mel.connect_material_expressions(mpc_node(m, "Effects", 200, 150), "", mul, "B")
    mel.connect_material_property(mul, "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(m); EAL.save_asset(m.get_path_name()); log.append("M_Road_Lighting x Effects")

# 2 ---- light function for street lamps
LF = "/Game/Neelam/Materials/MF_Neelam_NightLight"
lf = unreal.load_asset(LF)
if lf is None:
    lf = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MF_Neelam_NightLight", "/Game/Neelam/Materials", unreal.Material, unreal.MaterialFactoryNew())
    lf.set_editor_property("material_domain", unreal.MaterialDomain.MD_LIGHT_FUNCTION)
    mel.connect_material_property(mpc_node(lf, "Effects", -300, 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(lf); EAL.save_asset(LF); log.append("created " + LF)
lamp_bp = unreal.load_asset("/Game/ArchVizExplorer/Environment/Lighting/BP_Lamp")
for comp in ("SpotLight", "PointLight"):
    c = unreal.load_object(None, "/Game/ArchVizExplorer/Environment/Lighting/BP_Lamp.BP_Lamp_C:%s_GEN_VARIABLE" % comp)
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("cast_shadows", False)
    c.set_editor_property("light_function_material", lf)
    log.append("BP_Lamp.%s movable + night light function (intensity %s)" % (comp, c.get_editor_property("intensity")))
unreal.BlueprintEditorLibrary.compile_blueprint(lamp_bp); EAL.save_asset(lamp_bp.get_path_name())

# 3 ---- window lights on the tower glass
g = unreal.load_asset("/Game/Neelam/Buildings/WindTunnel/Materials/Master/M_Neelam_Glass")
if not tagged(g):
    wp = mel.create_material_expression(g, unreal.MaterialExpressionWorldPosition, -1200, 600)
    ratio = mel.create_material_expression(g, unreal.MaterialExpressionScalarParameter, -1200, 750)
    ratio.set_editor_property("parameter_name", "Window_Lit_Ratio"); ratio.set_editor_property("default_value", 0.55)
    cu = mel.create_material_expression(g, unreal.MaterialExpressionCustom, -900, 650); cu.set_editor_property("desc", TAG)
    cu.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    cu.set_editor_property("code", """float3 c = floor(float3(WP.x / 360.0, WP.y / 360.0, WP.z / 315.0));
float h  = frac(sin(dot(c, float3(12.9898, 78.233, 37.719))) * 43758.5453);
float h2 = frac(h * 17.13 + 0.37);
float lit = step(1.0 - Ratio, h);
float3 warm = lerp(float3(1.0, 0.58, 0.28), float3(1.0, 0.86, 0.66), h2);
return warm * lit * (0.5 + h2);""")
    ins = []
    for nm in ("WP", "Ratio"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    cu.set_editor_property("inputs", ins)
    mel.connect_material_expressions(wp, "", cu, "WP"); mel.connect_material_expressions(ratio, "", cu, "Ratio")
    inten = mel.create_material_expression(g, unreal.MaterialExpressionScalarParameter, -900, 850)
    inten.set_editor_property("parameter_name", "Window_Intensity"); inten.set_editor_property("default_value", 12.0)
    m1 = mel.create_material_expression(g, unreal.MaterialExpressionMultiply, -600, 650)
    mel.connect_material_expressions(cu, "", m1, "A"); mel.connect_material_expressions(inten, "", m1, "B")
    m2 = mel.create_material_expression(g, unreal.MaterialExpressionMultiply, -400, 650)
    mel.connect_material_expressions(m1, "", m2, "A"); mel.connect_material_expressions(mpc_node(g, "Buildings", -600, 850), "", m2, "B")
    prev = mel.get_material_property_input_node(g, MP.MP_EMISSIVE_COLOR)
    if prev is not None:                                   # keep any existing emissive
        add = mel.create_material_expression(g, unreal.MaterialExpressionAdd, -250, 650)
        mel.connect_material_expressions(prev, mel.get_material_property_input_node_output_name(g, MP.MP_EMISSIVE_COLOR), add, "A")
        mel.connect_material_expressions(m2, "", add, "B"); m2 = add
    zero = mel.create_material_expression(g, unreal.MaterialExpressionConstant, -250, 800)
    sw = mel.create_material_expression(g, unreal.MaterialExpressionStaticSwitchParameter, -100, 650)
    sw.set_editor_property("parameter_name", "Window_Lights"); sw.set_editor_property("default_value", False)
    mel.connect_material_expressions(m2, "", sw, "True"); mel.connect_material_expressions(zero, "", sw, "False")
    mel.connect_material_property(sw, "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(g); EAL.save_asset(g.get_path_name()); log.append("M_Neelam_Glass window lights")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in ar.get_assets(unreal.ARFilter(package_paths=["/Game/Neelam"], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")])):
    if str(ad.asset_name) in ("MI_Glass_Residential", "MI_Glass_Retail"):
        mi = unreal.load_asset(str(ad.package_name))
        if mi.get_base_material() == g:
            mel.set_material_instance_static_switch_parameter_value(mi, "Window_Lights", True)
            mel.update_material_instance(mi); EAL.save_asset(str(ad.package_name)); log.append("windows ON: " + str(ad.package_name))
result = log
