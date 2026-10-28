"""Records the pawn while the template flies to a POI (Select_POI). fly(label, anti_tunnel) then fly_result()."""
import sys, time
import unreal


def fly(label, anti_tunnel=True):
    w = unreal.EditorLevelLibrary.get_game_world(); pn = unreal.GameplayStatics.get_player_controller(w, 0).get_controlled_pawn()
    gc = [c for c in pn.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "NeelamGroundClampComponent"][0]
    gc.set_editor_property("bEnableAntiTunnelSweep", anti_tunnel)
    poi = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if a.get_actor_label() == label][0]
    st = {"rec": [], "t0": time.time(), "poi": poi.get_actor_location()}
    def tick(dt):
        t = time.time() - st["t0"]
        if t > 8: unreal.unregister_slate_post_tick_callback(st["h"]); return
        p = pn.get_actor_location(); st["rec"].append((round(t, 2), round(p.x), round(p.y), round(p.z)))
    st["h"] = unreal.register_slate_post_tick_callback(tick)
    sys.modules[__name__].__dict__["_st"] = st
    poi.call_method("Select_POI")
    return str(st["poi"])


def fly_result():
    st = sys.modules[__name__].__dict__["_st"]; r = st["rec"]
    return {"poi": str(st["poi"]), "n": len(r), "path": r[::max(1, len(r) // 12)] + r[-1:]}
