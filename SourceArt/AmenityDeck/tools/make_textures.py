"""Procedural textures the stores don't have at this quality (py -3.14, numpy + Pillow). Writes SourceArt/AmenityDeck/textures.
- pool_mosaic_{diff,nor,arm}: 25 mm glass mosaic, 2 mm grout, 20 x 20 tiles = 0.5 m per tile repeat, per-tile hue/value jitter
- chainlink_{diff,mask}: 50 mm diamond chain link, 3.5 mm wire, 0.2 m repeat (opacity mask)
- water_nor: tileable ripple normal (sum of random-direction waves, periodic on the tile)
"""
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")
rng = np.random.default_rng(11)


def save(a, name, mode="RGB"):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), mode).save(os.path.join(OUT, name), quality=95)


def normal_from_height(h, strength):
    gy, gx = np.gradient(h)
    n = np.dstack((-gx * strength, gy * strength, np.ones_like(h)))   # OpenGL (+Y up) normal
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return (n * 0.5 + 0.5) * 255


def mosaic(px=2048, tiles=20, grout_mm=2.0, tile_mm=25.0):
    per = px / tiles
    g = grout_mm / (tile_mm + grout_mm) * per / 2
    y, x = np.mgrid[0:px, 0:px].astype(np.float32)
    fx, fy = (x % per), (y % per)
    d = np.minimum.reduce([fx, per - fx, fy, per - fy])            # distance to tile edge (px)
    grout = d < g
    ti, tj = (x // per).astype(int), (y // per).astype(int)
    base = np.array([0.20, 0.55, 0.72])                            # aqua glass
    jit = rng.normal(0, 1, (tiles, tiles, 3)) * np.array([0.012, 0.025, 0.025]) + rng.normal(0, 0.03, (tiles, tiles, 1))
    col = np.clip(base + jit, 0, 1)[tj, ti]
    col[grout] = (0.78, 0.80, 0.80)
    # rounded tile shoulders + slight per-tile tilt for glinting
    h = np.clip((d - g) / (per * 0.08), 0, 1)
    tilt = rng.normal(0, 0.02, (tiles, tiles, 2))[tj, ti]
    h = h + (fx / per - 0.5) * tilt[..., 0] * per + (fy / per - 0.5) * tilt[..., 1] * per
    save(col * 255, "pool_mosaic_diff.jpg")
    save(normal_from_height(h, 2.5), "pool_mosaic_nor.jpg")
    arm = np.dstack((np.where(grout, 0.6, 1.0), np.where(grout, 0.85, 0.08), np.zeros_like(h)))  # AO, rough, metal
    save(arm * 255, "pool_mosaic_arm.jpg")


def chainlink(px=1024, wire_px=18):
    """Diamond chain link: two diagonal line families on a 45-degree lattice (0.2 m tile = 4 diamonds across)."""
    y, x = np.mgrid[0:px, 0:px].astype(np.float32)
    per = px / 4.0
    u, v = (x + y) % per, (x - y) % per
    du, dv = np.minimum(u, per - u), np.minimum(v, per - v)
    w = np.minimum(du, dv)
    mask = (w < wire_px / 2).astype(np.float32)
    save(mask * 255, "chainlink_mask.png", "L")
    shade = 0.10 + 0.08 * np.cos(np.clip(w / (wire_px / 2), 0, 1) * np.pi / 2)
    save(np.dstack([shade] * 3) * 255, "chainlink_diff.jpg")


def water(px=1024, waves=48):
    y, x = np.mgrid[0:px, 0:px].astype(np.float32) / px * 2 * np.pi
    h = np.zeros((px, px), np.float32)
    for _ in range(waves):
        kx, ky = rng.integers(-9, 10, 2)
        if kx == 0 and ky == 0:
            continue
        k = np.hypot(kx, ky)
        h += np.sin(kx * x + ky * y + rng.uniform(0, 6.283)) / k ** 1.4
    h = (h - h.min()) / (h.max() - h.min())
    save(normal_from_height(h * 40, 1.0), "water_nor.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mosaic(); chainlink(); water()
    for f in ("pool_mosaic_diff.jpg", "pool_mosaic_nor.jpg", "pool_mosaic_arm.jpg", "chainlink_mask.png", "chainlink_diff.jpg", "water_nor.png"):
        assert os.path.getsize(os.path.join(OUT, f)) > 1000, f
    print("ok")
