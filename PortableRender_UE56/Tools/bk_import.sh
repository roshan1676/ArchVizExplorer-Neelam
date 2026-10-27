#!/bin/bash
# BlenderKit asset -> Unreal-ready glTF + baked materials.  Usage: bash Tools/bk_import.sh <blenderkit model folder name> <PropName>
# Output: SourceArt/Props/<PropName>/ (scene.gltf, scene.json, baked/). Then in the editor: props.import_prop("<PropName>").
set -e
P="$(cd "$(dirname "$0")/.." && pwd)"; B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
SRC=$(ls /c/Users/Admin/blenderkit_data/models/$1/*.blend | head -1); OUT="$P/SourceArt/Props/$2"; mkdir -p "$OUT"
"$B" --background --factory-startup "$SRC" --python "$P/Tools/bk_prep.py" -- "$OUT/prep.blend" 2>&1 | grep "@@" || true
"$B" --background --factory-startup "$OUT/prep.blend" --python "$P/Tools/blend_export.py" -- "$OUT" 2>&1 | grep "@@" || true
"$B" --background --factory-startup "$OUT/prep.blend" --python "$P/Tools/bake_mats.py" -- "$OUT" 2>&1 | grep "@@DONE" || true
ls "$OUT"
