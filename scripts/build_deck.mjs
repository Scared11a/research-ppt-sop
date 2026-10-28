#!/usr/bin/env node
/** Native PPTX authoring backend. Requires explicitly installed local pptxgenjs. */
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname, isAbsolute } from 'node:path';

const [sceneArg, outArg, fontReportArg] = process.argv.slice(2);
if (!sceneArg || !outArg) {
  console.error('Usage: node build_deck.mjs scene.json output.pptx [font-report.json] (run from the project dependency directory)');
  process.exit(2);
}
const localRequire = createRequire(resolve(process.cwd(), 'package.json'));
let PptxGenJS;
try {
  PptxGenJS = localRequire('pptxgenjs');
} catch {
  console.error('MISSING_DEPENDENCY: pptxgenjs. Ask approval and use Hana downloader; this script never installs it.');
  process.exit(3);
}
const scenePath = resolve(sceneArg);
const scene = JSON.parse(readFileSync(scenePath, 'utf8'));
const pptx = new PptxGenJS();
const theme = scene.theme;
if (theme.fontVerificationRequired) {
  if (!fontReportArg) throw new Error('FONT_VERIFICATION_REQUIRED: provide a verified font report; no implicit substitution.');
  const report = JSON.parse(readFileSync(resolve(fontReportArg), 'utf8'));
  const required = [...new Set([theme.headingFont, theme.bodyFont, theme.latinFont].filter(Boolean))];
  const missing = required.filter(name => !(report.availableFamilies ?? []).includes(name));
  if (missing.length) throw new Error(`MISSING_REFERENCE_FONTS: ${missing.join(', ')}. Do not silently use a fallback.`);
}
const requirements = [];
pptx.defineLayout({ name: 'REFERENCE_LAYOUT', width: scene.width, height: scene.height });
pptx.layout = 'REFERENCE_LAYOUT';
pptx.author = 'Hana';
pptx.subject = 'Editable reference-inspired layout, not automatic PDF conversion';
pptx.title = scene.title;
pptx.lang = 'zh-CN';
pptx.theme = { headFontFace: theme.headingFont, bodyFontFace: theme.bodyFont, lang: 'zh-CN' };
pptx.defineSlideMaster({
  title: 'REFERENCE_SHARED',
  background: { color: theme.background },
  objects: [
    { rect: { x: 0, y: 0, w: scene.width, h: 0.12,
              fill: { color: theme.accent }, line: { color: theme.accent },
              objectName: 'shared_accent_band' } },
    { line: { x: 0.45, y: scene.height - 0.38, w: scene.width - 0.9, h: 0,
              line: { color: theme.muted, width: 0.5 }, objectName: 'shared_footer_rule' } },
  ],
});

function assetPath(value) {
  if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.startsWith('//')) {
    throw new Error('Remote asset URLs and data URIs are not allowed. Use an approved local image.');
  }
  return isAbsolute(value) ? value : resolve(dirname(scenePath), value);
}

function styledRuns(input, defaultFont = theme.bodyFont) {
  const output = [];
  for (const run of input) {
    const style = { ...(run.bold !== undefined ? { bold: run.bold } : {}),
                    ...(run.italic !== undefined ? { italic: run.italic } : {}),
                    ...(run.fontSize ? { fontSize: run.fontSize } : {}),
                    ...(run.subscript ? { subscript: true } : {}),
                    ...(run.superscript ? { superscript: true } : {}),
                    ...(run.colorRole ? { color: theme[run.colorRole] } : {}),
                    ...(run.color ? { color: run.color } : {}) };
    const pieces = run.text.replace(/\r\n/g, '\n').split('\n');
    pieces.forEach((piece, index) => {
      if (piece) {
        const forcedFont = run.fontFace ?? (run.fontRole === 'math' ? theme.mathFont : undefined);
        for (const part of piece.split(/([\x00-\x7F]+)/).filter(Boolean)) {
          const fontFace = forcedFont ?? (/^[\x00-\x7F]+$/.test(part) ? (theme.latinFont ?? defaultFont) : defaultFont);
          output.push({ text: part, options: { ...style, fontFace } });
        }
      }
      if (index < pieces.length - 1) {
        const last = output.at(-1);
        if (last && !last.options.breakLine) last.options.breakLine = true;
        else output.push({ text: '', options: { ...style, breakLine: true } });
      }
    });
  }
  return output;
}

