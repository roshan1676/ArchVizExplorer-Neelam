"""Luxury material palette (M_LuxSurface + instances) and swaps.
    import lux_mat as LM; LM.library(); LM.swap("3BHK", {"White_Veined_Marble": "Statuario"})
Textures: SourceArt/Textures (ambientCG Marble012/016, Poly Haven smoked_walnut_veneer; CC0)."""
import unreal, os
import scene_builder as SB

ACT, EAL, AT, MEL = SB.ACT, SB.EAL, SB.AT, SB.MEL
TEX_DIR = os.path.join(SB.PROJ, "SourceArt", "Textures")
LUX = "/Game/Neelam/Shared/Lux"

# World-scale slab tiling: per-tile random offset so the veining never repeats, plus a grout mask in .z
TILE_HLSL = """
float3 n = abs(Nrm);
float2 p = n.z > 0.5 ? Pos.xy : (n.x > n.y ? Pos.yz : Pos.xz);   // floors: top-down, walls: side-on
float2 id = floor(p / TileCm);
float2 f = frac(p / TileCm);
float2 h = frac(sin(float2(dot(id, float2(127.1, 311.7)), dot(id, float2(269.5, 183.3)))) * 43758.5453);
float2 uv = (f * TileCm) / TexCm + h * 7.0;
float2 e = min(f, 1.0 - f) * TileCm;
float grout = 1.0 - saturate((min(e.x, e.y) - GroutCm * 0.5) / 0.08);
return float4(uv, grout, 0);
"""

def _tex(path_on_disk, name, normal=False, srgb=True, flip_green=False):
    dest = LUX + "/Textures/" + name
    if not EAL.does_asset_exist(dest):
        t = unreal.AssetImportTask(); t.filename = path_on_disk; t.destination_path = LUX + "/Textures"
        t.destination_name = name; t.automated = True; t.save = False
        AT.import_asset_tasks([t])
    tx = EAL.load_asset(dest)
    if normal:
        tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tx.set_editor_property("srgb", False); tx.set_editor_property("flip_green_channel", flip_green)
    else:
        tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT); tx.set_editor_property("srgb", srgb)
    EAL.save_loaded_asset(tx)
    return tx

