"""Fusion 360 script: export everything needed to rebuild a design in FreeCAD.
See FusionExportForFreeCAD.md for what it writes and how to run it.
"""

import adsk.core
import adsk.fusion
import json
import os
import re
import traceback


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip() or 'unnamed'


def jsonable(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    for method in ('asArray',):
        if hasattr(value, method):
            arr = safe(lambda: list(getattr(value, method)()))
            if arr is not None:
                return arr
    for attrs in (('x', 'y', 'z'), ('x', 'y')):
        if all(hasattr(value, a) for a in attrs):
            return {a: getattr(value, a) for a in attrs}
    if hasattr(value, 'value'):
        return safe(lambda: value.value)
    return str(value)


def dump_parameter(p):
    return {
        'name': safe(lambda: p.name),
        'expression': safe(lambda: p.expression),
        'value': safe(lambda: p.value),
        'unit': safe(lambda: p.unit),
        'comment': safe(lambda: p.comment),
    }


def dump_feature(entity):
    data = {'classType': safe(lambda: entity.classType())}
    op = safe(lambda: entity.operation)
    if op is not None:
        data['operation'] = str(op)
    params = safe(lambda: entity.parameters)
    if params:
        data['parameters'] = [dump_parameter(params.item(i)) for i in range(params.count)]
    for coll_name in ('edges', 'faces', 'inputBodies', 'participantBodies', 'bodies'):
        coll = safe(lambda: getattr(entity, coll_name))
        if coll is not None:
            count = safe(lambda: coll.count)
            if count is not None:
                data[coll_name + '_count'] = count
    axis = safe(lambda: entity.axis)
    if axis is not None:
        data['axis'] = jsonable(safe(lambda: axis.geometry) or axis)
    return data


def dump_sketch(entity, sketches_dir, comp_name, exported_files):
    name = safe(lambda: entity.name, 'Sketch')
    filename = sanitize(comp_name) + '__' + sanitize(name) + '.dxf'
    full_path = os.path.join(sketches_dir, filename)
    ok = safe(lambda: entity.saveAsDXF(full_path))
    data = {
        'classType': 'Sketch',
        'name': name,
        'isVisible': safe(lambda: entity.isVisible),
        'dxfExported': bool(ok),
        'dxfFile': ('sketches/' + filename) if ok else None,
    }
    plane = safe(lambda: entity.referencePlane)
    if plane is not None:
        data['referencePlane'] = safe(lambda: plane.name)
    if ok:
        exported_files.append(full_path)
    return data


def dump_occurrence_entity(entity):
    comp = safe(lambda: entity.component)
    return {
        'classType': 'Occurrence',
        'name': safe(lambda: entity.name),
        'componentName': safe(lambda: comp.name) if comp else None,
        'transform': jsonable(safe(lambda: entity.transform)),
    }


def dump_timeline(design, sketches_dir, exported_files):
    timeline = design.timeline
    items = []
    for i in range(timeline.count):
        item = timeline.item(i)
        entry = {
            'index': item.index,
            'name': safe(lambda: item.name),
            'isSuppressed': safe(lambda: item.isSuppressed),
            'isGroup': safe(lambda: item.isGroup),
        }
        entity = safe(lambda: item.entity)
        class_type = safe(lambda: entity.classType()) if entity else None
        try:
            if entity is None:
                entry['entity'] = None
            elif class_type == 'adsk::fusion::Sketch':
                comp = safe(lambda: entity.parentComponent)
                comp_name = safe(lambda: comp.name, 'Component') if comp else 'Component'
                entry['entity'] = dump_sketch(entity, sketches_dir, comp_name, exported_files)
            elif class_type == 'adsk::fusion::Occurrence':
                entry['entity'] = dump_occurrence_entity(entity)
            elif hasattr(entity, 'parameters') or 'Feature' in (class_type or ''):
                entry['entity'] = dump_feature(entity)
            else:
                entry['entity'] = {'classType': class_type, 'name': safe(lambda: entity.name)}
        except Exception:
            entry['entity'] = {'classType': class_type, 'error': traceback.format_exc()}
        items.append(entry)
    return items


def dump_components(design):
    comps = []
    for comp in design.allComponents:
        sketch_names = [safe(lambda: s.name) for s in comp.sketches]
        body_names = [safe(lambda: b.name) for b in comp.bRepBodies]
        comps.append({
            'name': safe(lambda: comp.name),
            'sketches': sketch_names,
            'bodies': body_names,
        })
    return comps


def dump_occurrences(root):
    occs = []
    for occ in root.allOccurrences:
        occs.append({
            'fullPathName': safe(lambda: occ.fullPathName),
            'componentName': safe(lambda: occ.component.name),
            'isGrounded': safe(lambda: occ.isGrounded),
            'transform': jsonable(safe(lambda: occ.transform)),
        })
    return occs


def dump_joints(root):
    joints = []
    for joint in root.allJoints:
        motion = safe(lambda: joint.jointMotion)
        joints.append({
            'name': safe(lambda: joint.name),
            'isSuppressed': safe(lambda: joint.isSuppressed),
            'jointMotionType': safe(lambda: motion.classType()) if motion else None,
            'occurrenceOne': safe(lambda: joint.occurrenceOne.fullPathName),
            'occurrenceTwo': safe(lambda: joint.occurrenceTwo.fullPathName),
        })
    return joints


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design. Open a design (not a drawing) and re-run.')
            return

        folder_dlg = ui.createFolderDialog()
        folder_dlg.title = 'Choose export folder for FreeCAD hand-off'
        if folder_dlg.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        out_dir = folder_dlg.folder
        sketches_dir = os.path.join(out_dir, 'sketches')
        os.makedirs(sketches_dir, exist_ok=True)

        design_name = sanitize(safe(lambda: app.activeDocument.name, 'design'))
        root = design.rootComponent

        errors = []

        step_path = os.path.join(out_dir, design_name + '.step')
        try:
            export_mgr = design.exportManager
            step_options = export_mgr.createSTEPExportOptions(step_path, root)
            export_mgr.execute(step_options)
        except Exception:
            errors.append('STEP export failed (Personal Use plan may restrict it): ' + traceback.format_exc())

        exported_dxf_files = []
        model = {
            'designName': design_name,
            'lengthUnits': safe(lambda: design.unitsManager.defaultLengthUnits),
            'userParameters': [dump_parameter(design.userParameters.item(i))
                                for i in range(design.userParameters.count)],
            'components': dump_components(design),
            'occurrences': dump_occurrences(root),
            'joints': dump_joints(root),
            'timeline': dump_timeline(design, sketches_dir, exported_dxf_files),
            'errors': errors,
        }

        json_path = os.path.join(out_dir, 'model.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(model, f, indent=2)

        summary = (
            'Exported to {0}\n'
            '- STEP: {1}\n'
            '- Sketch DXFs: {2}\n'
            '- model.json (parameters/timeline/assembly)\n'
        ).format(out_dir, 'ok' if os.path.exists(step_path) else 'FAILED (see errors in model.json)',
                 len(exported_dxf_files))
        if errors:
            summary += '\n{0} error(s) logged in model.json.'.format(len(errors))
        ui.messageBox(summary)

    except Exception:
        if ui:
            ui.messageBox('Export failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    pass
