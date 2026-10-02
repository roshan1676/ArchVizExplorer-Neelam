"""Floor View + flat tour setup (runs inside UE via NeelamBridge). Re-runnable.
   step_material()  M_Neelam_FloorBox
   step_towers()    5 x NeelamTowerFloors actors from the real floor modules
   step_tables()    DT_Neelam_UnitTypes / DT_Neelam_Flats (+ struct-driven, edit in the editor)
   step_manager()   NeelamFlatTour actor
"""
import json, os, collections
import unreal

FV = "/Game/Neelam/FloorView"
TEX = FV + "/Textures"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

def _asset(path, cls, factory):
    a = unreal.load_asset(path) if EAL.does_asset_exist(path) else unreal.find_object(None, path + "." + path.rsplit("/", 1)[1])
    if a:
        return a
    folder, name = path.rsplit("/", 1)
    return AT.create_asset(name, folder, cls, factory)

# ------------------------------------------------------------------ material
def step_material():
    path = FV + "/Materials/M_Neelam_FloorBox"
    m = _asset(path, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", False)
    m.set_editor_property("used_with_instanced_static_meshes", True)
    m.set_editor_property("translucency_pass", unreal.MaterialTranslucencyPass.MTP_AFTER_DOF)
    cd = MEL.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData, -700, 0)
    cd.set_editor_property("data_index", 0)
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -700, 200)
    def custom(code, out_type, y, desc):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -350, y)
        c.set_editor_property("code", code)
        c.set_editor_property("output_type", out_type)
        c.set_editor_property("description", desc)
        ins = []
        for nm in ("S", "UV"):
            ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
        c.set_editor_property("inputs", ins)
        MEL.connect_material_expressions(cd, "", c, "S")
        MEL.connect_material_expressions(uv, "", c, "UV")
        return c
    edge = ("float2 d = abs(UV - 0.5) * 2.0; float e = max(d.x, d.y);"
            "float ed = smoothstep(0.90, 0.985, e);")
    em = custom(edge + "float3 idle = float3(0.95, 0.90, 0.80); float3 sel = float3(0.78, 0.55, 0.22);"
                "float3 c = lerp(idle, sel, saturate(S - 0.6));"
                "return c * (1.2 + 2.2 * saturate(S) + ed * (3.0 + 3.0 * saturate(S)));",
                unreal.CustomMaterialOutputType.CMOT_FLOAT3, 0, "FloorBoxEmissive")
    op = custom(edge + "float mask = saturate((S + 0.5) * 10.0);"
                "float body = saturate(0.05 + 0.20 * S);"
                "float rim = ed * saturate(0.30 + 0.35 * S);"
                "return saturate(body + rim) * mask;",
                unreal.CustomMaterialOutputType.CMOT_FLOAT1, 250, "FloorBoxOpacity")
    gain = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -350, -200)
    gain.set_editor_property("parameter_name", "Brightness"); gain.set_editor_property("default_value", 260.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -120, 0)
    MEL.connect_material_expressions(em, "", mul, "A"); MEL.connect_material_expressions(gain, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_asset(path)
    return path

# ------------------------------------------------------------------ towers
def _root():
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == "Neelam_WindTunnel_Root":
            return a
    raise RuntimeError("Neelam_WindTunnel_Root not found")

def step_towers():
    root = _root()
    rt = root.get_actor_transform()
    inv = rt.inverse()
    per = collections.defaultdict(list)
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        sm = a.static_mesh_component.static_mesh
        if not sm:
            continue
        n = sm.get_name()
        if not (n.startswith("SM_Tower") and "_Floor_" in n and n.endswith("_Shell")):
            continue
        tw = n.split("_")[1][-1]                       # A..E
        if tw not in INTERACTIVE_TOWERS:
            continue
        kind = n.split("_Floor_")[1].split("_")[0]     # PodiumTop / Refuge / Typical
        loc = unreal.MathLibrary.transform_location(inv, a.get_actor_location())
        bb = sm.get_bounding_box()
        mn, mx = bb.min, bb.max
        per[tw].append(dict(kind=kind, x0=loc.x + mn.x, x1=loc.x + mx.x, y0=loc.y + mn.y, y1=loc.y + mx.y, z0=loc.z + mn.z, z1=loc.z + mx.z))
    mat = unreal.load_asset(FV + "/Materials/M_Neelam_FloorBox")
    # remove old ones
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_class().get_name() == "NeelamTowerFloors":
            a.destroy_actor()
    out = {}
    for order, tw in enumerate(sorted(per)):
        fl = sorted(per[tw], key=lambda f: f["z0"])
        typ = [f for f in fl if f["kind"] == "Typical"] or fl
        x0 = min(f["x0"] for f in typ); x1 = max(f["x1"] for f in typ)
        y0 = min(f["y0"] for f in typ); y1 = max(f["y1"] for f in typ)
        floors = []
        num = 0
        for i, f in enumerate(fl):
            top = fl[i + 1]["z0"] if i + 1 < len(fl) else f["z0"] + 320.0
            fr = unreal.NeelamFloor()
            if f["kind"] == "PodiumTop":
                fr.set_editor_property("number", 0); fr.set_editor_property("label", "Podium level")
                fr.set_editor_property("residential", False)
            else:
                num += 1
                fr.set_editor_property("number", num)
                fr.set_editor_property("label", "Floor %d" % num + ("  (Refuge)" if f["kind"] == "Refuge" else ""))
                fr.set_editor_property("residential", f["kind"] != "Refuge")
            fr.set_editor_property("bottom_z", f["z0"])
            fr.set_editor_property("height", max(200.0, top - f["z0"]))
            floors.append(fr)
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.NeelamTowerFloors, rt.translation, rt.rotation.rotator())
        act.set_actor_label("Neelam_FloorView_Tower" + tw)
        act.set_folder_path("Neelam/FloorView")
        act.set_editor_property("tower_id", tw)
        act.set_editor_property("display_name", "Tower " + tw)
        act.set_editor_property("sort_order", order)
        act.set_editor_property("footprint_center", unreal.Vector2D((x0 + x1) / 2, (y0 + y1) / 2))
        act.set_editor_property("footprint_half_size", unreal.Vector2D((x1 - x0) / 2, (y1 - y0) / 2))
        act.set_editor_property("floors", floors)
        act.set_editor_property("box_material", mat)
        act.rebuild_boxes()
        out[tw] = dict(floors=len(floors), residential=sum(1 for f in floors if f.get_editor_property("residential")),
                       half=[round((x1 - x0) / 2), round((y1 - y0) / 2)])
    return out