def master():
    path = LUX + "/M_LuxSurface"
    if EAL.does_asset_exist(path): return EAL.load_asset(path)
    m = AT.create_asset("M_LuxSurface", LUX, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("two_sided", True)   # thin folded meshes (curtains, wavy panels): backfaces must shade
    E = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    def sp(name, v, x, y):
        e = E(unreal.MaterialExpressionScalarParameter, x, y); e.set_editor_property("parameter_name", name); e.set_editor_property("default_value", v); return e
    def vp(name, c, x, y):
        e = E(unreal.MaterialExpressionVectorParameter, x, y); e.set_editor_property("parameter_name", name); e.set_editor_property("default_value", unreal.LinearColor(*c)); return e
    wp = E(unreal.MaterialExpressionWorldPosition, -2200, -200)
    cus = E(unreal.MaterialExpressionCustom, -1900, -200)
    cus.set_editor_property("code", TILE_HLSL); cus.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4)
    ins = []
    for nm in ("Pos", "TileCm", "TexCm", "GroutCm", "Nrm"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    cus.set_editor_property("inputs", ins)
    MEL.connect_material_expressions(wp, "", cus, "Pos")
    MEL.connect_material_expressions(E(unreal.MaterialExpressionVertexNormalWS, -2200, -280), "", cus, "Nrm")
    MEL.connect_material_expressions(sp("TileCm", 120.0, -2200, -60), "", cus, "TileCm")
    MEL.connect_material_expressions(sp("TexCm", 200.0, -2200, 20), "", cus, "TexCm")
    MEL.connect_material_expressions(sp("GroutCm", 0.2, -2200, 100), "", cus, "GroutCm")
    uvw = E(unreal.MaterialExpressionComponentMask, -1650, -200)
    for ch, on in (("r", True), ("g", True), ("b", False), ("a", False)): uvw.set_editor_property(ch, on)
    MEL.connect_material_expressions(cus, "", uvw, "")
    grout = E(unreal.MaterialExpressionComponentMask, -1650, -80)
    for ch, on in (("r", False), ("g", False), ("b", True), ("a", False)): grout.set_editor_property(ch, on)  # NB masks default to R+G on
    MEL.connect_material_expressions(cus, "", grout, "")
    tc = E(unreal.MaterialExpressionTextureCoordinate, -1900, 200)
    uvs = E(unreal.MaterialExpressionMultiply, -1650, 200)
    MEL.connect_material_expressions(tc, "", uvs, "A"); MEL.connect_material_expressions(sp("UVScale", 1.0, -1900, 300), "", uvs, "B")
    sw = E(unreal.MaterialExpressionStaticSwitchParameter, -1450, 0); sw.set_editor_property("parameter_name", "WorldTiles")
    MEL.connect_material_expressions(uvw, "", sw, "True"); MEL.connect_material_expressions(uvs, "", sw, "False")
    gsw = E(unreal.MaterialExpressionStaticSwitchParameter, -1450, 150); gsw.set_editor_property("parameter_name", "WorldTiles")
    zero = E(unreal.MaterialExpressionConstant, -1650, 260)
    MEL.connect_material_expressions(grout, "", gsw, "True"); MEL.connect_material_expressions(zero, "", gsw, "False")
    def tex(name, default, x, y, sampler):
        t = E(unreal.MaterialExpressionTextureSampleParameter2D, x, y); t.set_editor_property("parameter_name", name)
        t.set_editor_property("texture", unreal.load_asset(default)); t.set_editor_property("sampler_type", sampler)
        MEL.connect_material_expressions(sw, "", t, "UVs"); return t
    tcol = tex("Color", "/Engine/EngineResources/WhiteSquareTexture", -1100, -300, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    tnor = tex("Normal", "/Engine/EngineMaterials/DefaultNormal", -1100, 0, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    trgh = tex("Roughness", "/Engine/EngineResources/WhiteSquareTexture", -1100, 300, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)  # sRGB like the default; remapped by RoughMin/Max
    bc = E(unreal.MaterialExpressionMultiply, -800, -300)
    MEL.connect_material_expressions(tcol, "RGB", bc, "A"); MEL.connect_material_expressions(vp("Tint", (1, 1, 1, 1), -1100, -450), "", bc, "B")
    bcg = E(unreal.MaterialExpressionLinearInterpolate, -550, -300)
    MEL.connect_material_expressions(bc, "", bcg, "A"); MEL.connect_material_expressions(vp("GroutColor", (0.55, 0.54, 0.52, 1), -800, -450), "", bcg, "B")
    MEL.connect_material_expressions(gsw, "", bcg, "Alpha")
    MEL.connect_material_property(bcg, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rl = E(unreal.MaterialExpressionLinearInterpolate, -800, 300)
    MEL.connect_material_expressions(sp("RoughMin", 0.05, -1100, 450), "", rl, "A"); MEL.connect_material_expressions(sp("RoughMax", 0.35, -1100, 530), "", rl, "B")
    MEL.connect_material_expressions(trgh, "R", rl, "Alpha")
    rg = E(unreal.MaterialExpressionLinearInterpolate, -550, 300)
    MEL.connect_material_expressions(rl, "", rg, "A"); MEL.connect_material_expressions(sp("GroutRough", 0.8, -800, 450), "", rg, "B")
    MEL.connect_material_expressions(gsw, "", rg, "Alpha")
    MEL.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
    flat = E(unreal.MaterialExpressionConstant3Vector, -1000, 60); flat.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 0))
    fn = E(unreal.MaterialExpressionLinearInterpolate, -800, 0)   # lerp(flat, map, NormalStrength)
    MEL.connect_material_expressions(flat, "", fn, "A"); MEL.connect_material_expressions(tnor, "RGB", fn, "B")
    MEL.connect_material_expressions(sp("NormalStrength", 1.0, -1250, 120), "", fn, "Alpha")
    MEL.connect_material_property(fn, "", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(sp("Metallic", 0.0, -550, 150), "", unreal.MaterialProperty.MP_METALLIC)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)
    return m

def mi(name, color=None, normal=None, rough=None, flip_green=False, world_tiles=False, **params):
    """Create/refresh /Game/Neelam/Shared/Lux/MI_<name>. Texture args are paths under SourceArt/Textures."""
    path = LUX + "/MI_" + name
    m = EAL.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset("MI_" + name, LUX, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, master())
    if color: MEL.set_material_instance_texture_parameter_value(m, "Color", _tex(os.path.join(TEX_DIR, color), "T_%s_C" % name))
    if normal: MEL.set_material_instance_texture_parameter_value(m, "Normal", _tex(os.path.join(TEX_DIR, normal), "T_%s_N" % name, normal=True, flip_green=flip_green))
    if rough: MEL.set_material_instance_texture_parameter_value(m, "Roughness", _tex(os.path.join(TEX_DIR, rough), "T_%s_R" % name))
    MEL.set_material_instance_static_switch_parameter_value(m, "WorldTiles", world_tiles)
    for k, v in params.items():
        if isinstance(v, (tuple, list)): MEL.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(*v))
        else: MEL.set_material_instance_scalar_parameter_value(m, k, float(v))
    MEL.update_material_instance(m); EAL.save_loaded_asset(m)
    return m

def library():
    """Statuario floor slabs, Nero Marquina accent, smoked walnut, satin brass."""
    return {
        "Statuario": mi("Statuario", "Marble021/Marble021_4K-JPG_Color.jpg", "Marble021/Marble021_4K-JPG_NormalDX.jpg",
                        "Marble021/Marble021_4K-JPG_Roughness.jpg", world_tiles=True, TileCm=120.0, TexCm=160.0, GroutCm=0.15,
                        RoughMin=0.04, RoughMax=0.12, NormalStrength=0.25, GroutColor=(0.70, 0.69, 0.67, 1), Tint=(1.0, 1.0, 1.0, 1)),
        "NeroMarquina": mi("NeroMarquina", "Marble016/Marble016_4K-JPG_Color.jpg", "Marble016/Marble016_4K-JPG_NormalDX.jpg",
                           "Marble016/Marble016_4K-JPG_Roughness.jpg", UVScale=1.0, RoughMin=0.04, RoughMax=0.15, NormalStrength=0.3),
        "Walnut": mi("Walnut", "smoked_walnut_veneer/smoked_walnut_veneer_Diffuse.jpg", "smoked_walnut_veneer/smoked_walnut_veneer_nor_gl.jpg",
                     "smoked_walnut_veneer/smoked_walnut_veneer_Rough.jpg", flip_green=True, UVScale=1.0, RoughMin=0.25, RoughMax=0.55, NormalStrength=0.6, Tint=(0.62, 0.48, 0.40, 1)),
        "Brass": mi("Brass", Tint=(0.93, 0.72, 0.40, 1), Metallic=1.0, RoughMin=0.22, RoughMax=0.22),
    }

def swap(name, mapping):
    """mapping: {existing material name (or prefix + '*'): library key}. Swaps on every actor in the open level."""
    lib = {k: EAL.load_asset(LUX + "/MI_" + k) for k in set(mapping.values())}
    def target(mname):
        for pat, key in mapping.items():
            if (pat.endswith("*") and mname.lower().startswith(pat[:-1].lower())) or mname == pat: return lib[key]
    n = 0
    for a in ACT.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if not c: continue
        for i, m in enumerate(c.get_materials()):
            t = m and target(m.get_name())
            if t: c.set_material(i, t); n += 1
    return n

def world_variants():
    """World-projected versions for meshes with poor UVs (kitchen set): no grout, big tiles so seams are rare."""
    return {
        "WalnutWorld": mi("WalnutWorld", "smoked_walnut_veneer/smoked_walnut_veneer_Diffuse.jpg", "smoked_walnut_veneer/smoked_walnut_veneer_nor_gl.jpg",
                          "smoked_walnut_veneer/smoked_walnut_veneer_Rough.jpg", flip_green=True, world_tiles=True, TileCm=244.0, TexCm=120.0,
                          GroutCm=0.0, RoughMin=0.25, RoughMax=0.55, NormalStrength=0.6, Tint=(0.40, 0.28, 0.22, 1)),
        "StatuarioSlab": mi("StatuarioSlab", "Marble021/Marble021_4K-JPG_Color.jpg", "Marble021/Marble021_4K-JPG_NormalDX.jpg",
                            "Marble021/Marble021_4K-JPG_Roughness.jpg", world_tiles=True, TileCm=320.0, TexCm=160.0, GroutCm=0.0,
                            RoughMin=0.04, RoughMax=0.12, NormalStrength=0.25, Tint=(1.0, 1.0, 1.0, 1)),
    }
