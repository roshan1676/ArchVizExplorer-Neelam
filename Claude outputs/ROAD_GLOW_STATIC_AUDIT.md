# Road glow static audit (27 Oct 2026)

Scope: inspect the road-glow scripts, road data, and saved editor reports without running Unreal, Blender, or any GPU work. No project scripts, assets, or road data were changed.

## What the existing fix actually targets

In its key-road glow pass, `Scripts/Neelam/Fix_Highway_Glow.py` modifies at most three spline actors: `Road_eeh`, `Road_vb`, and `Road_mar` (lines 65–99). These are the long shared glow ribbons for Eastern Express Highway, V B Phadke Marg, and Mulund–Airoli Link Road. It also processes `Route_*` landmark-route actors separately (lines 100 onward).

The 61 `rd_<OSM id>` entries in `Scripts/Neelam/Data/road_build.json` are road-deck source segments, not individual glow ribbons. The fix builds its per-group spatial lookup from all 61 entries. The saved editor inventory in `Saved/NeelamBridge/outbox/50_check_roadglow_vaze.json` shows the same distinction: three `BP_Route_C` glow actors plus `StaticMeshActor` deck actors named `Road_<group>_<OSM id>`. `54_tag_roadglow.json` confirms that the three top-level glow actors were tagged; it does not record a per-segment height change.

Therefore, the verified answer is **three group-level glow actors were targeted; no `rd_*` deck actor receives an individual height offset from `Fix_Highway_Glow.py`.** The source does not support a definitive per-OSM-ID “+60 cm applied” list.

## Height values in checked-in road scripts

- `Fix_Highway_Glow.py`: it adds `DECK=12 cm` and `LIFT=30 cm` to the selected `road_build.json` point Z; the median branch adds another 10 cm. Thus generated glow points are `+42 cm` over the selected point Z for a single-carriageway snap and `+52 cm` over the higher selected point Z for a detected median.
- `Ribbon_Heights.py`: sets each of the three key-road ribbons to traced surface plus `35 cm`.
- `Ribbon_Clearance.py`: audits/raises ribbons against traced surfaces to the documented `35 cm` road-glow clearance.
- `Glow_Smooth.py`: adjusts XY zig-zags only and explicitly leaves Z unchanged.

I found no `+60 cm` road-glow constant in the checked-in `Scripts/Neelam` Python files. That reported value may have come from an untracked/editor-only operation or an earlier state; it needs live-editor verification after the current render batch is clear.

## Static approximation of which deck IDs the key-glow alignment uses

I replayed the candidate-selection logic from `Fix_Highway_Glow.py` against `road_build.json` and the saved original line points in `Data/key_road_src.json`, using straight interpolation between source points at the script’s 8 m sampling interval. The candidate filters were preserved: same group, width at least 6.9 m, tangent alignment at least 0.85, within 26 m; for a single-road snap the nearest point must be within 12 m. This estimates which deck IDs could contribute to the line’s snapping; it is not a substitute for an Unreal spline/report and does not prove a per-ID Z edit.

| Group | Total deck IDs | IDs selected as nearest deck references in the static approximation | Not selected in the approximation |
|---|---:|---|---|
| `eeh` | 33 | `rd_131599713`, `rd_1327359089`, `rd_1327359090`, `rd_1329846727`, `rd_1329846728`, `rd_1329846729`, `rd_1329846730`, `rd_185467297`, `rd_376048885`, `rd_376048886`, `rd_52514696`, `rd_618748746`, `rd_618748750`, `rd_618748755`, `rd_618748758`, `rd_618748759`, `rd_618748765`, `rd_618748767`, `rd_618748774` | `rd_131599712`, `rd_1327359091`, `rd_1327359092`, `rd_1327359093`, `rd_185467270`, `rd_185467274`, `rd_606337023`, `rd_606337024`, `rd_618748788`, `rd_618748795`, `rd_620343767`, `rd_620857542`, `rd_620857546`, `rd_620857547` |
| `vb` | 15 | `rd_1272021839`, `rd_1272021840`, `rd_1273848775`, `rd_1392319089`, `rd_1525111941`, `rd_49591909`, `rd_632266778`, `rd_666847768`, `rd_666848287` | `rd_1094395914`, `rd_1273848776`, `rd_1457086517`, `rd_1457086522`, `rd_632266774`, `rd_788448077` |
| `mar` | 13 | `rd_1199966858`, `rd_1199966898`, `rd_1238856880`, `rd_469039168`, `rd_469039169`, `rd_469497530`, `rd_469497532`, `rd_584887817`, `rd_584887818`, `rd_621990857`, `rd_621990858`, `rd_621990859` | `rd_621990856` |

The selected/unselected split is **algorithmic alignment coverage only**. “Not selected” means that ID was never the nearest qualifying deck point at an 8 m sample in this approximation; it does not establish that the deck or road is visually broken.

## Likely Eastern Express Highway segment near the road label

`Build_Surroundings.py` places `Label_eeh` at the midpoint of the `eeh` connectivity path. That midpoint is `[19.1442477, 72.9504122]`. Comparing it with the OSM way geometries whose IDs are in `road_build.json` gives these nearest EEH deck segments:

1. `rd_618748759` — effectively on the midpoint line.
2. `rd_1327359090` — about 14 m away.
3. `rd_376048886` — about 17 m away.
4. `rd_1327359089` — about 29 m away.

`rd_618748759` and `rd_1327359090` are the strongest pair to inspect first for a symptom at/near the `Label_eeh` position. This does **not** uniquely identify the location in the user’s screenshot: the highway label is just the midpoint of a roughly 5 km path, and the screenshot’s camera/road coordinates are not in the static data I reviewed.

## Practical follow-up for Claude

After the amenity render batch completes, verify the reported stretch in the live editor before applying any offset. Start with `Road_eeh` and the four nearby deck IDs above. For a strict all-road audit, `Ribbon_Clearance.py` currently reads only three top-level road ribbons (`Road_eeh`, `Road_vb`, `Road_mar`) from `ribbon_surface.json`; it does not audit each of the 61 deck mesh actors individually. A per-deck visual/height audit still needs a deliberate editor-side check once the GPU is available.
