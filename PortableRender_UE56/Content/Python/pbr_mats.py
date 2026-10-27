"""Real PBR materials for amenity / flat scenes whose Blender procedural shaders exported white or wrong.
Poly Haven CC0 2K sets (diff / nor_gl / rough) from the Neelam project's SourceArt/PolyHaven, world-aligned
(no UVs needed, real-world tile size in cm), plus an opaque glossy pool water.
    import pbr_mats as PM
    PM.master()                                     # builds /Game/Neelam/PBR/M_PBR_WorldAligned once
    PM.assign({"Wood_Floor_Teak1": ("oak_wood_planks", 180, (1.0, 0.8, 0.6), 1.0)})   # material name -> (set, tile cm, tint, rough mul)
    PM.water(["Pool_Water_02"])                     # glossy dark-teal water on those materials
Only touches actors in the OPEN level; swaps the slot material, never edits the imported material assets."""
import os
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = r"C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/PolyHaven"
DST = "/Game/Neelam/PBR"
MASTER = DST + "/M_PBR_WorldAligned"
WATER = DST + "/M_PoolWater"
WAT_FN = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture.WorldAlignedTexture"
WAN_FN = "/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal.WorldAlignedNormal"


def textures(name):
    """diff / nor / rough of a Poly Haven set, imported once into /Game/Neelam/PBR."""
    out = {}
    for kind, suf in (("diff", "diff_2k.jpg"), ("nor", "nor_gl_2k.jpg"), ("rough", "rough_2k.jpg")):
        path = "%s/T_%s_%s" % (DST, name, kind)
        if not EAL.does_asset_exist(path):
            t = unreal.AssetImportTask()
            t.filename = os.path.join(SRC, name, "%s_%s" % (name, suf))
            t.destination_path, t.destination_name = DST, "T_%s_%s" % (name, kind)
            t.automated, t.save, t.replace_existing = True, False, True
            AT.import_asset_tasks([t])
            tex = unreal.load_asset(path)
            if kind == "nor":   # Poly Haven ships OpenGL normals; UE is DirectX -> flip green
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("flip_green_channel", True)
                tex.set_editor_property("srgb", False)
            elif kind == "rough":
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                tex.set_editor_property("srgb", False)
            EAL.save_asset(path)
        out[kind] = unreal.load_asset(path)
    return out


def _fn(mat, path, x, y):
    e = MEL.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    e.set_editor_property("material_function", unreal.load_asset(path))
    return e


def master():
    """M_PBR_WorldAligned: world-aligned diff * Tint, normal, rough * RoughMul; Tile = cm per texture repeat."""
    if EAL.does_asset_exist(MASTER):
        return unreal.load_asset(MASTER)
    m = AT.create_asset("M_PBR_WorldAligned", DST, unreal.Material, unreal.MaterialFactoryNew())
    tile = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1400, 0)
    tile.set_editor_property("parameter_name", "Tile"); tile.set_editor_property("default_value", 200.0)
    size = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -1200, 0)
    size2 = MEL.create_material_expression(m, unreal.MaterialExpressionAppendVector, -1100, 0)
    MEL.connect_material_expressions(tile, "", size, "A"); MEL.connect_material_expressions(tile, "", size, "B")
    MEL.connect_material_expressions(size, "", size2, "A"); MEL.connect_material_expressions(tile, "", size2, "B")
    outs = {}
    for i, (pname, fn) in enumerate((("Diff", WAT_FN), ("Nor", WAN_FN), ("Rough", WAT_FN))):
        to = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -1000, i * 300 - 300)
        to.set_editor_property("parameter_name", pname)
        f = _fn(m, fn, -700, i * 300 - 300)
        MEL.connect_material_expressions(to, "", f, "TextureObject")
        MEL.connect_material_expressions(size2, "", f, "TextureSize")
        outs[pname] = f
    tint = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, -450)
    tint.set_editor_property("parameter_name", "Tint"); tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, -300)
    MEL.connect_material_expressions(outs["Diff"], "XYZ Texture", mul, "A"); MEL.connect_material_expressions(tint, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(outs["Nor"], "XYZ Texture", unreal.MaterialProperty.MP_NORMAL)
    rm = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 350)
    rm.set_editor_property("parameter_name", "RoughMul"); rm.set_editor_property("default_value", 1.0)
    mask = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -400, 250)
    mask.set_editor_property("r", True); mask.set_editor_property("g", False); mask.set_editor_property("b", False); mask.set_editor_property("a", False)
    MEL.connect_material_expressions(outs["Rough"], "XYZ Texture", mask, "")
    rmul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 300)
    MEL.connect_material_expressions(mask, "", rmul, "A"); MEL.connect_material_expressions(rm, "", rmul, "B")
    MEL.connect_material_property(rmul, "", unreal.MaterialProperty.MP_ROUGHNESS)
    met = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -250, 450)
    met.set_editor_property("parameter_name", "Metallic"); met.set_editor_property("default_value", 0.0)
    MEL.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.recompile_material(m); EAL.save_asset(MASTER)
    return m


