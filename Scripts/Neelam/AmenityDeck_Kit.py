"""Neelam amenity deck asset kit (28 Oct 2026): SourceArt/AmenityDeck/kit/KIT_*/ (from tools/extract_kit.py: FBX +
textures + materials.json) -> /Game/Neelam/AmenityDeck/Kit/KIT_*/. Bridge job, globals MODE "masters" | "kits" | "all",
KITS (list of kit names, default every folder).
Masters (/Game/Neelam/AmenityDeck/Materials):
  M_AD_KitFoliage  masked, two-sided foliage shading: base (x tint), opacity from any texture channel (ChannelMask dot),
                   normal, roughness channel, subsurface colour = translucency texture x SSS tint.
  M_AD_KitProp     opaque: base texture or constant colour, normal, roughness / metallic channel or constant.
One instance per material slot (MI_<KIT>_<n>), Nanite on (masked foliage included)."""
import json, os
import unreal

MODE = globals().get("MODE", "all")
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
KITDIR = os.path.join(PROJ, "SourceArt", "AmenityDeck", "kit")
DST, MAT = "/Game/Neelam/AmenityDeck/Kit", "/Game/Neelam/AmenityDeck/Materials"
MEL, EAL = unreal.MaterialEditingLibrary, unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
WHITE = unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture")
LINW_PATH = "/Game/Neelam/AmenityDeck/Textures/T_AD_WhiteLinear"


def white_linear():
    """8x8 white, linear (masks) - default for the linear samplers so the masters compile."""
    if not EAL.does_asset_exist(LINW_PATH):
        t = unreal.AssetImportTask(); t.filename = os.path.join(PROJ, "SourceArt", "AmenityDeck", "textures", "_white_lin.png")
        t.destination_path = "/Game/Neelam/AmenityDeck/Textures"; t.destination_name = "T_AD_WhiteLinear"; t.automated = True; t.save = True
        AT.import_asset_tasks([t])
        a = unreal.load_asset(LINW_PATH)
        a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS); a.set_editor_property("srgb", False)
        EAL.save_loaded_asset(a)
    return unreal.load_asset(LINW_PATH)
FLAT = unreal.load_asset("/Engine/EngineMaterials/FlatNormal")
CH = {"R": (1, 0, 0, 0), "G": (0, 1, 0, 0), "B": (0, 0, 1, 0), "A": (0, 0, 0, 1)}
out = {}


def E(m, cls, x, y, **p):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in p.items():
        e.set_editor_property(k, v)
    return e


def C(a, ao, b, bi):
    MEL.connect_material_expressions(a, ao, b, bi)


