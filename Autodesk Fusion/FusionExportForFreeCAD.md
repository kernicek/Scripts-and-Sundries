# FusionExportForFreeCAD

Fusion 360 script that exports everything needed to hand a design off to FreeCAD.
Fusion has no automatic parametric-tree conversion for FreeCAD (different kernels/history
models), so this gets you the raw material for a manual rebuild rather than a one-click import.

## Install/run

Fusion -> Utilities tab -> Scripts and Add-Ins -> Scripts -> "+" (Create) -> paste
`FusionExportForFreeCAD.py`'s contents (or point Fusion at the file) -> Run. Open the design
you want to export first; the script then asks for an output folder and writes:

- `<design>.step` - whole design as one static solid (fit-check/printing use)
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

- Fusion's free Personal Use plan has, at various times, restricted STEP/IGES/SAT export.
  If the STEP export call fails, the script logs the error into `model.json` and still
  writes the DXFs and JSON - check File > Export in the UI to see what your account allows.
- Confirmed working (STEP export included) on a Personal Use account, 2026-09-08.
- Every Fusion API property access is wrapped defensively, but some fields (especially under
  `joints`/`jointMotion`) haven't been verified against every Fusion API version - a `null`
  where you expected a value likely means that property name needs adjusting.
- The first version of this script always omitted `parameters` on every timeline feature
  (an `if params:` truthiness check against an always-empty-ish API collection object).
  Fixed 2026-09-08 to check `params is not None` instead - re-export if your `model.json`
  predates this fix and has no per-feature `parameters`.
- Body-level `appearanceName`/`materialName` reflect whatever look/material is assigned per
  body in Fusion - a reasonable stand-in for "which print-color group a body belongs to"
  since body folders themselves aren't exposed by the API.
- `volume`/`area`/`boundingBox` on each body are in the API's internal database units (cm,
  cm^3), not `lengthUnits` - convert when cross-checking against the design's own units.
