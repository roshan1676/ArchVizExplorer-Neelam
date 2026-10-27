#!/bin/bash
# Hero still of each amenity level's BL_Camera -> Saved/ClaudeBridge/shots/Amen_<name>.png
# Usage: bash Tools/render_amenities.sh [ticks=30] Gym Pool ...   (names without "Amenity_")
T="$(dirname "$0")"; UE="$T/../Saved/ClaudeBridge/ue.sh"; N=${1:-30}; shift
for n in "$@"; do
  echo "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Neelam/Amenity_$n/L_Amenity_$n'); result='ok'" | bash "$UE" - 300 | grep -q '"ok": true' || { echo "$n: load FAILED"; continue; }
  echo "$n: $(bash "$T/shot.sh" BL_Camera "Amen_$n" "$N")"
done
