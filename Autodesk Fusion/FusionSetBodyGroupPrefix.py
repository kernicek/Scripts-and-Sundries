"""Fusion 360 script: prefix the selected bodies' names with a group tag (Type_Letter or Letter).
One-time setup for FusionExportBodyGroupsToSTL.py, which groups bodies by this prefix instead of
by browser folder (Fusion's custom Bodies folders have no API - see that script's .md).
See FusionSetBodyGroupPrefix.md for details.
"""

import adsk.core
import adsk.fusion
import re
import traceback

PREFIX_INPUT_RE = re.compile(r'^(?:[A-Za-z0-9]+_)?[A-Z]$')
EXISTING_PREFIX_RE = re.compile(r'^(?:[A-Za-z0-9]+_)?[A-Z]_')


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design. Open a design (not a drawing) and re-run.')
            return

        selections = ui.activeSelections
        bodies = []
        for i in range(selections.count):
            body = adsk.fusion.BRepBody.cast(selections.item(i).entity)
            if body:
                bodies.append(body)

        if not bodies:
            ui.messageBox(
                'Nothing selected.\n\n'
                'Select every body for this group in the browser (visible and hidden alike), '
                'then run this script.'
            )
            return

        prefix, cancelled = ui.inputBox(
            'Group prefix for the {} selected body(ies) - "PRAHA_A", "CREW_E", or just "A" '
            'if there\'s no top-level type for this file:'.format(len(bodies)),
            'Set body group prefix', ''
        )
        if cancelled:
            return
        prefix = prefix.strip()
        if not PREFIX_INPUT_RE.match(prefix):
            ui.messageBox(
                'Prefix must be a single trailing uppercase letter, optionally preceded by a '
                'type and underscore - e.g. "A" or "PRAHA_A". Got: {!r}'.format(prefix)
            )
            return

        renamed = 0
        for body in bodies:
            base = EXISTING_PREFIX_RE.sub('', body.name, count=1)
            body.name = prefix + '_' + base if base else prefix

            renamed += 1

        ui.messageBox('Prefixed {} body(ies) with "{}_".'.format(renamed, prefix))

    except Exception:
        if ui:
            ui.messageBox('Script failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    pass
