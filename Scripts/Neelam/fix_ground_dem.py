"""Re-seat floating context buildings on the real terrain (client 27 Oct: "buildings are flying").
1518 of 3305 blocks never got a traced ground (not in Data/massing_heights.json) and used a 5-nearest-neighbour guess,
which floats tens of metres on uneven ground. Ground here = Copernicus DEM via Open-Meteo (Data/_massing_dem.json from
Data/_dem_fetch.py), calibrated to the traced buildings (median offset). A block is re-seated when its ground was a guess
OR it sits > FLOAT_M above the DEM ground. Height (top - base) is kept. Writes Data/massing_build.json (backup *_pre_dem).
Then: Blender/build_facades.py + Build_Facades.step_import() (all blocks are facade blocks now)."""
import json, os, shutil, numpy as np
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
FLOAT_M = 8.0
B = json.load(open(os.path.join(D, "massing_build.json"))); H = json.load(open(os.path.join(D, "massing_heights.json")))
dem = json.load(open(os.path.join(D, "_massing_dem.json")))["massing_build.json"]
assert len(dem) == len(B), "DEM incomplete: %d of %d" % (len(dem), len(B))
off = float(np.median([H[str(b["id"])][0] - 100 * e for b, e in zip(B, dem) if str(b["id"]) in H]))
bak = os.path.join(D, "massing_build_pre_dem.json")
if not os.path.exists(bak): shutil.copy(os.path.join(D, "massing_build.json"), bak)
moved, drops = 0, []
for b, e in zip(B, dem):
    g = 100 * e + off                       # DEM ground, UE cm
    cur = b["base"] + 300                   # base sits 3 m below the ground it was given
    if str(b["id"]) not in H or cur - g > FLOAT_M * 100:
        h = b["top"] - b["base"]; b["base"] = g - 300; b["top"] = b["base"] + h
        drops.append((cur - g) / 100); moved += 1
json.dump(B, open(os.path.join(D, "massing_build.json"), "w"))
d = np.array(drops)
print("calib %.0f cm | re-seated %d | change m: median %.1f  max drop %.1f  max raise %.1f" % (off, moved, np.median(d), d.max(), -d.min()))
