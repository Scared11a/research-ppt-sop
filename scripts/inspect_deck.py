#!/usr/bin/env python3
"""Local PDF/PPTX measurements; never uploads, modifies the source, or OCRs implicitly."""
import argparse
from collections import Counter
import json
from pathlib import Path
import posixpath
from zipfile import ZipFile
import xml.etree.ElementTree as ET

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
}
REL = '{http://schemas.openxmlformats.org/package/2006/relationships}'
EMU = 914400


def ranked(counter, limit=20):
    return [{'value': key, 'count': count} for key, count in counter.most_common(limit)]


def page_numbers(spec, total):
    if not spec:
        return list(range(1, total + 1))
    numbers = set()
    for token in spec.split(','):
        bounds = [int(n) for n in token.strip().split('-')]
        if len(bounds) > 2:
            raise ValueError('Invalid page range')
        lo, hi = bounds[0], bounds[-1]
        if lo < 1 or hi > total or hi < lo:
            raise ValueError(f'Page range must be between 1 and {total}')
        numbers.update(range(lo, hi + 1))
    return sorted(numbers)


def pdf_color(value):
    """Device colors are measurements, not guaranteed color-managed sRGB."""
    if value is None:
        return 'unspecified'
    values = tuple(value) if isinstance(value, (tuple, list)) else (value,)
    values = tuple(round(float(v), 4) for v in values)
    if len(values) == 3:
        return '#' + ''.join(f'{max(0, min(255, round(v * 255))):02X}' for v in values)
    return 'device:' + ','.join(str(v) for v in values)


def inspect_pdf(source, pages, output_dir, preview=False):
    import pdfplumber
    all_fonts, all_sizes, all_colors = Counter(), Counter(), Counter()
    with pdfplumber.open(source) as pdf:
        result = {'format': 'PDF', 'page_count': len(pdf.pages), 'pages': [],
                  'limits': ['No original master, notes, chart data or formula syntax recovered.',
                             'Arrow direction, icon meaning and evidence roles require visual/semantic review.',
                             'Font resource names do not establish local availability or font licensing.',
                             'RGB values are device values; no ICC color conversion is applied.']}
        for number in page_numbers(pages, len(pdf.pages)):
            page = pdf.pages[number - 1]
            fonts = Counter(c.get('fontname', 'unknown') for c in page.chars)
            sizes = Counter(round(c.get('size', 0), 2) for c in page.chars)
            colors = Counter(pdf_color(c.get('non_stroking_color')) for c in page.chars)
            all_fonts.update(fonts)
            all_sizes.update(sizes)
            all_colors.update(colors)
            images = [{'bbox_pt': [im['x0'], im['top'], im['x1'], im['bottom']],
                       'source_pixels': im.get('srcsize'), 'name': im.get('name')}
                      for im in page.images]
            drawing_colors = Counter(pdf_color(obj.get('non_stroking_color'))
                                     for obj in page.rects + page.curves)
            words = page.extract_words(extra_attrs=['fontname', 'size', 'non_stroking_color'])
            row = {'page': number, 'size_pt': [page.width, page.height],
                   'counts': {key: len(getattr(page, key))
                              for key in ['chars', 'lines', 'rects', 'curves', 'images']},
                   'fonts_by_character_count': ranked(fonts), 'sizes_pt': ranked(sizes),
                   'text_colors': ranked(colors), 'path_fill_colors': ranked(drawing_colors),
                   'words': words,
                   'emphasis_candidates': [
                       {'text': word['text'], 'fontname': word['fontname'],
                        'size_pt': word['size'],
                        'color': pdf_color(word.get('non_stroking_color')),
                        'bbox_pt': [word['x0'], word['top'], word['x1'], word['bottom']],
                        'role': 'unassigned_requires_visual_and_content_review'}
                       for word in words
                       if 'bold' in word['fontname'].lower() or
                          pdf_color(word.get('non_stroking_color')) not in ['#000000', '#222222', '#FFFFFF', 'device:0.0', 'device:1.0']],
                   'images': images,
                   'paths': [{'kind': kind, 'bbox_pt': [o['x0'], o['top'], o['x1'], o['bottom']],
                              'stroke': pdf_color(o.get('stroking_color')),
                              'fill': pdf_color(o.get('non_stroking_color')),
                              'line_width_pt': o.get('linewidth')}
                             for kind, objects in [('line', page.lines), ('rect', page.rects),
                                                   ('curve', page.curves)] for o in objects]}
            if preview:
                filename = f'page-{number:02d}.png'
                image = page.to_image(resolution=120)
                image.save(output_dir / filename, quantize=False)
                row['reference_render'] = filename
                quantized = image.original.convert('RGB').quantize(colors=12)
                palette = quantized.getpalette()
                count_total = quantized.width * quantized.height
                row['rendered_palette_observed'] = [
                    {'approx_rgb': '#' + ''.join(f'{n:02X}' for n in palette[idx * 3:idx * 3 + 3]),
                     'pixel_fraction': round(count / count_total, 5)}
                    for count, idx in sorted(quantized.getcolors(), reverse=True)]
            result['pages'].append(row)
        result['aggregate'] = {'fonts': ranked(all_fonts), 'sizes_pt': ranked(all_sizes),
                               'text_colors': ranked(all_colors)}
    return result


