# FusionExportForFreeCAD

Fusion 360 script that exports everything needed to hand a design off to FreeCAD.
Fusion has no automatic parametric-tree conversion for FreeCAD (different kernels/history
models), so this gets you the raw material for a manual rebuild rather than a one-click import.

## Install/run

Fusion -> Utilities tab -> Scripts and Add-Ins -> Scripts -> "+" (Create) -> paste
`FusionExportForFreeCAD.py`'s contents (or point Fusion at the file) -> Run. Open the design
you want to export first; the script then asks for an output folder and writes:

- `<design>.step` - whole design as one static solid (fit-check/printing use)
- `<design>.f3d` - full Fusion archive (native format, includes the parametric feature
  history) - an offline backup of the source design outside Autodesk's cloud, re-importable
  into any Fusion install via File > Open. Not consumed by FreeCAD; this is purely a backup.
- `sketches/*.dxf` - every sketch, one DXF each, re-traceable in FreeCAD
- `model.json` - user parameters, the full timeline in feature order (each feature's type,
  operation, driving dimensions via Fusion's generic `parameters` collection, plus
  type-specific detail: extrude extents/distances, chamfer edge-set distances, pattern
  quantities/spacing and input names, combine target/tool body names, split-tool name,
  construction plane offset/reference), component/body list (each body's name, visibility,
  appearance/material name, volume, area, bounding box), occurrence tree with transforms,
  and joints

Use `model.json` as the reference while manually rebuilding the feature tree in FreeCAD's
Part Design workbench: import each DXF as a sketch trace, re-add constraints, redo
Pad/Pocket/Revolve/Fillet/etc. in the same timeline order, using the JSON's parameter values
for dimensions.

## Caveats

- Fusion's free Personal Use plan has, at various times, restricted STEP/IGES/SAT export
  (the Fusion archive/.f3d export is Fusion's own native format and isn't known to be
  restricted the same way). If either export call fails, the script logs the error into
  `model.json` and still writes everything else - check File > Export in the UI to see
  what your account allows.
- Confirmed working (STEP export included) on a Personal Use account, 2026-09-08.
- Every Fusion API property access is wrapped defensively, but some fields (especially under
  `joints`/`jointMotion`) haven't been verified against every Fusion API version - a `null`
  where you expected a value likely means that property name needs adjusting.
- The first version of this script always omitted `parameters` on every timeline feature
  (an `if params:` truthiness check against an always-empty-ish API collection object).
  Fixed 2026-09-08 to check `params is not None` instead - though in practice Fusion's
  generic `Feature.parameters` collection is empty for most feature types anyway; the
  real dimensions live on type-specific sub-objects, which is what the type-specific
  detail (extentOne/edgeSets/quantityOne/etc.) actually pulls from.
- Second round of fixes, also 2026-09-08, against the real Fusion API stubs
  (github.com/AutodeskFusion360/FusionAPIReference): `ChamferFeature.edgeSets` (not
  `chamferEdgeSets`), `SplitBodyFeature.splitBodies` (not `participantBodies`), and a
  routing bug that skipped `ConstructionPlane.definition` entirely (it isn't a `Feature`
  subtype, so it never reached the feature-detail dumper). Also: `CombineFeature.targetBody`/
  `toolBodies`, `SplitBodyFeature.splittingTool`, `RectangularPatternFeature.inputEntities`,
  `ChamferEdgeSet.edges`, and `CopyPasteBody.sourceBody` only resolve correctly with the
  timeline marker rolled back to immediately before that feature (Autodesk's own docs note
  this per-property); the script now does `item.rollTo(True)` before reading these and
  `timeline.moveToEnd()` afterward every time, restoring the full model at the end. If
  your `model.json` predates this fix, re-export.
- Body-level `appearanceName`/`materialName` reflect whatever look/material is assigned per
  body in Fusion - a reasonable stand-in for "which print-color group a body belongs to"
  since body folders themselves aren't exposed by the API. If body names already encode
  the folder/variant (e.g. a naming convention like `PRAHA_A_...`), that's more reliable
  than appearance and should be preferred when present.
- `volume`/`area`/`boundingBox` on each body are in the API's internal database units (cm,
  cm^3), not `lengthUnits` - convert when cross-checking against the design's own units.
- The rollback described above means the export visibly scrubs the 3D view back and forth
  through the timeline as it runs (once per Combine/Split/Pattern/CopyPasteBody/Chamfer
  feature) - that's expected, not a hang; it's navigation only, nothing is edited, and the
  script always ends by moving the marker back to the end of the timeline.
