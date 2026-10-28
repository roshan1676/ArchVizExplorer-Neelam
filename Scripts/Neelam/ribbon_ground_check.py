"""Offline (plain py): every ribbon sample vs its REAL ground (27 Oct). Ground = our road deck (road_build.json centreline
z + 12 cm) where the ribbon runs ALONG that carriageway (within its half width + 1 m, direction within 25 deg - so a
road crossing under / over a flyover is not mistaken for the ribbon's own deck), else the traced map (ribbon_surface.json).
Inputs: Data/ribbon_surface.json, Data/ribbon_z_now.json (UE dump), Data/road_build.json.
Writes Data/ribbon_ground.json {label: {"g": [cm|None], "deck": [road id|None]}}. Prints buried / floating spots.
  py ribbon_ground_check.py            -> report
  py ribbon_ground_check.py --selftest -> asserts on a synthetic road"""
import json, math, os, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
DECK = 12.0


def deck_z(roads, x, y, tx, ty):
    """deck top under (x, y) of a carriageway the ribbon runs along (direction tx, ty), else None"""
    best = None
    for rid, r in roads:
        half = r["width_m"] * 50 + 100; P = r["pts"]
        if not (r["bb"][0] - half <= x <= r["bb"][2] + half and r["bb"][1] - half <= y <= r["bb"][3] + half): continue
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]; dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
            if L2 < 1: continue
            t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
            dist = math.hypot(a[0] + t * dx - x, a[1] + t * dy - y)
            if dist > half: continue
            L = math.sqrt(L2)
            if abs(dx / L * tx + dy / L * ty) < math.cos(math.radians(25)): continue
            z = a[2] + t * (b[2] - a[2]) + DECK
            if best is None or dist < best[0]: best = (dist, z, rid)
    return best


def load_roads():
    R = json.load(open(os.path.join(D, "road_build.json")))["roads"]; out = []
    for rid, r in R.items():
        xs = [p[0] for p in r["pts"]]; ys = [p[1] for p in r["pts"]]
        r = dict(r, bb=(min(xs), min(ys), max(xs), max(ys))); out.append((rid, r))
    return out


def run():
    RS = json.load(open(os.path.join(D, "ribbon_surface.json"))); RZ = json.load(open(os.path.join(D, "ribbon_z_now.json")))
    roads = load_roads(); G = {}; rep = {}
    for l, d in RS.items():
        g = []; dk = []; low = []; high = []
        for i, (dd, xy, mz) in enumerate(zip(d["d"], d["xy"], d["z"])):
            rz = RZ[l]["rz"][i]; tx, ty = RZ[l]["t"][i]
            b = deck_z(roads, xy[0], xy[1], tx, ty) if xy else None
            gz = b[1] if b else mz
            g.append(None if gz is None else round(gz, 1)); dk.append(b[2] if b else None)
            if gz is None: continue
            h = rz - gz
            if h < 15: low.append((round(dd / 100), round(h), b[2] if b else "map"))
            if h > 150: high.append((round(dd / 100), round(h), b[2] if b else "map"))
        G[l] = {"g": g, "deck": dk}
        if low or high: rep[l] = (low, high)
    json.dump(G, open(os.path.join(D, "ribbon_ground.json"), "w"))
    return rep


def selftest():
    roads = [("r1", {"width_m": 7.0, "pts": [[0, 0, 500], [10000, 0, 900]], "bb": (0, 0, 10000, 0)})]
    assert abs(deck_z(roads, 5000, 100, 1, 0)[1] - 712) < 1          # along the road: deck = 700 + 12
    assert deck_z(roads, 5000, 100, 0, 1) is None                    # crossing it: not this ribbon's deck
    assert deck_z(roads, 5000, 600, 1, 0) is None                    # 6 m off a 7 m road: off the deck
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit()
    rep = run()
    def runs(lst):   # group consecutive samples (3 m apart) into spots: (start m, length m, worst cm, ground)
        out = []
        for d, h, g in lst:
            if out and d - out[-1][1] <= 6: out[-1][1] = d; out[-1][2] = (min if h < 15 else max)(out[-1][2], h)
            else: out.append([d, d, h, g])
        return [(a, b - a, c, g) for a, b, c, g in out]
    nl = sum(1 for v in rep.values() if v[0]); nh = sum(1 for v in rep.values() if v[1])
    print("ribbons too LOW (< 15 cm over ground) somewhere: %d   floating (> 1.5 m) somewhere: %d" % (nl, nh))
    for l, (low, high) in sorted(rep.items()):
        if low: print("LOW  %-26s %s" % (l, runs(low)[:8]))
    for l, (low, high) in sorted(rep.items()):
        if high: print("HIGH %-26s %s" % (l, runs(high)[:8]))
