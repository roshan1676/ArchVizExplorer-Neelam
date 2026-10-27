import bpy, os, json, re
from mathutils import Vector
root=r'C:/Users/Admin/Documents/Unreal Projects/Room_render/SourceArt/FreeAssets/PolyHaven'
names=['outdoor_table_chair_set_01','modular_street_seating','painted_wooden_bench','shrub_01','flower_gazania','planter_box_01']
out=[]
for name in names:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(root,name+'_2k.blend'))
    all_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
    lod_present=any(re.search(r'_LOD\d+$',o.name,re.I) for o in all_meshes)
    meshes=[o for o in all_meshes if (re.search(r'_LOD0$',o.name,re.I) if lod_present else True)]
    # Exporter uses the active view layer; select only highest-detail meshes that are actually in it.
    visible=[]
    for o in meshes:
        try:
            if o.visible_get(): visible.append(o)
        except: pass
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in visible:
        try: o.select_set(True)
        except: pass
    if visible: bpy.context.view_layer.objects.active=visible[0]
    corners=[]
    for o in visible:
        for v in o.bound_box: corners.append(o.matrix_world @ Vector(v))
    lo=[min(getattr(v,k) for v in corners) for k in ('x','y','z')] if corners else [0,0,0]
    hi=[max(getattr(v,k) for v in corners) for k in ('x','y','z')] if corners else [0,0,0]
    dest=os.path.join(root,name+'.glb')
    ret=bpy.ops.export_scene.gltf(filepath=dest,export_format='GLB',use_selection=True,export_apply=True,export_materials='EXPORT',export_image_format='AUTO',export_cameras=False,export_lights=False)
    out.append({'asset':name,'mesh_objects':len(visible),'bounds':[[round(x,3) for x in lo],[round(x,3) for x in hi]],'export':str(ret),'path':dest,'bytes':os.path.getsize(dest) if os.path.exists(dest) else 0})
open(os.path.join(root,'converted_assets.json'),'w').write(json.dumps(out,indent=2))
print('POLYHAVEN_EXPORTS',json.dumps(out))