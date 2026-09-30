"""Remove the broken parapet stubs on the AB podium roof (30 Sep): SM_Podium_Structure_Skin keeps a backup
(SM_Podium_Structure_Skin_BeforeABClean); every polygon lying fully above the AB deck level (the parapet pieces and the
old tower-wall stubs, 248 polys) is deleted. A clean continuous parapet is added by Place_PodiumAB_Parapet (same job)."""
import unreal
EAL = unreal.EditorAssetLibrary; EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
P = "/Game/Neelam/Buildings/WindTunnel/Meshes/Podium/SM_Podium_Structure_Skin"
if not EAL.does_asset_exist(P + "_BeforeABClean"): EAL.duplicate_asset(P, P + "_BeforeABClean")
sm = unreal.load_asset(P)
md = sm.get_static_mesh_description(0)
DECK_LOCAL = 3767.54 - 218.54
kill = []
for p in range(md.get_polygon_count()):
    pid = unreal.PolygonID(p)
    zs = [md.get_vertex_position(v).z for v in md.get_polygon_vertices(pid)]
    if min(zs) >= DECK_LOCAL - 0.5: kill.append(pid)
for pid in kill: md.delete_polygon(pid)
sm.build_from_static_mesh_descriptions([md])
EAL.save_asset(P)
result = {"deleted_polys": len(kill), "tris_now": sm.get_num_triangles(0)}
result["materials"] = [str(s.material_slot_name) + ":" + (s.material_interface.get_name() if s.material_interface else "None") for s in sm.static_materials]
