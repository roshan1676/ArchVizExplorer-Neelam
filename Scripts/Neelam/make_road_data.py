"""road_surface.json -> Data/road_build.json: per carriageway a smoothed centreline (UE cm) with road-surface Z.
Surface = 2nd-lowest of the 5 cross traces (skips the photogrammetry cars), gaps interpolated, then median(7) +
mean(5) along the road so the deck is smooth. Runs anywhere (pure python)."""
import json, os, math
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
R = json.load(open(os.path.join(D, "road_surface.json")))
out = {"roads": {}, "rings": {}}
def fill(v):
    good = [i for i, q in enumerate(v) if q is not None]
    if not good: return None
    for i in range(len(v)):
        if v[i] is None:
            a = max([g for g in good if g < i], default=None); b = min([g for g in good if g > i], default=None)
            v[i] = v[b] if a is None else v[a] if b is None else v[a] + (v[b] - v[a]) * (i - a) / (b - a)
    return v
for k, it in R.items():
    if it["kind"] == "road":
        z = []
        for zs in it["z"]:
            vals = sorted(q for q in (zs or []) if q is not None)
            z.append(vals[1] if len(vals) >= 3 else (vals[0] if vals else None))
        z = fill(z)
        if z is None: continue
        med = [sorted(z[max(0, i - 3): i + 4])[len(z[max(0, i - 3): i + 4]) // 2] for i in range(len(z))]
        sm = [sum(med[max(0, i - 2): i + 3]) / len(med[max(0, i - 2): i + 3]) for i in range(len(med))]
        pts = [[round(d[1], 1), round(d[2], 1), round(zz, 1)] for d, zz in zip(it["dense"], sm)]
        out["roads"][k] = {"group": it["group"], "lanes": it["lanes"], "width_m": it["width_m"], "bridge": it["bridge"], "name": it["name"], "pts": pts}
    else:
        zs = [zz[0] for zz in it["z"] if zz and zz[0] is not None]
        zs.sort()
        out["rings"][k[3:]] = {"ground_p15": zs[len(zs) * 15 // 100] if zs else None, "ground_min": zs[0] if zs else None, "n": len(zs),
                               "center": it["center"], "yaw_deg": it["yaw_deg"], "w_m": it["w_m"], "d_m": it["d_m"]}
json.dump(out, open(os.path.join(D, "road_build.json"), "w"))
print(len(out["roads"]), "carriageways,", sum(len(v["pts"]) for v in out["roads"].values()), "pts;", {k: (v["n"], v["ground_p15"]) for k, v in out["rings"].items()})
