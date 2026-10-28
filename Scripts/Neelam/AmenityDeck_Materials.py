"""Neelam amenity deck materials (28 Oct 2026). Bridge job, MODE "textures" | "masters" | "instances" | "assign" | "all".
Textures: SourceArt/AmenityDeck/textures (Poly Haven 4K CC0 scans + tools/make_textures.py) -> /Game/Neelam/AmenityDeck/Textures
Masters (/Game/Neelam/AmenityDeck/Materials):
  M_AD_Surface   opaque PBR: diff * tint (texture colour amount), OpenGL normals flipped on import, ARM (AO/rough/metal),
                 UV0 = metres (Blender UV_World) / TileM, macro variation = same diff sampled 13x larger (kills tiling),
                 vertex colour multiply (per-board / per-hold variation baked in Blender, white = none).
  M_AD_ChainLink masked two-sided wire mesh.     M_AD_Water   single layer water, two panning ripple normals.
  M_AD_Emissive  LED / pool light.
Instances MI_AD_<slot> replace the FBX placeholder M_AD_<slot> on every AD_* static mesh (assign)."""
import os
import unreal

MODE = globals().get("MODE", "all")
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJ, "SourceArt", "AmenityDeck", "textures")
TEX, MAT, MESH = "/Game/Neelam/AmenityDeck/Textures", "/Game/Neelam/AmenityDeck/Materials", "/Game/Neelam/AmenityDeck/Meshes"
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
out = {}

# slot -> (texture set or None, tile metres, tint, colour-texture amount, rough mult, metal, normal strength)
SURF = {
    "Timber":      ("fine_grained_wood", 1.6, (5.2, 5.0, 4.4), 1.0, 0.85, 0, 1.0),         # scan is dark walnut -> honey teak (linear tint)
    "KotaPath":    ("large_grey_tiles", 2.4, (0.86, 0.93, 0.86), 1.0, 1.0, 0, 1.0),
    "KotaTrackA":  ("patterned_slate_tiles", 1.8, (0.80, 0.86, 0.82), 1.0, 1.0, 0, 1.0),
    "KotaTrackB":  ("grey_tiles", 1.8, (1.0, 0.97, 0.90), 1.0, 1.0, 0, 1.0),
    "Granite":     ("granite_tile_02", 1.2, (1.0, 1.0, 1.0), 1.0, 0.75, 0, 0.6),
    "StoneSeat":   ("granite_tile", 1.5, (1.05, 1.02, 0.97), 1.0, 0.8, 0, 0.6),
    "PoolTile":    ("pool_mosaic", 0.5, (1.0, 1.0, 1.0), 1.0, 1.0, 0, 1.0),
    "PlanterClad": ("painted_plaster_wall", 2.0, (0.97, 0.95, 0.90), 0.35, 1.0, 0, 0.5),
    "Soil":        ("brown_mud_leaves_01", 1.5, (0.75, 0.72, 0.68), 1.0, 1.0, 0, 1.0),
    "LawnBase":    ("brown_mud_leaves_01", 1.5, (0.55, 0.60, 0.40), 1.0, 1.0, 0, 1.0),
    "CourtGreen":  ("painted_concrete_02", 3.0, (0.07, 0.30, 0.17), 0.12, 0.9, 0, 0.35),
    "CourtBlue":   ("painted_concrete_02", 3.0, (0.04, 0.13, 0.48), 0.12, 0.9, 0, 0.35),
    "CourtBlueDark": ("painted_concrete_02", 3.0, (0.02, 0.06, 0.20), 0.12, 0.9, 0, 0.35),
    "CourtLine":   ("painted_concrete_02", 3.0, (0.92, 0.92, 0.90), 0.1, 0.9, 0, 0.3),
    "SteelBlack":  ("concrete_floor_01", 1.0, (0.025, 0.025, 0.027), 0.0, 0.45, 0, 0.15),
    "PergolaWood": ("dark_wood", 1.8, (0.6, 1.25, 1.8), 1.0, 0.9, 0, 1.0),               # red-brown scan -> dark walnut
    "RubberMat":   ("rubber_tiles", 1.0, (0.75, 0.32, 0.24), 0.6, 1.0, 0, 1.0),
    "ClimbPanel":  ("painted_plaster_wall", 2.0, (0.80, 0.82, 0.84), 0.3, 1.0, 0, 0.6),
    "ClimbHolds":  ("painted_concrete_02", 0.5, (1.0, 1.0, 1.0), 0.0, 0.7, 0, 0.5),
    "Concrete":    ("concrete_floor_01", 2.0, (0.9, 0.9, 0.9), 1.0, 1.0, 0, 1.0),
    "HoopOrange":  ("painted_concrete_02", 1.0, (0.85, 0.22, 0.02), 0.0, 0.5, 0, 0.2),
    "LEDHead":     ("concrete_floor_01", 1.0, (0.12, 0.12, 0.13), 0.0, 0.35, 1, 0.1),
}
SPECIAL = {"NetMesh": "M_AD_ChainLink", "Water": "M_AD_Water", "PoolLight": "M_AD_Emissive", "Glass": None}


