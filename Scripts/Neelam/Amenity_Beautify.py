"""Amenity deck beautify (29 Sep): realistic Poly Haven CC0 trees replace the low-poly SM_Amenity_Trees,
lawn texture, night lights on every amenity light fixture. Re-runnable. Runs inside UE via NeelamBridge."""
import os, glob, json
import unreal
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
PH = os.path.join(PROJ, "SourceArt", "PolyHaven")
VEG = "/Game/Neelam/Vegetation"
CLUS = os.path.join(PROJ, "Scripts", "Neelam", "Data", "amenity_clusters.json")

def _import_tex(files, dest):
    tasks = []
    for f in files:
        t = unreal.AssetImportTask(); t.filename = f; t.destination_path = dest; t.automated = True; t.replace_existing = True; t.save = True
        tasks.append(t)
    AT.import_asset_tasks(tasks)
    out = {}
    for t in tasks:
        for p in t.imported_object_paths:
            tex = unreal.load_asset(p); n = tex.get_name().lower()
            if "nor" in n:
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP); tex.set_editor_property("srgb", False)
                tex.set_editor_property("flip_green_channel", False)
            elif "rough" in n or "alpha" in n:
                tex.set_editor_property("srgb", False); tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
            elif "arm" in n:
                tex.set_editor_property("srgb", False)
            EAL.save_asset(p)
            out[n] = tex
    return out

