"""Cube faces (Unreal cameras, 92 deg FOV) -> equirectangular panorama.
python stitch_pano.py <faces_dir> <out_base> [width=16384] [fov=92]
faces_dir holds F,R,B,L,U,D as either F.png ... or MRQ frames <anything>.0000.png .. .0005.png (order F R B L U D).
Writes <out_base>_16K.jpg (and _8K.jpg when width is 16384). Unreal axes: X forward, Y right, Z up.
Self-check: python stitch_pano.py --test"""
import sys, os, glob, math
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

# face: forward, right, up (camera image x -> right, y -> down)
BASIS = {"F": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), "R": ((0, 1, 0), (-1, 0, 0), (0, 0, 1)),
         "B": ((-1, 0, 0), (0, -1, 0), (0, 0, 1)), "L": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
         "U": ((0, 0, 1), (0, 1, 0), (-1, 0, 0)), "D": ((0, 0, -1), (0, 1, 0), (1, 0, 0))}
ORDER = "FRBLUD"

def load_faces(d):
    faces = {}
    for k in ORDER:
        p = os.path.join(d, k + ".png")
        if os.path.exists(p): faces[k] = p
    if len(faces) < 6:
        frames = sorted(glob.glob(os.path.join(d, "*.png")))
        frames = [f for f in frames if f.rsplit(".", 2)[-2].isdigit()]
        assert len(frames) >= 6, "need 6 faces in %s, found %d" % (d, len(frames))
        faces = dict(zip(ORDER, frames[:6]))
    return {k: np.asarray(Image.open(v).convert("RGB"), dtype=np.float32) for k, v in faces.items()}

def stitch(faces, width=16384, fov=92.0, rows_per_chunk=256):
    H, W = width // 2, width
    t = math.tan(math.radians(fov / 2))
    out = np.zeros((H, W, 3), np.uint8)
    lon = (np.arange(W) + 0.5) / W * 2 * math.pi - math.pi          # -pi..pi, 0 = forward (+X), increasing to the right (+Y)
    for r0 in range(0, H, rows_per_chunk):
        r1 = min(H, r0 + rows_per_chunk)
        lat = math.pi / 2 - (np.arange(r0, r1) + 0.5) / H * math.pi  # +pi/2 top
        la, lo = np.meshgrid(lat, lon, indexing="ij")
        d = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
        acc = np.zeros(d.shape, np.float32); best = np.full(d.shape[:2], -1.0, np.float32)
        for k, (f, r, u) in BASIS.items():
            img = faces[k]; h, w = img.shape[:2]
            df = d @ np.array(f, np.float32)
            m = df > 1e-6
            a = np.where(m, (d @ np.array(r, np.float32)) / np.where(m, df, 1), 9)
            b = np.where(m, (d @ np.array(u, np.float32)) / np.where(m, df, 1), 9)
            a, b = a / t, b / t
            ok = m & (np.abs(a) <= 1) & (np.abs(b) <= 1) & (df > best)   # most head-on face wins
            if not ok.any(): continue
            x = (a[ok] + 1) / 2 * w - 0.5; y = (1 - b[ok]) / 2 * h - 0.5
            x0 = np.clip(np.floor(x).astype(int), 0, w - 2); y0 = np.clip(np.floor(y).astype(int), 0, h - 2)
            fx = np.clip(x - x0, 0, 1)[:, None]; fy = np.clip(y - y0, 0, 1)[:, None]
            c = (img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy) + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy
            acc[ok] = c; best[ok] = df[ok]
        out[r0:r1] = np.clip(acc + 0.5, 0, 255).astype(np.uint8)
    return out

def save(eq, base):
    im = Image.fromarray(eq)
    paths = []
    if eq.shape[1] >= 16384:
        im.save(base + "_16K.jpg", quality=97, subsampling=0); paths.append(base + "_16K.jpg")
        im.resize((8192, 4096), Image.LANCZOS).save(base + "_8K.jpg", quality=97, subsampling=0); paths.append(base + "_8K.jpg")
    else:
        im.save(base + ".jpg", quality=95); paths.append(base + ".jpg")
    return paths

def _test():
    # synthetic scene: each face a flat colour -> every equirect pixel must come from the face its direction points at
    cols = {k: np.full((64, 64, 3), 40 * i + 20, np.float32) for i, k in enumerate(ORDER)}
    eq = stitch(cols, width=512, fov=92.0)
    H, W = eq.shape[:2]
    def at(lat, lon): return eq[int((90 - lat) / 180 * H), int((lon + 180) / 360 * W)][0]
    assert at(0, 0) == 20 and at(0, 90) == 60 and at(0, 179) == 100 and at(0, -90) == 140
    assert at(85, 0) == 180 and at(-85, 0) == 220
    print("stitch self-check ok")

if __name__ == "__main__":
    if sys.argv[1] == "--test": _test(); sys.exit()
    d, base = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 16384
    fov = float(sys.argv[4]) if len(sys.argv) > 4 else 92.0
    print(save(stitch(load_faces(d), width, fov), base))
