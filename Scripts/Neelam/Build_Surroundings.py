"""Neelam - surroundings / connectivity builder (run INSIDE Unreal via the bridge).
Reads Data/landmarks_<phase>.json + Data/connectivity_<phase>.json and creates, per phase:
  * BP_POI pins (3D label, icon, info card 'distance · drive time', category tags for the Surroundings lists)
  * BP_Route drive routes site -> landmark (category colour, toggled with the category list)
  * BP_Route glow lines + BP_POI name labels for key roads
  * BP_RoadTool pole lights / night light-trails along selected roads
Everything goes to Outliner folder Neelam/Surroundings/<phase>; re-running a phase replaces it."""
import json, os, sys, importlib, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
sys.path.insert(0, P)
import connectivity_lib as C; importlib.reload(C)
import poi_highlight as H; importlib.reload(H)
PHASE = globals().get("NEELAM_PHASE", "phase2")
L = json.load(open(os.path.join(P, "Data", "landmarks_%s.json" % PHASE)))
G = json.load(open(os.path.join(P, "Data", "connectivity_%s.json" % PHASE)))
EAL = unreal.EditorAssetLibrary
POI = EAL.load_blueprint_class("/Game/ArchVizExplorer/Blueprints/BP_POI")
ROUTE = EAL.load_blueprint_class("/Game/ArchVizExplorer/Blueprints/BP_Route")
ROAD = EAL.load_blueprint_class("/Game/ArchVizExplorer/Blueprints/BP_RoadTool")
FOLDER = "Neelam/Surroundings/" + PHASE
ICONS = "/Game/ArchVizExplorer/Textures/UI/Icons/"
ROUTE_LIFT, LABEL_LIFT = globals().get("NEELAM_ROUTE_LIFT", 250.0), 0.0
report = {"pois": [], "routes": [], "roads": [], "poles": []}

for a in [a for a in C.EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]:
    C.EAS.destroy_actor(a)


def txt(s):
    return 'INVTEXT("%s")' % s.replace('"', "'")


def set_info(poi, name, info, footer, color, icon):
    s = poi.get_editor_property("POI_Info_Struct")
    ico = ("\"/Script/Engine.Texture2D'%s%s.%s'\"" % (ICONS, icon, icon)) if icon else "None"
    s.import_text("(Name_25_4748782941ED18FE2304D484A513143E=%s,Information_27_C6F10FCE43C331CB9E996BA1CC9C8519=%s,"
                  "Footer_48_614C73F541F0F937071671A9E3E3A90B=\"%s\",Color_31_7C59AD004573552ECE0FA9BA31C6F514=(R=%f,G=%f,B=%f,A=1.0),"
                  "Icon_34_E4C0A1FB4BCEA6793DD975B5EE116A1C=%s)" % (txt(name), txt(info), footer.replace('"', "'"), color[0], color[1], color[2], ico))
    poi.set_editor_property("POI_Info_Struct", s)


def spawn_poi(label, lat, lon, name, info, footer, cat, icon, lift=0.0):
    v, ok = C.to_ue(lat, lon)
    a = C.EAS.spawn_actor_from_class(POI, unreal.Vector(v.x, v.y, v.z + lift))
    a.set_actor_label(label); a.set_folder_path(FOLDER)
    cc = L["categories"][cat]
    set_info(a, name, info, footer, cc["color"], icon)
    a.set_editor_property("Widget_Text_Color", unreal.LinearColor(1, 1, 1, 1))
    a.tags = [unreal.Name(t) for t in cc["tags"] + ["Surroundings", "Neelam_Surroundings", "Neelam_" + cat]]
    return a, ok


