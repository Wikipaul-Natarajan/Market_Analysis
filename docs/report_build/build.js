const fs = require('fs');
const lib = require('./lib');
const { d, P, H1u, reg, FONT } = lib;
const { Document, Packer, Paragraph, TextRun, Footer, AlignmentType, PageNumber, NumberFormat, LevelFormat, TableOfContents, TabStopType, TabStopPosition } = d;
const A = require('./ch1_2'); const { ch3 } = require('./ch3'); const { ch4 } = require('./ch4'); const B = require('./ch5_app');

// Build body first so the table/figure registry is populated for the lists.
const body = [A.ch1(), A.ch2(), ch3(), ch4(), B.ch5(), B.references(), B.appendices()].flat(Infinity);
const abbr = A.abbreviations().flat(Infinity);
const entry = (label, cap) => new Paragraph({ spacing: { after: 60, line: 276 }, indent: { left: 1134, hanging: 1134 },
  children: [new TextRun({ text: `${label}\t`, font: FONT, size: 22, bold: true }), new TextRun({ text: cap, font: FONT, size: 22 })],
  tabStops: [{ type: TabStopType.LEFT, position: 1134 }] });
const note = P('Page numbers appear when fields are updated in Microsoft Word (accept the prompt on opening, or press Ctrl+A then F9).', { run: { size: 18, italics: true }, align: AlignmentType.CENTER });
const lot = [H1u('List of Tables'), new TableOfContents('List of Tables', { hyperlink: true, stylesWithLevels: [new d.StyleLevel('TableCaption', 1)] }), note];
const lof = [H1u('List of Figures'), new TableOfContents('List of Figures', { hyperlink: true, stylesWithLevels: [new d.StyleLevel('FigureCaption', 1)] }), note];
const toc = [H1u('Table of Contents'), new TableOfContents('Table of Contents', { hyperlink: true, headingStyleRange: '1-2' }),
  P('Page numbers appear when fields are updated in Microsoft Word (accept the prompt on opening, or press Ctrl+A then F9).', { run: { size: 18, italics: true }, align: AlignmentType.CENTER })];
const front = [A.bonafide(), A.declaration(), A.acknowledgement(), A.abstract(), toc, lot, lof, abbr].flat(Infinity);

const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 22 })] })] });
const margin = { top: 1814, right: 1304, bottom: 1531, left: 2154, header: 720, footer: 720 };
const page = { size: { width: 11906, height: 16838 }, margin };

const numbering = { config: [{ reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 567, hanging: 340 } } } }] },
  ...Array.from({ length: 40 }, (_, i) => ({ reference: `num${i}`, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 567, hanging: 397 } } } }] }))] };

const hstyle = (id, name, size, extra = {}) => ({ id, name, basedOn: 'Normal', next: 'Normal', quickFormat: true,
  run: { font: FONT, size, bold: true, color: '000000', ...(extra.run || {}) }, paragraph: { keepNext: true, keepLines: true, outlineLevel: extra.lvl, ...(extra.p || {}) } });

const doc = new Document({
  creator: 'Vignesh Natarajan', title: 'AgriSight Final Project Report', description: 'MBA Business Analytics project report',
  features: { updateFields: true },
  styles: { default: { document: { run: { font: FONT, size: 24 } } },
    paragraphStyles: [hstyle('Heading1', 'Heading 1', 28, { lvl: 0, p: { alignment: AlignmentType.CENTER } }), hstyle('Heading2', 'Heading 2', 26, { lvl: 1 }),
      hstyle('Heading3', 'Heading 3', 24, { lvl: 2, run: { italics: true } }),
      { id: 'TableCaption', name: 'TableCaption', basedOn: 'Normal', run: { font: FONT, size: 22 }, paragraph: { alignment: AlignmentType.CENTER } },
      { id: 'FigureCaption', name: 'FigureCaption', basedOn: 'Normal', run: { font: FONT, size: 22 }, paragraph: { alignment: AlignmentType.CENTER } }] },
  numbering,
  sections: [
    { properties: { page }, children: A.titlePage() },
    { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } } }, footers: { default: footer }, children: front },
    { properties: { page: { ...page, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } }, footers: { default: footer }, children: body },
  ],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(require('path').resolve(__dirname, '../../outputs/final_project_report_20261018/AgriSight_Final_Project_Report.docx'), b);
  console.log('written', b.length, 'tables', reg.tables.length, 'figures', reg.figures.length); });
setTimeout(() => { const t = reg.tables.filter(x => /^4\./.test(x.id)).map(x => `${x.id} ${x.caption.slice(0, 45)}`); const f = reg.figures.filter(x => /^4\./.test(x.id)).map(x => `${x.id} ${x.caption.slice(0, 45)}`);
  fs.writeFileSync(require('path').join(require('os').tmpdir(), 'reg.txt'), t.join('\n') + '\n---\n' + f.join('\n')); }, 100);
