"""Amenity deck lighting = client lighting plan "Amenities Floor design.pdf" (7th podium floor lighting layout, 1 Oct 2026).

Legend (plan)                       switch  model
  Tree uplighter        6 W  x27    S1      SM_Neelam_Lt_Uplight   + spot up      (27 placed = plan)
  Bollard light         9 W  x47    S3      SM_Neelam_Lt_Bollard   + point        (37 drawn on the plan -> 37 placed)
  LED strip light      10 W  61 RMT S2      SM_Neelam_Lt_Strip     + points/5 m   (~57 m on the model's garden channels)
  Underwater focus     10 W  x18    S1      SM_Neelam_Lt_PoolLight + spot         (14 drawn on the pool walls -> 14 placed)
  Flood light          60 W  x4     S2      SM_Neelam_Lt_FloodPole + spot 7 m     (diagonal corners of both courts)
  Speakers                   x10    -       SM_Neelam_Speaker
Switch schedule (plan): S1 aesthetic (water feature / uplights) - on after dark, "switched off manually";
  S2 function (strip / floods) - timer 7 pm-10 pm; S3 security (bollards) - 6 pm-6 am.
Runtime: MPC_Neelam_Lighting.Hour is written every frame by UNeelamTimeWidget (C++, time slider 6-22 h);
  Hour < 0 (never written) -> every group falls back to Emissive_MPC.Effects (night factor).
  Light functions M_Neelam_LF_S1/2/3 and the lens material use the same HLSL switch.
Data: Data/amenity_lighting.json (fixtures in world XY, mapped from the PDF region by region onto the deck ortho).
Meshes: Blender/build_amenity_fixtures.py -> Saved/NeelamBridge/fixtures_fbx.
Re-run safe: run() removes everything tagged Neelam_AmenityLighting (and the old Neelam_AmenityLight set) first.
"""
import json, math, os
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
DATA = os.path.join(PROJ, "Scripts/Neelam/Data/amenity_lighting.json")
FBX = os.path.join(PROJ, "Saved/NeelamBridge/fixtures_fbx")
ROOT = "/Game/Neelam/Amenities/Lighting"
MPC_L = ROOT + "/MPC_Neelam_Lighting"
MPC_E = "/Game/ArchVizExplorer/Materials/MPC/Emissive_MPC"
FOLDER = "Neelam/WindTunnel/Amenities/Lighting"
TAG = "Neelam_AmenityLighting"
DECK_C = (5640.0, 4793.0); DECK_YAW = 40.0
WATER_Z = 2473.0

ON_HLSL = """float on = saturate(E);
if (H >= 0.0) {
  if (S > 2.5)      on = max(saturate((H - 18.0) * 6.0), saturate((6.0 - H) * 6.0));   // S3 security 18-06
  else if (S > 1.5) on = saturate((H - 19.0) * 6.0) * saturate((22.0 - H) * 60.0 + 1.0); // S2 function 19-22
}
return on;"""

# LED strips, deck-local cm (image right = +X, down = +Y): snapped onto the garden's path channels
STRIPS = [
    [(-1050, -1912), (-668, -1912)],                                            # outer run, upper-left channel
    [(-535, -1810), (520, -1810), (520, -640)],                                 # outer run, top + east channel
    [(-1213, -1918), (-1213, -1641), (351, -1641), (351, -805), (233, -805), (233, -441)],  # inner run round the lawn
]
# underwater lights: wall normal into the pool (deck-local axis) per fixture index in the json
POOL_DIR = {78: (0, 1), 79: (0, 1), 80: (0, 1), 81: (0, 1), 82: (0, 1), 83: (0, 1), 84: (0, 1),
            85: (1, 0), 86: (0, -1), 87: (0, -1), 88: (0, -1), 89: (0, 1), 90: (1, 0), 91: (0, -1)}