def tex_files():
    sets = {}
    for f in os.listdir(SRC):
        if f.startswith("_") or not f.lower().endswith((".jpg", ".png")):
            continue
        sets[f] = os.path.join(SRC, f)
    return sets


def import_textures():
    tasks = []
    for name, path in tex_files().items():
        if EAL.does_asset_exist(TEX + "/" + os.path.splitext(name)[0]):
            continue
        t = unreal.AssetImportTask(); t.filename = path; t.destination_path = TEX; t.automated = True; t.save = True; t.replace_existing = True
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    n = 0
    for p in EAL.list_assets(TEX, False, False):
        tx = unreal.load_asset(p); nm = tx.get_name()
        if "_nor" in nm:
            tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tx.set_editor_property("srgb", False); tx.set_editor_property("flip_green_channel", True)
        elif "_arm" in nm or "_mask" in nm:
            tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS if "_arm" in nm else unreal.TextureCompressionSettings.TC_GRAYSCALE)
            tx.set_editor_property("srgb", False)
        tx.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        EAL.save_loaded_asset(tx); n += 1
    out["textures"] = n


def T(n):
    return unreal.load_asset("%s/%s" % (TEX, n))


def new_mat(name, fresh=False):
    """Fresh graph; an existing asset is cleared in place so instances keep their parent (fresh=True recreates it:
    clearing leaves custom output nodes such as the single-layer-water output behind)."""
    path = "%s/%s" % (MAT, name)
    if fresh and EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path); MEL.delete_all_material_expressions(m)
    else:
        m = AT.create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_nanite", True)
    return m


def E(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def C(a, ao, b, bi):
    MEL.connect_material_expressions(a, ao, b, bi)


def scalar(m, name, v, x, y):
    return E(m, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=v)


def tex_param(m, name, tex, st, uv, x, y):
    e = E(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=name, texture=tex, sampler_type=st)
    C(uv, "", e, "UVs")
    return e


def master_surface():
    m = new_mat("M_AD_Surface")
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 0)
    tile = scalar(m, "TileM", 2.0, -1600, 150)
    uv = E(m, unreal.MaterialExpressionDivide, -1400, 50); C(tc, "", uv, "A"); C(tile, "", uv, "B")
    macro_k = scalar(m, "MacroScale", 13.0, -1600, 300)
    uvm = E(m, unreal.MaterialExpressionDivide, -1400, 250); C(uv, "", uvm, "A"); C(macro_k, "", uvm, "B")
    d = tex_param(m, "Diffuse", T("large_grey_tiles_diff_4k"), unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, uv, -1150, -200)
    dm = tex_param(m, "Diffuse", T("large_grey_tiles_diff_4k"), unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, uvm, -1150, 300)
    n = tex_param(m, "Normal", T("large_grey_tiles_nor_4k"), unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, uv, -1150, 600)
    a = tex_param(m, "ARM", T("large_grey_tiles_arm_4k"), unreal.MaterialSamplerType.SAMPLERTYPE_MASKS, uv, -1150, 900)
    tint = E(m, unreal.MaterialExpressionVectorParameter, -900, -400, parameter_name="Tint", default_value=unreal.LinearColor(1, 1, 1, 1))
    amt = scalar(m, "TexColorAmount", 1.0, -900, -250)
    # colour = lerp(tint, diff*tint, amount) * macro, macro = lerp(1, 2*luma(macro diff), MacroStrength)
    dt = E(m, unreal.MaterialExpressionMultiply, -700, -250); C(d, "RGB", dt, "A"); C(tint, "", dt, "B")
    lc = E(m, unreal.MaterialExpressionLinearInterpolate, -500, -300); C(tint, "", lc, "A"); C(dt, "", lc, "B"); C(amt, "", lc, "Alpha")
    lum = E(m, unreal.MaterialExpressionDesaturation, -900, 300); C(dm, "RGB", lum, "")
    two = E(m, unreal.MaterialExpressionMultiply, -700, 300, const_b=2.2); C(lum, "", two, "A")
    ms = scalar(m, "MacroStrength", 0.35, -700, 450)
    mac = E(m, unreal.MaterialExpressionLinearInterpolate, -500, 300, const_a=1.0); C(two, "", mac, "B"); C(ms, "", mac, "Alpha")
    vc = E(m, unreal.MaterialExpressionVertexColor, -500, 0)
    c1 = E(m, unreal.MaterialExpressionMultiply, -300, -200); C(lc, "", c1, "A"); C(mac, "", c1, "B")
    c2 = E(m, unreal.MaterialExpressionMultiply, -150, -200); C(c1, "", c2, "A"); C(vc, "RGB", c2, "B")
    MEL.connect_material_property(c2, "", unreal.MaterialProperty.MP_BASE_COLOR)
    # normal strength: lerp(flat, N, s)
    ns = scalar(m, "NormalStrength", 1.0, -900, 750)
    flat = E(m, unreal.MaterialExpressionConstant3Vector, -900, 650, constant=unreal.LinearColor(0, 0, 1, 1))
    nl = E(m, unreal.MaterialExpressionLinearInterpolate, -500, 650); C(flat, "", nl, "A"); C(n, "RGB", nl, "B"); C(ns, "", nl, "Alpha")
    MEL.connect_material_property(nl, "", unreal.MaterialProperty.MP_NORMAL)
    rm = scalar(m, "RoughMult", 1.0, -900, 1050)
    r = E(m, unreal.MaterialExpressionMultiply, -500, 950); C(a, "G", r, "A"); C(rm, "", r, "B")
    MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    met = scalar(m, "Metallic", 0.0, -500, 1100)
    MEL.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(a, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)


