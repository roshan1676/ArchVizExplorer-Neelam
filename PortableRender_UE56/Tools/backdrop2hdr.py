"""Neelam real-site backdrop (LDR equirect from Context_Backdrop.py + stitch_pano.py) -> Radiance .hdr sky for the
amenity levels. sRGB -> linear, sky brightness matched to aerial_city_sunny.hdr (already calibrated with the sun /
manual exposure). The sun itself comes from the level's DirectionalLight (PL.add_sun with Neelam's noon direction).
usage: py backdrop2hdr.py <in.jpg> <out_name>"""
import sys, os, numpy as np, cv2
R = os.path.join(os.path.dirname(__file__), "..", "SourceArt", "HDRI")
src, name = sys.argv[1], sys.argv[2]
ldr = cv2.imread(src, cv2.IMREAD_COLOR).astype(np.float32) / 255.0
lin = np.where(ldr <= 0.04045, ldr / 12.92, ((ldr + 0.055) / 1.055) ** 2.4)
ref = cv2.imread(os.path.join(R, "aerial_city_sunny.hdr"), cv2.IMREAD_UNCHANGED)
def sky_mean(a):   # upper hemisphere, without the brightest 0.5 % (sun / hot clouds)
    up = a[: a.shape[0] // 2].mean(-1).ravel(); return up[up < np.percentile(up, 99.5)].mean()
k = sky_mean(ref) / max(sky_mean(lin), 1e-6)
cv2.imwrite(os.path.join(R, name + ".hdr"), (lin * k).astype(np.float32))
print("wrote", name, "scale %.3f" % k, lin.shape)