# sunken party lawn (deck-local y -305..625): the plan's edge bollards / speakers sit ON the lawn border; mapped straight they
# landed half on the jogging-track lane on the south side -> both long rows 50 cm inside the lawn edge (x unchanged)
LAWN_EDGE_Y = {i: -255.0 for i in (11, 12, 13, 14, 15, 16, 17, 18, 19, 71, 72, 73)}
LAWN_EDGE_Y.update({i: 575.0 for i in (25, 26, 27, 28, 29, 30, 31, 32, 33, 74, 75, 76)})
# court centres (deck-local) for the flood aim
COURT_BASKET = (1972, -1025); COURT_BLUE = (-230, 155)

def _l2w(lx, ly):
    r = math.radians(DECK_YAW); c, s = math.cos(r), math.sin(r)
    return DECK_C[0] + lx * c - ly * s, DECK_C[1] + lx * s + ly * c

def _w2l(wx, wy):
    r = math.radians(DECK_YAW); c, s = math.cos(r), math.sin(r); dx, dy = wx - DECK_C[0], wy - DECK_C[1]
    return dx * c + dy * s, -dx * s + dy * c

def _actors():
    return {a.get_actor_label(): a for a in EAS.get_all_level_actors()}

# ------------------------------------------------------------------ surfaces
GROUND = ["SM_Amenity_Hardscape", "SM_Amenity_Lawns_Planting", "SM_Amenity_Furniture_Planters", "SM_Amenity_Pools",
          "SM_Podium_Deck_CDE_v2", "SM_Amenity_TrackLanes"]
class Surf:
    def __init__(self):
        A = _actors()
        self.g = [A[n].get_component_by_class(unreal.StaticMeshComponent) for n in GROUND if n in A]
        self.hedge = A["SM_Amenity_Shrubs_Hedges"].get_component_by_class(unreal.StaticMeshComponent)
        self.pool = A["SM_Amenity_Pools"].get_component_by_class(unreal.StaticMeshComponent)
    @staticmethod
    def _t(c, x, y):
        r = c.line_trace_component(unreal.Vector(x, y, 3400), unreal.Vector(x, y, 2300), True, False, False)
        return r[0].z if r else None
    def ground(self, x, y):
        zs = [z for z in (self._t(c, x, y) for c in self.g) if z is not None]
        return max(zs) if zs else 2478.0
    def hedge_top(self, x, y):
        return self._t(self.hedge, x, y)
    def in_pool(self, x, y):
        z = self._t(self.pool, x, y); return z is not None and z < 2465.0
    def pool_floor(self, x, y):
        return self._t(self.pool, x, y)

