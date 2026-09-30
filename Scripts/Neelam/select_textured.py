"""Which grey massing blocks get realistic facades (30 Sep, client): everything around the site (<= NEAR_M from the
site centre) + a few tall landmark blocks further out (>= TALL_M high, <= FAR_M). -> Data/massing_textured.json
(ids). Blender/build_facades.py builds them textured, Blender/build_massing.py skips them."""
import json, math, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
SITE = (4500.0, 3500.0)          # UE cm, amenity deck / towers
NEAR_M, FAR_M, TALL_M = 650.0, 1300.0, 45.0
B = json.load(open(os.path.join(D, "massing_build.json")))
sel, near, far = [], 0, 0
for b in B:
    xs = [p[0] for p in b["pts"]]; ys = [p[1] for p in b["pts"]]
    d = math.hypot(sum(xs) / len(xs) - SITE[0], sum(ys) / len(ys) - SITE[1]) / 100.0
    h = (b["top"] - b["base"] - 300.0) / 100.0
    if d <= NEAR_M: sel.append(b["id"]); near += 1
    elif d <= FAR_M and h >= TALL_M: sel.append(b["id"]); far += 1
json.dump(sel, open(os.path.join(D, "massing_textured.json"), "w"))
print(len(sel), "textured (near", near, "far landmarks", far, ")")
