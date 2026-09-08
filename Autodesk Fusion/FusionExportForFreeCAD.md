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
  operation, and driving dimensions via Fusion's generic `parameters` collection, plus
  edge/face counts for fillets/chamfers), component/body list, occurrence tree with
  transforms, and joints

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