# ------------------------------------------------------------------ data tables
def _soft(path):
    return path  # soft object refs are written as strings in the JSON import

UNIT_TYPES = {
    "2BHK": dict(DisplayName="2 BHK", AreaText="RERA 652.54 sq.ft (incl. balcony)", FloorPlan=TEX + "/T_FloorPlan_2BHK.T_FloorPlan_2BHK",
                 StartRoom=0, Accent=dict(R=0.12, G=0.5, B=1.0, A=1.0),
                 Rooms=[("Living", "T_Pano_2BHK_Living", False, (0.38, 0.17), 0),
                        ("Dining", "T_Pano_2BHK_Dining", False, (0.30, 0.08), 0),
                        ("Balcony", "T_Pano_2BHK_Living", True, (0.89, 0.22), 0),
                        ("Kitchen", "T_Pano_Kitchen_A", False, (0.70, 0.40), 0),
                        ("Bedroom 2", "T_Pano_2BHK_Bedroom2", False, (0.73, 0.63), 0),
                        ("Master Bedroom", "T_Pano_2BHK_MasterBedroom", False, (0.62, 0.88), 0)]),
    "3BHK": dict(DisplayName="3 BHK", AreaText="RERA 855.86 sq.ft (incl. balcony)", FloorPlan=TEX + "/T_FloorPlan_3BHK.T_FloorPlan_3BHK",
                 StartRoom=0, Accent=dict(R=0.55, G=0.35, B=1.0, A=1.0),
                 Rooms=[("Living", "T_Pano_3BHK_Living", False, (0.42, 0.82), 0),
                        ("Dining", "T_Pano_3BHK_Dining", False, (0.60, 0.72), 0),
                        ("Balcony", "T_Pano_3BHK_Living", True, (0.13, 0.88), 0),
                        ("Kitchen", "T_Pano_Kitchen_A", False, (0.30, 0.65), 0),
                        ("Bedroom 1", "T_Pano_3BHK_Bedroom1", False, (0.81, 0.28), 0),
                        ("Bedroom 2", "T_Pano_3BHK_Bedroom2", False, (0.26, 0.19), 0),
                        ("Bedroom 3", "T_Pano_3BHK_Bedroom3", False, (0.30, 0.44), 0)]),
}
# top floor (client 2 Oct): no flat plan, one 360 from the top of the building.
# Balcony rule: own BalconyPanorama = 360 (use T_Pano_TopFloor for any flat on floor 41); empty = photo gallery (Balcony_Views.py)
UNIT_TYPES["TOPVIEW"] = dict(DisplayName="Top Floor View", AreaText="360° view from the top of Tower E", FloorPlan="",
                             StartRoom=0, Accent=dict(R=0.578, G=0.397, B=0.144, A=1.0),
                             Rooms=[("Top Floor 360°", "T_Pano_TopFloor", False, (0.5, 0.5), 0)])
