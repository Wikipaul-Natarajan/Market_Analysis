const fs = require('fs');
const path = require('path');
const d = require('docx');
const { Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel, WidthType,
  BorderStyle, ShadingType, PageBreak, VerticalAlign } = d;

const FIG = require('path').resolve(__dirname, '../../outputs/figures');
const FONT = 'Times New Roman';
const TEXT_W = 8448; // A4 width 11906 - left 2154 - right 1304

const reg = { tables: [], figures: [] };
let chap = 0, tcount = 0, fcount = 0;
function setChapter(n) { chap = n; tcount = 0; fcount = 0; }

// Inline markup: **bold**, *italic*
function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, ...base }));
    const t = m[0];
    if (t.startsWith('**')) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, ...base }));
  return out;
}

const P = (text, opts = {}) => new Paragraph({
  children: runs(text, opts.run || {}), alignment: opts.align || AlignmentType.JUSTIFIED,
  spacing: { line: opts.line || 360, after: opts.after ?? 120, before: opts.before || 0 },
  indent: opts.indent, keepNext: opts.keepNext,
});
const C = (text, opts = {}) => P(text, { ...opts, align: AlignmentType.CENTER });
const blank = (n = 1) => Array.from({ length: n }, () => new Paragraph({ children: [new TextRun({ text: '', font: FONT })] }));
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

function chapter(num, title) {
  setChapter(num);
  return [
    new Paragraph({ pageBreakBefore: true, alignment: AlignmentType.CENTER, spacing: { before: 240, after: 0 },
      children: [new TextRun({ text: `CHAPTER ${num}`, bold: true, font: FONT, size: 28 })] }),
    new Paragraph({ heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, spacing: { before: 120, after: 360 },
      children: [new TextRun({ text: title.toUpperCase(), bold: true, font: FONT, size: 28 })] }),
  ];
}
// Unnumbered front/back-matter heading that still appears in the TOC
const H1u = (title, pageBreakBefore = true) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore,
  alignment: AlignmentType.CENTER, spacing: { before: 240, after: 360 },
  children: [new TextRun({ text: title.toUpperCase(), bold: true, font: FONT, size: 28 })] });
const H2 = (title) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 280, after: 120 },
  children: [new TextRun({ text: title, bold: true, font: FONT, size: 26 })] });
const H3 = (title) => new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, spacing: { before: 200, after: 100 },
  children: [new TextRun({ text: title, bold: true, italics: true, font: FONT, size: 24 })] });

const bullets = (items, ref = 'bul') => items.map(t => new Paragraph({ numbering: { reference: ref, level: 0 },
  alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 60 }, children: runs(t) }));
let numListId = 0;
function numbered(items) {
  const ref = `num${numListId++}`;
  return { ref, paras: items.map(t => new Paragraph({ numbering: { reference: ref, level: 0 }, alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 60 }, children: runs(t) })) };
}

const border = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
const borders = { top: border, bottom: border, left: border, right: border };

// table(caption, header[], rows[][], {widths, source, size, align})
function table(caption, header, rows, opts = {}) {
  tcount += 1; const id = `${chap || 'A'}.${tcount}`;
  const label = opts.label || id; reg.tables.push({ id: label, caption });
  const n = header.length;
  const widths = opts.widths ? opts.widths.map(w => Math.round(w / opts.widths.reduce((a, b) => a + b, 0) * TEXT_W))
                             : Array(n).fill(Math.floor(TEXT_W / n));
  widths[n - 1] += TEXT_W - widths.reduce((a, b) => a + b, 0);
  const size = opts.size || 19;
  const cell = (txt, i, head) => new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { fill: 'D9E2F3', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 }, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: head ? AlignmentType.CENTER : ((opts.align && opts.align[i]) || (i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER)),
      spacing: { line: 240, after: 0 }, children: runs(String(txt), { size, bold: head || undefined }) })] });
  const out = [new Paragraph({ style: 'TableCaption', keepNext: true, alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80, line: 276 },
      children: [new TextRun({ text: `Table ${label}: `, bold: true, font: FONT, size: 22 }), new TextRun({ text: caption, font: FONT, size: 22 })] }),
    new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths,
      rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, i) => cell(h, i, true)) }),
             ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false)) }))] })];
  out.push(new Paragraph({ spacing: { before: 60, after: 200, line: 240 }, children: runs(opts.source ? `Source: ${opts.source}` : '', { size: 18, italics: true }) }));
  return out;
}

function pngSize(file) { const b = fs.readFileSync(file); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; }
function figure(rel, caption, opts = {}) {
  fcount += 1; const id = `${chap}.${fcount}`; reg.figures.push({ id, caption });
  const file = path.join(FIG, rel); const { w, h } = pngSize(file);
  const maxW = (opts.width || 1) * 560, maxH = opts.maxH || 640;
  let W = maxW, H = Math.round(h * W / w); if (H > maxH) { H = maxH; W = Math.round(w * H / h); }
  return [new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 60 },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(file), transformation: { width: W, height: H },
        altText: { title: caption, description: caption, name: `Figure ${id}` } })] }),
    new Paragraph({ style: 'FigureCaption', alignment: AlignmentType.CENTER, spacing: { after: opts.source ? 40 : 220, line: 276 },
      children: [new TextRun({ text: `Figure ${id}: `, bold: true, font: FONT, size: 22 }), new TextRun({ text: caption, font: FONT, size: 22 })] }),
    ...(opts.source ? [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 220, line: 240 }, children: runs(`Source: ${opts.source}`, { size: 18, italics: true }) })] : [])];
}

module.exports = { d, P, C, blank, pageBreak, chapter, H1u, H2, H3, bullets, numbered, table, figure, reg, runs, FONT, TEXT_W, setChapter };
