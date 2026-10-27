import json, urllib.request, time, os
fit = json.load(open("_ue_latlon_fit.json"))
def latlon(x, y): return (y - fit["cy"][1]) / fit["cy"][0], (x - fit["cx"][1]) / fit["cx"][0]
out = json.load(open("_massing_dem.json")) if os.path.exists("_massing_dem.json") else {}
for fname in ("massing_far_build.json", "massing_build.json"):
    if fname in out and len(out[fname]) == len(json.load(open(fname))): continue
    B = json.load(open(fname)); elev = out.get(fname, [])
    pts = [latlon(sum(p[0] for p in b["pts"]) / len(b["pts"]), sum(p[1] for p in b["pts"]) / len(b["pts"])) for b in B]
    for i in range(len(elev), len(pts), 50):
        q = pts[i:i + 50]
        u = "https://api.open-meteo.com/v1/elevation?latitude=%s&longitude=%s" % (",".join("%.5f" % p[0] for p in q), ",".join("%.5f" % p[1] for p in q))
        while True:
            try: elev += json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "neelam-archviz"}), timeout=30).read())["elevation"]; break
            except Exception as e: print("wait", e, flush=True); time.sleep(65)
        out[fname] = elev; json.dump(out, open("_massing_dem.json", "w")); time.sleep(6)
    print(fname, len(elev), flush=True)
print("DEM_DONE", flush=True)
