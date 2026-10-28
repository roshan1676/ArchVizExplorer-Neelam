"""Rebuild the hardscape (build_deck.py) and export AD_Hardscape.fbx for UE (Scripts/Neelam/AmenityDeck_Import.py).
Run in the live Blender: exec(open(r'<this file>').read())  -> result = {objects, fbx_mb}"""
import os
import bpy

D = r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck'
g = {}
exec(open(D + '/tools/build_deck.py').read(), g)
for o in list(bpy.data.collections['AD_Hardscape'].objects):
    if o.name.startswith('_cut'):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_mainfile()
os.makedirs(D + '/export', exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.collections['AD_Hardscape'].objects:
    o.select_set(True)
bpy.ops.export_scene.fbx(filepath=D + '/export/AD_Hardscape.fbx', use_selection=True, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_UNITS', use_mesh_modifiers=True, mesh_smooth_type='FACE',
                         use_tspace=False, colors_type='SRGB', add_leaf_bones=False, bake_anim=False, object_types={'MESH'})
result = {"objects": len(g['result']), "fbx_mb": round(os.path.getsize(D + '/export/AD_Hardscape.fbx') / 1e6, 2)}
