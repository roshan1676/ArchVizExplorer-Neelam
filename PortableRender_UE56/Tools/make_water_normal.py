"""Seamless pool-water ripple normal map (OpenGL-style +Y green is NOT used: written DirectX, so no flip in UE).
Height = sum of random sine waves with integer frequencies (tileable), soft calm-pool amplitude."""
import numpy as np, os
from PIL import Image
N = 1024; rng = np.random.default_rng(7)
y, x = np.mgrid[0:N, 0:N] / N * 2 * np.pi
h = np.zeros((N, N))
for _ in range(48):
    kx, ky = rng.integers(-14, 15, 2)
    if kx == 0 and ky == 0: continue
    k = np.hypot(kx, ky); h += np.sin(kx * x + ky * y + rng.uniform(0, 2 * np.pi)) / k ** 1.2
gy, gx = np.gradient(h)
s = 6.0                                        # bump strength (material RippleAmount scales it further)
n = np.dstack([-gx * s, gy * s, np.ones_like(h)])   # DirectX: green = -dH/dy in image space -> +gy
n /= np.linalg.norm(n, axis=2, keepdims=True)
out = os.path.join(os.path.dirname(__file__), "..", "SourceArt", "PBR", "T_WaterRipple_N.png")
Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).save(out); print("wrote", os.path.abspath(out))