def xml(z, part):
    data = z.read(part)
    # OOXML requires neither DTDs nor entity expansion for this reader.
    if b'<!DOCTYPE' in data or b'<!ENTITY' in data:
        raise ValueError('DTD/entity declarations are not accepted')
    return ET.fromstring(data)


def relationships(z, part):
    directory, name = posixpath.split(part)
    relpart = posixpath.join(directory, '_rels', name + '.rels')
    if relpart not in z.namelist():
        return {}
    rows = {}
    for rel in xml(z, relpart):
        target = rel.get('Target', '')
        external = rel.get('TargetMode') == 'External'
        resolved = target if external else posixpath.normpath(
            target.lstrip('/') if target.startswith('/') else posixpath.join(directory, target))
        rows[rel.get('Id')] = {'type': rel.get('Type', '').rsplit('/', 1)[-1],
                              'target': resolved, 'external': external}
    return rows


def box(xfrm, matrix):
    if xfrm is None:
        return None
    off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
    if off is None or ext is None:
        return None
    sx, sy, tx, ty = matrix
    return [round((tx + sx * int(off.get('x'))) / EMU, 5),
            round((ty + sy * int(off.get('y'))) / EMU, 5),
            round(sx * int(ext.get('cx')) / EMU, 5),
            round(sy * int(ext.get('cy')) / EMU, 5)]


def group_matrix(xfrm, parent):
    if xfrm is None:
        return parent
    off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
    child_off, child_ext = xfrm.find('a:chOff', NS), xfrm.find('a:chExt', NS)
    if any(n is None for n in [off, ext, child_off, child_ext]):
        return parent
    sx, sy, tx, ty = parent
    ax = int(ext.get('cx')) / (int(child_ext.get('cx')) or 1)
    ay = int(ext.get('cy')) / (int(child_ext.get('cy')) or 1)
    return (sx * ax, sy * ay,
            tx + sx * (int(off.get('x')) - ax * int(child_off.get('x'))),
            ty + sy * (int(off.get('y')) - ay * int(child_off.get('y'))))


