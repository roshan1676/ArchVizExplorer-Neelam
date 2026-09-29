"""Apply Verify_Ribbons.py results: fill holes in Data/surface_dense.json (> 3 m below the +-450 m median along the
polyline), raise samples to the full-detail PIE traces (max +4 m; bigger = building beside the route; skipped on built
road decks), then rebuild routes + traffic. Needs env[\"sa\"] from Surface_Align prep (run in the same editor session)."""
import os, sys, json, math, importlib
P=os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),"Scripts","Neelam"); sys.path.insert(0,P)
import connectivity_lib as C; importlib.reload(C)
SP=os.path.join(P,"Data","surface_dense.json")
S={pid:{"s":v["s"],"z":[None if q is None else round(q,1) for q in v["z"]]} for pid,v in env["sa"].items()}   # original record
fix=json.load(open(os.path.join(P,"Data","surface_fix.json")))
holes=0
for pid,v in S.items():                                   # fill holes: values > 3 m below the local median (+-60 m)
    z=v["z"]; zz=[q for q in z]
    for j in range(len(z)):
        if z[j] is None: continue
        w=sorted(q for q in zz[max(0,j-150):j+151] if q is not None); med=w[len(w)//2]   # +-450 m ground level
        if z[j] < med-300: z[j]=med; holes+=1
print("holes filled", holes)
sa=env["sa"]; grid={}
for pid,v in sa.items():
    for j,(x,y,_,_) in enumerate(v["xy"]): grid.setdefault((pid,int(x//600),int(y//600)),[]).append((j,x,y))
raised=0; capped=0; deck=0; hist=[0,0,0,0]
for pid,x,y,hz in fix:
    if pid not in S: continue
    if C.road_deck(x,y,-100.0) is not None: deck+=1; continue
    for i in (-1,0,1):
        for k in (-1,0,1):
            for j,sx,sy in grid.get((pid,int(x//600)+i,int(y//600)+k),[]):
                if math.hypot(sx-x,sy-y)<=450:
                    z=S[pid]["z"][j]
                    if z is None: continue
                    d=hz-z
                    if d<=0: continue
                    if d>400: capped+=1; continue
                    S[pid]["z"][j]=round(hz,1); raised+=1; hist[min(3,int(d//200))]+=1
json.dump(S,open(SP,"w"))
print("raised", raised, "hist <1m,1-2,2-3,3-4m", hist, "ignored >4m (buildings beside route)", capped, "on decks", deck)
importlib.reload(C)
for ph in ("phase3","phase2"):
    g={"NEELAM_PHASE":ph,"unreal":unreal}; exec(open(os.path.join(P,"Build_Surroundings.py"),encoding="utf-8").read(), g)
g={"unreal":unreal}; exec(open(os.path.join(P,"Build_Traffic.py"),encoding="utf-8").read(), g); print("traffic", g["result"]["strips"])
print("saved", unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
