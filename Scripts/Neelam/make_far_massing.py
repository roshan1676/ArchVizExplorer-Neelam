"""Context buildings round the FAR landmarks (4 Oct, client: 'landmarks without surroundings'). The grey massing only covers
2.5 km round the site; Billabong, Korum, Singhania, Viviana and Jupiter (3.4-5.3 km) stood on bare map.
Runs inside UE (Windows network for Overpass, CesiumGeoreference for lat/lon -> UE):
OSM buildings within R_M of each far landmark -> Data/osm/buildings_far.json -> Data/massing_far_sel.json (same format as
massing_sel.json; landmark cut-outs excluded, footprints simplified 0.6 m, >= 120 m2).
Then: Massing_PIE.py with SEL=massing_far_sel.json (ground heights) -> make_massing.py logic in make_far_build() ->
Data/massing_far_build.json -> Blender/build_facades.py (all textured) -> Build_Facades.step_import()."""
import json, math, os, urllib.request, urllib.parse
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam"); D = os.path.join(P, "Data")
FAR = ("billabong", "korum", "singhania", "viviana", "jupiter"); R_M = 420
GEO = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(a, unreal.CesiumGeoreference)][0]
def to_xy(la, lo):
    v = GEO.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(lo, la, GEO.get_editor_property("origin_height"))); return v.x, v.y
def area(p): return abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2 / 1e4
def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c
def dp(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1e-9
    i, dm = 0, 0
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + b[0] * a[1] - b[1] * a[0]) / L
        if d > dm: i, dm = k, d
    return dp(pts[:i + 1], eps)[:-1] + dp(pts[i:], eps) if dm > eps else [a, b]

def fetch():
    L = json.load(open(os.path.join(D, "landmarks_phase3.json"), encoding="utf-8"))["landmarks"]
    lms = [l for l in L if l["id"] in FAR]
    q = "[out:json][timeout:90];(%s);out geom tags;" % "".join('way(around:%d,%f,%f)["building"];' % (R_M, l["lat"], l["lon"]) for l in lms)
    data, err = None, None
    for url in ("https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass-api.de/api/interpreter"):
        try:
            data = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "neelam-archviz"}), timeout=90).read()); break
        except Exception as e: err = e
    if data is None: raise RuntimeError(err)
    json.dump(data, open(os.path.join(D, "osm", "buildings_far.json"), "w"))
    have = {b["id"] for b in json.load(open(os.path.join(D, "massing_src.json")))}
    C = json.load(open(os.path.join(D, "cut_polys.json")))
    sel = []
    for w in data["elements"]:
        if w.get("type") != "way" or "geometry" not in w or w["id"] in have: continue
        p = [list(to_xy(g["lat"], g["lon"])) for g in w["geometry"]]
        if p[0] == p[-1]: p = p[:-1]
        if len(p) < 3: continue
        a = area(p); cx = sum(q[0] for q in p) / len(p); cy = sum(q[1] for q in p) / len(p)
        if a < 120 or any(inside(cx, cy, poly) for poly in C.values()): continue
        q = dp(p + [p[0]], 60.0)[:-1]
        if len(q) < 3: q = p
        t = w.get("tags", {}); lv = t.get("building:levels"); h = t.get("height")
        try: h = float(str(h).replace("m", "").strip()) if h else None
        except Exception: h = None
        try: lv = float(lv) if lv else None
        except Exception: lv = None
        sel.append({"id": w["id"], "pts": [[round(x, 1), round(y, 1)] for x, y in q], "area": round(a), "c": [round(cx, 1), round(cy, 1)],
                    "h_osm": h if h else (lv * 3.2 if lv else None), "b": t.get("building", "yes")})
    json.dump(sel, open(os.path.join(D, "massing_far_sel.json"), "w"))
    return {"osm_ways": len(data["elements"]), "selected": len(sel), "with_height": sum(1 for s in sel if s["h_osm"])}

def make_far_build():
    """massing_far_sel + massing_far_heights -> massing_far_build.json (same rules as make_massing.py; all of them get facades)."""
    import random
    S = json.load(open(os.path.join(D, "massing_far_sel.json"))); H = json.load(open(os.path.join(D, "massing_far_heights.json")))
    def guess(b, typ, a):
        r = random.Random(b["id"]).uniform(0.8, 1.2)
        if typ in ("industrial", "warehouse", "roof", "shed", "garage", "construction", "stadium"): return 9.0 * r
        if typ in ("school", "hospital", "public", "temple", "commercial", "retail", "mall"): return 15.0 * r
        if a < 400: return 13.0 * r
        if a < 800: return 19.0 * r
        if a < 1500: return 26.0 * r
        return 30.0 * r
    out = []
    for b in S:
        g = H.get(str(b["id"]))
        if not g: continue
        h = b["h_osm"] if b["h_osm"] and 3 <= b["h_osm"] <= 250 else guess(b, b.get("b") or "yes", b["area"])
        out.append({"id": b["id"], "pts": b["pts"], "base": round(g[0] - 300, 1), "top": round(g[0] + h * 100, 1),
                    "chunk": "%d_%d" % (math.floor(b["c"][0] / 50000), math.floor(b["c"][1] / 50000))})
    json.dump(out, open(os.path.join(D, "massing_far_build.json"), "w"))
    json.dump([o["id"] for o in out], open(os.path.join(D, "massing_far_textured.json"), "w"))
    return len(out)

def import_far():
    """Saved/NeelamBridge/facade_far_fbx/facade_far_*.fbx -> /Game/Neelam/Massing/Facades/Meshes + actors Facade_far_* in the
    ContextFacades folder (only the far actors are replaced; the near facades are untouched)."""
    import glob
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
    DIRF = "/Game/Neelam/Massing/Facades"; FOLDER = "Neelam/ContextFacades"
    SRCF = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "facade_far_fbx")
    mf = unreal.load_asset(DIRF + "/M_Neelam_Facade"); mr = unreal.load_asset(DIRF + "/M_Neelam_Roof")
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith("Facade_far_"): EAS.destroy_actor(a)
    tasks = []
    for f in sorted(glob.glob(os.path.join(SRCF, "facade_far_*.fbx"))):
        t = unreal.AssetImportTask(); t.filename = f; t.destination_path = DIRF + "/Meshes"; t.destination_name = os.path.splitext(os.path.basename(f))[0]
        t.automated = True; t.replace_existing = True; t.save = True
        ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
        sd = ui.static_mesh_import_data; sd.combine_meshes = True; sd.auto_generate_collision = False; sd.generate_lightmap_u_vs = False
        sd.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE
        t.options = ui; tasks.append(t)
    AT.import_asset_tasks(tasks); n = tris = 0
    for t in tasks:
        sm = unreal.load_asset(DIRF + "/Meshes/" + t.destination_name)
        if sm is None: continue
        for i, s in enumerate(sm.static_materials): sm.set_material(i, mr if "Roof" in str(s.material_slot_name) else mf)
        EAL.save_asset(sm.get_path_name()); tris += sm.get_num_triangles(0)
        a = EAS.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        a.set_actor_label("Facade_" + t.destination_name[7:]); a.set_folder_path(FOLDER); a.tags = [unreal.Name("Neelam_Facades")]
        c = a.static_mesh_component; c.set_collision_profile_name("NoCollision"); c.set_editor_property("cast_shadow", True); n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {"chunks": n, "triangles": tris}
