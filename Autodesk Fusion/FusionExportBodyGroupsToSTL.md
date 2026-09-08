# FusionExportBodyGroupsToSTL

Fusion 360 script for multi-material prints on Wanda: each body group (e.g. `PRAHA_A`, `CREW_E`)
is one filament/color, so the slicer needs one STL per group instead of one for the whole model.
Fully automatic - one run exports every group in the design.

## Setup (once per design)

Fusion's custom Bodies browser folders have no API in this Fusion version (confirmed by
dumping every `folder`/`group`/`item`-named class in `adsk.fusion` - nothing matched), so this
script can't see them. Instead it groups bodies by a name prefix. Run
[FusionSetBodyGroupPrefix](FusionSetBodyGroupPrefix.md) once on each group's selected bodies to
tag their names before using this script. Already-prefixed bodies don't need re-tagging.

**Two prefix shapes, picked per design, not mixed within one:**
- `Type_Letter_...` (e.g. `PRAHA_A_contact`) - for a design with a top-level Type split, like
  this one's `PRAHA`/`CREW` folders each holding `A`-`E` letter folders.
- `Letter_...` (e.g. `A_contact`) - for a design with **no** Type level, just letter groups.

Which shape to use for a given file follows that file's own folder structure (or lack of a
top level) - it's a per-file choice, made once when you run the prefix script on that file's
bodies, not something this export script decides on its own.

## What it does

1. Reads every body directly under the root component's name and parses a leading
   `Type_Letter_` or `Letter_` prefix. Unprefixed bodies are left alone and listed as skipped
   in the summary.
2. Groups bodies by `(Type, Letter)`.
3. Within a group, keeps only the bodies that were **already visible** before the script ran -
   that's how you choose which alternate (e.g. a binary-encoded year's 0/1 bit) gets exported;
   the script only reads visibility, it doesn't decide anything from names alone. A group with
   no visible member is skipped.
4. Asks once for an output folder (remembered between runs, pre-filled next time).
5. For each non-empty group: temporarily hides every body not in that group's visible set,
   exports the whole design to `<design-name>_<Type>_<Letter>.stl` (or `<design-name>_<Letter>.stl`
   for a Type-less design), moves to the next group. Every body's visibility is restored to
   exactly what it was before the script ran once all exports are done - it only ever hides
   bodies mid-run, never un-hides one, so nothing you'd deliberately hidden stays shown.

Example: `Future Gate ID Badge(2) v52_PRAHA_A.stl`.

## Run

Fusion -> Utilities -> Scripts and Add-Ins -> Scripts -> Run `FusionExportBodyGroupsToSTL`. No
selection needed - it scans every body in the design.

## Caveats

- Not run against a live Fusion session yet - `ui.activeSelections`/`ui.inputBox` behavior was
  confirmed missing-folder-wise, but this script's own calls (`BRepBody.entityToken`,
  `createSTLExportOptions(component, filename)`, `design.attributes`) haven't been. Failures
  show a traceback in a message box, which is enough to patch the exact line.
- Assumes all bodies live directly in the root component (no sub-components/occurrences) - the
  visibility save/restore loop only walks `root.bRepBodies`.
- STL mesh refinement is set to Fusion's "High" setting; edit `stl_options.meshRefinement` in
  the script to change it.
