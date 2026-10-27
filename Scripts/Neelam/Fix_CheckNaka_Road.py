"""Check Naka toll plaza: the EEH deck looked broken (client 27 Oct). Plain Python (no UE): edits Data/road_build.json.
- rd_1327359091 + rd_1327359093 (northbound) and rd_1327359092 (southbound) dipped ~2 m at the plaza (photogrammetry pit)
  -> deck sank under the map tiles. Pits filled (each point = min(max left, max right) along the chain); `ground`
  stays, so the side walls still reach the real surface.
- rd_1327359091 was 15 m wide next to 17.5 m pieces -> 17.5.
- northbound started 46 m short of the southbound end -> extended south to the same latitude.
Then: Blender/build_roads.py on Data/road_checknaka.json (--split) and Fix_CheckNaka_Import.py (UE)."""
import json, math, os, shutil
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
P = os.path.join(D, "road_build.json")
if not os.path.exists(P + ".pre_checknaka"): shutil.copy(P, P + ".pre_checknaka")
J = json.load(open(P)); R = J["roads"]
NB, SB = ["rd_1327359091", "rd_1327359093"], ["rd_1327359092"]


def fill_pits(chain):
    z = [p[2] for k in chain for p in R[k]["pts"]]
    lm = [max(z[:i + 1]) for i in range(len(z))]; rm = [max(z[i:]) for i in range(len(z))]
    f = [max(z[i], min(lm[i], rm[i])) for i in range(len(z))]
    i = 0
    for k in chain:
        for p in R[k]["pts"]: p[2] = f[i]; i += 1
    return max(a - b for a, b in zip(f, z))


r = R["rd_1327359091"]
if r["width_m"] != 17.5: r["width_m"] = 17.5
end_y = R["rd_1327359092"]["pts"][-1][1]
p0, p1 = r["pts"][0], r["pts"][1]
if p0[1] > end_y + 500:                                   # extend the northbound start south (once)
    dx, dy = p0[0] - p1[0], p0[1] - p1[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    n = int((p0[1] - end_y) / -uy / 1000) + 1
    new = [[p0[0] + ux * 1000 * s, p0[1] + uy * 1000 * s, p0[2]] for s in range(n, 0, -1)]
    r["pts"] = new + r["pts"]; r["ground"] = [p0[2]] * len(new) + r["ground"]
lift = {"NB": fill_pits(NB), "SB": fill_pits(SB)}
json.dump(J, open(P, "w"))
json.dump({"roads": {k: R[k] for k in NB + SB}}, open(os.path.join(D, "road_checknaka.json"), "w"))
print("max lift cm", lift, "NB start", [round(v) for v in r["pts"][0]], "SB end", [round(v) for v in R["rd_1327359092"]["pts"][-1]])