def build_spline(actor, pts, lift, pid=None):
    if pid:   # precise: max real surface over both neighbouring segments (Surface_Align.py) -> never under the map
        vs, _ = C.envelope_z(pid, pts, list(range(len(pts))), lift)
    else:
        vs = [unreal.Vector(v.x, v.y, v.z + lift) for v in C.smooth_z([C.to_ue(la, lo)[0] for la, lo in pts])]
    spl = actor.get_component_by_class(unreal.SplineComponent)
    spl.clear_spline_points(False)
    for v in vs:
        spl.add_spline_point(v, unreal.SplineCoordinateSpace.WORLD, False)
    spl.update_spline()
    for p in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: spl.set_editor_property(p, True)
        except Exception: pass
    return vs


def spawn_route(label, pts, cat, width=7.0, pid=None):
    v0 = C.to_ue(*pts[0])[0]
    a = C.EAS.spawn_actor_from_class(ROUTE, v0)
    a.set_actor_label(label); a.set_folder_path(FOLDER)
    build_spline(a, pts, ROUTE_LIFT, pid)
    a.set_editor_property("Scale_X", width)          # BP_Route: Scale_X = ribbon width (m), Scale_Y = thickness
    a.set_editor_property("Scale_Y", 1.0)
    col = L["categories"][cat]["color"]
    a.set_editor_property("Route_Color", unreal.LinearColor(col[0], col[1], col[2], 1))      # also re-runs construction
    a.tags = [unreal.Name(t) for t in L["categories"][cat]["tags"] + ["Surroundings", "Neelam_Surroundings", "Neelam_" + cat]]
    return a, len(a.get_components_by_class(unreal.SplineMeshComponent))


# ---- landmarks + drive routes
for lm in L["landmarks"]:
    r = G["routes"].get(lm["id"])
    drive = ("%s min drive (%.1f km)" % (int(round(r["min"])) or 1, r["km_route"])) if r else ""
    info = " · ".join(x for x in (lm["dist"], drive) if x)
    a, ok = spawn_poi("POI_" + lm["id"], lm["lat"], lm["lon"], lm["name"], info, lm.get("about", ""), lm["cat"], lm.get("icon"))
    report["pois"].append([lm["name"], info, ok])
    report.setdefault("boxes", []).append(H.apply(C, a, lm, r["pts"] if r else None))
    if r:
        ra, n = spawn_route("Route_" + lm["id"], r["pts"], lm["cat"], pid="route_" + lm["id"])
        report["routes"].append([lm["id"], n])

# ---- key roads: glow line + name label (+ poles / light trails)
for rd in L["roads"]:
    g = G["roads"][rd["id"]]
    ra, n = spawn_route("Road_" + rd["id"], g["pts"], rd["cat"], width=12.0, pid="road_" + rd["id"])
    mid = g["pts"][len(g["pts"]) // 2]
    spawn_poi("Label_" + rd["id"], mid[0], mid[1], rd["label"], rd["dist"], "%.1f km shown" % g["km"], rd["cat"], "T_Icon_Place_01")
    report["roads"].append([rd["id"], n])
    if rd.get("poles"):
        v0 = C.to_ue(*g["pts"][0])[0]
        t = C.EAS.spawn_actor_from_class(ROAD, v0)
        t.set_actor_label("Poles_" + rd["id"]); t.set_folder_path(FOLDER)
        build_spline(t, g["pts"], globals().get("NEELAM_POLE_LIFT", -30.0), "road_" + rd["id"])
        for k, val in (("DrawSplinePointNumbers?", False), ("CenterOffset_LightPoles", float(rd["poles"]["offset"])),
                       ("Spacing_LightPoles", float(rd["poles"]["spacing"])), ("Collision_Road?", False),
                       ("Width_Road", 0.01)):                     # poles only - the traffic strip is Build_Traffic.py
            t.set_editor_property(k, val)
        t.set_editor_property("Build_LightPoles?", True)                              # last: re-runs construction
        poles = [a for a in C.EAS.get_all_level_actors() if a.get_class().get_name() == "BP_Pole_C" and a.get_attach_parent_actor() == t]
        report["poles"].append([rd["id"], len(poles)])
result = report
