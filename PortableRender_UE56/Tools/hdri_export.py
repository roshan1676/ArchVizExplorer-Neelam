"""World HDRI -> <out_dir>/sky.hdr + world.json (Easy HDRI sky strength + mapping rotation). NEVER saves the .blend.
blender --background --factory-startup <file.blend> --python hdri_export.py -- <out_dir>"""
import bpy, sys, os, json
out = sys.argv[sys.argv.index("--") + 1]
img, info = None, {"strength": 1.0, "rot_z": 0.0}
def walk(nt):
    global img
    for n in nt.nodes:
        if n.type == 'TEX_ENVIRONMENT' and n.image: img = n.image
        if n.type == 'MAPPING': info["rot_z"] = n.inputs["Rotation"].default_value[2]
        if n.type == 'GROUP' and n.node_tree:
            if "Sky Strength" in n.inputs: info["strength"] = n.inputs["Sky Strength"].default_value * n.inputs["Strength"].default_value
            if "Rotation" in n.inputs: info["rot_z"] += n.inputs["Rotation"].default_value[2]
            walk(n.node_tree)
        if n.type == 'BACKGROUND' and nt == bpy.context.scene.world.node_tree: info["strength"] = n.inputs["Strength"].default_value
walk(bpy.context.scene.world.node_tree)
img.file_format = 'HDR'
img.save_render(os.path.join(out, "sky.hdr"))
info["source"] = bpy.path.abspath(img.filepath)
json.dump(info, open(os.path.join(out, "world.json"), "w"), indent=1)
print("@@DONE", info)
