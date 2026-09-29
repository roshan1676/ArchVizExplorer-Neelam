#!/bin/bash
# usage: pv.sh NAME BUTTON  (run in Cowork VM) - PIE must be running
NB="$HOME/mnt/ArchVizExplorer-Neelam/Saved/NeelamBridge"
cat > $NB/inbox/pv_$1.py <<PY
import sys, importlib; sys.path.insert(0, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam")
import ui_preview as U; importlib.reload(U)
mm = U.pc().get_editor_property("MasterMenu")
if "$2": mm.get_editor_property("$2").on_clicked.broadcast()
result = 1
PY
sleep 4
cat > $NB/inbox/pvr_$1.py <<PY
import ui_preview as U
mm = U.pc().get_editor_property("MasterMenu")
result = [U.render(mm, "$1"), U.scene("$1")]
PY
sleep 12
python3 $HOME/mnt/ArchVizExplorer-Neelam/Scripts/Neelam/ui_comp.py $1
