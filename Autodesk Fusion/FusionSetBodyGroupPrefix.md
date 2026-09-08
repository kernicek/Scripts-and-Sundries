# FusionSetBodyGroupPrefix

One-time setup for [FusionExportBodyGroupsToSTL](FusionExportBodyGroupsToSTL.md): tags a batch
of selected bodies with a group prefix (`PRAHA_A_`, `A_`, ...) so that script can find them by
name. Needed because Fusion's custom Bodies browser folders (the ones you organize bodies into,
e.g. `PRAHA` > `A_...`) have no API in this Fusion version - there's nothing to read folder
membership from, so the group has to live in the body name instead.

## Run

1. In the browser, select every body belonging to one group - both a binary contact's visible
   bit and its hidden alternate, everything nominally under that folder.
2. Fusion -> Utilities -> Scripts and Add-Ins -> Scripts -> Run `FusionSetBodyGroupPrefix`.
3. Type the group prefix. Two shapes, pick whichever matches *this file's* folder structure -
   don't mix them within one design:
   - `PRAHA_A` (type + letter) - for a design that has top-level Type folders, like this one's
     `PRAHA`/`CREW`.
   - `A` (letter only) - for a design with no Type level at all, just letter folders.
4. Repeat per group.

Each selected body's name becomes `<prefix>_<rest of its old name>`. Re-running on bodies that
already carry a recognized prefix (`Word_X_...` or `X_...`) replaces just that prefix rather
than stacking a new one in front - safe to re-run if you picked the wrong prefix the first time.

## Caveats

- Not run against a live Fusion session yet - if `ui.inputBox` or `BRepBody.name` assignment
  don't behave as expected, the failure shows in a message box with the traceback.
- The prefix-detection regex only recognizes a *single trailing uppercase letter* as the
  "letter" part (`A`-`Z`, not `AA` or `1`). If your letters are ever multi-character, both this
  script's `EXISTING_PREFIX_RE` and the export script's `GROUP_RE` need the same adjustment.
