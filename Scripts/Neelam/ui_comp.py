"""run in the Cowork VM: composite Saved/NeelamBridge/outbox/ui/<name>.png over Saved/Screenshots/WindowsEditor/<name>_scene.png"""
import sys, os
from PIL import Image
root = os.path.dirname(os.path.abspath(__file__)) + "/../../Saved/"
for name in sys.argv[1:]:
    ui = Image.open(root + "NeelamBridge/outbox/ui/%s.png" % name).convert("RGBA")
    sp = root + "Screenshots/WindowsEditor/%s_scene.png" % name
    bg = Image.open(sp).convert("RGBA").resize(ui.size) if os.path.exists(sp) else Image.new("RGBA", ui.size, (70, 80, 90, 255))
    out = Image.alpha_composite(bg, ui).convert("RGB"); out.save(root + "NeelamBridge/outbox/ui/%s_comp.jpg" % name, quality=88)
    print(name, os.path.exists(sp))
