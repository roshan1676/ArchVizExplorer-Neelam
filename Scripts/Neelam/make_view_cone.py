"""Neelam - floor-plan view cone (plain Python + Pillow, NOT in UE). Writes SourceArt/UI/T_UI_ViewCone.png.
Authored pointing UP with its pivot at the bottom-centre: UNeelamTourWidget puts that point on the active room's
PlanPosition and rotates the image (live, from the 360 camera yaw). The room's own hotspot dot sits on top of the
pivot, so the texture is just the beam. 27 Oct: gold, more opaque wedge (the old cream beam vanished on the cream plan).
"""
import os, math
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "SourceArt", "UI", "T_UI_ViewCone.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

W, H = 800, 640                # W >= 2*tan(HALF)*H so the wedge is not clipped
HALF = math.radians(32)          # beam half angle (64 deg wedge, ~ a 360 viewer's horizontal FOV feel)
GOLD = (255, 238, 200)   # 27 Oct pm: warm white fill - gold vanished on the wood floors; the outline keeps the gold-brown
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = x - W / 2, (H - 1) - y                 # up = +dy
r = np.hypot(dx, dy) / (H - 1)                  # 0 at pivot .. 1 at the beam length
ang = np.abs(np.arctan2(dx, np.maximum(dy, 1e-3)))
inside = np.clip((HALF - ang) / math.radians(3), 0, 1) * (dy > 0)        # soft 3 deg side edge
body = 0.70 * inside * np.clip(1 - 0.75 * r, 0, 1) * (r < 1)            # 27 Oct pm: flatter fade - the steep one vanished on the wood floors
edge = np.exp(-((ang - HALF + math.radians(1.6)) / math.radians(1.4)) ** 2) * (dy > 0) * np.clip((1 - r) / 0.15, 0, 1)  # dark outline = contrast on wood
alpha = np.maximum(body, 0.92 * edge)
rgb = np.zeros((H, W, 3), np.float32); rgb[:] = GOLD
rim = np.clip(edge, 0, 1)[..., None]
rgb = rgb * (1 - rim) + np.array((110, 74, 22), np.float32) * rim
img = Image.fromarray(np.dstack([rgb, np.clip(alpha, 0, 1) * 255]).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(0.6))
img.save(OUT)
print("wrote", OUT, img.size)