function drawLine(slide, name, start, end, style, arrow = false) {
  const dx = end.x - start.x, dy = end.y - start.y;
  slide.addShape(pptx.ShapeType.line, {
    x: Math.min(start.x, end.x), y: Math.min(start.y, end.y),
    w: Math.abs(dx), h: Math.abs(dy), flipH: dx < 0, flipV: dy < 0,
    objectName: name,
    line: { color: style.color, width: style.width ?? 1.6,
            ...(style.dashed ? { dashType: 'dash' } : {}),
            ...(arrow ? { endArrowType: 'triangle' } : {}) },
  });
}

function drawRelations(slide, page) {
  const nodes = new Map(page.objects.map(object => [object.name, object]));
  const defaults = {
    progression: { color: theme.accent, width: 1.8 },
    support: { color: theme.muted, width: 1.2 },
    decomposition: { color: theme.accent, width: 1.3 },
    aggregation: { color: theme.accent, width: 1.8 },
    training: { color: theme.secondary, width: 1.5, dashed: true },
    inference: { color: theme.accent, width: 1.8 },
  };
  for (const relation of page.relations ?? []) {
    if (!defaults[relation.kind]) throw new Error(`Unsupported relation kind: ${relation.kind}`);
    const style = { ...defaults[relation.kind], ...(scene.relationStyles?.[relation.kind] ?? {}),
                    ...(relation.style ?? {}) };
    const vertical = relation.direction === 'TB';
    const anchor = (name, outgoing) => {
      const node = nodes.get(name);
      if (!node) throw new Error(`Unknown relation endpoint: ${name}`);
      return vertical
        ? { x: node.x + node.w / 2, y: node.y + (outgoing ? node.h : 0) }
        : { x: node.x + (outgoing ? node.w : 0), y: node.y + node.h / 2 };
    };
    const from = (Array.isArray(relation.from) ? relation.from : [relation.from]).map(n => anchor(n, true));
    const to = (Array.isArray(relation.to) ? relation.to : [relation.to]).map(n => anchor(n, false));
    const line = (suffix, a, b, arrow = false) => drawLine(slide, `${relation.name}_${suffix}`, a, b, style, arrow);
    if (relation.kind === 'decomposition') {
      if (from.length !== 1 || to.length < 2) throw new Error('Decomposition requires one source and multiple targets.');
      const bus = vertical ? (from[0].y + Math.min(...to.map(p => p.y))) / 2
                           : (from[0].x + Math.min(...to.map(p => p.x))) / 2;
      const joint = vertical ? { x: from[0].x, y: bus } : { x: bus, y: from[0].y };
      line('trunk', from[0], joint);
      const branches = to.map(p => vertical ? { x: p.x, y: bus } : { x: bus, y: p.y });
      const positions = [...branches, joint];
      if (vertical) line('bus', { x: Math.min(...positions.map(p => p.x)), y: bus }, { x: Math.max(...positions.map(p => p.x)), y: bus });
      else line('bus', { x: bus, y: Math.min(...positions.map(p => p.y)) }, { x: bus, y: Math.max(...positions.map(p => p.y)) });
      to.forEach((p, i) => line(`branch_${i}`, branches[i], p));
    } else if (relation.kind === 'aggregation') {
      if (from.length < 2 || to.length !== 1) throw new Error('Aggregation requires multiple sources and one target.');
      const bus = vertical ? (Math.max(...from.map(p => p.y)) + to[0].y) / 2
                           : (Math.max(...from.map(p => p.x)) + to[0].x) / 2;
      const branches = from.map(p => vertical ? { x: p.x, y: bus } : { x: bus, y: p.y });
      from.forEach((p, i) => line(`branch_${i}`, p, branches[i]));
      const joint = vertical ? { x: to[0].x, y: bus } : { x: bus, y: to[0].y };
      const positions = [...branches, joint];
      if (vertical) line('bus', { x: Math.min(...positions.map(p => p.x)), y: bus }, { x: Math.max(...positions.map(p => p.x)), y: bus });
      else line('bus', { x: bus, y: Math.min(...positions.map(p => p.y)) }, { x: bus, y: Math.max(...positions.map(p => p.y)) });
      line('trunk', joint, to[0], true);
    } else {
      if (from.length !== 1 || to.length !== 1) throw new Error('This relation requires one source and one target.');
      line('main', from[0], to[0], true);
    }
    if (relation.label) {
      const a = from[0], b = to[0];
      slide.addText(relation.label, {
        x: relation.labelX ?? (a.x + b.x) / 2 - 0.5,
        y: relation.labelY ?? (a.y + b.y) / 2 - 0.28,
        w: relation.labelW ?? 1.1, h: 0.22,
        fontFace: theme.bodyFont, fontSize: 11, color: style.color,
        margin: 0, objectName: `${relation.name}_label`,
      });
    }
  }
}

