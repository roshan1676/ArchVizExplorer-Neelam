#!/bin/bash
# Top view + world box per amenity level -> Saved/Pano/_topdown/<name>.png + .json
R="$(cygpath -m "$(cd "$(dirname "$0")/.." && pwd)")"; UE="$R/Saved/ClaudeBridge/ue.sh"
for n in "$@"; do
  U="Amenity_$n"
  echo "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Neelam/$U/L_$U'); result='ok'" | bash "$UE" - 600 | grep -q '"ok": true' || { echo "$n: load FAILED"; continue; }
  echo "import pano_lumen as PL, importlib, json; importlib.reload(PL); PL.cleanup_orphans(); r = PL.topdown('$n'); open(r'$R/Saved/Pano/_topdown/$n.json','w').write(json.dumps(r)); result = r" | bash "$UE" - 120 | grep -q '"ok": true' && echo "$n ok" || echo "$n FAILED"
done
