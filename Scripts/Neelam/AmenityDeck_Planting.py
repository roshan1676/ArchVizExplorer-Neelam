"""Neelam amenity deck planting + furniture (28 Oct 2026). Bridge job; rebuilds every ADP_* actor in L_AmenityDeck.
Coordinates are the DWG "7TH PODIUM FLOOR PLAN" in model metres (same as SourceArt/AmenityDeck/tools/build_deck.py:
x = DWG X - 42617.4, y = DWG Y + 5314, + SH registration), z from the DWG grading notes (soil = TW - 0.05).
Each planter gets a layered scheme (tree / back row / mid / front groundcover), jittered with a fixed seed so re-runs
give the same garden. Lawns are tiled with the low grass-carpet kit. Meshes come from /Game/Neelam/AmenityDeck/Kit."""
import math, random
import unreal

SH = (0.35, 1.96)
ROOT, YAW, Z0 = (950.0, 4430.0), 40.0, 2477.5
KIT = "/Game/Neelam/AmenityDeck/Kit/%s/%s"
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
rnd = random.Random(2810)
PLACED = []          # (kit, x, y, z, yaw_deg, scale, label_hint)


def world(x, y, z):
    c, s = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
    lx, ly = (x + SH[0]) * 100.0, -(y + SH[1]) * 100.0
    return unreal.Vector(ROOT[0] + lx * c - ly * s, ROOT[1] + lx * s + ly * c, Z0 + z * 100.0)


def put(kit, x, y, z, yaw=None, scale=1.0, jitter=0.0):
    if jitter:
        x += rnd.uniform(-jitter, jitter); y += rnd.uniform(-jitter, jitter)
    PLACED.append((kit, x, y, z, rnd.uniform(0, 360) if yaw is None else yaw, scale))


def row(kits, x0, y0, x1, y1, z, step, scale=(0.9, 1.1), jitter=0.12, along_yaw=None):
    """Plants along a line, cycling through `kits`, spacing `step` m."""
    L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / step))
    ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    for i in range(n):
        t = (i + 0.5) / n
        k = kits[i % len(kits)]
        put(k, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z,
            yaw=None if along_yaw is None else ang + along_yaw + rnd.uniform(-8, 8), scale=rnd.uniform(*scale), jitter=jitter)


def scatter(kits, poly_rect, z, spacing, avoid=(), scale=(0.8, 1.15)):
    """Jittered-grid scatter inside a rect (x0, y0, x1, y1), skipping points within r of `avoid` (x, y, r)."""
    x0, y0, x1, y1 = poly_rect
    nx, ny = max(1, int((x1 - x0) / spacing)), max(1, int((y1 - y0) / spacing))
    for i in range(nx):
        for j in range(ny):
            x = x0 + (i + 0.5) * (x1 - x0) / nx + rnd.uniform(-0.3, 0.3) * spacing
            y = y0 + (j + 0.5) * (y1 - y0) / ny + rnd.uniform(-0.3, 0.3) * spacing
            if any(math.hypot(x - ax, y - ay) < r for ax, ay, r in avoid):
                continue
            put(rnd.choice(kits), min(max(x, x0 + 0.15), x1 - 0.15), min(max(y, y0 + 0.15), y1 - 0.15), z, scale=rnd.uniform(*scale))


def lawn(x0, y0, x1, y1, z=-0.10):
    """Grass carpet tiles (2.98 x 1.53 m) on a staggered grid, random 0/180 deg and mirror for variety."""
    sx, sy = 2.7, 1.35
    j = 0; y = y0 + sy / 2
    while y < y1 + 0.2:
        x = x0 + sx / 2 - (sx / 2 if j % 2 else 0)
        while x < x1 + 0.3:
            PLACED.append(("KIT_GrassCarpet", min(max(x, x0 + 1.35), x1 - 1.35), min(max(y, y0 + 0.66), y1 - 0.66), z,
                           rnd.choice((0, 180)) + rnd.uniform(-3, 3), rnd.uniform(0.95, 1.08)))
            x += sx
        y += sy; j += 1


