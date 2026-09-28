# Auto-start the NeelamBridge (live link for Claude) when the editor opens.
import os, unreal
_p = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam", "NeelamBridge.py")
if os.path.exists(_p):
    exec(compile(open(_p).read(), _p, "exec"), {"__name__": "__main__", "__file__": _p})