def instance(set_name, tile, tint=(1, 1, 1), rough_mul=1.0, metallic=0.0):
    tx = textures(set_name)
    name = "MI_%s_%d" % (set_name, int(tile))
    path = "%s/%s" % (DST, name)
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else \
        AT.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master())
    MEL.set_material_instance_texture_parameter_value(mi, "Diff", tx["diff"])
    MEL.set_material_instance_texture_parameter_value(mi, "Nor", tx["nor"])
    MEL.set_material_instance_texture_parameter_value(mi, "Rough", tx["rough"])
    MEL.set_material_instance_scalar_parameter_value(mi, "Tile", float(tile))
    MEL.set_material_instance_scalar_parameter_value(mi, "RoughMul", float(rough_mul))
    MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", float(metallic))
    MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1))
    EAL.save_asset(path)
    return mi


def _swap(names, mat):
    n = 0
    for a in ACT.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        c = a.static_mesh_component
        for i, m in enumerate(c.get_materials()):
            if m and m.get_name() in names:
                a.modify(); c.modify()   # without this the level is not marked dirty -> save skips it, the render reloads the old level
                c.set_material(i, mat); n += 1
    return n


def save_level():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()


def assign(table):
    """table: imported material name -> (poly haven set, tile cm, tint, rough mul[, metallic])"""
    return {k: _swap({k}, instance(*v)) for k, v in table.items()}


def flat(names, color, rough, metallic=0.0):
    """plain coloured material for exported-white surfaces that need no texture (frames, grass blades...)"""
    key = "MI_Flat_%02x%02x%02x_r%d_m%d" % (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), int(rough * 100), int(metallic * 100))
    path = "%s/%s" % (DST, key)
    if not EAL.does_asset_exist(path):
        base = "%s/M_Flat" % DST
        if not EAL.does_asset_exist(base):
            m = AT.create_asset("M_Flat", DST, unreal.Material, unreal.MaterialFactoryNew())
            for pn, prop, y, dv in (("Color", unreal.MaterialProperty.MP_BASE_COLOR, 0, None), ("Rough", unreal.MaterialProperty.MP_ROUGHNESS, 200, 0.5),
                                    ("Metal", unreal.MaterialProperty.MP_METALLIC, 300, 0.0)):
                e = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter if dv is None else unreal.MaterialExpressionScalarParameter, -300, y)
                e.set_editor_property("parameter_name", pn)
                if dv is not None: e.set_editor_property("default_value", dv)
                MEL.connect_material_property(e, "", prop)
            m.set_editor_property("two_sided", True)   # grass blades / thin planes
            MEL.recompile_material(m); EAL.save_asset(base)
        mi = AT.create_asset(key, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", unreal.load_asset(base))
        MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(color[0], color[1], color[2], 1))
        MEL.set_material_instance_scalar_parameter_value(mi, "Rough", rough)
        MEL.set_material_instance_scalar_parameter_value(mi, "Metal", metallic)
        EAL.save_asset(path)
    return _swap(set(names), unreal.load_asset(path))


def _ripple():
    """SourceArt/PBR/T_WaterRipple_N.png (Tools/make_water_normal.py, seamless sine ripples, DirectX normal)."""
    path = DST + "/T_WaterRipple_N"
    if not EAL.does_asset_exist(path):
        t = unreal.AssetImportTask()
        t.filename = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt", "PBR", "T_WaterRipple_N.png")
        t.destination_path, t.destination_name, t.automated, t.replace_existing = DST, "T_WaterRipple_N", True, True
        AT.import_asset_tasks([t])
        tex = unreal.load_asset(path)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("srgb", False)
        EAL.save_asset(path)
    return unreal.load_asset(path)


