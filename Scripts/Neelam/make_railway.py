"""Central Railway line + Mulund station in 3D (4 Oct, client: 'railway is just a flat photo').
Runs inside UE (Overpass via Windows network, CesiumGeoreference for lat/lon -> UE):
fetch() -> Data/osm/railway.json (raw) + Data/railway.json {rails, platforms, stations, bridges} in UE cm, R_M round the site."""
import json, math, os, urllib.request, urllib.parse
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam"); D = os.path.join(P, "Data")
R_M = 2700; SITE_UE = (944.0 * 100 / 100, 4429.0)
def _geo():
    return [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(a, unreal.CesiumGeoreference)][0]
def fetch():
    G = _geo(); oh = G.get_editor_property("origin_height")
    ll = G.transform_unreal_position_to_longitude_latitude_height(unreal.Vector(SITE_UE[0], SITE_UE[1], 0))
    la, lo = ll.y, ll.x
    dla = R_M / 110540.0; dlo = R_M / (111320.0 * math.cos(math.radians(la)))
    bb = "%f,%f,%f,%f" % (la - dla, lo - dlo, la + dla, lo + dlo)
    q = ("[out:json][timeout:90][bbox:%s];(way[railway];way[building=train_station];way[public_transport=platform];"
         "way[highway=footway][bridge];);out geom tags;") % bb
    data, err = None, None
    for url in ("https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass-api.de/api/interpreter"):
        try:
            data = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": "neelam-archviz"}), timeout=120).read()); break
        except Exception as e: err = e
    if data is None: raise RuntimeError(err)
    json.dump(data, open(os.path.join(D, "osm", "railway.json"), "w"))
    def xy(g):
        v = G.transform_longitude_latitude_height_position_to_unreal(unreal.Vector(g["lon"], g["lat"], oh)); return [round(v.x, 1), round(v.y, 1)]
    out = {"rails": [], "platforms": [], "stations": [], "bridges": []}
    for w in data["elements"]:
        if w.get("type") != "way" or "geometry" not in w: continue
        t = w.get("tags", {}); pts = [xy(g) for g in w["geometry"]]
        rec = {"id": w["id"], "pts": pts, "tags": t}
        if t.get("railway") == "rail" and t.get("service") not in ("yard", "siding", "spur") or t.get("railway") == "rail" and len(pts) > 30: out["rails"].append(rec)
        elif t.get("railway") in ("platform", "platform_edge") or t.get("public_transport") == "platform": out["platforms"].append(rec)
        elif t.get("building") in ("train_station", "transportation") or t.get("railway") == "station": out["stations"].append(rec)
        elif t.get("highway"): out["bridges"].append(rec)
    json.dump(out, open(os.path.join(D, "railway.json"), "w"))
    return {k: len(v) for k, v in out.items()} | {"site_ll": [la, lo]}
