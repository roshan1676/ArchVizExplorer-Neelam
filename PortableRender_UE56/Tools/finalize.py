"""After rendering: Saved/Final/_raw -> Saved/Final
  Stills/8K/<name>_8K.png, Stills/4K/<name>_4K.png
  Panoramas/16K/<name>_16K.jpg, Panoramas/8K/<name>_8K.jpg   (also picks up faces in Saved/Pano/faces)
Re-runnable; skips what already exists.  python Tools/finalize.py"""
import os, sys, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stitch_pano as SP
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

SAVED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Saved")
FINAL = os.path.abspath(os.path.join(SAVED, "Final")); RAW = os.path.join(FINAL, "_raw")
for d in ("Stills/8K", "Stills/4K", "Panoramas/16K", "Panoramas/8K"): os.makedirs(os.path.join(FINAL, d), exist_ok=True)

def main():
    for p in sorted(glob.glob(os.path.join(RAW, "stills", "*.png"))):
        name = os.path.splitext(os.path.basename(p))[0]
        o8 = os.path.join(FINAL, "Stills/8K", name + "_8K.png"); o4 = os.path.join(FINAL, "Stills/4K", name + "_4K.png")
        if not os.path.exists(o8): shutil.copy2(p, o8)
        if not os.path.exists(o4):
            im = Image.open(p); im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(o4); print("still", name)
    dirs = glob.glob(os.path.join(RAW, "faces", "*")) + glob.glob(os.path.join(SAVED, "Pano", "faces", "*"))
    for d in sorted(dirs, key=os.path.basename):
        name = os.path.basename(d)
        p16 = os.path.join(FINAL, "Panoramas/16K", name + "_16K.jpg"); p8 = os.path.join(FINAL, "Panoramas/8K", name + "_8K.jpg")
        if os.path.exists(p16) and os.path.exists(p8): continue
        if len(glob.glob(os.path.join(d, "face.*.png"))) < 6: print("not rendered yet:", name); continue
        print("stitching", name, flush=True)
        im = Image.fromarray(SP.stitch(SP.load_faces(d), 16384, 92.0))
        im.save(p16, quality=97, subsampling=0); im.resize((8192, 4096), Image.LANCZOS).save(p8, quality=97, subsampling=0)
    print("\nDONE ->", FINAL)

if __name__ == "__main__":
    main()
    try: input("Press Enter to close")
    except EOFError: pass
