"""Warm-grade the amenity 360s (the aerial HDRI gives a strong blue cast) and copy them to the Neelam project as
SourceArt/Amenities/Panoramas/UE/<pin id>.jpg (8K), ready for import as T_Pano_Amenity_<id>_UE.
usage: python grade_amenity_panos.py [Name ...]   (default: every level in MAP that has a render)"""
import sys, os, numpy as np
from PIL import Image, ImageEnhance

SRC = r"C:/Users/Admin/Documents/Unreal Projects/Room_render/Saved/Final/Panoramas/8K"
DST = r"C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/Amenities/Panoramas/UE"
MAP = {"Pool": ["pool", "toddler"], "Court": ["court"], "PickleBall": ["padel"], "JoggingTrack": ["track"],
       "PartyLawn": ["lawn"], "Pavilion": ["pergola"], "Senior": ["senior"], "Washroom": ["toilets"], "FireRoom": ["fire"],
       "STP": ["stp"], "CarPark": ["parking"], "Gym": ["gym"], "Path": ["garden"], "Lightings": ["wall"],
       "Building": ["clubhouse"], "Cabin": ["cabin"]}   # clubhouse / cabin: no pin in the app yet

LIFT = {"CarPark": 0.6, "FireRoom": 0.8}

def grade(im):
    return im   # ponytail: sun renders need no grade (old warm grade looked grey); re-enable below if wanted
    a = np.asarray(im).astype(np.float32) / 255
    a = a * np.array([1.14, 1.03, 0.80])                       # warm white balance (sky-only light is very blue)
    lum = a.mean(-1, keepdims=True)
    a = lum + (a - lum) * 0.80                                 # tame the saturated HDRI blue
    a = np.clip(a * 1.08, 0, 1) ** 0.85                        # lift the shadowed floors
    out = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    return ImageEnhance.Contrast(out).enhance(1.04)

if __name__ == "__main__":
    os.makedirs(DST, exist_ok=True)
    for name in (sys.argv[1:] or MAP):
        f = os.path.join(SRC, "Amenity_%s_360_8K.jpg" % name)
        if not os.path.exists(f): print("skip", name); continue
        g = grade(Image.open(f).convert("RGB"))
        if name in LIFT:   # dark enclosed interiors: lift shadows (gamma), cheaper than another render
            a = np.asarray(g).astype(np.float32) / 255
            g = Image.fromarray((np.clip(a, 0, 1) ** LIFT[name] * 255 + 0.5).astype(np.uint8))
        for pid in MAP[name]:
            g.save(os.path.join(DST, pid + ".jpg"), quality=92); print(name, "->", pid)
