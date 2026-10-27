#!/usr/bin/env node
/**
 * build.js — The Polycrisis Apocalypse Humanity Is Facing
 * Reads sections/*.md (markdown) and emits a styled .docx (US Letter, Arial,
 * navy H1 / blue H2, TOC, headers/footers, embedded figures and tables).
 * Pipeline: docx-js → .docx, chartParagraph/pngSize pattern (EMU-safe),
 * JSZip post-processing: outlineLvl injection + wp:docPr id dedup.
 * Each H1 section starts on a new page (pageBreakBefore: true).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, ShadingType, WidthType,
  ImageRun, PageBreak, TableOfContents, Header, Footer, PageNumber,
  ExternalHyperlink,
} = require("docx");
const JSZip = require("jszip");

// docx-js does not emit a "Normal" paragraph style (it only sets w:docDefaults),
// which breaks pandoc heading detection (its style map starts from basedOn-less
// roots). Word has "Normal" built-in, so inserting it is safe and restores
// heading recognition for pandoc / navigation tooling.
function addNormalStyle(xml) {
  const normal = '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>';
  return xml.replace(/<w:style /, normal + "<w:style ");
}

// Inject w:outlineLvl into the Heading styles so Word's TOC (\o "1-2"),
// navigation pane, and pandoc all recognize the headings.
function fixHeadingStyles(xml) {
  const map = { Heading1: "0", Heading2: "1", Heading3: "2" };
  const names = { Heading1: "heading 1", Heading2: "heading 2", Heading3: "heading 3" };
  for (const [styleId, level] of Object.entries(map)) {
    // Inject w:outlineLvl into the heading style (before <w:rPr>) so the TOC \o field populates.
    const re = new RegExp(`(<w:style w:type="paragraph" w:styleId="${styleId}">[\\s\\S]*?)(<w:rPr>)`);
    xml = xml.replace(re, `$1<w:pPr><w:outlineLvl w:val="${level}"/></w:pPr>$2`);
    // docx-js writes the built-in heading style name as "Heading N" (title case);
    // Word/pandoc key off the lowercase built-in name "heading n".
    const reName = new RegExp(
      `(<w:style w:type="paragraph" w:styleId="${styleId}">[\\s\\S]*?<w:name w:val=")Heading ${styleId.slice(-1)}("\\s*/>)`
    );
    xml = xml.replace(reName, `$1${names[styleId]}$2`);
  }
  return xml;
}

const DIR = __dirname;
const CHART_DIR = path.join(DIR, "figures");
const CHART_TARGET_W_PX = Math.round(5.5 * 96); // 528px = 5.5in

const FONT = "Arial";
const BODY = 22;   // 11pt
const SMALL = 20;  // 10pt
const H1_SIZE = 32; // 16pt
const H2_SIZE = 26; // 13pt
const CAPTION = 18; // 9pt

const C = {
  navy: "#0F4D92", blue: "#3775BA", dark: "#2C3E50", grey: "#6C757D",
  lightGrey: "#ADB5BD", black: "#1A1A1A", white: "#FFFFFF", accent: "#E67E22",
};

function pngSize(buf) { return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }; }
function loadChart(name) {
  const p = path.join(CHART_DIR, `${name}.png`);
  if (!fs.existsSync(p)) { console.warn("  ! missing figure:", name); return null; }
  return fs.readFileSync(p);
}

let figureNumber = 0;
function chartParagraph(chartData, caption) {
  figureNumber++;
  if (!chartData) return [para(`[Figure ${figureNumber}: ${caption}]`)];
  const { w, h } = pngSize(chartData);
  const hPx = Math.round(CHART_TARGET_W_PX * (h / w));
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 280, after: 80 },
      children: [new ImageRun({
        type: "png", data: chartData,
        transformation: { width: CHART_TARGET_W_PX, height: hPx },
        altText: { title: caption, description: caption, name: caption.substring(0, 30) },
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 320 },
      children: [new TextRun({
        text: `Figure ${figureNumber}: ${caption}`,
        font: FONT, size: CAPTION, italics: true, color: C.grey,
      })],
    }),
  ];
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    ...opts,
    children: [new TextRun({ text, font: FONT, size: opts.size || BODY, color: C.black, ...opts })],
  });
}

function h1(text, opts = {}) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore: opts.pageBreak || false,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text, font: FONT, size: H1_SIZE, bold: true, color: C.navy })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 320, after: 160 },
    children: [new TextRun({ text, font: FONT, size: H2_SIZE, bold: true, color: C.blue })],
  });
}
function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 280, after: 140 },
    children: [new TextRun({ text, font: FONT, size: BODY, bold: true, color: C.dark })],
  });
}

// inline **bold** / *italic* / [text](url) parsing → runs
function inlineRuns(text) {
  const runs = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) runs.push({ text: text.slice(last, m.index) });
    const tok = m[0];
    if (tok.startsWith("[")) {
      const mm = tok.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      runs.push({ text: mm[1], link: mm[2] });
    } else {
      const bold = tok.startsWith("**");
      runs.push({ text: tok.replace(/\*/g, ""), bold, italics: !bold });
    }
    last = m.index + tok.length;
  }
  if (last < text.length) runs.push({ text: text.slice(last) });
  return runs;
}
function richParagraph(runs) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: runs.map(r => {
      if (r.link) {
        return new ExternalHyperlink({
          link: r.link,
          children: [new TextRun({
            text: r.text, font: FONT, size: BODY, color: C.blue, underline: {},
          })],
        });
      }
      return new TextRun({
        font: FONT, size: BODY, color: C.black,
        bold: r.bold || false, italics: r.italics || false, text: r.text,
      });
    }),
  });
}

function makeTable(header, rows) {
  const border = { style: BorderStyle.SINGLE, size: 4, color: "D5D8DC" };
  const cb = { top: border, bottom: border, left: border, right: border };
  const headerRow = new TableRow({
    tableHeader: true,
    children: header.map(t => new TableCell({
      shading: { fill: C.navy, type: ShadingType.CLEAR, color: "auto" },
      borders: cb,
      children: [new Paragraph({
        children: [new TextRun({ text: t, font: FONT, size: SMALL, bold: true, color: C.white })],
      })],
    })),
  });
  const bodyRows = rows.map(r => new TableRow({
    children: r.map(t => new TableCell({
      borders: cb,
      children: [new Paragraph({
        children: [new TextRun({ text: t, font: FONT, size: SMALL, color: C.black })],
      })],
    })),
  }));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [headerRow, ...bodyRows],
  });
}

function isSeparatorRow(cells) {
  return cells.length > 0 && cells.every(c => /^:?-+:?$/.test(c));
}

function parseMarkdown(md) {
  const lines = md.split("\n");
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("### ")) { out.push(h3(line.slice(4).trim())); i++; continue; }
    if (line.startsWith("## ")) { out.push(h2(line.slice(3).trim())); i++; continue; }
    if (line.startsWith("# ")) { out.push(h1(line.slice(2).trim(), { pageBreak: true })); i++; continue; }
    if (line.startsWith("FIG|")) {
      const parts = line.split("|");
      out.push(...chartParagraph(loadChart(parts[1]), parts.slice(2).join("|")));
      i++; continue;
    }
    if (line.trim().startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const cells = lines[i].trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(c => c.trim());
        if (!isSeparatorRow(cells)) rows.push(cells);
        i++;
      }
      if (rows.length >= 2) {
        out.push(makeTable(rows[0], rows.slice(1)));
        out.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
      }
      continue;
    }
    if (line.trim() === "") { i++; continue; }
    out.push(richParagraph(inlineRuns(line.trim())));
    i++;
  }
  return out;
}

function emptyPara() {
  return new Paragraph({ spacing: { after: 120 }, children: [] });
}

function titlePage() {
  return [
    emptyPara(), emptyPara(), emptyPara(), emptyPara(),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({
        text: "THE POLYCRISIS APOCALYPSE\nHUMANITY IS FACING",
        font: FONT, size: 50, bold: true, color: C.navy,
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 160 },
      children: [new TextRun({
        text: "Survivability risk regions, demographic tectonics, and the long road\nto human extinction — a scenario analysis",
        font: FONT, size: 26, color: C.blue, italics: true,
      })],
    }),
    emptyPara(),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 80 },
      children: [new TextRun({ text: "Hunter Hughes · H Heuristics", font: FONT, size: 24, color: C.dark })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 80 },
      children: [new TextRun({ text: "October 2026", font: FONT, size: 22, color: C.grey })],
    }),
    emptyPara(), emptyPara(), emptyPara(),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({
        text: "Prepared for policymakers, development finance institutions, demographers, security planners,\nand long-run risk analysts working on the reduction of human exposure to compounding catastrophe.",
        font: FONT, size: SMALL, color: C.grey, italics: true,
      })],
    }),
    new Paragraph({ children: [new PageBreak()] }),
  ];
}

function tableOfContents() {
  return [
    h1("Table of Contents"),
    emptyPara(),
    new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  ];
}

async function main() {
  const SEC_DIR = path.join(DIR, "sections");
  const files = fs.existsSync(SEC_DIR)
    ? fs.readdirSync(SEC_DIR).filter(f => f.endsWith(".md")).sort()
    : [];
  let md;
  if (files.length) {
    md = files.map(f => fs.readFileSync(path.join(SEC_DIR, f), "utf8")).join("\n\n");
    console.log(`Read ${files.length} section files: ${files.join(", ")}`);
  } else {
    md = fs.readFileSync(path.join(DIR, "draft.md"), "utf8");
  }
  const body = parseMarkdown(md);

  const doc = new Document({
    creator: "Hunter Hughes · H Heuristics",
    title: "The Polycrisis Apocalypse Humanity Is Facing",
    description: "Survivability risk regions, demographic tectonics, and the long road to human extinction — a scenario analysis.",
    features: { updateFields: true },
    styles: {
      default: { document: { run: { font: FONT, size: BODY } } },
    },
    sections: [
      {
        properties: {
          page: {
            size: { width: 12240, height: 15840 }, // US Letter
            margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 }, // 1 inch
          },
        },
        headers: {
          default: new Header({
            children: [new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({
                text: "The Polycrisis Apocalypse Humanity Is Facing  |  H Heuristics  |  October 2026",
                font: FONT, size: 16, color: C.lightGrey, italics: true,
              })],
            })],
          }),
        },
        footers: {
          default: new Footer({
            children: [new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Page ", font: FONT, size: 16, color: C.grey }),
                new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: C.grey }),
              ],
            })],
          }),
        },
        children: [...titlePage(), ...tableOfContents(), ...body],
      },
    ],
  });

  const buffer = await Packer.toBuffer(doc);

  // Post-process: (1) add outline levels so the TOC populates; (2) dedup wp:docPr ids.
  const zip = await JSZip.loadAsync(buffer);
  const stylesXml = await zip.file("word/styles.xml").async("string");
  zip.file("word/styles.xml", addNormalStyle(fixHeadingStyles(stylesXml)));

  const docXml = await zip.file("word/document.xml").async("string");
  let n = 0;
  const deduped = docXml.replace(/(<wp:docPr\b[^>]*?\bid=")1(")/g, (_m, pre, post) => `${pre}${++n}${post}`);
  zip.file("word/document.xml", deduped);

  const outBuffer = await zip.generateAsync({
    type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 6 },
  });

  const outPath = path.join(__dirname, "The_Polycrisis_Apocalypse_Humanity_Is_Facing.docx");
  fs.writeFileSync(outPath, outBuffer);
  console.log(`Report written: ${outPath}`);
  console.log(`Size: ${(outBuffer.length / 1024 / 1024).toFixed(1)} MB`);
  console.log(`Figures embedded: ${figureNumber}`);
}

main().catch(err => { console.error("Build failed:", err); process.exit(1); });
