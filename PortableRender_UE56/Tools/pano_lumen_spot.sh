#!/bin/bash
# Full-res (4096 per face) Lumen panorama of ONE spot, done safely: one spot's 6 captures spawned, ticked
# across separate bridge calls (real engine frames between them, same proven pattern as pano_preview.sh),
# then exported+destroyed before returning - never leaves a heavy batch sitting in the level.
# Usage: bash Tools/pano_lumen_spot.sh <unit> <spot> <x> <y> [ticks=6] [bias=0.0]
R="$(cd "$(dirname "$0")/.." && pwd)"; UE="$R/Saved/ClaudeBridge/ue.sh"
UNIT=$1; SPOT=$2; X=$3; Y=$4; N=${5:-6}; BIAS=${6:-0.0}
echo "import pano_lumen as PL, importlib; importlib.reload(PL); result = PL.render_spot_start('$UNIT', '$SPOT', $X, $Y, bias=$BIAS)" | bash "$UE" - 60
for i in $(seq 1 "$N"); do
  echo "import pano_lumen as PL; result = PL.tick_batch()" | bash "$UE" - 60 >/dev/null
done
echo "import pano_lumen as PL; result = PL.render_spot_finish('$UNIT')" | bash "$UE" - 90
D="$R/Saved/Pano/faces/${UNIT}_${SPOT}"
OUT="$R/Saved/Final/Panoramas"
mkdir -p "$OUT/16K" "$OUT/8K" "$R/Saved/Pano/_stitched"
"C:/Users/Admin/AppData/Local/Programs/Python/Python314/python.exe" "$R/Tools/stitch_pano.py" "$D" "$R/Saved/Pano/_stitched/${UNIT}_${SPOT}" 16384
mv "$R/Saved/Pano/_stitched/${UNIT}_${SPOT}_16K.jpg" "$OUT/16K/${UNIT}_${SPOT}_16K.jpg"
mv "$R/Saved/Pano/_stitched/${UNIT}_${SPOT}_8K.jpg" "$OUT/8K/${UNIT}_${SPOT}_8K.jpg"
echo "DONE $UNIT $SPOT -> $OUT/16K/${UNIT}_${SPOT}_16K.jpg"
