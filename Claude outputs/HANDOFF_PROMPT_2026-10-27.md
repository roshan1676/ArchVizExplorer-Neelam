Continue my Neelam archviz work from a previous Claude session that ran out of credits. Two Unreal 5.6 projects on this PC:
- C:\Users\Admin\Documents\Unreal Projects\Room_render  (render project, Python bridge in Saved/ClaudeBridge, run jobs with `bash Saved/ClaudeBridge/ue.sh <file.py|-> <timeout>`)
- C:\Users\Admin\Documents\Unreal Projects\ArchVizExplorer-Neelam  (my client app, bridge in Saved/NeelamBridge, read CLAUDE.md + NEELAM_CONTEXT.md)

FIRST read the full hand-off: C:\Users\Admin\.claude\projects\C--Users-Admin-Documents-builds-AP-stream-1-Windows\memory\neelam-amenities-session-2026-10-27.md
Start with the top block ">>> HAND-OFF 12:45 <<<", then the "FLOOR PLAN AGENT STATUS" section at the bottom. It has the exact state, scripts, coordinates and gotchas. Don't re-discover what's written there.

Hard rules:
- NEVER render anything in Blender (this PC crashes). Unreal renders are OK, but tell me before you start a GPU batch and when it ends, because my Neelam preview must stay closed while Room_render renders (shared GPU: it crashed with DXGI_ERROR_DEVICE_HUNG).
- Both editors are open; don't close the Room_render editor. Close only the Neelam editor when a C++ rebuild needs it.
- Don't commit to git. I'm on a hard deadline: work in parallel where possible, give short progress updates, ask only when it really matters, and make everything look good and consistent ("nothing weird").

Remaining work, in order:
1. Amenity 360 panoramas (Room_render). Re-run the paused batch `Saved/ClaudeBridge/batch6.sh`. It renders every amenity with the new warm sun (Path is already done with sun), then rebuilds the empty Gym and CarPark levels and makes their top-downs. Then pick Gym/CarPark standing spots from the grid sheets (Tools/topdown_sheet.py) and render them. Review every result on a contact sheet: check Building (was black), the Lighting wall twilight shot (must face the lit front), and Cabin/FireRoom interiors. Re-render any that look bad.
2. Dress the amenities that look empty (Court, Party Lawn, maybe Jogging Track and the Pickleball surround). Use only props the same artist made in other amenity files (Content/Python/dress.py; untested). Check each with a top-down, then re-render.
3. Import the finished panoramas into the Neelam app SIDE BY SIDE as T_Pano_Amenity_<id>_UE. Do NOT replace the client's panoramas on the pins. Show me a before/after sheet so I can choose which to swap. The level-to-pin-id map is in the memory file.
4. Floor plan panel (Neelam). The realistic drawn 2BHK/3BHK plans, room markers, 15 new room panoramas and the live "which way the camera looks" cone are in and built. The cone's yaw mapping is NOT verified. Calibrate it in PIE with the dev pano T_Dev_PanoAxes (steps are in the memory file), then check that markers and labels are readable and don't overlap. Send me a screenshot.
5. Keep the memory file updated as you go, so another session can always take over.