def master(name, foliage):
    path = "%s/%s" % (MAT, name)
    if EAL.does_asset_exist(path):          # delete_all_material_expressions leaves nodes behind -> recreate (kits re-parent)
        EAL.delete_asset(path)
    m = AT.create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_nanite", True)
    if foliage:
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        m.set_editor_property("two_sided", True)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    S = unreal.MaterialSamplerType
    tex = lambda n, t, st, x, y: E(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=n, texture=t, sampler_type=st)
    vec = lambda n, v, x, y: E(m, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=n, default_value=unreal.LinearColor(*v))
    sca = lambda n, v, x, y: E(m, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=n, default_value=v)

    def chan(t, maskname, default, x, y):          # dot(texture RGBA, mask) -> one channel
        mk = vec(maskname, default, x - 250, y + 120)
        m4 = E(m, unreal.MaterialExpressionAppendVector, x, y + 120); C(mk, "", m4, "A"); C(mk, "A", m4, "B")  # vector params have no RGBA pin
        d = E(m, unreal.MaterialExpressionDotProduct, x + 200, y); C(t, "RGBA", d, "A"); C(m4, "", d, "B")
        return d
    base = tex("Base", WHITE, S.SAMPLERTYPE_COLOR, -1200, -300)
    tint = vec("Tint", (1, 1, 1, 1), -1200, -480)
    bc = E(m, unreal.MaterialExpressionMultiply, -800, -350); C(base, "RGB", bc, "A"); C(tint, "", bc, "B")
    MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    nrm = tex("Normal", FLAT, S.SAMPLERTYPE_NORMAL, -1200, 0)
    MEL.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    LW = white_linear()
    rt = tex("RoughTex", LW, S.SAMPLERTYPE_MASKS, -1200, 300)
    rc = chan(rt, "RoughChannel", (1, 0, 0, 0), -950, 300)
    rmul = sca("RoughMult", 1.0, -650, 420)
    rr = E(m, unreal.MaterialExpressionMultiply, -500, 300); C(rc, "", rr, "A"); C(rmul, "", rr, "B")
    MEL.connect_material_property(rr, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if foliage:
        at = tex("AlphaTex", LW, S.SAMPLERTYPE_MASKS, -1200, 600)
        ac = chan(at, "AlphaChannel", (1, 0, 0, 0), -950, 600)
        MEL.connect_material_property(ac, "", unreal.MaterialProperty.MP_OPACITY_MASK)
        tt = tex("TranslTex", WHITE, S.SAMPLERTYPE_COLOR, -1200, 900)
        st = vec("SSSTint", (0.55, 0.65, 0.25, 1), -1200, 1080)
        ss = E(m, unreal.MaterialExpressionMultiply, -800, 900); C(tt, "RGB", ss, "A"); C(st, "", ss, "B")
        MEL.connect_material_property(ss, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
        m.set_editor_property("opacity_mask_clip_value", 0.4)
    else:
        mt = tex("MetalTex", LW, S.SAMPLERTYPE_MASKS, -1200, 600)
        mc = chan(mt, "MetalChannel", (1, 0, 0, 0), -950, 600)
        mm = sca("MetalMult", 0.0, -650, 720)
        mr = E(m, unreal.MaterialExpressionMultiply, -500, 600); C(mc, "", mr, "A"); C(mm, "", mr, "B")
        MEL.connect_material_property(mr, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)
    return m


def import_tex(kit, files, roles):
    """files: texture file names; roles: name -> roles (base/normal/rough_tex/alpha/transl/metal_tex).
    Colour roles -> sRGB asset <name>; mask roles -> linear asset (<name>_lin when the image is also a colour map);
    normal -> normal map. Returns {(file, kind): asset} with kind 'srgb' | 'lin' | 'nrm'."""
    dst = "%s/%s/Textures" % (DST, kit)
    want = []
    for f in sorted(files):
        r = roles[f]; stem = os.path.splitext(f)[0]
        if r & {"base", "transl"}:
            want.append((f, "srgb", stem))
        if r & {"rough_tex", "alpha", "metal_tex"}:
            want.append((f, "lin", stem + "_lin" if r & {"base", "transl"} else stem))
        if "normal" in r and not (r & {"base", "transl", "rough_tex", "alpha", "metal_tex"}):
            want.append((f, "nrm", stem))
    tasks = []
    for f, kind, nm in want:
        if EAL.does_asset_exist("%s/%s" % (dst, nm)):
            continue
        t = unreal.AssetImportTask(); t.filename = os.path.join(KITDIR, kit, "textures", f); t.destination_path = dst
        t.destination_name = nm; t.automated = True; t.save = True; t.replace_existing = True
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    res = {}
    for f, kind, nm in want:
        a = unreal.load_asset("%s/%s" % (dst, nm))
        if a is None:
            continue
        if kind == "nrm":
            a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            a.set_editor_property("srgb", False); a.set_editor_property("flip_green_channel", True)
        elif kind == "lin":
            a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            a.set_editor_property("srgb", False)
        else:
            a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
            a.set_editor_property("srgb", True)
        EAL.save_loaded_asset(a)
        res[(f, kind)] = a
    return res


def do_kit(kit):
    info = json.load(open(os.path.join(KITDIR, kit, "materials.json")))
    roles = {}
    for md in info["materials"]:
        for k in ("base", "normal", "rough_tex", "alpha", "transl", "metal_tex"):
            if md.get(k):
                roles.setdefault(md[k], set()).add(k)
    # an image used as base colour must stay sRGB; never use it as a normal map
    tx = import_tex(kit, set(roles), roles)
    t = unreal.AssetImportTask()
    t.filename = os.path.join(KITDIR, kit, kit + ".fbx"); t.destination_path = "%s/%s" % (DST, kit)
    t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sm_d = o.static_mesh_import_data; sm_d.combine_meshes = True; sm_d.auto_generate_collision = False; sm_d.generate_lightmap_u_vs = False
    t.options = o
    AT.import_asset_tasks([t])
    sm = unreal.load_asset("%s/%s/%s" % (DST, kit, kit))
    fol = unreal.load_asset(MAT + "/M_AD_KitFoliage"); prop = unreal.load_asset(MAT + "/M_AD_KitProp")
    for i, md in enumerate(info["materials"]):
        a = md.get("alpha")
        real_alpha = bool(a) and not (md.get("alpha_ch") == "A" and a.lower().endswith(".jpg"))   # jpg has no A channel
        leaf = real_alpha and (md.get("foliage") or a != md.get("base"))
        name = "MI_%s_%d" % (kit, i); path = "%s/%s/%s" % (DST, kit, name)
        mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, "%s/%s" % (DST, kit), unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, fol if leaf else prop)
        if (md.get("base"), "srgb") in tx and not md.get("base_ch"):      # a single packed channel is not a colour map
            MEL.set_material_instance_texture_parameter_value(mi, "Base", tx[(md["base"], "srgb")])
        else:
            col = md.get("color", [0.5] * 3) if not md.get("base_ch") else [0.32, 0.30, 0.28]   # pots etc: warm grey
            MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(*(col + [1])))
            MEL.set_material_instance_texture_parameter_value(mi, "Base", WHITE)
        if (md.get("normal"), "nrm") in tx:
            MEL.set_material_instance_texture_parameter_value(mi, "Normal", tx[(md["normal"], "nrm")])
        if (md.get("rough_tex"), "lin") in tx:
            MEL.set_material_instance_texture_parameter_value(mi, "RoughTex", tx[(md["rough_tex"], "lin")])
            MEL.set_material_instance_vector_parameter_value(mi, "RoughChannel", unreal.LinearColor(*CH[md.get("rough_tex_ch", "R")]))
        else:
            MEL.set_material_instance_scalar_parameter_value(mi, "RoughMult", float(md.get("rough", 0.6)))
        if leaf:
            MEL.set_material_instance_texture_parameter_value(mi, "AlphaTex", tx[(md["alpha"], "lin")])
            MEL.set_material_instance_vector_parameter_value(mi, "AlphaChannel", unreal.LinearColor(*CH[md.get("alpha_ch", "R")]))
            if (md.get("transl"), "srgb") in tx:
                MEL.set_material_instance_texture_parameter_value(mi, "TranslTex", tx[(md["transl"], "srgb")])
        else:
            if (md.get("metal_tex"), "lin") in tx:
                MEL.set_material_instance_texture_parameter_value(mi, "MetalTex", tx[(md["metal_tex"], "lin")])
                MEL.set_material_instance_vector_parameter_value(mi, "MetalChannel", unreal.LinearColor(*CH[md.get("metal_tex_ch", "R")]))
                MEL.set_material_instance_scalar_parameter_value(mi, "MetalMult", 1.0)
            else:
                MEL.set_material_instance_scalar_parameter_value(mi, "MetalMult", float(md.get("metal", 0.0)))
        MEL.update_material_instance(mi); EAL.save_loaded_asset(mi)
        if i < len(sm.get_editor_property("static_materials")):
            sm.set_material(i, mi)
    ns = sm.get_editor_property("nanite_settings"); ns.enabled = True; sm.set_editor_property("nanite_settings", ns)
    EAL.save_loaded_asset(sm)
    return {"faces": info["faces"], "mats": len(info["materials"]), "size_m": info["size_m"]}


if MODE in ("masters", "all"):
    master("M_AD_KitFoliage", True); master("M_AD_KitProp", False)
if MODE in ("kits", "all"):
    for k in globals().get("KITS") or sorted(d for d in os.listdir(KITDIR) if d.startswith("KIT_")):
        try:
            out[k] = do_kit(k)
        except Exception as e:
            out[k] = "ERROR %s" % e
result = out
