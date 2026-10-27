#!/bin/bash
# One 360 Lumen panorama per amenity level, at BL_Camera x/y, eye height above ground.
# Usage: bash Tools/pano_amenities.sh [ticks=20] Pool:4.5:6 Court ...   (names without "Amenity_"; :u:v = top-down grid pick, else auto spot)
#   :u:v:sky = also swap the level's HDRI for SourceArt/HDRI/<sky>.hdr (re-runs scene_builder.environment, saves)
# -> Saved/Final/Panoramas/{16K,8K}/Amenity_<name>_360_{16K,8K}.jpg
R="$(cd "$(dirname "$0")/.." && pwd)"; UE="$R/Saved/ClaudeBridge/ue.sh"; N=${1:-20}; shift
OUT="$R/Saved/Final/Panoramas"; mkdir -p "$OUT/16K" "$OUT/8K" "$R/Saved/Pano/_stitched"
for a in "$@"; do
  IFS=: read n PU PV SKY H0 <<< "$a"; U="Amenity_$n"
  [ -n "$PV" ] && Q="PL.spot_at('$n', $PU, $PV, ${H0:-250})" || Q="PL.amenity_spot()"
  echo "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Neelam/$U/L_$U'); result='ok'" | bash "$UE" - 600 | grep -q '"ok": true' || { echo "$n: load FAILED"; continue; }
  echo "import pano_lumen as PL; result = PL.cleanup_orphans()" | bash "$UE" - 60 >/dev/null
  if [ -n "$SKY" ]; then
    cp "$R/SourceArt/HDRI/$SKY.hdr" "$R/SourceArt/$U/sky.hdr"
    echo "import unreal, importlib, scene_builder as SB; importlib.reload(SB); SB.environment('$U'); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); result='ok'" | bash "$UE" - 300 | grep -q '"ok": true' || { echo "$n: sky FAILED"; continue; }
  fi
  if [ -n "$SUN" ]; then
    echo "import unreal, pano_lumen as PL, importlib; importlib.reload(PL); PL.add_sun($SUN${SUNDIR:+, $SUNDIR}); unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); result='ok'" | bash "$UE" - 120 | grep -q '"ok": true' || echo "$n: sun FAILED"
  fi
  S=$(echo "import pano_lumen as PL, importlib; importlib.reload(PL); result = $Q" | bash "$UE" - 60 | tr -d '\n ' | grep -o '"result":\[[^]]*\]' | grep -o '\[.*\]' | tr -d '[]')
  [ -z "$S" ] && { echo "$n: no BL_Camera spot"; continue; }
  IFS=, read X Y Z <<< "$S"
  echo "import pano_lumen as PL; result = PL.render_spot_start('$U', '360', $X, $Y, z=$Z, bias=${BIAS:-0.0})" | bash "$UE" - 60 | grep -q '"ok": true' || { echo "$n: start FAILED"; continue; }
  for i in $(seq 1 "$N"); do echo "import pano_lumen as PL; result = PL.tick_batch()" | bash "$UE" - 60 >/dev/null; done
  echo "import pano_lumen as PL; result = PL.render_spot_finish('$U')" | bash "$UE" - 120 >/dev/null
  "C:/Users/Admin/AppData/Local/Programs/Python/Python314/python.exe" "$R/Tools/stitch_pano.py" "$R/Saved/Pano/faces/${U}_360" "$R/Saved/Pano/_stitched/${U}_360" 16384 >/dev/null \
    && mv "$R/Saved/Pano/_stitched/${U}_360_16K.jpg" "$OUT/16K/" && mv "$R/Saved/Pano/_stitched/${U}_360_8K.jpg" "$OUT/8K/" \
    && echo "$(date +%H:%M) DONE $n at ($X,$Y,$Z)" || echo "$n: stitch FAILED"
done