def _master(path, foliage, defaults=None):
    defaults = defaults or {}
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(path.rsplit("/", 1)[1], path.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    if foliage:
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        m.set_editor_property("two_sided", True)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    def tp(name, x, y, normal=False):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        e.set_editor_property("parameter_name", name)
        t = defaults.get(name)
        if t:
            e.set_editor_property("texture", t)
            MST = unreal.MaterialSamplerType; srgb = t.get_editor_property("srgb")
            gray = str(t.get_editor_property("compression_settings")).find("GRAYSCALE") >= 0
            if normal: st = MST.SAMPLERTYPE_NORMAL
            elif gray: st = MST.SAMPLERTYPE_GRAYSCALE if srgb else MST.SAMPLERTYPE_LINEAR_GRAYSCALE
            else: st = MST.SAMPLERTYPE_COLOR if srgb else MST.SAMPLERTYPE_LINEAR_COLOR
            e.set_editor_property("sampler_type", st)
        return e
    def sp(name, v, x, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", name); e.set_editor_property("default_value", v); return e
    def vp(name, v, x, y):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, x, y)
        e.set_editor_property("parameter_name", name); e.set_editor_property("default_value", unreal.LinearColor(*v)); return e
    d = tp("Diffuse", -900, -300); tint = vp("Tint", (1, 1, 1, 1), -900, -520)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, -300)
    MEL.connect_material_expressions(d, "RGB", mul, "A"); MEL.connect_material_expressions(tint, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
    n = tp("Normal", -900, 0, True); MEL.connect_material_property(n, "RGB", unreal.MaterialProperty.MP_NORMAL)
    r = tp("Roughness", -900, 300)
    rm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, 300)
    MEL.connect_material_expressions(r, "R", rm, "A"); MEL.connect_material_expressions(sp("RoughnessScale", 1.0, -900, 520), "", rm, "B")
    MEL.connect_material_property(rm, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if foliage:
        a = tp("Alpha", -900, 700); MEL.connect_material_property(a, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
        sub = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -500, 900)
        MEL.connect_material_expressions(mul, "", sub, "A"); MEL.connect_material_expressions(sp("Translucency", 0.45, -900, 950), "", sub, "B")
        MEL.connect_material_property(sub, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    MEL.recompile_material(m); EAL.save_asset(path)
    return m

def _mi(path, parent, texs, tint=None, extra=None):
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(path.rsplit("/", 1)[1], path.rsplit("/", 1)[0], unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, parent)
    for k, t in texs.items():
        if t: MEL.set_material_instance_texture_parameter_value(mi, k, t)
    if tint: MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(*tint))
    for k, v in (extra or {}).items(): MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    EAL.save_asset(path); return mi

def step_tree_materials():
    res = {}; fol = bark = None
    for aid in ("jacaranda_tree", "island_tree_02"):
        tx = _import_tex(sorted(glob.glob(os.path.join(PH, "models", aid, "textures", "*_2k.png"))), VEG + "/" + aid + "/Textures")
        if fol is None:
            T = lambda *k: next((t for n, t in tx.items() if all(x in n for x in k)), None)
            fol = _master(VEG + "/Materials/M_Neelam_Foliage", True, {"Diffuse": T("leaves", "diff"), "Normal": T("leaves", "nor"), "Roughness": T("leaves", "rough"), "Alpha": T("leaves", "alpha")})
            bark = _master(VEG + "/Materials/M_Neelam_Bark", False, {"Diffuse": T("trunk", "diff"), "Normal": T("trunk", "nor"), "Roughness": T("trunk", "rough")})
            for mm in (fol, bark):
                mm.set_editor_property("used_with_nanite", True); MEL.recompile_material(mm); EAL.save_asset(mm.get_path_name())
        def g(*keys):
            for n, t in tx.items():
                if all(k in n for k in keys): return t
        sm = unreal.load_asset("%s/%s/%s_2k" % (VEG, aid, aid))
        mats = sm.get_editor_property("static_materials")
        for i, s in enumerate(mats):
            slot = str(s.get_editor_property("material_slot_name")).lower()
            part = "leaves" if "leaves" in slot else "branches" if "branches" in slot else "trunk"
            if part == "leaves":
                mi = _mi("%s/%s/MI_%s_leaves" % (VEG, aid, aid), fol, {"Diffuse": g("leaves", "diff"), "Normal": g("leaves", "nor"), "Roughness": g("leaves", "rough"), "Alpha": g("leaves", "alpha")},
                         tint=(0.85, 1.0, 0.8, 1) if aid == "island_tree_02" else (0.95, 1.0, 0.95, 1))
            else:
                key = "branches" if (part == "branches" and g("branches", "diff")) else ("trunk" if g("trunk", "diff") else "branches")
                mi = _mi("%s/%s/MI_%s_%s" % (VEG, aid, aid, part), bark, {"Diffuse": g(key, "diff"), "Normal": g(key, "nor"), "Roughness": g(key, "rough")})
            sm.set_material(i, mi)
        EAL.save_asset(sm.get_path_name())
        res[aid] = [str(m.get_editor_property("material_interface").get_name()) for m in sm.get_editor_property("static_materials")]
    return res

def step_place_trees(big_scale=0.28, small_scale=0.17):
    cl = json.load(open(CLUS))["trees"]
    old = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == "SM_Amenity_Trees"][0]
    old.set_actor_hidden_in_game(True); old.set_is_temporarily_hidden_in_editor(True)
    old.static_mesh_component.set_visibility(False, True)
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == "Neelam_AmenityTrees" or a.get_actor_label().startswith("AmenityTree_"): a.destroy_actor()
    big = unreal.load_asset(VEG + "/jacaranda_tree/jacaranda_tree_2k"); small = big   # island_tree_02 leaned out of the planters; a small jacaranda looks better
    host = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0))
    host.set_actor_label("Neelam_AmenityTrees"); host.set_folder_path("Neelam/WindTunnel/Amenities")
    import random; rnd = random.Random(7)
    placed = []
    for c in cl:
        isbig = c["h"] > 400
        # the jacaranda canopy leans towards local (-71,-37): turn that lean towards the middle of the deck (away from pool edges)
        import math
        yaw = math.degrees(math.atan2(2700 - c["wy"], 4700 - c["wx"]) - math.atan2(-37.0, -71.0)) + rnd.uniform(-20, 20)
        a = unreal.EditorLevelLibrary.spawn_actor_from_object(big if isbig else small, unreal.Vector(c["wx"], c["wy"], c["wz"] - 5), unreal.Rotator(0, yaw, 0))
        s = (big_scale if isbig else small_scale) * rnd.uniform(0.92, 1.08)
        a.set_actor_scale3d(unreal.Vector(s, s, s))
        a.set_actor_label(("AmenityTree_Big_%d" if isbig else "AmenityTree_Planter_%d") % len(placed))
        a.set_folder_path("Neelam/WindTunnel/Amenities/Trees")
        a.static_mesh_component.set_editor_property("cast_shadow", True)
        a.attach_to_actor(host, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
        placed.append(a.get_actor_label())
    return placed

def step_grass():
    tx = _import_tex(sorted(glob.glob(os.path.join(PH, "textures_grass", "leafy_grass", "*_2k.jpg"))), "/Game/Neelam/Materials/Grass")
    mi = unreal.load_asset("/Game/Neelam/Buildings/WindTunnel/Materials/Instances/MI_Grass_Lawn")
    parent = mi.get_editor_property("parent")
    info = {"parent": parent.get_path_name(),
            "tex_params": [str(p) for p in MEL.get_texture_parameter_names(mi)],
            "scalar_params": [str(p) for p in MEL.get_scalar_parameter_names(mi)],
            "vector_params": [str(p) for p in MEL.get_vector_parameter_names(mi)], "tex": list(tx.keys())}
    return info

# ------------------------------------------------------------------ night lights on the amenity fixtures
LF = "/Game/Neelam/Materials/MF_Neelam_NightLight"      # light function = Emissive_MPC.Effects (0 day -> 1 night)
WARM = unreal.Color(r=255, g=196, b=137, a=255)        # ~3000 K
POOL = unreal.Color(r=150, g=215, b=255, a=255)

def _light(cls, loc, rot, lm, radius, color, label, cone=None):
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, loc, rot)
    c = a.get_component_by_class(unreal.LocalLightComponent)
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    c.set_editor_property("intensity", lm)
    c.set_editor_property("attenuation_radius", radius)
    c.set_editor_property("light_color", color)
    c.set_editor_property("cast_shadows", False)
    c.set_editor_property("indirect_lighting_intensity", 0.3)
    c.set_editor_property("light_function_material", unreal.load_asset(LF))
    if cone:
        c.set_editor_property("outer_cone_angle", cone); c.set_editor_property("inner_cone_angle", cone * 0.55)
    a.set_actor_label(label); a.set_folder_path("Neelam/WindTunnel/Amenities/NightLights")
    a.tags = ["Neelam_AmenityLight"]
    return a