# two test flats, middle of Tower E (30 Sep: client - only Tower E is interactive; C/D showcase, A/B removed ->
# "Upcoming project" label). One 2BHK + one 3BHK; balcony panoramas are still the temp C-2001/C-2002 images.
FLATS = {
    "E_20_01": dict(Tower="E", Floor=20, FlatNumber="E-2001", UnitType="2BHK", Status="Available", Facing="East",
                    BalconyPanorama="", FacadeYaw=-90.0, FacadeOffset=-700.0),
    "E_20_02": dict(Tower="E", Floor=20, FlatNumber="E-2002", UnitType="3BHK", Status="Available", Facing="East",
                    BalconyPanorama="", FacadeYaw=-90.0, FacadeOffset=700.0),
}
FLATS["E_41_TOP"] = dict(Tower="E", Floor=41, FlatNumber="Top Floor View", UnitType="TOPVIEW", Status="Available", Facing="360°",
                         BalconyPanorama="T_Pano_TopFloor", FacadeYaw=-90.0, FacadeOffset=0.0)
INTERACTIVE_TOWERS = ("E",)      # step_towers only builds floor boxes for these

def _tex(n):
    return "%s/%s.%s" % (TEX, n, n)

def step_tables():
    res = {}
    f = unreal.DataTableFactory(); f.set_editor_property("struct", unreal.NeelamUnitTypeRow.static_struct())
    dt = _asset(FV + "/Data/DT_Neelam_UnitTypes", unreal.DataTable, f)
    rows = []
    for k, v in UNIT_TYPES.items():
        rows.append(dict(Name=k, DisplayName=v["DisplayName"], AreaText=v["AreaText"], FloorPlan=v["FloorPlan"],
                         StartRoom=v["StartRoom"], Accent=v["Accent"],
                         Rooms=[dict(Name=n, Panorama=_tex(t), bUseFlatBalcony=b, PlanPosition=dict(X=p[0], Y=p[1]), StartYaw=y)
                                for (n, t, b, p, y) in v["Rooms"]]))
    res["unit_types"] = unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(rows))
    EAL.save_asset(FV + "/Data/DT_Neelam_UnitTypes")
    f2 = unreal.DataTableFactory(); f2.set_editor_property("struct", unreal.NeelamFlatRow.static_struct())
    dt2 = _asset(FV + "/Data/DT_Neelam_Flats", unreal.DataTable, f2)
    rows = []
    for k, v in FLATS.items():
        r = dict(v); r["Name"] = k; r["BalconyPanorama"] = _tex(v["BalconyPanorama"]) if v["BalconyPanorama"] else ""; rows.append(r)
    res["flats"] = unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt2, json.dumps(rows))
    EAL.save_asset(FV + "/Data/DT_Neelam_Flats")
    res["rows"] = [str(n) for n in unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)] + \
                  [str(n) for n in unreal.DataTableFunctionLibrary.get_data_table_row_names(dt2)]
    return res

def step_manager():
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_class().get_name() == "NeelamFlatTour":
            a.destroy_actor()
    m = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.NeelamFlatTour, unreal.Vector(0, 0, 0))
    m.set_actor_label("Neelam_FlatTour")
    m.set_folder_path("Neelam/FloorView")
    m.set_editor_property("flats_table", unreal.load_asset(FV + "/Data/DT_Neelam_Flats"))
    m.set_editor_property("unit_types_table", unreal.load_asset(FV + "/Data/DT_Neelam_UnitTypes"))
    fv = unreal.load_asset(FV + "/UI/WBP_Neelam_FloorView")
    tw = unreal.load_asset(FV + "/UI/WBP_Neelam_Tour")
    if fv: m.set_editor_property("floor_view_widget_class", fv.generated_class())
    if tw: m.set_editor_property("tour_widget_class", tw.generated_class())
    return m.get_name()
