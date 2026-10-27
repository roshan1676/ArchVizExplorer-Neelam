# Runs automatically when the Unreal Editor starts (Python plugin).
import os, sys, importlib
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.append(_here)
import claude_bridge
importlib.reload(claude_bridge)
# One-click render: RENDER_ALL.bat creates this flag before opening the editor
import unreal as _u, os as _os
_flag = _os.path.join(_u.Paths.convert_relative_path_to_full(_u.Paths.project_saved_dir()), "ClaudeBridge", "RENDER_ALL.flag")
if _os.path.exists(_flag):
    _os.remove(_flag)
    import run_all  # waits 90 s, then renders everything and finalizes
