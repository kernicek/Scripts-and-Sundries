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


def dump_extent_definition(ext):
    if ext is None:
        return None
    data = {'classType': safe(lambda: ext.classType())}
    dist = safe(lambda: ext.distance)
    if dist is not None:
        data['distance'] = dump_parameter(dist)
    entity = safe(lambda: ext.entity)
    if entity is not None:
        data['toEntity'] = safe(lambda: entity.name) or safe(lambda: entity.classType())
    is_chained = safe(lambda: ext.isChained)
    if is_chained is not None:
        data['isChained'] = is_chained
    return data


def dump_body_ref(body):
    if body is None:
        return None
    return safe(lambda: body.name)


def dump_edge_set(edge_set):
    data = {'classType': safe(lambda: edge_set.classType())}
    for attr in ('distance', 'distanceOne', 'distanceTwo'):
        p = safe(lambda: getattr(edge_set, attr))
        if p is not None:
            data[attr] = dump_parameter(p)
    angle = safe(lambda: edge_set.angle)
    if angle is not None:
        data['angle'] = dump_parameter(angle)
    edges = safe(lambda: edge_set.edges)
    if edges is not None:
        data['edges_count'] = safe(lambda: edges.count)
    return data


def dump_feature(entity, class_type):
    data = {'classType': safe(lambda: entity.classType())}
    op = safe(lambda: entity.operation)
    if op is not None:
        data['operation'] = str(op)
    params = safe(lambda: entity.parameters)
    if params is not None:
        count = safe(lambda: params.count, 0) or 0
        dumped = [dump_parameter(params.item(i)) for i in range(count)]
        if dumped:
            data['parameters'] = dumped
    for coll_name in ('edges', 'faces', 'inputBodies', 'participantBodies', 'bodies'):
        coll = safe(lambda: getattr(entity, coll_name))
        if coll is not None:
            count = safe(lambda: coll.count)
            if count is not None:
                data[coll_name + '_count'] = count
    axis = safe(lambda: entity.axis)
    if axis is not None:
        data['axis'] = jsonable(safe(lambda: axis.geometry) or axis)

    if class_type == 'adsk::fusion::ExtrudeFeature':
        ext_type = safe(lambda: entity.extentType)
        if ext_type is not None:
            data['extentType'] = str(ext_type)
        e1 = safe(lambda: entity.extentOne)
        if e1 is not None:
            data['extentOne'] = dump_extent_definition(e1)
        e2 = safe(lambda: entity.extentTwo)
        if e2 is not None:
            data['extentTwo'] = dump_extent_definition(e2)
        taper = safe(lambda: entity.taperAngleOne)
        if taper is not None:
            data['taperAngleOne'] = dump_parameter(taper)
        bodies = safe(lambda: entity.bodies)
        if bodies is not None:
            data['outputBodyNames'] = [safe(lambda: bodies.item(i).name)
                                        for i in range(safe(lambda: bodies.count, 0) or 0)]

    elif class_type == 'adsk::fusion::ChamferFeature':
        edge_sets = safe(lambda: entity.chamferEdgeSets)
        if edge_sets is not None:
            data['edgeSets'] = [dump_edge_set(edge_sets.item(i))
                                 for i in range(safe(lambda: edge_sets.count, 0) or 0)]

    elif class_type == 'adsk::fusion::RectangularPatternFeature':
        for attr in ('quantityOne', 'quantityTwo', 'distanceOne', 'distanceTwo'):
            p = safe(lambda: getattr(entity, attr))
            if p is not None:
                data[attr] = dump_parameter(p)
        compute_option = safe(lambda: entity.patternComputeOption)
        if compute_option is not None:
            data['patternComputeOption'] = str(compute_option)
        inputs = safe(lambda: entity.inputEntities)
        if inputs is not None:
            data['inputEntityNames'] = [safe(lambda: inputs.item(i).name)
                                         for i in range(safe(lambda: inputs.count, 0) or 0)]

    elif class_type == 'adsk::fusion::CombineFeature':
        data['targetBodyName'] = dump_body_ref(safe(lambda: entity.targetBody))
        tools = safe(lambda: entity.toolBodies)
        if tools is not None:
            data['toolBodyNames'] = [dump_body_ref(tools.item(i))
                                      for i in range(safe(lambda: tools.count, 0) or 0)]
        is_new_comp = safe(lambda: entity.isNewComponent)
        if is_new_comp is not None:
            data['isNewComponent'] = is_new_comp

    elif class_type == 'adsk::fusion::SplitBodyFeature':
        tool = safe(lambda: entity.splittingTool)
        if tool is not None:
            data['splittingToolName'] = safe(lambda: tool.name) or safe(lambda: tool.classType())
        participants = safe(lambda: entity.participantBodies)
        if participants is not None:
            data['participantBodyNames'] = [dump_body_ref(participants.item(i))
                                             for i in range(safe(lambda: participants.count, 0) or 0)]

    elif class_type == 'adsk::fusion::ConstructionPlane':
        definition = safe(lambda: entity.definition)
        if definition is not None:
            def_data = {'classType': safe(lambda: definition.classType())}
            offset = safe(lambda: definition.offset)
            if offset is not None:
                def_data['offset'] = dump_parameter(offset)
            plane_entity = safe(lambda: definition.planarEntity)
            if plane_entity is not None:
                def_data['planarEntity'] = safe(lambda: plane_entity.name) or safe(lambda: plane_entity.classType())
            data['definition'] = def_data

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
                entry['entity'] = dump_feature(entity, class_type)
            else:
                entry['entity'] = {'classType': class_type, 'name': safe(lambda: entity.name)}
        except Exception:
            entry['entity'] = {'classType': class_type, 'error': traceback.format_exc()}
        items.append(entry)
    return items


def dump_bounding_box(bbox):
    if bbox is None:
        return None
    return {
        'minPoint': jsonable(safe(lambda: bbox.minPoint)),
        'maxPoint': jsonable(safe(lambda: bbox.maxPoint)),
    }


def dump_body(body):
    data = {
        'name': safe(lambda: body.name),
        'isVisible': safe(lambda: body.isVisible),
    }
    appearance = safe(lambda: body.appearance)
    if appearance is not None:
        data['appearanceName'] = safe(lambda: appearance.name)
    material = safe(lambda: body.material)
    if material is not None:
        data['materialName'] = safe(lambda: material.name)
    props = safe(lambda: body.physicalProperties)
    if props is not None:
        data['volume'] = safe(lambda: props.volume)
        data['area'] = safe(lambda: props.area)
        data['boundingBox'] = dump_bounding_box(safe(lambda: body.boundingBox))
    return data


def dump_components(design):
    comps = []
    for comp in design.allComponents:
        sketch_names = [safe(lambda: s.name) for s in comp.sketches]
        bodies = [dump_body(b) for b in comp.bRepBodies]
        comps.append({
            'name': safe(lambda: comp.name),
            'sketches': sketch_names,
            'bodies': bodies,
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