# ------------------------------------------------------------------ assets
def step_mpc():
    mpc = unreal.load_asset(MPC_L)
    if mpc is None:
        mpc = AT.create_asset("MPC_Neelam_Lighting", ROOT, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    ps = list(mpc.get_editor_property("scalar_parameters"))
    if not any('ParameterName="Hour"' in p.export_text() for p in ps):
        p = unreal.CollectionScalarParameter()
        gid = unreal.GuidLibrary.conv_guid_to_string(unreal.GuidLibrary.new_guid()).replace("-", "")
        p.import_text('(DefaultValue=-1.000000,ParameterName="Hour",Id=%s)' % gid)
        ps.append(p); mpc.set_editor_property("scalar_parameters", ps)
    EAL.save_asset(MPC_L)
    return [p.export_text() for p in mpc.get_editor_property("scalar_parameters")]

def _new_material(name):
    """create, or reuse and empty (re-run safe: keeps references from lights / meshes intact)"""
    path = ROOT + "/Materials/" + name
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else None
    if m is None:
        m = AT.create_asset(name, ROOT + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    else:
        MEL.delete_all_material_expressions(m)
    return m, path

def _on_node(m, s_expr, x, y):
    """custom HLSL on-factor with inputs H (MPC Hour), E (Emissive_MPC Effects), S (switch)"""
    h = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, x - 400, y)
    h.set_editor_property("collection", unreal.load_asset(MPC_L)); h.set_editor_property("parameter_name", "Hour")
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCollectionParameter, x - 400, y + 120)
    e.set_editor_property("collection", unreal.load_asset(MPC_E)); e.set_editor_property("parameter_name", "Effects")
    c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    c.set_editor_property("code", ON_HLSL); c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    c.set_editor_property("desc", "NeelamSwitchOn")
    ins = []
    for nm in ("H", "E", "S"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    c.set_editor_property("inputs", ins)
    MEL.connect_material_expressions(h, "", c, "H"); MEL.connect_material_expressions(e, "", c, "E"); MEL.connect_material_expressions(s_expr, "", c, "S")
    return c

def step_materials():
    out = []
    # light functions S1..S3
    for s in (1, 2, 3):
        m, path = _new_material("M_Neelam_LF_S%d" % s)
        m.set_editor_property("material_domain", unreal.MaterialDomain.MD_LIGHT_FUNCTION)
        k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -700, 300); k.set_editor_property("r", float(s))
        MEL.connect_material_property(_on_node(m, k, -250, 0), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.recompile_material(m); EAL.save_asset(path); out.append(path)
    # lens: emissive = Color x Intensity x on(Switch)
    m, path = _new_material("M_Neelam_FixtureLens")
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -900, -200)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(1.0, 0.72, 0.45, 1))
    inten = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, -50)
    inten.set_editor_property("parameter_name", "Intensity"); inten.set_editor_property("default_value", 30.0)
    sw = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 350)
    sw.set_editor_property("parameter_name", "Switch"); sw.set_editor_property("default_value", 3.0)
    idle = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 500)
    idle.set_editor_property("parameter_name", "OffGlow"); idle.set_editor_property("default_value", 0.0)
    on = _on_node(m, sw, -450, 250)
    mx = MEL.create_material_expression(m, unreal.MaterialExpressionMax, -250, 300)
    MEL.connect_material_expressions(on, "", mx, "A"); MEL.connect_material_expressions(idle, "", mx, "B")
    m1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, -120)
    MEL.connect_material_expressions(col, "", m1, "A"); MEL.connect_material_expressions(inten, "", m1, "B")
    m2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -100, 0)
    MEL.connect_material_expressions(m1, "", m2, "A"); MEL.connect_material_expressions(mx, "", m2, "B")
    MEL.connect_material_property(m2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    bc = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, -350); bc.set_editor_property("constant", unreal.LinearColor(0.62, 0.62, 0.6, 1))
    MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    ro = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, -250); ro.set_editor_property("r", 0.18)
    MEL.connect_material_property(ro, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m); EAL.save_asset(path); out.append(path)
    # body: BaseColor / Metallic / Roughness
    b, bpath = _new_material("M_Neelam_FixtureBody")
    for i, (nm, v) in enumerate((("Metallic", 0.6), ("Roughness", 0.45))):
        p = MEL.create_material_expression(b, unreal.MaterialExpressionScalarParameter, -400, 100 + 120 * i)
        p.set_editor_property("parameter_name", nm); p.set_editor_property("default_value", v)
        MEL.connect_material_property(p, "", unreal.MaterialProperty.MP_METALLIC if nm == "Metallic" else unreal.MaterialProperty.MP_ROUGHNESS)
    p = MEL.create_material_expression(b, unreal.MaterialExpressionVectorParameter, -400, -100)
    p.set_editor_property("parameter_name", "BaseColor"); p.set_editor_property("default_value", unreal.LinearColor(0.03, 0.03, 0.03, 1))
    MEL.connect_material_property(p, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(b); EAL.save_asset(bpath); out.append(bpath)
    # instances
    def mi(name, parent, vec=None, sca=None):
        path = ROOT + "/Materials/" + name
        inst = unreal.load_asset(path) if EAL.does_asset_exist(path) else None
        if inst is None:
            inst = AT.create_asset(name, ROOT + "/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(inst, unreal.load_asset(parent))
        for k, v in (vec or {}).items(): MEL.set_material_instance_vector_parameter_value(inst, k, unreal.LinearColor(*v))
        for k, v in (sca or {}).items(): MEL.set_material_instance_scalar_parameter_value(inst, k, v)
        EAL.save_asset(path); out.append(path)
    L = ROOT + "/Materials/M_Neelam_FixtureLens"; B = ROOT + "/Materials/M_Neelam_FixtureBody"
    WARM = (1.0, 0.70, 0.42, 1); NEUTRAL = (1.0, 0.86, 0.70, 1); COOL = (0.78, 0.93, 1.0, 1)
    mi("MI_Lens_Bollard_S3", L, {"Color": WARM}, {"Intensity": 40.0, "Switch": 3.0})
    mi("MI_Lens_Uplight_S1", L, {"Color": WARM}, {"Intensity": 60.0, "Switch": 1.0})
    mi("MI_Lens_Pool_S1", L, {"Color": COOL}, {"Intensity": 300.0, "Switch": 1.0})   # seen through the pool water
    mi("MI_Lens_Flood_S2", L, {"Color": NEUTRAL}, {"Intensity": 120.0, "Switch": 2.0})
    mi("MI_Lens_Strip_S2", L, {"Color": WARM}, {"Intensity": 30.0, "Switch": 2.0})
    mi("MI_Fixture_Graphite", B, {"BaseColor": (0.022, 0.022, 0.024, 1)}, {"Metallic": 0.55, "Roughness": 0.42})
    mi("MI_Fixture_Steel", B, {"BaseColor": (0.62, 0.62, 0.6, 1)}, {"Metallic": 1.0, "Roughness": 0.25})
    mi("MI_Fixture_Galvanised", B, {"BaseColor": (0.33, 0.34, 0.35, 1)}, {"Metallic": 0.8, "Roughness": 0.5})
    mi("MI_Fixture_Aluminium", B, {"BaseColor": (0.5, 0.5, 0.52, 1)}, {"Metallic": 1.0, "Roughness": 0.35})
    mi("MI_Speaker_Green", B, {"BaseColor": (0.02, 0.035, 0.02, 1)}, {"Metallic": 0.0, "Roughness": 0.6})
    mi("MI_Speaker_Grille", B, {"BaseColor": (0.01, 0.012, 0.01, 1)}, {"Metallic": 0.4, "Roughness": 0.5})
    return out

MESHES = {  # mesh: [slot materials]
    "SM_Neelam_Lt_Bollard": ["MI_Fixture_Graphite", "MI_Lens_Bollard_S3"],
    "SM_Neelam_Lt_Uplight": ["MI_Fixture_Graphite", "MI_Lens_Uplight_S1"],
    "SM_Neelam_Lt_PoolLight": ["MI_Fixture_Steel", "MI_Lens_Pool_S1"],
    "SM_Neelam_Lt_FloodPole": ["MI_Fixture_Galvanised", "MI_Lens_Flood_S2"],
    "SM_Neelam_Speaker": ["MI_Speaker_Green", "MI_Speaker_Grille"],
    "SM_Neelam_Lt_Strip": ["MI_Fixture_Aluminium", "MI_Lens_Strip_S2"],
}

def step_meshes():
    out = {}
    for name, mats in MESHES.items():
        t = unreal.AssetImportTask(); t.filename = os.path.join(FBX, name + ".fbx"); t.destination_path = ROOT + "/Meshes"
        t.destination_name = name; t.automated = True; t.replace_existing = True; t.save = True
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
        ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False
        t.options = ui; AT.import_asset_tasks([t])
        sm = unreal.load_asset(ROOT + "/Meshes/" + name)
        slots = [str(s.material_slot_name) for s in sm.static_materials]
        for i, s in enumerate(slots):
            k = 1 if s in ("Lens", "Grille") else 0
            sm.set_material(i, unreal.load_asset(ROOT + "/Materials/" + mats[k]))
        sm.set_editor_property("light_map_resolution", 16)
        EAL.save_asset(sm.get_path_name()); out[name] = slots
    return out

# ------------------------------------------------------------------ placement
def _clear():
    n = 0
    for a in EAS.get_all_level_actors():
        tags = [str(t) for t in a.tags]
        if TAG in tags or "Neelam_AmenityLight" in tags:
            EAS.destroy_actor(a); n += 1
    return n

def _mesh(name, loc, yaw=0.0, label="", scale=None, pitch=0.0):
    sm = unreal.load_asset(ROOT + "/Meshes/" + name)
    a = EAS.spawn_actor_from_object(sm, loc, unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw))
    c = a.static_mesh_component
    c.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", name not in ("SM_Neelam_Lt_Strip", "SM_Neelam_Lt_PoolLight"))
    if scale: a.set_actor_scale3d(scale)
    a.set_actor_label(label); a.set_folder_path(FOLDER + "/Fixtures"); a.tags = [TAG]
    return a

def _light(cls, loc, rot, lm, radius, kelvin, sw, label, cone=None, src=2.0, color=None):
    a = EAS.spawn_actor_from_class(cls, loc, rot)
    c = a.get_component_by_class(unreal.LocalLightComponent)
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    c.set_editor_property("intensity", lm)
    c.set_editor_property("attenuation_radius", radius)
    c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", kelvin)
    if color: c.set_editor_property("light_color", color)
    c.set_editor_property("cast_shadows", False)
    c.set_editor_property("indirect_lighting_intensity", 0.25)
    c.set_editor_property("source_radius", src)
    c.set_editor_property("light_function_material", unreal.load_asset(ROOT + "/Materials/M_Neelam_LF_S%d" % sw))
    if cone:
        c.set_editor_property("outer_cone_angle", cone); c.set_editor_property("inner_cone_angle", cone * 0.6)
    a.set_actor_label(label); a.set_folder_path(FOLDER + "/Lights"); a.tags = [TAG, "S%d" % sw]
    return a

def step_place():
    d = json.load(open(DATA)); S = Surf(); log = {"bollard": 0, "uplight": 0, "pool": 0, "flood": 0, "speaker": 0, "strip_pieces": 0, "strip_lights": 0, "strip_m": 0.0}
    removed = _clear(); rep = []
    for i, f in enumerate(d["fixtures"]):
        k = f["kind"]; x, y = f["w"]; lx, ly = _w2l(x, y)
        if i in LAWN_EDGE_Y:
            ly = LAWN_EDGE_Y[i]; x, y = _l2w(lx, ly)
        z = S.ground(x, y)
        if k == "bollard":
            _mesh("SM_Neelam_Lt_Bollard", unreal.Vector(x, y, z), DECK_YAW, "AmenLt_Bollard_%02d" % i)
            _light(unreal.PointLight, unreal.Vector(x, y, z + 68), unreal.Rotator(0, 0, 0), 320, 520, 3000, 3, "AmenLt_Bollard_%02d_L" % i, src=5)
        elif k == "uplight":
            ht = S.hedge_top(x, y)
            _mesh("SM_Neelam_Lt_Uplight", unreal.Vector(x, y, z), DECK_YAW, "AmenLt_TreeUp_%02d" % i)
            lz = max(z + 14, (ht or 0) + 6)
            _light(unreal.SpotLight, unreal.Vector(x, y, lz), unreal.Rotator(roll=0, pitch=90, yaw=0), 650, 900, 3000, 1, "AmenLt_TreeUp_%02d_L" % i, cone=28, src=3)
        elif k == "speaker":
            _mesh("SM_Neelam_Speaker", unreal.Vector(x, y, z), DECK_YAW, "AmenLt_Speaker_%02d" % i)
        elif k == "pool":
            ux, uy = POOL_DIR[i]
            # walk along the wall normal (1 cm) to the nearest outside -> inside transition = pool wall
            wall = None
            for s in sorted(range(-45, 61), key=abs):
                ax, ay = _l2w(lx + ux * s, ly + uy * s); bx, by = _l2w(lx + ux * (s - 1), ly + uy * (s - 1))
                if S.in_pool(ax, ay) and not S.in_pool(bx, by): wall = s; break
            if wall is None: rep.append(("pool wall not found", i)); continue
            wx, wy = _l2w(lx + ux * (wall - 0.5), ly + uy * (wall - 0.5))
            floor = S.pool_floor(*_l2w(lx + ux * (wall + 30), ly + uy * (wall + 30))) or 2353.0
            zc = WATER_Z - 45 if floor < 2400 else (WATER_Z + floor) * 0.5
            yaw = DECK_YAW + math.degrees(math.atan2(uy, ux))
            _mesh("SM_Neelam_Lt_PoolLight", unreal.Vector(wx, wy, zc), yaw, "AmenLt_Pool_%02d" % i)
            fx, fy = _l2w(lx + ux * (wall + 6), ly + uy * (wall + 6))
            _light(unreal.SpotLight, unreal.Vector(fx, fy, zc), unreal.Rotator(roll=0, pitch=-8, yaw=yaw), 900, 850, 5600, 1, "AmenLt_Pool_%02d_L" % i, cone=42, src=4)
            rep.append(("pool", i, wall, round(zc, 1), round(floor, 1)))
        elif k == "flood":
            cc = COURT_BASKET if abs(lx - COURT_BASKET[0]) < 1000 else COURT_BLUE
            tx, ty = _l2w(*cc); yaw = math.degrees(math.atan2(ty - y, tx - x))
            _mesh("SM_Neelam_Lt_FloodPole", unreal.Vector(x, y, z), yaw, "AmenLt_Flood_%02d" % i)
            hx, hy = x + 34 * math.cos(math.radians(yaw)), y + 34 * math.sin(math.radians(yaw)); hz = z + 690
            dist = math.hypot(tx - hx, ty - hy); pitch = -math.degrees(math.atan2(hz - (S.ground(tx, ty) + 100), dist))
            _light(unreal.SpotLight, unreal.Vector(hx + 4 * math.cos(math.radians(yaw)), hy + 4 * math.sin(math.radians(yaw)), hz - 4), unreal.Rotator(roll=0, pitch=pitch, yaw=yaw),
                   7200, 4200, 4000, 2, "AmenLt_Flood_%02d_L" % i, cone=48, src=12)
            rep.append(("flood", i, round(yaw, 1), round(pitch, 1), round(dist)))
        log[k] += 1
    # LED strips: pieces <= 1 m along each run, flush with the path; a warm point every ~5 m
    for si, pl in enumerate(STRIPS):
        acc = 0.0; nxt = 150.0
        for (x0, y0), (x1, y1) in zip(pl[:-1], pl[1:]):
            L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(math.ceil(L / 100.0))); seg = L / n
            yaw = DECK_YAW + math.degrees(math.atan2(y1 - y0, x1 - x0))
            for j in range(n):
                t0 = j / n; cxl, cyl_ = x0 + (x1 - x0) * (t0 + 0.5 / n), y0 + (y1 - y0) * (t0 + 0.5 / n)
                sx, sy = _l2w(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0)
                zg = S.ground(*_l2w(cxl, cyl_))
                _mesh("SM_Neelam_Lt_Strip", unreal.Vector(sx, sy, zg - 0.3), yaw, "AmenLt_Strip_%d_%03d" % (si, log["strip_pieces"]), scale=unreal.Vector(seg / 100.0, 1, 1))
                log["strip_pieces"] += 1
            # lights along this run: first at 1.5 m, then every 5 m (cumulative over the run's corners)
            while nxt < acc + L:
                s = nxt - acc; px, py = x0 + (x1 - x0) * s / L, y0 + (y1 - y0) * s / L; wx, wy = _l2w(px, py)
                _light(unreal.PointLight, unreal.Vector(wx, wy, S.ground(wx, wy) + 6), unreal.Rotator(0, 0, 0), 180, 300, 3000, 2,
                       "AmenLt_Strip_%d_L%02d" % (si, log["strip_lights"]), src=20)
                log["strip_lights"] += 1; nxt += 500.0
            acc += L; log["strip_m"] += L / 100.0
    # old low-poly fixture block no longer matches the plan -> hidden (not deleted)
    A = _actors()
    if "SM_Amenity_Lighting_Fixtures" in A:
        o = A["SM_Amenity_Lighting_Fixtures"]; o.set_actor_hidden_in_game(True); o.set_is_temporarily_hidden_in_editor(True)
        o.static_mesh_component.set_editor_property("visible", False)
    unreal.EditorLevelLibrary.save_current_level()
    log["removed_old"] = removed; log["report"] = rep
    return log

def run():
    return {"mpc": step_mpc(), "materials": step_materials(), "meshes": step_meshes(), "place": step_place()}
