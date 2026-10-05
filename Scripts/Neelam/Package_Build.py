"""Windows Shipping build (4 Oct, client pitch): saves, closes the editor, runs BuildCookRun via a Task Scheduler batch
(survives the editor exit), archives to C:/Users/rosha/Documents/Neelam (Windows/ inside), adds a 'Neelam.lnk' shortcut,
reopens the editor. Log: Saved/NeelamBridge/package.log ("PACKAGE EXITCODE n" at the end).
Settings: Config/DefaultGame.ini (Shipping, pak+iostore, compressed, prereqs, map Realistic_01, always cook /Game/Neelam)
and Config/DefaultGameUserSettings.ini (scalability High = 2, windowed fullscreen, VSync, 60 fps cap)."""
import os, subprocess
import unreal
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()).rstrip("/").replace("/", "\\")
ENG = unreal.Paths.convert_relative_path_to_full(unreal.Paths.engine_dir()).rstrip("/").replace("/", "\\")
NB = os.path.join(PROJ, "Saved", "NeelamBridge"); LOG = os.path.join(NB, "package.log")
UPROJ = os.path.join(PROJ, "ArchVizExplorer.uproject"); OUT = r"C:\Users\rosha\Documents\Neelam"

def run():
    bat = os.path.join(NB, "package_build.bat")
    open(bat, "w", newline="\r\n").write(f'''@echo off
title Neelam - packaging Windows build (Unreal reopens by itself)
:wait
tasklist /FI "IMAGENAME eq UnrealEditor.exe" | find /I "UnrealEditor.exe" >nul && (timeout /t 3 /nobreak >nul & goto wait)
if not exist "{OUT}" mkdir "{OUT}"
echo start %DATE% %TIME% > "{LOG}"
call "{ENG}\\Build\\BatchFiles\\RunUAT.bat" BuildCookRun -project="{UPROJ}" -noP4 -platform=Win64 -clientconfig=Shipping -serverconfig=Shipping -build -cook -map=/Game/ArchVizExplorer/Maps/Realistic_01 -stage -pak -iostore -compressed -prereqs -archive -archivedirectory="{OUT}" -utf8output -unattended >> "{LOG}" 2>&1
set RC=%ERRORLEVEL%
echo PACKAGE EXITCODE %RC% %DATE% %TIME% >> "{LOG}"
if "%RC%"=="0" powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{OUT}\\Neelam.lnk'); $s.TargetPath='{OUT}\\Windows\\ArchVizExplorer.exe'; $s.WorkingDirectory='{OUT}\\Windows'; $s.Save()" >> "{LOG}" 2>&1
start "" "{ENG}\\Binaries\\Win64\\UnrealEditor.exe" "{UPROJ}"
''')
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    subprocess.run(["schtasks", "/create", "/tn", "NeelamPackage", "/tr", '"' + bat + '"', "/sc", "once", "/st", "23:59", "/f"],
                   capture_output=True, text=True, creationflags=0x08000000)
    out = subprocess.run(["schtasks", "/run", "/tn", "NeelamPackage"], capture_output=True, text=True, creationflags=0x08000000).stdout
    unreal.SystemLibrary.quit_editor()
    return out