def shapes(tree, matrix=(1, 1, 0, 0), parent=None, ancestry_uncertain=False):
    rows = []
    for order, shape in enumerate(tree):
        tag = shape.tag.rsplit('}', 1)[-1]
        if tag not in ['sp', 'pic', 'cxnSp', 'graphicFrame', 'grpSp']:
            continue
        info = shape.find('.//p:cNvPr', NS)
        xfrm = shape.find('p:spPr/a:xfrm', NS)
        if tag == 'graphicFrame':
            xfrm = shape.find('p:xfrm', NS)
        if tag == 'grpSp':
            xfrm = shape.find('p:grpSpPr/a:xfrm', NS)
        uncertain = ancestry_uncertain or (xfrm is not None and
                    any(xfrm.get(k, '0') not in ['0', 'false'] for k in ['rot', 'flipH', 'flipV']))
        text = '\n'.join(''.join(t.text or '' for t in p.findall('.//a:t', NS))
                         for p in shape.findall('p:txBody/a:p', NS))
        kind = {'sp': 'native_shape', 'pic': 'image', 'cxnSp': 'native_connector',
                'grpSp': 'group', 'graphicFrame': 'graphic_frame'}[tag]
        if shape.find('.//a:tbl', NS) is not None:
            kind = 'native_table'
        if shape.find('.//{http://schemas.openxmlformats.org/drawingml/2006/chart}chart') is not None:
            kind = 'native_chart'
        if shape.find('.//p:oleObj', NS) is not None:
            kind = 'embedded_object'
        if shape.find('.//m:oMath', NS) is not None or shape.find('.//m:oMathPara', NS) is not None:
            kind = 'native_equation'
        geometry = shape.find('p:spPr/a:prstGeom', NS)
        if tag == 'sp' and geometry is not None and geometry.get('prst') == 'line':
            kind = 'native_line'
        if tag == 'sp' and text and kind == 'native_shape':
            kind = 'native_text'
        row = {'id': info.get('id') if info is not None else None,
               'name': info.get('name') if info is not None else None,
               'kind': kind, 'parent_id': parent, 'z_order_in_parent': order,
               'bbox_inches': box(xfrm, matrix),
               'bounds_uncertain_due_to_rotation_or_flip': uncertain,
               'text': text,
               'run_style_declarations': [node.attrib for node in shape.findall('p:txBody//a:rPr', NS)],
               'font_declarations': [{k: node.get(k) for k in node.keys()}
                                     for node in shape.findall('p:txBody//a:latin', NS) +
                                                 shape.findall('p:txBody//a:ea', NS)],
               'color_declarations': [{'type': n.tag.rsplit('}', 1)[-1], **n.attrib}
                                      for n in shape.findall('p:spPr//a:srgbClr', NS) +
                                               shape.findall('p:spPr//a:schemeClr', NS)],
               'resource_ids': [n.get('{' + NS['r'] + '}' + key)
                                for n in shape.iter() for key in ['embed', 'link', 'id']
                                if n.get('{' + NS['r'] + '}' + key)],
               'connection_refs': [n.attrib for n in shape.findall('.//a:stCxn', NS) +
                                                      shape.findall('.//a:endCxn', NS)],
               'arrowheads': [n.attrib for n in shape.findall('p:spPr/a:ln/a:headEnd', NS) +
                                              shape.findall('p:spPr/a:ln/a:tailEnd', NS)]}
        rows.append(row)
        if tag == 'grpSp':
            rows.extend(shapes(shape, group_matrix(xfrm, matrix), row['id'], uncertain))
    return rows


