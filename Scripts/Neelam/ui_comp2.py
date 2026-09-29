import sys, os
from PIL import Image
root = os.path.dirname(os.path.abspath(__file__)) + "/../../Saved/"
name, layers = sys.argv[1], sys.argv[2:]
sp = root + "Screenshots/WindowsEditor/%s_scene.png" % name
base = Image.open(sp).convert("RGBA").resize((1920, 1080)) if os.path.exists(sp) else Image.new("RGBA", (1920, 1080), (70, 80, 90, 255))
for l in layers:
    base = Image.alpha_composite(base, Image.open(root + "NeelamBridge/outbox/ui/%s.png" % l).convert("RGBA"))
base.convert("RGB").save(root + "NeelamBridge/outbox/ui/%s_comp.jpg" % name, quality=88); print("ok", os.path.exists(sp))
