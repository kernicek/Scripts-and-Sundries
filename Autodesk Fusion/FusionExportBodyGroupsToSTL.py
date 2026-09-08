"""Fusion 360 script: export every name-prefixed body group as its own STL.
Groups are read from body names (Type_Letter_... or Letter_..., see FusionSetBodyGroupPrefix.py),
not from Fusion's browser folders - those have no API in this Fusion version. Within a group,
only the currently-visible bodies are exported (that's how a binary-encoded alternate, e.g. a
year's bit pattern, gets chosen - visibility is read, never changed by this script beyond the
temporary hide/restore needed to produce each STL).
See FusionExportBodyGroupsToSTL.md for details and setup.
"""

import adsk.core
import adsk.fusion
import os
import re
import traceback

ATTR_GROUP = 'FusionExportBodyGroupsToSTL'
ATTR_OUT_DIR = 'outDir'
GROUP_RE = re.compile(r'^(?:(?P<type>[A-Za-z0-9]+)_)?(?P<letter>[A-Z])_')


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip() or 'unnamed'


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design. Open a design (not a drawing) and re-run.')
            return

        root = design.rootComponent
        all_bodies = [root.bRepBodies.item(i) for i in range(root.bRepBodies.count)]

        groups = {}  # (type_or_None, letter) -> [body, ...]
        unprefixed = []
        for b in all_bodies:
            name = safe(lambda b=b: b.name, '')
            m = GROUP_RE.match(name)
            if not m:
                unprefixed.append(name)
                continue
            key = (m.group('type'), m.group('letter'))
            groups.setdefault(key, []).append(b)

        if not groups:
            ui.messageBox(
                'No body names matched the Type_Letter_... / Letter_... group prefix.\n'
                'Run FusionSetBodyGroupPrefix.py on each group\'s bodies first.'
            )
            return

        folder_dlg = ui.createFolderDialog()
        folder_dlg.title = 'Choose export folder for the STL files'
        last_dir = safe(lambda: design.attributes.itemByName(ATTR_GROUP, ATTR_OUT_DIR).value)
        if last_dir:
            safe(lambda: setattr(folder_dlg, 'initialDirectory', last_dir))
        if folder_dlg.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        out_dir = folder_dlg.folder
        safe(lambda: design.attributes.add(ATTR_GROUP, ATTR_OUT_DIR, out_dir))

        design_name = sanitize(safe(lambda: app.activeDocument.name, 'design'))
        original_state = [(b, safe(lambda b=b: b.isVisible, True)) for b in all_bodies]
        # Original-visibility lookup, independent of live state - a body's original visibility
        # must not depend on what a previous group's export left it toggled to mid-loop.
        original_by_token = {safe(lambda b=b: b.entityToken): state for b, state in original_state}

        errors = []
        written = []
        skipped_empty = []
        try:
            for (type_name, letter), members in sorted(groups.items(), key=lambda kv: (kv[0][0] or '', kv[0][1])):
                visible_members = [
                    b for b in members
                    if original_by_token.get(safe(lambda b=b: b.entityToken), False)
                ]
                name_parts = [design_name] + ([type_name] if type_name else []) + [letter]
                stl_name = sanitize('_'.join(name_parts)) + '.stl'

                if not visible_members:
                    skipped_empty.append(stl_name)
                    continue

                visible_tokens = set(safe(lambda b=b: b.entityToken) for b in visible_members)
                for b, state in original_state:
                    safe(lambda b=b, state=state: setattr(b, 'isVisible', state))
                for b, _ in original_state:
                    if safe(lambda b=b: b.entityToken) not in visible_tokens:
                        safe(lambda b=b: setattr(b, 'isVisible', False))

                stl_path = os.path.join(out_dir, stl_name)
                try:
                    export_mgr = design.exportManager
                    stl_options = export_mgr.createSTLExportOptions(root, stl_path)
                    stl_options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                    export_mgr.execute(stl_options)
                    written.append(stl_name)
                except Exception:
                    errors.append('{}: {}'.format(stl_name, traceback.format_exc()))
        finally:
            for b, state in original_state:
                safe(lambda b=b, state=state: setattr(b, 'isVisible', state))

        summary = 'Exported {} of {} group(s) to {}'.format(len(written), len(groups), out_dir)
        if skipped_empty:
            summary += '\n\n{} group(s) skipped (no visible body): '.format(len(skipped_empty)) + ', '.join(skipped_empty)
        if unprefixed:
            summary += '\n\n{} body(ies) with no recognized group prefix (ignored): '.format(len(unprefixed)) + ', '.join(unprefixed)
        if errors:
            summary += '\n\n{} error(s):\n'.format(len(errors)) + '\n'.join(errors)
        ui.messageBox(summary)

    except Exception:
        if ui:
            ui.messageBox('Script failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    pass
