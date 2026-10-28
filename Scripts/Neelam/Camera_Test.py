"""Explorer-camera smoothness / wall test (PIE, through the NeelamBridge). Written 27 Oct for the client complaint
"panning is not smooth, camera goes inside the building / under the map".
Each run records the camera every frame for 20 s while the pivot pans along a straight line (swept move, like the
template's pan) and the view orbits 25 deg/s. Per frame it also traces pivot -> camera and records the first
non-map actor in between (= camera behind / inside a wall).

Bridge jobs (each its own .py in Saved/NeelamBridge/inbox, PIE running, Surroundings/Amenities menus closed = Home):
  1)  import sys; sys.path.insert(0, r"<project>/Scripts/Neelam"); import Camera_Test as CT; result = CT.start("towers")
  2)  ~1 s later: CT.arm()  (anti-tunnel back on after the start teleport), then wait ~25 s
  3)  import Camera_Test as CT; result = CT.dump()      -> Saved/NeelamBridge/outbox/cam_<name>.json
Then on the PC:  py Scripts/Neelam/Camera_Test.py Saved/NeelamBridge/outbox/cam_towers.json [more files]
PASS = 0 frames behind a wall, zoom snaps (camera-pivot distance change > 20 m/s) <= 3, and for "deck" the pivot
reaches close to the target (panning over the property must NOT be blocked)."""
import json, os, sys, time

PATHS = {   # name: (start xy, end xy, pivot z cm)
    "towers": ((-4000.0, -3000.0), (12000.0, 11000.0), 5000.0),   # straight through towers C/D/E at 50 m (40 m touched the AB podium top: pawn could not move): pivot must stop 8 m off the facade
    "deck": ((5200.0, 2600.0), (10500.0, 3000.0), 3500.0),        # 10 m over the open CDE deck, >8 m clear of towers / podium skin (old end was 8 m from Tower E): must reach the end
}


def start(name):
    import unreal
    w = unreal.EditorLevelLibrary.get_game_world(); pc = unreal.GameplayStatics.get_player_controller(w, 0)
    pn = pc.get_controlled_pawn(); cm = unreal.GameplayStatics.get_player_camera_manager(w, 0)
    (ax, ay), (bx, by), z = PATHS[name]
    st = {"rec": [], "t0": time.time(), "name": name}
    gc = [c for c in pn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "NeelamGroundClampComponent"]
    # same start every run (else it inherits the last run's end); the anti-tunnel would treat the jump as a pan -> off for it
    if gc: gc[0].set_editor_property("bEnableAntiTunnelSweep", False)
    pn.set_actor_location(unreal.Vector(ax, ay, z), False, True)

    def tick(dt):
        t = time.time() - st["t0"]
        if t > 20:
            unreal.unregister_slate_post_tick_callback(st["h"]); return
        p = pn.get_actor_location(); c = cm.get_camera_location()
        h = unreal.SystemLibrary.line_trace_single(w, p, c, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pn], unreal.DrawDebugTrace.NONE, True)
        tt = h.to_tuple() if h else None
        blocked = bool(tt and tt[0] and tt[9] is not None and "Cesium" not in tt[9].get_class().get_name())
        st["rec"].append((t, c.x, c.y, c.z, p.x, p.y, p.z, blocked, tt[9].get_actor_label() if blocked else ""))
        f = min(1.0, t / 14.0); tx, ty = ax + (bx - ax) * f, ay + (by - ay) * f
        pn.set_actor_location(unreal.Vector(p.x + (tx - p.x) * 0.25, p.y + (ty - p.y) * 0.25, z), True, False)
        pc.set_control_rotation(unreal.Rotator(pitch=-20, yaw=t * 25.0, roll=0))

    st["h"] = unreal.register_slate_post_tick_callback(tick)
    sys.modules[__name__].__dict__["_st"] = st
    return {"clamp_component": bool(gc), "props": {k: str(gc[0].get_editor_property(k)) for k in ("bEnableAntiTunnelSweep", "bClampCamera", "PivotStandoff", "CamAnticipate")} if gc else None}


def arm():
    """Run ~1 s after start(): anti-tunnel back on (setting it from the tick hit a stale component wrapper)."""
    import unreal
    w = unreal.EditorLevelLibrary.get_game_world(); pn = unreal.GameplayStatics.get_player_controller(w, 0).get_controlled_pawn()
    gc = [c for c in pn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "NeelamGroundClampComponent"][0]
    gc.set_editor_property("bEnableAntiTunnelSweep", True)
    return gc.get_editor_property("bEnableAntiTunnelSweep")


def dump():
    import unreal
    st = sys.modules[__name__].__dict__["_st"]
    out = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "outbox", "cam_%s.json" % st["name"])
    json.dump({"name": st["name"], "rec": st["rec"]}, open(out, "w"))
    return out


def report(path):
    import numpy as np, collections
    d = json.load(open(path)); R = [r for r in d["rec"] if r[0] > 1.0];   # skip the start teleport + camera-lag catch-up
    A = np.array([r[:7] for r in R], float)
    t = A[:, 0]; C = A[:, 1:4]; P = A[:, 4:7]; dist = np.linalg.norm(C - P, axis=1); dt = np.diff(t); ok = dt > 1e-3
    rate = np.abs(np.diff(dist))[ok] / dt[ok]
    walls = [r[8] for r in R if r[7]]
    end = PATHS[d["name"]][1]
    print("%-7s %3d frames (%2.0f fps) | zoom snaps >20 m/s: %d (max %.0f m/s) | camera behind/inside wall: %d %s | pivot end %s target %s"
          % (d["name"], len(R), len(R) / (t[-1] - t[0]), (rate > 2000).sum(), rate.max() / 100, len(walls),
             collections.Counter(walls).most_common(3), [round(v) for v in P[-1, :2]], end))


if __name__ == "__main__":
    for f in sys.argv[1:]: report(f)