def plan():
    # ---------------- trees exactly on the DWG canopy symbols
    pool_sq = [(1.455, 36.353), (7.305, 36.353), (13.155, 36.353), (17.825, 36.343)]
    for i, (x, y) in enumerate(pool_sq):
        put("KIT_Plumeria_" + "ABCA"[i], x + 0.75, y + 0.75, 0.25, scale=rnd.uniform(0.95, 1.05))
        for a in (30, 150, 270):
            put("KIT_SmallPlant", x + 0.75 + 0.33 * math.cos(math.radians(a)), y + 0.75 + 0.33 * math.sin(math.radians(a)), 0.25, scale=0.55)
    west_trees = [(-12.258, 34.146), (-12.258, 39.746), (-12.258, 45.032)]
    for i, (x, y) in enumerate(west_trees):
        put("KIT_Plumeria_" + "BCA"[i], x, y, 0.50, scale=rnd.uniform(0.95, 1.05))
    put("KIT_Terminalia_A", 26.631, 45.017, 0.50, scale=1.0)
    put("KIT_Terminalia_B", 42.627, 31.043, 0.50, scale=1.0)
    for x, y in ((26.631, 45.017), (42.627, 31.043)):
        for a in (0, 120, 240):
            put("KIT_SmallPlant", x + 0.32 * math.cos(math.radians(a)), y + 0.32 * math.sin(math.radians(a)), 0.50, scale=0.5)

    # ---------------- planters (soil = TW - 0.05)
    # west tree planter: fern / big-leaf underplanting between the three plumerias
    scatter(["KIT_Fern", "KIT_BigLeaf", "KIT_Shrub01"], (-14.2, 33.6, -11.95, 47.9), 0.50, 1.1,
            avoid=[(x, y, 0.7) for x, y in west_trees], scale=(0.55, 0.75))
    # west edge strip (0.9 m soil, 30 m): clipped shrub row with grass tufts
    row(["KIT_Shrub01", "KIT_GrassTuft", "KIT_Shrub01", "KIT_Shrub04"], -15.21, 18.1, -15.21, 47.9, 0.50, 1.15, scale=(0.5, 0.6))
    # mid strip between pool deck and central lawn (0.9 m x 18 m): spikes + ornamental grass
    row(["KIT_FlowerSpikes", "KIT_GrassBig", "KIT_FlowerBush", "KIT_GrassBig"], 23.33, 30.8, 23.33, 48.6, 0.50, 1.6,
        scale=(0.55, 0.65), along_yaw=0)
    # east strip by the courts (1 m x 33 m): taller hedge screen
    row(["KIT_Shrub05", "KIT_Shrub04", "KIT_Shrub06"], 68.84, 19.8, 68.84, 52.4, 0.50, 1.25, scale=(0.48, 0.58))
    # north planter along the parapet (2.5 m x 22 m): back hedge, mid flowers, front groundcover
    row(["KIT_Shrub06", "KIT_Shrub05", "KIT_Shrub04"], 24.6, 49.85, 46.6, 49.85, 0.50, 1.7, scale=(0.75, 0.9))
    row(["KIT_FlowerSpikes", "KIT_GrassBig", "KIT_FlowerBush", "KIT_GroundFlower"], 24.8, 48.6, 46.4, 48.6, 0.50, 1.5,
        scale=(0.6, 0.75), along_yaw=0)
    row(["KIT_GroundFlower", "KIT_SmallPlant", "KIT_Fern"], 24.8, 47.95, 46.4, 47.95, 0.50, 0.9, scale=(0.45, 0.6))
    row(["KIT_Shrub01", "KIT_FlowerBush"], 19.7, 48.33, 22.3, 48.33, 0.50, 1.3, scale=(0.55, 0.65))
    # planted mound behind the seating steps (L-shape, +0.62)
    scatter(["KIT_Shrub06", "KIT_FlowerBush", "KIT_GrassBig", "KIT_BigLeaf", "KIT_GroundFlower", "KIT_Fern"],
            (27.7, 43.5, 44.9, 45.5), 0.62, 1.2, avoid=[(26.631, 45.017, 1.0)], scale=(0.55, 0.8))
    scatter(["KIT_Shrub06", "KIT_FlowerBush", "KIT_GrassBig", "KIT_BigLeaf", "KIT_GroundFlower"],
            (43.0, 32.1, 45.0, 43.4), 0.62, 1.2, avoid=[(42.627, 31.043, 1.0)], scale=(0.55, 0.8))
    # small planters at the tower doors (TW +0.40)
    for x in (1.13, 23.93):
        row(["KIT_GroundFlower", "KIT_FlowerBush"], x + 0.4, 16.64, x + 2.4, 16.64, 0.35, 0.9, scale=(0.45, 0.55))

    # ---------------- lawns
    lawn(-12.821, 19.193, 24.079, 28.493)
    lawn(25.881, 30.293, 41.331, 41.743)

    # ---------------- furniture
    # pool loungers on the east deck (facing the pool, west) and the west deck strip (facing north)
    # (the source lounger is a 4.4 x 2.0 m daybed - scaled 0.5 to a real 2.2 x 1.0 m sun lounger)
    for y in (38.9, 40.4, 41.9, 43.4, 44.9):
        put("KIT_Lounger", 20.95, y, 0.10, yaw=90, scale=0.5)
    put("KIT_Umbrella", 21.0, 46.6, 0.10, yaw=0, scale=0.75)
    for x in (-13.6, -12.1, -10.6, -9.1):
        put("KIT_Lounger", x, 31.75, 0.10, yaw=0, scale=0.5)
    # dining under the pergola (reference): 2 rows x 4 bistro sets between the posts (posts at x -1.9 + 5.95 k)
    for x in (1.07, 7.02, 12.97, 18.92):
        for y in (32.35, 34.45):
            put("KIT_DiningSet", x + rnd.uniform(-0.15, 0.15), y, 0.10, yaw=rnd.choice((0, 180)) + rnd.uniform(-6, 6), scale=1.0)
    put("KIT_PalmPot", 21.6, 37.2, 0.10, scale=0.75)
    put("KIT_PalmPot", -14.0, 30.9, 0.10, scale=0.75)


