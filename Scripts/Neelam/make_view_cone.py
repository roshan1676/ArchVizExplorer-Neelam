"""Neelam - "you are here" floor-plan indicator: a point + spreading cone showing camera position/facing inside a
room (plain Python + Pillow, NOT in UE - like make_branding.py). Writes SourceArt/UI/T_UI_ViewCone.png.
Authored pointing UP (local +Y) with its pivot (the dot) at the bottom-centre, so UNeelamTourWidget can place the
dot at FNeelamRoom.PlanPosition and rotate the whole image by FNeelamRoom.StartYaw around that same point.
"""
import os, math
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "SourceArt", "UI", "T_UI_ViewCone.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

W, H = 420, 640
S = 4   # supersample for soft edges
img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
cx, cy = W * S / 2, H * S - 1   # pivot: bottom-centre
cone_len = H * S * 0.92
half_angle = math.radians(28)   # beam spread

# soft conical beam (several overlaid wide-to-narrow triangles for a smooth falloff instead of a hard edge)
for i in range(60, 0, -1):
    t = i / 60.0                      # 1 (wide/near, faint) -> 0 (tip, would be bright but we stop short)
    length = cone_len * (0.25 + 0.75 * (1 - t) ** 0.6)
    ang = half_angle * (0.35 + 0.65 * t)
    ax, ay = cx - math.sin(ang) * length, cy - math.cos(ang) * length
    bx, by = cx + math.sin(ang) * length, cy - math.cos(ang) * length
    alpha = int(70 * (1 - t) ** 1.6)
    draw.polygon([(cx, cy), (ax, ay), (bx, by)], fill=(255, 247, 225, alpha))
img = img.filter(ImageFilter.GaussianBlur(S * 3))

# bright point glow at the pivot, drawn last (sharper, on top of the softened beam)
glow = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r, a in ((9, 255), (20, 160), (34, 90), (52, 40)):
    rr = r * S
    gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(255, 250, 235, a))
glow = glow.filter(ImageFilter.GaussianBlur(S * 1.5))
img = Image.alpha_composite(img, glow)
# crisp white core
cd = ImageDraw.Draw(img)
r0 = 7 * S
cd.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], fill=(255, 255, 255, 255))

img = img.resize((W, H), Image.LANCZOS)
img.save(OUT)
print("wrote", OUT, img.size)
