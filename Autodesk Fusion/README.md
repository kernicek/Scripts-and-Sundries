# Autodesk Fusion

Scripts that run inside Fusion 360's Python API. Each script's `.py`/`.md` pair here is the
source of truth; Fusion doesn't read from this repo directly.

## Install/update a script

1. **Create it in Fusion first**, even for a brand-new script: Utilities tab -> Scripts and
   Add-Ins -> Scripts -> "+" (Create) -> Python -> name it to match this repo's filename exactly
   (e.g. `FusionExportBodyGroupsToSTL`). This is what makes Fusion generate the script's folder
   at `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\<Name>\<Name>.py` - that folder can't
   be created by just copying files into place ahead of time; Fusion needs to register it first.
2. **Copy this repo's `.py` file over the one Fusion just created**, replacing its placeholder
   contents. From then on, editing the repo file and re-copying it to that same path is enough
   to update the script - no need to go through Fusion's UI again for updates, only for the
   first creation of a given script name.