def spawn():
    old = [a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("ADP_")]
    for a in old:
        EAS.destroy_actor(a)
    LES.set_current_level_by_name("L_AmenityDeck")
    if "L_AmenityDeck" not in LES.get_current_level().get_path_name():
        raise RuntimeError("amenity sublevel not current")
    meshes = {}
    n = 0
    for kit, x, y, z, yaw, sc in PLACED:
        sm = meshes.get(kit) or unreal.load_asset(KIT % (kit, kit))
        if sm is None:
            continue
        meshes[kit] = sm
        a = EAS.spawn_actor_from_object(sm, world(x, y, z), unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW - yaw))
        a.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        a.set_actor_label("ADP_%s_%03d" % (kit[4:], n)); n += 1
        folder = "Planting" if kit not in ("KIT_Lounger", "KIT_Umbrella", "KIT_PalmPot") else "Furniture"
        if kit == "KIT_GrassCarpet":
            folder = "Lawn"
        a.set_folder_path("Neelam/AmenityDeck/" + folder)
        c = a.static_mesh_component
        c.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION) if kit not in ("KIT_Lounger", "KIT_Umbrella") else None
        if kit == "KIT_GrassCarpet":
            c.set_editor_property("cast_shadow", False)
    LES.save_current_level()
    LES.set_current_level_by_name("Realistic_01")
    return n, len(old)


plan()
made, removed = spawn()
counts = {}
for p in PLACED:
    counts[p[0]] = counts.get(p[0], 0) + 1
result = {"spawned": made, "removed": removed, "by_kit": counts}
