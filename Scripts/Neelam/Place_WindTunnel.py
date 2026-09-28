"""Neelam - place the Wind Tunnel development on the construction plot (UE 5.5).

Run in the editor:  Output Log > Cmd dropdown "Python" >  py "<project>/Scripts/Neelam/Place_WindTunnel.py"
             or:  Tools > Execute Python Script...

What it does (safe to re-run; the previous copy is removed first, one Undo step):
  1. Reads Neelam_SiteAnchor (location = plot centre, red X arrow = building frontage).
  2. Finds ground height with a grid of downward traces over the plot (ignores tall hits
     such as the existing concrete structures) unless GROUND_Z_CM is set.
  3. Spawns a root actor "Neelam_WindTunnel_Root" and all 511 placements from
     Data/level_manifest.json, attached to it, in Outliner folder Neelam/WindTunnel/...
     Move / rotate the root to fine-tune: everything follows.
  4. Writes Saved/Neelam/place_report.json.
"""
import json, math, os, sys
try:
    import unreal
except ImportError:
    sys.exit("This script must run INSIDE the Unreal Editor (Output Log > Python, or Tools > Execute Python Script), not in VS Code.")

# ---- tweakables ------------------------------------------------------------------
ANCHOR_LABEL  = "Neelam_SiteAnchor"
ROOT_LABEL    = "Neelam_WindTunnel_Root"
MESH_ROOT     = "/Game/Neelam/Buildings/WindTunnel"   # contains Meshes/<same sub-folders as FBX package>
OUTLINER      = "Neelam/WindTunnel"
FLIP_Y        = True     # Blender +Y -> Unreal -Y (matches how the meshes were imported)
YAW_EXTRA_DEG = 0.0      # set 180 if the gates/road side ends up facing the wrong way
GROUND_Z_CM   = None     # e.g. 330.0 to force the base height; None = auto trace
Z_LIFT_CM     = 0.0      # small lift if the plinth sinks into the terrain
# Model-space pivot (metres) placed on the anchor: centre of the boundary-wall perimeter
PIVOT_M = ((-83.28 + 114.82) / 2.0, (-64.50 + 62.12) / 2.0)
SITE_HALF_M = (99.05, 63.31)   # half extents of the boundary wall, used for the ground traces
# -----------------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
DATA = os.path.join(HERE, "Data")
NO_COLLISION = ("Glass", "Water", "Lighting")

actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def find_label(label):
    for a in actor_sub.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def rot2(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def trace_z(x, y, ignore):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 500000.0), unreal.Vector(x, y, -500000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None
    t = hit.to_tuple()
    return float(t[4].z) if t[0] else None      # (blocking_hit, initial_overlap, time, distance, location, ...)


def main():
    anchor = find_label(ANCHOR_LABEL)
    if anchor is None:
        raise RuntimeError("Actor '%s' not found in the open level." % ANCHOR_LABEL)
    manifest = json.load(open(os.path.join(DATA, "level_manifest.json")))

    # 1. remove a previous run
    old = [a for a in actor_sub.get_all_level_actors()
           if str(a.get_folder_path()).startswith(OUTLINER) or a.get_actor_label() == ROOT_LABEL]
    for a in old:
        actor_sub.destroy_actor(a)

    a_loc = anchor.get_actor_location()
    yaw = anchor.get_actor_rotation().yaw + YAW_EXTRA_DEG

    # 2. ground height
    samples = []
    if GROUND_Z_CM is None:
        hx, hy = SITE_HALF_M[0] * 100.0, SITE_HALF_M[1] * 100.0
        for i in range(-3, 4):
            for j in range(-3, 4):
                ox, oy = rot2(hx * i / 3.0 * 0.9, hy * j / 3.0 * 0.9, yaw)
                z = trace_z(a_loc.x + ox, a_loc.y + oy, [anchor])
                if z is not None:
                    samples.append(z)
        if not samples:
            raise RuntimeError("No ground hit under the anchor; set GROUND_Z_CM manually.")
        samples.sort()
        ground = samples[int(len(samples) * 0.25)]   # low quartile: ignores existing structures/cranes
    else:
        ground = float(GROUND_Z_CM)
    base = unreal.Vector(a_loc.x, a_loc.y, ground + Z_LIFT_CM)

    # 3. spawn
    root = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, base, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    root.set_actor_label(ROOT_LABEL)
    root.set_folder_path(OUTLINER)

    cache, missing, spawned = {}, set(), 0
    with unreal.ScopedSlowTask(len(manifest), "Placing Wind Tunnel development") as task:
        task.make_dialog(True)
        for e in manifest:
            if task.should_cancel():
                break
            task.enter_progress_frame(1)
            name, folder = e["asset"], e["folder"]
            path = "%s/%s/%s.%s" % (MESH_ROOT, folder, name, name)
            if path not in cache:
                cache[path] = unreal.EditorAssetLibrary.load_asset(path)
            sm = cache[path]
            if not isinstance(sm, unreal.StaticMesh):
                missing.add(path)
                continue
            x, y, z = e["location_m"]
            lx = (x - PIVOT_M[0]) * 100.0
            ly = (y - PIVOT_M[1]) * 100.0 * (-1.0 if FLIP_Y else 1.0)
            wx, wy = rot2(lx, ly, yaw)
            loc = unreal.Vector(base.x + wx, base.y + wy, base.z + z * 100.0)
            act = actor_sub.spawn_actor_from_object(sm, loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
            act.set_actor_label(e.get("actor", name))
            act.set_folder_path(OUTLINER + "/" + folder.replace("Meshes/", ""))
            if any(k in name for k in NO_COLLISION):
                act.static_mesh_component.set_collision_profile_name("NoCollision")
            act.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                                unreal.AttachmentRule.KEEP_WORLD, False)
            spawned += 1

    report = {
        "anchor_cm": [a_loc.x, a_loc.y, a_loc.z], "yaw_deg": yaw,
        "ground_samples_cm": samples, "base_cm": [base.x, base.y, base.z],
        "placements": len(manifest), "spawned": spawned, "missing": sorted(missing),
        "level": world.get_path_name(),
    }
    out = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Neelam")
    os.makedirs(out, exist_ok=True)
    json.dump(report, open(os.path.join(out, "place_report.json"), "w"), indent=1)
    actor_sub.set_selected_level_actors([root])
    unreal.log("Neelam WindTunnel: spawned %d/%d at %s yaw %.1f (ground %.0f cm), missing %d"
               % (spawned, len(manifest), base, yaw, ground, len(missing)))


with unreal.ScopedEditorTransaction("Place Neelam Wind Tunnel"):
    main()
