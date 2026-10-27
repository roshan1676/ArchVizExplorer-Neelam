import bpy, os, json
root=r'C:/Users/Admin/Documents/Unreal Projects/Room_render/SourceArt/FreeAssets/PolyHaven'; out=[]
for name in ['shrub_01','flower_gazania','planter_box_01','outdoor_table_chair_set_01','modular_street_seating','painted_wooden_bench']:
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,name+'_2k.blend'))
 objs=[]
 for o in bpy.data.objects:
  if o.type=='MESH': objs.append({'name':o.name,'data':o.data.name,'users':o.users,'collections':[c.name for c in o.users_collection],'hide_viewport':o.hide_viewport,'hide_render':o.hide_render,'dimensions':list(o.dimensions),'selected':o.select_get() if o.name in bpy.context.view_layer.objects else False})
 imgs=[{'name':i.name,'packed':bool(i.packed_file),'path':i.filepath,'has_data':i.has_data,'size':list(i.size)} for i in bpy.data.images if i.source=='FILE']
 out.append({'asset':name,'scene_objects':[o.name for o in bpy.context.scene.objects],'mesh_objects':objs,'images':imgs,'collections':[c.name for c in bpy.data.collections]})
open(os.path.join(root,'inspect_assets.json'),'w').write(json.dumps(out,indent=2,default=str))
print('ASSET_INSPECT_DONE')