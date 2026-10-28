"""Offline report on Data/infra_ground.json (Infra_Ground_PIE.py): broken / buried spots of every road and the railway.
Per sample: top (road deck / track top), mapL / mapR (photogrammetry just outside both edges).
  HOLE  road: no deck surface at the centreline; rail: no track mesh, between two stretches that have one
  SUNK  top lower than the map on BOTH sides by > SUNK cm (inside the ground; one high side = wall/building, ignored)
  STEP  height jump > STEP cm between consecutive 3 m samples (broken / stepped surface)
Runs of samples are merged (gap <= 2 samples). py infra_ground_report.py [--json out.json] | --selftest"""
import json, os, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
SUNK, STEP = 50.0, 60.0


def classify(S):
    out = []                                                                 # (kind, id, issue, d, xy, value_cm)
    by = {}
    for s in S: by.setdefault((s[0], s[1]), []).append(s)
    for (kind, rid), ss in by.items():
        ss.sort(key=lambda s: s[2]); have = [s[8] is not None for s in ss]
        for i, s in enumerate(ss):
            _, _, d, x, y, _, _, _, top, ml, mr = s
            if top is None:
                if kind == "road" or (any(have[:i]) and any(have[i + 1:])): out.append((kind, rid, "HOLE", d, (x, y), None))
                continue
            if ml is not None and mr is not None and top < min(ml, mr) - SUNK: out.append((kind, rid, "SUNK", d, (x, y), round(min(ml, mr) - top)))
            if i and ss[i - 1][8] is not None and abs(top - ss[i - 1][8]) > STEP: out.append((kind, rid, "STEP", d, (x, y), round(top - ss[i - 1][8])))
    return out


def runs(issues, gap):
    """merge consecutive samples of the same (id, issue): -> (kind, id, issue, start d, end d, worst cm, xy of worst, n)"""
    issues = sorted(issues, key=lambda t: (t[1], t[2], t[3])); out = []
    for k, rid, iss, d, xy, v in issues:
        o = out[-1] if out else None
        if o and o[1] == rid and o[2] == iss and d - o[4] <= gap:
            o[4] = d; o[7] += 1
            if v is not None and (o[5] is None or abs(v) > abs(o[5])): o[5] = v; o[6] = xy
        else: out.append([k, rid, iss, d, d, v, xy, 1])
    return out


def selftest():
    S = [["road", "r", i * 3.0, i * 300.0, 0, 0, 1, 700, 1000.0, 900.0, 900.0] for i in range(10)]
    S[4][8] = None                                              # hole
    S[6][8] = 700.0; S[6][9] = S[6][10] = 900.0                 # sunk 2 m (and steps in/out)
    r = {(t[2], t[3]) for t in classify(S)}
    assert ("HOLE", 12.0) in r and ("SUNK", 18.0) in r and ("STEP", 18.0) in r, r
    rail = [["rail", "rail", i, i * 300.0, 0, 0, 1, 600, None if i in (0, 1, 5) else 500.0, 400.0, 400.0] for i in range(8)]
    assert [t[3] for t in classify(rail) if t[2] == "HOLE"] == [5]   # leading samples without mesh are outside the build
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit()
    S = json.load(open(os.path.join(D, "infra_ground.json")))
    road = [s for s in S if s[0] == "road"]; rail = [s for s in S if s[0] == "rail"]
    print("road samples %d (deck found %d, map traced both sides %d) | rail points %d (track mesh %d, map both sides %d)" % (
        len(road), sum(s[8] is not None for s in road), sum(s[9] is not None and s[10] is not None for s in road),
        len(rail), sum(s[8] is not None for s in rail), sum(s[9] is not None and s[10] is not None for s in rail)))
    iss = classify(S); R = runs([t for t in iss if t[0] == "road"], 9.0) + runs([t for t in iss if t[0] == "rail"], 3)
    for kind in ("road", "rail"):
        for what in ("HOLE", "SUNK", "STEP"):
            rr = [r for r in R if r[0] == kind and r[2] == what]
            print("\n%s %s: %d spots" % (kind.upper(), what, len(rr)))
            for r in sorted(rr, key=lambda r: -abs(r[5] or 0))[:25]:
                print("  %-12s %7s-%-7s  worst %5s cm  n=%-3d at %s" % (r[1], r[3], r[4], r[5], r[7], [round(v) for v in r[6]]))
    if "--json" in sys.argv: json.dump(R, open(sys.argv[sys.argv.index("--json") + 1], "w"))