def water(names, color=(0.012, 0.075, 0.085), rough=0.035):
    """Opaque glossy pool water: dark teal + seamless ripple normal (opaque reflects reliably in Lumen scene
    captures, translucent water does not)."""
    if not EAL.does_asset_exist(WATER):
        m = AT.create_asset("M_PoolWater", DST, unreal.Material, unreal.MaterialFactoryNew())
        col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, -100)
        col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(color[0], color[1], color[2], 1))
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        r = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 100)
        r.set_editor_property("parameter_name", "Rough"); r.set_editor_property("default_value", rough)
        MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
        sp = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200)
        sp.set_editor_property("r", 0.5)
        MEL.connect_material_property(sp, "", unreal.MaterialProperty.MP_SPECULAR)
        nt = _ripple()
        tn = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, -1000, 300)
        tn.set_editor_property("parameter_name", "Ripple"); tn.set_editor_property("texture", nt)
        f = _fn(m, WAN_FN, -700, 300)
        sz = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -1000, 450)
        sz.set_editor_property("constant", unreal.LinearColor(900, 700, 900, 1))
        MEL.connect_material_expressions(tn, "", f, "TextureObject"); MEL.connect_material_expressions(sz, "", f, "TextureSize")
        flat_n = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 450)
        flat_n.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 1))
        lerp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -250, 350)
        amt = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 550)
        amt.set_editor_property("parameter_name", "RippleAmount"); amt.set_editor_property("default_value", 0.12)
        MEL.connect_material_expressions(flat_n, "", lerp, "A"); MEL.connect_material_expressions(f, "XYZ Texture", lerp, "B")
        MEL.connect_material_expressions(amt, "", lerp, "Alpha")
        MEL.connect_material_property(lerp, "", unreal.MaterialProperty.MP_NORMAL)
        MEL.recompile_material(m); EAL.save_asset(WATER)
    return _swap(set(names), unreal.load_asset(WATER))


# ---------- automatic pass for any amenity level (open level) ----------
import re as _re
AUTO_SKIP = _re.compile(r"white|glass|vidro|light|luz|lamp|bulb|emiss|led|sky|mirror|chrome|gold|silver", _re.I)
AUTO_RULES = [   # first match wins: regex on the imported material name -> PBR instance args
    (r"water|pool_?w", "water"),
    (r"grass|lawn|turf|gramado", ("leafy_grass", 150, (0.85, 0.95, 0.75), 1.0)),
    (r"rubber|track|jog|epdm", ("rubberized_track", 200, (1, 1, 1), 1.0)),
    (r"asphalt|road|tarmac", ("asphalt_02", 400, (1, 1, 1), 1.0)),
    (r"teak|oak|walnut|wood|madeira|madera|plank|parquet|timber|deck", ("oak_wood_planks", 200, (1.0, 0.8, 0.6), 1.0)),
    (r"marble|granite|slate|stone|pedra", ("slate_floor", 200, (0.5, 0.5, 0.52), 0.6)),
    (r"paver|paving|tile|floor|piso|ground", ("precast_stone_paving", 190, (0.92, 0.91, 0.88), 1.0)),
    (r"concrete|cement|plaster|stucco|wall|parede", ("white_stucco", 300, (0.95, 0.94, 0.92), 1.0)),
]
WOODY = _re.compile(r"wood|madeira|teak|oak|walnut|plank|parquet|floor|deck", _re.I)


def _is_white(mi):
    try: t = MEL.get_material_instance_texture_parameter_value(mi, "BaseColorTexture")
    except Exception: t = None
    if t and t.get_name() != "T_White_srgb": return False
    try: c = MEL.get_material_instance_vector_parameter_value(mi, "BaseColorFactor"); return min(c.r, c.g, c.b) > 0.6
    except Exception: return True


def auto(name):
    """relink dropped glTF textures, un-metal the woods, give every still-white material a real PBR by its name."""
    import importlib, relink_gltf as RG
    importlib.reload(RG)
    rep = {"relink": len(RG.run(name)["relinked"]), "unmetal": [], "pbr": {}, "left_white": []}
    seen = {}
    for a in ACT.get_all_level_actors():
        if isinstance(a, unreal.StaticMeshActor):
            for m in a.static_mesh_component.get_materials():
                if isinstance(m, unreal.MaterialInstanceConstant) and not m.get_path_name().startswith(DST): seen[m.get_name()] = m
    for n, m in seen.items():
        if WOODY.search(n):
            try:
                if MEL.get_material_instance_scalar_parameter_value(m, "MetallicFactor") > 0.2:
                    MEL.set_material_instance_scalar_parameter_value(m, "MetallicFactor", 0.0); EAL.save_loaded_asset(m); rep["unmetal"].append(n)
            except Exception: pass
        if AUTO_SKIP.search(n) or not _is_white(m): continue
        for rx, spec in AUTO_RULES:
            if _re.search(rx, n, _re.I):
                rep["pbr"][n] = water([n]) if spec == "water" else _swap({n}, instance(*spec))
                break
        else:
            rep["left_white"].append(n)
    save_level()
    return rep


def fix_worldgrid(default=("granite_tile", 120, (0.55, 0.53, 0.5), 0.7)):
    """meshes left on Unreal's default WorldGridMaterial (checker = nothing exported) -> a real stone PBR"""
    mi = instance(*default); n = 0
    for a in ACT.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor): continue
        c = a.static_mesh_component
        for i, m in enumerate(c.get_materials()):
            if m is None or m.get_name() == "WorldGridMaterial":
                a.modify(); c.modify(); c.set_material(i, mi); n += 1
    save_level()
    return n
