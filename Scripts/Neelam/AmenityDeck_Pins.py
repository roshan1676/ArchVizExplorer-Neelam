"""Amenity pins -> where the client DWG puts each amenity (28 Oct 2026 audit: Saved/Neelam/Review/amenity_pins_vs_dwg.jpg).
Bridge job, MODE "preview" (report only) | "apply" (move + rename in place; NEVER saves - Realistic_01 is saved only
when Roshan says so). Pins are edited in place, not rebuilt: the 360 panorama in POI_Info_Struct (Codex's assignments)
is left untouched - only the Name / Information text, the actor position, the hologram box and the camera target move.
Targets are DWG model metres (build_deck.py frame) + SH, z = metres above the 7th-podium deck FFL (2477.5 cm)
or absolute cm when given as ('abs', cm). Service rooms are not on the deck sheet; their spots are from the other DWG
sheets (west lift core / podium-09 pump room / podium-top fitness centre) and are approximate."""
import math, re
import unreal

MODE = globals().get("MODE", "preview")
SH = (0.35, 1.96)
ROOT, YAW, Z0 = (950.0, 4430.0), 40.0, 2477.5
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# id: (x, y, z, name or None (keep), info or None, box (w along deck, d across, h) or None)
TARGETS = {
    "pool":    (3.88, 42.70, 0.0, "Swimming Pool", "30.9 x 9.7 m pool, 1.2 m deep", (31, 9.7, 1.5)),
    "toddler": (-7.18, 35.37, 0.0, "Kids' Pool", "8.8 x 4.35 m, 0.45 m deep, next to the main pool", (8.8, 4.4, 1.2)),
    "pergola": (9.9, 33.3, 0.1, "Pool Deck & Pergola Dining", "Timber deck with a louvred pergola over dining", (24, 7.5, 3.5)),
    "lawn":    (5.63, 23.84, 0.0, "Party Lawn", "37 x 9.3 m events lawn", (36.9, 9.3, 1.5)),
    "garden":  (33.6, 37.0, 0.0, "Central Lawn & Seating Steps", "Lawn with stepped seating and a planted mound", (19.5, 15.5, 1.5)),
    "padel":   (35.61, 23.84, 0.0, "Pickleball Court", "Fenced pickleball court", (19.5, 9.3, 3.0)),
    "court":   (57.59, 36.09, 0.0, "Multipurpose Court", "Full basketball court, floodlit and fenced", (20.9, 33.8, 4.5)),
    "track":   (20.0, 18.29, 0.0, "Jogging Track", "1.2 m Kota stone loop around the lawns", (60, 1.2, 1.0)),
    "senior":  (41.0, 38.0, 0.25, "Senior Citizens' Corner", "Shaded seating steps under the Terminalia", (6, 6, 2)),
    "gym":     (-61.5, 23.0, ("abs", 3468.0), "Gymnasium", "Fitness centre, podium top (west block)", (12, 8, 4)),
    "toilets": (-66.0, 40.0, 0.0, None, None, (8, 6, 4)),
    "fire":    (-51.4, 41.0, ("abs", 1300.0), None, None, (8, 6, 4)),
    "stp":     (-55.0, 30.0, ("abs", 600.0), None, None, (10, 8, 4)),
    "parking": (-48.0, 25.0, ("abs", 1300.0), None, None, None),
}
NEW = {"climb": (48.2, 15.8, 0.35, "Rock Climbing Wall", "4.5 m bouldering wall with safety surface", (3.2, 2.4, 4.8), "court")}


def world(x, y, z):
    c, s = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
    lx, ly = (x + SH[0]) * 100.0, -(y + SH[1]) * 100.0
    zz = z[1] if isinstance(z, tuple) else Z0 + z * 100.0
    return unreal.Vector(ROOT[0] + lx * c - ly * s, ROOT[1] + lx * s + ly * c, zz)


def set_text(poi, name, info):
    s = poi.get_editor_property("POI_Info_Struct"); t = s.export_text()
    if name:
        t = re.sub(r'(Name_[0-9A-Za-z_]+=)(INVTEXT\("[^"]*"\)|NSLOCTEXT\([^)]*\)|"[^"]*")', lambda m: m.group(1) + 'INVTEXT("%s")' % name, t, count=1)
    if info:
        t = re.sub(r'(Information_[0-9A-Za-z_]+=)(INVTEXT\("[^"]*"\)|NSLOCTEXT\([^)]*\)|"[^"]*")', lambda m: m.group(1) + 'INVTEXT("%s")' % info, t, count=1)
    s.import_text(t); poi.set_editor_property("POI_Info_Struct", s)


def move(a, x, y, z, box):
    old = a.get_actor_location(); new = world(x, y, z) + unreal.Vector(0, 0, 150)
    d = new - old
    a.set_actor_location(new, False, True)
    if a.get_editor_property("Use_LookAt_Target?"):
        a.set_editor_property("LookAt_Target_Location", a.get_editor_property("LookAt_Target_Location") + d)
    geo = [c for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == "POI_Geometry"]
    if geo and box:
        w, dd, h = box
        geo[0].set_world_location_and_rotation(world(x, y, z) + unreal.Vector(0, 0, h * 50), unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW + 90), False, False)
        geo[0].set_world_scale3d(unreal.Vector(dd, w, h))      # box X runs at yaw 130 = across the deck
    return round(d.length / 100, 1)


pins = {a.get_actor_label()[8:]: a for a in EAS.get_all_level_actors()
        if a.get_class().get_name() == "BP_POI_C" and a.get_actor_label().startswith("Amenity_")}
out = {}
for aid, (x, y, z, name, info, box) in TARGETS.items():
    a = pins.get(aid)
    if not a:
        out[aid] = "missing"; continue
    tgt = world(x, y, z) + unreal.Vector(0, 0, 150)
    out[aid] = {"move_m": round((tgt - a.get_actor_location()).length / 100, 1), "rename": name}
    if MODE == "apply":
        move(a, x, y, z, box); set_text(a, name, info)
for aid, (x, y, z, name, info, box, donor) in NEW.items():
    if aid in pins:
        out[aid] = "exists"; continue
    out[aid] = {"new": name}
    if MODE == "apply" and donor in pins:
        a = EAS.duplicate_actor(pins[donor])
        a.set_actor_label("Amenity_" + aid)
        a.tags = [unreal.Name(t) for t in ("Amenities", "Fitness", "Neelam_Amenities", "Neelam_Amenity_" + aid)]
        move(a, x, y, z, box); set_text(a, name, info)
        s = a.get_editor_property("POI_Info_Struct")      # no panorama of its own yet
        s.import_text(re.sub(r'(Texture_360_[0-9A-Za-z_]+=)("[^"]*"|None)', lambda m: m.group(1) + "None", s.export_text(), count=1))
        a.set_editor_property("POI_Info_Struct", s)
result = out
