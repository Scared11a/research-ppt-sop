#!/usr/bin/env python3
"""Apply explicitly authored native OOXML gradients; never rasterize or modify source files in place."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
from inspect_deck import NS, relationships, xml

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def q(name):
    return '{' + NS['a'] + '}' + name


def apply_gradient(shape, spec):
    props = shape.find('p:spPr', NS)
    if props is None:
        raise ValueError('Gradient target is not a native shape')
    fill_names = {q(n) for n in ['solidFill', 'noFill', 'grpFill', 'gradFill', 'pattFill', 'blipFill']}
    for node in list(props):
        if node.tag in fill_names:
            props.remove(node)
    gradient = ET.Element(q('gradFill'), {'rotWithShape': '1'})
    stops = ET.SubElement(gradient, q('gsLst'))
    for position, color in [(0, spec['from']), (100000, spec['to'])]:
        if len(color) != 6 or any(c not in '0123456789abcdefABCDEF' for c in color):
            raise ValueError('Gradient colors must be six hex digits')
        stop = ET.SubElement(stops, q('gs'), {'pos': str(position)})
        ET.SubElement(stop, q('srgbClr'), {'val': color.upper()})
    ET.SubElement(gradient, q('lin'), {'ang': str(round(spec.get('angle', 0) * 60000)), 'scaled': '1'})
    ET.SubElement(gradient, q('tileRect'))
    # xfrm/geometry precede fill; line/effects must follow it.
    insert_at = next((i for i, node in enumerate(props)
                      if node.tag in {q('ln'), q('effectLst'), q('effectDag'), q('scene3d'), q('sp3d'), q('extLst')}), len(props))
    props.insert(insert_at, gradient)


def apply_adjustments(shape, adjustments):
    geometry = shape.find('p:spPr/a:prstGeom', NS)
    if geometry is None:
        raise ValueError('Adjustment target must use an Office preset geometry')
    values = geometry.find('a:avLst', NS)
    if values is None:
        values = ET.SubElement(geometry, q('avLst'))
    for node in list(values):
        if node.get('name') in adjustments:
            values.remove(node)
    for name, value in adjustments.items():
        if not name.startswith('adj') or not isinstance(value, int):
            raise ValueError('Preset adjustments require integer adj/adjN guide values')
        ET.SubElement(values, q('gd'), {'name': name, 'fmla': f'val {value}'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('scene', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise ValueError('Save to a new file, not over the input')
    scene = json.loads(args.scene.read_text(encoding='utf-8'))
    applied = []
    adjusted = []
    with ZipFile(args.source) as z:
        presentation = xml(z, 'ppt/presentation.xml')
        slide_rels = relationships(z, 'ppt/presentation.xml')
        slide_ids = presentation.findall('p:sldIdLst/p:sldId', NS)
        if len(slide_ids) != len(scene['slides']):
            raise ValueError('Scene and PPTX slide counts differ')
        changed = {}
        for index, page in enumerate(scene['slides']):
            targets = {o['name']: o for o in page['objects'] if 'gradient' in o or 'adjustments' in o}
            if not targets:
                continue
            part = slide_rels[slide_ids[index].get('{' + NS['r'] + '}id')]['target']
            root = xml(z, part)
            found = set()
            for shape in root.findall('p:cSld/p:spTree/p:sp', NS):
                info = shape.find('p:nvSpPr/p:cNvPr', NS)
                name = info.get('name') if info is not None else None
                if name in targets:
                    spec = targets[name]
                    if 'gradient' in spec:
                        apply_gradient(shape, spec['gradient'])
                        applied.append({'slide': index + 1, 'name': name})
                    if 'adjustments' in spec:
                        apply_adjustments(shape, spec['adjustments'])
                        adjusted.append({'slide': index + 1, 'name': name, 'values': spec['adjustments']})
                    found.add(name)
            if found != set(targets):
                raise ValueError(f'Gradient target missing: {set(targets) - found}')
            changed[part] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(args.output, 'w', compression=ZIP_DEFLATED) as out:
            for info in z.infolist():
                out.writestr(info, changed.get(info.filename, z.read(info.filename)))
    print(json.dumps({'output': str(args.output), 'native_gradients': applied,
                      'native_preset_adjustments': adjusted,
                      'status': 'written_not_office_rendered'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
