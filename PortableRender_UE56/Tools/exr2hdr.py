import bpy, glob
for src, name in [(glob.glob(r"C:/Users/Admin/blenderkit_data/hdrs/*/aerial-city-neighborhood-sunny*.exr")[0], "aerial_city_sunny"),
                  (glob.glob(r"C:/Users/Admin/blenderkit_data/hdrs/*/city-night-sky-twilight*.exr")[0], "city_twilight"),
                  (glob.glob(r"C:/Users/Admin/blenderkit_data/hdrs/*/aerial-city-neighborhood-morning*.exr")[0], "aerial_city_morning")]:
    im = bpy.data.images.load(src)
    s = bpy.context.scene.render.image_settings
    s.file_format = 'HDR'; im.save_render(r"C:/Users/Admin/Documents/Unreal Projects/Room_render/SourceArt/HDRI/" + name + ".hdr")
    s.file_format = 'JPEG'; s.quality = 85; im.save_render(r"C:/Users/Admin/AppData/Local/Temp/claude/C--Users-Admin-Documents-builds-AP-stream-1-Windows/2eebb9b9-5d11-4dc8-a6cd-c387432deaf6/scratchpad/" + name + ".jpg")
    print("@@", name, im.size[:])