def step_lights():
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if "Neelam_AmenityLight" in [str(t) for t in a.tags]: a.destroy_actor()
    cl = json.load(open(CLUS))
    trees = cl["trees"]
    n = {"pole": 0, "flood": 0, "bollard": 0, "uplight": 0, "pool": 0, "step": 0}
    down = unreal.Rotator(pitch=-90, yaw=0, roll=0); up = unreal.Rotator(pitch=90, yaw=0, roll=0)
    for i, l in enumerate(cl["lights"]):
        x, y, z, h = l["wx"], l["wy"], l["wz"], l["h"]
        if h >= 550:      # tall court/deck floodlight
            _light(unreal.SpotLight, unreal.Vector(x, y, z + h - 20), down, 9000, 2600, WARM, "AmenLight_Flood_%d" % i, cone=62); n["flood"] += 1
        elif h >= 300:    # garden pole
            _light(unreal.PointLight, unreal.Vector(x, y, z + h - 25), down, 1800, 1100, WARM, "AmenLight_Pole_%d" % i); n["pole"] += 1
        elif h >= 40:     # bollard
            _light(unreal.PointLight, unreal.Vector(x, y, z + h - 6), down, 220, 420, WARM, "AmenLight_Bollard_%d" % i); n["bollard"] += 1
        else:
            near_tree = any(abs(t["wx"] - x) < 120 and abs(t["wy"] - y) < 120 for t in trees)
            if z < 2470:  # inside the pool
                _light(unreal.PointLight, unreal.Vector(x, y, z + 15), up, 900, 700, POOL, "AmenLight_Pool_%d" % i); n["pool"] += 1
            elif near_tree:
                _light(unreal.SpotLight, unreal.Vector(x, y, z + 15), up, 1200, 900, WARM, "AmenLight_TreeUp_%d" % i, cone=40); n["uplight"] += 1
            else:
                _light(unreal.PointLight, unreal.Vector(x, y, z + 12), up, 90, 260, WARM, "AmenLight_Step_%d" % i); n["step"] += 1
    return n

def step_emissive_night(boost=18.0):
    """M_Neelam_Emissive: emissive x (1 + NightBoost x Effects) - fixture heads and pool lights glow at night."""
    m = unreal.load_asset("/Game/Neelam/Buildings/WindTunnel/Materials/Master/M_Neelam_Emissive")
    tag = "NEELAM_NIGHTBOOST"
    exprs = [e for e in unreal.ObjectIterator(unreal.MaterialExpression) if e.get_outer() == m]
    if not any(e.get_editor_property("desc") == tag for e in exprs):
        src = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        src_out = MEL.get_material_property_input_node_output_name(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mpc = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, -600, 500)
        mpc.set_editor_property("collection", unreal.load_asset("/Game/ArchVizExplorer/Materials/MPC/Emissive_MPC")); mpc.set_editor_property("parameter_name", "Effects")
        nb = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 620)
        nb.set_editor_property("parameter_name", "NightBoost"); nb.set_editor_property("default_value", 0.0)
        mul1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -400, 550); MEL.connect_material_expressions(mpc, "", mul1, "A"); MEL.connect_material_expressions(nb, "", mul1, "B")
        add = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -250, 550); add.set_editor_property("const_a", 1.0)
        MEL.connect_material_expressions(mul1, "", add, "B")
        mul2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -100, 450); mul2.set_editor_property("desc", tag)
        MEL.connect_material_expressions(src, src_out or "", mul2, "A"); MEL.connect_material_expressions(add, "", mul2, "B")
        MEL.connect_material_property(mul2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.recompile_material(m); EAL.save_asset(m.get_path_name())
    for n in ("MI_Light_Emissive", "MI_Pool_Light"):
        mi = unreal.load_asset("/Game/Neelam/Buildings/WindTunnel/Materials/Instances/" + n)
        MEL.set_material_instance_scalar_parameter_value(mi, "NightBoost", boost); EAL.save_asset(mi.get_path_name())
    return "ok"