for (const [index, page] of scene.slides.entries()) {
  const slide = pptx.addSlide({ masterName: 'REFERENCE_SHARED' });
  slide.addText(styledRuns(page.titleRuns ?? [{ text: page.title, bold: true }], theme.headingFont), {
    x: 0.48, y: 0.3, w: page.titleWidth ?? scene.width - 0.96, h: 0.55,
    fontFace: theme.headingFont, fontSize: 26, bold: true, color: theme.ink,
    margin: 0, breakLine: false, objectName: 'page_title',
  });
  requirements.push({ slide: index + 1, name: 'page_title', kind: 'native_text', text_contains: page.title });
  for (const object of page.objects) {
    const options = { x: object.x, y: object.y, w: object.w, h: object.h,
                      objectName: object.name };
    if (!object.name) throw new Error('Each object needs a stable name for the editability audit.');
    switch (object.type) {
      case 'text': {
        const text = object.runs ? object.runs.map(run => run.text).join('') : object.text;
        const runs = styledRuns(object.runs ?? [{ text }], object.fontFace ?? theme.bodyFont);
        slide.addText(runs, {
          ...options, fontFace: object.fontFace ?? theme.bodyFont,
          fontSize: object.fontSize ?? 18, color: object.color ?? theme.ink,
          bold: object.bold ?? false, margin: object.margin ?? 0,
          valign: object.valign ?? 'top', align: object.align ?? 'left',
          ...(object.vert ? { vert: object.vert } : {}),
          ...(object.rotate ? { rotate: object.rotate } : {}),
          ...(object.lineSpacingMultiple ? { lineSpacingMultiple: object.lineSpacingMultiple } : {}),
        });
        requirements.push({ slide: index + 1, name: object.name, kind: 'native_text', text_contains: text });
        break;
      }
      case 'node':
      case 'custom': {
        const preset = object.type === 'custom' ? 'custGeom' : (object.shape ?? 'rect');
        if (!pptx.ShapeType[preset]) throw new Error(`Unknown native shape preset: ${preset}`);
        slide.addShape(pptx.ShapeType[preset], {
          ...options,
          fill: { color: object.fill ?? theme.surface, transparency: object.transparency ?? 0 },
          line: { color: object.stroke ?? theme.accent, width: object.lineWidth ?? 1.25,
                  ...(object.stroke === null ? { transparency: 100 } : {}),
                  ...(object.endArrowType ? { endArrowType: object.endArrowType } : {}),
                  ...(object.lineDash ? { dashType: object.lineDash } : {}) },
          ...(object.shadow ? { shadow: object.shadow } : {}),
          ...(object.points ? { points: object.points } : {}),
          ...(object.rotate ? { rotate: object.rotate } : {}),
          ...(object.flipV ? { flipV: true } : {}),
          ...(object.flipH ? { flipH: true } : {}),
          ...(object.rectRadius ? { rectRadius: object.rectRadius } : {}),
        });
        requirements.push({ slide: index + 1, name: object.name, kind: 'native_shape' });
        break;
      }
      case 'arrow':
        // A native line with an arrowhead; no endpoint attachment is promised.
        slide.addShape(pptx.ShapeType.line, {
          ...options,
          x: object.w < 0 ? object.x + object.w : object.x,
          y: object.h < 0 ? object.y + object.h : object.y,
          w: Math.abs(object.w), h: Math.abs(object.h),
          flipH: object.w < 0, flipV: object.h < 0,
          line: { color: object.color ?? theme.accent,
                             width: object.lineWidth ?? 1.8, endArrowType: 'triangle',
                             ...(object.dashed ? { dashType: 'dash' } : {}) },
        });
        break;
      case 'image':
        if (object.wholeSlide || object.role === 'page_title' || object.role === 'body_text') {
          throw new Error('Titles/body cannot be flattened into an image. Whole-slide images are forbidden.');
        }
        {
          const path = assetPath(object.path);
          let sizing = options;
          if (object.fit !== 'stretch') {
            const [sw, sh] = object.sourceSize ?? [];
            if (!(sw > 0 && sh > 0)) throw new Error(`Image sourceSize is required for lossless contain sizing: ${object.name}`);
            const scale = Math.min(options.w / sw, options.h / sh);
            sizing = { x: options.x + (options.w - sw * scale) / 2,
                       y: options.y + (options.h - sh * scale) / 2,
                       w: sw * scale, h: sh * scale };
          }
          slide.addImage({ ...options, ...sizing, path });
        }
        requirements.push({ slide: index + 1, name: object.name, kind: 'image' });
        break;
      case 'table':
        slide.addTable(object.rows, {
          ...options, fontFace: theme.bodyFont, fontSize: object.fontSize ?? 14,
          color: theme.ink, border: { type: 'solid', color: theme.muted, pt: 0.5 },
          autoPage: false, margin: object.margin ?? 4,
          ...(object.colW ? { colW: object.colW } : {}),
          ...(object.rowH ? { rowH: object.rowH } : {}),
        });
        requirements.push({ slide: index + 1, name: object.name, kind: 'native_table' });
        break;
      case 'chart':
        if (!['bar', 'line', 'pie', 'scatter'].includes(object.chartType)) {
          throw new Error('Unsupported chart type; use explicit data and a supported native chart.');
        }
        slide.addChart(pptx.ChartType[object.chartType], object.data, {
          chartColors: object.colors ?? [theme.accent, theme.secondary],
          showLegend: true, showTitle: false, ...(object.chartOptions ?? {}), ...options,
        });
        requirements.push({ slide: index + 1, name: object.name, kind: 'native_chart' });
        break;
      default:
        throw new Error(`Unsupported object type: ${object.type}. Equations require a separately verified native-Office path.`);
    }
  }
  drawRelations(slide, page);
  slide.addText(styledRuns([{ text: page.source ?? '' }]), {
    x: 0.48, y: scene.height - 0.32, w: scene.width - 0.96, h: 0.2,
    fontFace: theme.bodyFont, fontSize: 9, color: theme.muted, margin: 0,
    objectName: 'source_label',
  });
  if (page.pageNumber !== false) slide.addText(String(index + 1), {
    x: scene.width - 0.56, y: scene.height - 0.33, w: 0.28, h: 0.22,
    fontFace: theme.latinFont ?? theme.bodyFont, fontSize: 10, color: theme.muted,
    margin: 0, align: 'right', objectName: 'page_number',
  });
  if (page.notes) slide.addNotes(page.notes);
}
const output = resolve(outArg);
mkdirSync(dirname(output), { recursive: true });
await pptx.writeFile({ fileName: output });
writeFileSync(output + '.requirements.json', JSON.stringify(requirements, null, 2));
console.log(JSON.stringify({ output, slides: scene.slides.length,
  status: 'generated_not_rendered_or_edit_tested',
  requirements: output + '.requirements.json' }, null, 2));