def master_chainlink():
    m = new_mat("M_AD_ChainLink")
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED); m.set_editor_property("two_sided", True)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    tile = scalar(m, "TileM", 0.2, -900, 150)
    uv = E(m, unreal.MaterialExpressionDivide, -700, 50); C(tc, "", uv, "A"); C(tile, "", uv, "B")
    mk = tex_param(m, "Mask", T("chainlink_mask"), unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE, uv, -450, 100)
    col = E(m, unreal.MaterialExpressionVectorParameter, -450, -150, parameter_name="Color", default_value=unreal.LinearColor(0.02, 0.02, 0.022, 1))
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(mk, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.connect_material_property(scalar(m, "Roughness", 0.45, -450, 350), "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)


def master_water():
    m = new_mat("M_AD_Water", fresh=True)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    outs = []
    for i, (sp, sc, ang) in enumerate(((0.035, 1.6, 0.0), (0.022, 2.7, 0.35))):
        uv = E(m, unreal.MaterialExpressionDivide, -1000, i * 300, const_b=sc); C(tc, "", uv, "A")
        p = E(m, unreal.MaterialExpressionPanner, -800, i * 300, speed_x=sp, speed_y=sp * (0.6 if i else -0.4)); C(uv, "", p, "Coordinate")
        n = tex_param(m, "Ripple%d" % i, T("water_nor"), unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL, p, -550, i * 300)
        outs.append(n)
    add = E(m, unreal.MaterialExpressionAdd, -300, 100); C(outs[0], "RGB", add, "A"); C(outs[1], "RGB", add, "B")
    ns = scalar(m, "RippleStrength", 0.35, -300, 300)
    flat = E(m, unreal.MaterialExpressionConstant3Vector, -300, 400, constant=unreal.LinearColor(0, 0, 1, 1))
    nrm = E(m, unreal.MaterialExpressionNormalize, -150, 100); C(add, "", nrm, "")
    nl = E(m, unreal.MaterialExpressionLinearInterpolate, 0, 200); C(flat, "", nl, "A"); C(nrm, "", nl, "B"); C(ns, "", nl, "Alpha")
    MEL.connect_material_property(nl, "", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(scalar(m, "Roughness", 0.03, 0, 450), "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(E(m, unreal.MaterialExpressionConstant3Vector, 0, -150, constant=unreal.LinearColor(0.0, 0.03, 0.05, 1)), "", unreal.MaterialProperty.MP_BASE_COLOR)
    wo = E(m, unreal.MaterialExpressionSingleLayerWaterMaterialOutput, 300, 600)
    sc = E(m, unreal.MaterialExpressionVectorParameter, 0, 600, parameter_name="Scattering", default_value=unreal.LinearColor(0.02, 0.10, 0.12, 1))
    ab = E(m, unreal.MaterialExpressionVectorParameter, 0, 750, parameter_name="Absorption", default_value=unreal.LinearColor(0.30, 0.06, 0.03, 1))
    C(sc, "", wo, "ScatteringCoefficients"); C(ab, "", wo, "AbsorptionCoefficients")
    C(scalar(m, "PhaseG", 0.2, 0, 900), "", wo, "PhaseG")
    C(scalar(m, "ColorScaleBehindWater", 1.0, 0, 1000), "", wo, "ColorScaleBehindWater")
    MEL.recompile_material(m); EAL.save_loaded_asset(m)


def master_emissive():
    m = new_mat("M_AD_Emissive")
    col = E(m, unreal.MaterialExpressionVectorParameter, -500, 0, parameter_name="Color", default_value=unreal.LinearColor(1.0, 0.92, 0.8, 1))
    k = scalar(m, "Intensity", 20.0, -500, 150)
    mul = E(m, unreal.MaterialExpressionMultiply, -250, 50); C(col, "", mul, "A"); C(k, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)


def mi(name, parent):
    path = "%s/%s" % (MAT, name)
    inst = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MAT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, parent)
    return inst


def instances():
    surf = unreal.load_asset(MAT + "/M_AD_Surface")
    for slot, (ts, tile, tint, amt, rough, metal, nstr) in SURF.items():
        inst = mi("MI_AD_" + slot, surf)
        MEL.set_material_instance_texture_parameter_value(inst, "Diffuse", T(ts + ("_diff" if ts == "pool_mosaic" else "_diff_4k")))
        MEL.set_material_instance_texture_parameter_value(inst, "Normal", T(ts + ("_nor" if ts == "pool_mosaic" else "_nor_4k")))
        MEL.set_material_instance_texture_parameter_value(inst, "ARM", T(ts + ("_arm" if ts == "pool_mosaic" else "_arm_4k")))
        MEL.set_material_instance_scalar_parameter_value(inst, "TileM", tile)
        MEL.set_material_instance_vector_parameter_value(inst, "Tint", unreal.LinearColor(*tint, 1))
        MEL.set_material_instance_scalar_parameter_value(inst, "TexColorAmount", amt)
        MEL.set_material_instance_scalar_parameter_value(inst, "RoughMult", rough)
        MEL.set_material_instance_scalar_parameter_value(inst, "Metallic", float(metal))
        MEL.set_material_instance_scalar_parameter_value(inst, "NormalStrength", nstr)
        if slot.startswith("Court") or slot in ("SteelBlack", "HoopOrange", "LEDHead", "ClimbHolds"):
            MEL.set_material_instance_scalar_parameter_value(inst, "MacroStrength", 0.08)
        MEL.update_material_instance(inst); EAL.save_loaded_asset(inst)
    cl = mi("MI_AD_NetMesh", unreal.load_asset(MAT + "/M_AD_ChainLink")); EAL.save_loaded_asset(cl)
    w = mi("MI_AD_Water", unreal.load_asset(MAT + "/M_AD_Water")); EAL.save_loaded_asset(w)
    pl = mi("MI_AD_PoolLight", unreal.load_asset(MAT + "/M_AD_Emissive")); EAL.save_loaded_asset(pl)
    out["instances"] = len(SURF) + 3


def glass():
    for p in EAL.list_assets("/Game/ArchVizExplorer/Materials/Glass", True, False):
        a = unreal.load_asset(p)
        if isinstance(a, (unreal.MaterialInstanceConstant, unreal.Material)):
            return a
    return None


def assign():
    g = glass(); n = 0; miss = set()
    for p in EAL.list_assets(MESH, False, False):
        sm = unreal.load_asset(p)
        if not isinstance(sm, unreal.StaticMesh):
            continue
        mats = sm.get_editor_property("static_materials")
        changed = False
        for i, s in enumerate(mats):
            slot = str(s.material_slot_name).replace("M_AD_", "")
            path = "%s/MI_AD_%s" % (MAT, slot)
            target = g if slot == "Glass" else (unreal.load_asset(path) if EAL.does_asset_exist(path) else None)
            if target is None:
                miss.add(slot); continue
            if s.material_interface != target:
                sm.set_material(i, target); changed = True; n += 1
        if changed:
            EAL.save_loaded_asset(sm)
    out["assigned"] = n; out["missing"] = sorted(miss); out["glass"] = g.get_path_name() if g else None


if MODE in ("textures", "all"):
    import_textures()
if MODE in ("masters", "all"):
    master_surface(); master_chainlink(); master_water(); master_emissive()
if MODE in ("instances", "all"):
    instances()
if MODE in ("assign", "all"):
    assign()
result = out
