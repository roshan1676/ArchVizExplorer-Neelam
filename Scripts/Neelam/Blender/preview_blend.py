# blender -b file --python preview_blend.py -- out.png : quick Workbench/Eevee render of the whole file from a 3/4 view
import bpy, sys, mathutils, math
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
mn = mathutils.Vector((1e9,)*3); mx = mathutils.Vector((-1e9,)*3)
for o in sc.objects:
    if o.type == "MESH":
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c); mn = mathutils.Vector(map(min, mn, w)); mx = mathutils.Vector(map(max, mx, w))
ctr = (mn + mx) / 2; r = (mx - mn).length
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.location = ctr + mathutils.Vector((r * 0.6, -r * 1.1, r * 0.55))
cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun); sun.rotation_euler = (0.8, 0.3, 0.6)
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
sc.render.resolution_x, sc.render.resolution_y = 640, 400; sc.render.filepath = out
bpy.ops.render.render(write_still=True)