def inspect_pptx(source, pages):
    with ZipFile(source) as z:
        presentation = xml(z, 'ppt/presentation.xml')
        rels = relationships(z, 'ppt/presentation.xml')
        size = presentation.find('p:sldSz', NS)
        width, height = int(size.get('cx')) / EMU, int(size.get('cy')) / EMU
        slides = presentation.findall('p:sldIdLst/p:sldId', NS)
        result = {'format': 'PPTX', 'slide_count': len(slides), 'size_inches': [width, height],
                  'slides': [], 'masters': [], 'themes': [],
                  'limits': ['This is an object inventory, not an Office renderer.',
                             'Font/theme declarations are not resolved effective styles.',
                             'Bounds for rotation/flips are deliberately marked uncertain.',
                             'XML presence does not prove editing in WPS/PowerPoint works.',
                             'Equation/chart provenance, layout roles and arrow meaning require review.']}
        for name in z.namelist():
            if name.startswith('ppt/theme/') and name.endswith('.xml'):
                root = xml(z, name)
                result['themes'].append({'part': name,
                    'font_scheme': [node.attrib for node in root.findall('.//a:fontScheme//a:latin', NS) +
                                                             root.findall('.//a:fontScheme//a:ea', NS) +
                                                             root.findall('.//a:fontScheme//a:font', NS)],
                    'colors': [{'slot': slot.tag.rsplit('}', 1)[-1],
                                'declarations': [n.attrib for n in slot]}
                               for slot in root.findall('.//a:clrScheme/*', NS)]})
            if name.startswith('ppt/slideMasters/') and name.endswith('.xml'):
                root = xml(z, name)
                tree = root.find('p:cSld/p:spTree', NS)
                result['masters'].append({'part': name, 'relationships': relationships(z, name),
                                          'objects': shapes(tree) if tree is not None else []})
        for number in page_numbers(pages, len(slides)):
            part = rels[slides[number - 1].get('{' + NS['r'] + '}id')]['target']
            root = xml(z, part)
            local_rels = relationships(z, part)
            tree = root.find('p:cSld/p:spTree', NS)
            objects = shapes(tree) if tree is not None else []
            notes = []
            for rel in local_rels.values():
                if rel['type'] == 'notesSlide' and not rel['external']:
                    note_root = xml(z, rel['target'])
                    notes = [n.text or '' for n in note_root.findall('.//a:t', NS)]
            warnings = []
            for obj in objects:
                bounds = obj['bbox_inches']
                if not bounds or obj['bounds_uncertain_due_to_rotation_or_flip']:
                    continue
                x, y, w, h = bounds
                if x < -0.01 or y < -0.01 or x + w > width + 0.01 or y + h > height + 0.01:
                    warnings.append({'object': obj['name'], 'issue': 'outside_slide_bounds'})
                if obj['kind'] == 'image' and w * h >= 0.6 * width * height:
                    warnings.append({'object': obj['name'], 'issue': 'large_image_requires_flattening_review'})
            result['slides'].append({'slide': number, 'part': part, 'relationships': local_rels,
                                     'objects': objects, 'counts': dict(Counter(o['kind'] for o in objects)),
                                     'notes_text': notes, 'warnings': warnings})
    return result


def audit_requirements(report, requirements):
    checks = []
    slides = {s['slide']: s for s in report['slides']}
    for requirement in requirements:
        slide = slides.get(requirement['slide'], {})
        matches = [o for o in slide.get('objects', []) if o['name'] == requirement['name']]
        valid = len(matches) == 1 and matches[0]['kind'] == requirement['kind']
        if valid and 'text_contains' in requirement:
            valid = requirement['text_contains'] in matches[0]['text']
        checks.append({**requirement, 'structural_match': valid,
                       'actual_kinds': [o['kind'] for o in matches]})
    return {'checks': checks, 'all_structural_matches': all(c['structural_match'] for c in checks),
            'render_and_edit_test': 'not_performed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--pages', help='1-based pages/slides, e.g. 8,14-15')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--preview', action='store_true', help='Render PDF references locally, never a PPTX proxy')
    parser.add_argument('--requirements', type=Path, help='JSON list of required editable objects (PPTX only)')
    args = parser.parse_args()
    source = args.source.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    if suffix == '.pdf':
        if args.requirements:
            raise ValueError('PPTX object requirements cannot be checked against a PDF')
        report = inspect_pdf(source, args.pages, args.out, args.preview)
    elif suffix == '.pptx':
        if args.preview:
            raise ValueError('No PPTX renderer is bundled; use an approved Office rendering route')
        report = inspect_pptx(source, args.pages)
        if args.requirements:
            report['editability_audit'] = audit_requirements(report, json.loads(args.requirements.read_text()))
    else:
        raise ValueError('Only PDF and PPTX are supported')
    report['source'] = str(source)
    target = args.out / 'inspection.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = {key: value for key, value in report.items()
               if key in ['format', 'page_count', 'slide_count', 'aggregate']}
    if 'editability_audit' in report:
        audit = report['editability_audit']
        summary['editability_audit'] = {
            'required_objects': len(audit['checks']),
            'all_structural_matches': audit['all_structural_matches'],
            'failed_objects': [{'slide': row['slide'], 'name': row['name']} for row in audit['checks']
                               if not row['structural_match']],
            'render_and_edit_test': audit['render_and_edit_test']}
    summary['report'] = str(target)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if 'editability_audit' in report and not report['editability_audit']['all_structural_matches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
