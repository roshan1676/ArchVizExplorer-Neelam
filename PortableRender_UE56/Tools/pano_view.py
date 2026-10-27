"""Perspective view (what the 360 viewer shows) from an equirect pano.  py pano_view.py in.jpg out.jpg yaw_deg [pitch] [fov] [w] [h]
yaw 0 = pano centre column, + = right."""
import sys, numpy as np
from PIL import Image
f, out, yaw = sys.argv[1], sys.argv[2], float(sys.argv[3])
pitch = float(sys.argv[4]) if len(sys.argv) > 4 else 0; fov = float(sys.argv[5]) if len(sys.argv) > 5 else 90
W = int(sys.argv[6]) if len(sys.argv) > 6 else 1600; H = int(sys.argv[7]) if len(sys.argv) > 7 else 900
Image.MAX_IMAGE_PIXELS = None
eq = np.asarray(Image.open(f).convert("RGB")); EH, EW = eq.shape[:2]
fx = W / 2 / np.tan(np.radians(fov) / 2)
x, y = np.meshgrid(np.arange(W) - W / 2 + 0.5, np.arange(H) - H / 2 + 0.5)
d = np.stack([np.full_like(x, fx), x, -y], -1); d /= np.linalg.norm(d, axis=-1, keepdims=True)
cp, sp, cy, sy = np.cos(np.radians(pitch)), np.sin(np.radians(pitch)), np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
X = d[..., 0] * cp - d[..., 2] * sp; Z = d[..., 0] * sp + d[..., 2] * cp; Y = d[..., 1]
X, Y = X * cy - Y * sy, X * sy + Y * cy
lon = np.arctan2(Y, X); lat = np.arcsin(np.clip(Z, -1, 1))
u = ((lon / (2 * np.pi) + 0.5) * EW).astype(int) % EW; v = np.clip(((0.5 - lat / np.pi) * EH).astype(int), 0, EH - 1)
Image.fromarray(eq[v, u]).save(out, quality=92)
