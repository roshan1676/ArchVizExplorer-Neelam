"""Rebuild C++ (NeelamTools plugin) and restart the editor - run as a NeelamBridge job.
The helper batch runs from Task Scheduler so it survives the editor closing."""
import os, subprocess
import unreal
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()).rstrip("/").replace("/", "\\")
ENG = unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir()).rstrip("/").replace("/", "\\")
NB = os.path.join(PROJ, "Saved", "NeelamBridge")
LOG = os.path.join(NB, "build_plugin.log")
PLUG = os.path.join(PROJ, "Plugins", "NeelamTools")
UPROJ = os.path.join(PROJ, "ArchVizExplorer.uproject")

def run(save=True):
    bat = os.path.join(NB, "rebuild_restart.bat")
    open(bat, "w", newline="\r\n").write(f'''@echo off
title Neelam - rebuilding C++ (Unreal reopens by itself)
:wait
tasklist /FI "IMAGENAME eq UnrealEditor.exe" | find /I "UnrealEditor.exe" >nul && (timeout /t 2 /nobreak >nul & goto wait)
echo editor closed %DATE% %TIME% > "{LOG}"
call "{ENG}\\Build\\BatchFiles\\Build.bat" Development Win64 -Project="{UPROJ}" -TargetType=Editor -Progress -NoEngineChanges -NoHotReloadFromIDE >> "{LOG}" 2>&1
set RC=%ERRORLEVEL%
echo EXITCODE %RC% >> "{LOG}"
if not "%RC%"=="0" echo BUILD FAILED - editor reopens with the previous plugin DLLs >> "{LOG}"
start "" "{ENG}\\Binaries\\Win64\\UnrealEditor.exe" "{UPROJ}"
''')
    if save:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    # Task Scheduler runs it outside the editor's process tree (child processes are killed when the editor exits)
    subprocess.run(["schtasks", "/create", "/tn", "NeelamRebuildRestart", "/tr", '"' + bat + '"', "/sc", "once", "/st", "23:59", "/f"],
                   capture_output=True, text=True, creationflags=0x08000000)
    out = subprocess.run(["schtasks", "/run", "/tn", "NeelamRebuildRestart"], capture_output=True, text=True, creationflags=0x08000000).stdout
    unreal.SystemLibrary.quit_editor()
    return out
