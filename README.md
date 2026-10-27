# The Polycrisis Apocalypse Humanity Is Facing

**H Heuristics digital report · October 2026 · Hunter Hughes**

A scenario analysis of survivability risk regions, demographic tectonics, and the long road to human extinction.

- **Format:** Word (.docx) + PDF, 38 pages, 12,000+ words, 10 figures, 4 tables, hyperlinked in-text citations
- **Claim:** Humanity is not heading for a sudden apocalypse but for a centuries-long polycrisis apocalypse — a demographic and environmental re-sorting that traps the majority of the species inside survivability risk regions, stabilizes it at unsafe levels, and only then decays toward extinction — unless the compounding loops are broken now.
- **Binding term:** Move the median human out of the survivability risk region, or merely manage their suffering inside it.

## Files

| File | Purpose |
|---|---|
| `The_Polycrisis_Apocalypse_Humanity_Is_Facing.docx` | Master Word deliverable (each section starts on a new page) |
| `The_Polycrisis_Apocalypse_Humanity_Is_Facing.pdf` | PDF export (38 pages) |
| `index.html` | **Digital report webpage** — digitalreports.hheuristics.com house format: masthead caption, sticky nav, exec-grid, stat-grid, chart-containers, pull-quotes, ref-list, report footer. 4 figures are interactive Chart.js charts |
| `build_site.py` | Builds `index.html` from `sections/*.md` via pandoc |
| `sections/*.md` | Source markdown sections (13 files) |
| `figures/*.png` | 10 brand-styled matplotlib figures (6 embedded as PNG; 4 re-rendered interactively) |
| `OUTLINE.md` | Budgeted outline (word counts, figures, tables, sources) |
| `build.js` | docx-js assembly script (US Letter, TOC, headers/footers) |
| `make_figures.py` | Figure generation (save_chart docx-safe pattern) |

## Rebuild

```bash
# digital report webpage
python3 build_site.py

# figures
source ../.reasonix-env.sh && python3 make_figures.py
# document
node build.js
# pdf
soffice --headless -env:UserInstallation=file:///tmp/lo_profile --convert-to pdf --outdir . The_Polycrisis_Apocalypse_Humanity_Is_Facing.docx
# verify
python3 ../.reasonix/skills/docx/scripts/office/validate.py The_Polycrisis_Apocalypse_Humanity_Is_Facing.docx
```

## Verification status

- docx validation: PASSED
- EMU image sizing: all `cx="5029200"` (5.5 in)
- CJK scan: 0 characters (English-only)
- Pandoc word count: 12,351
- Page count: 38 (US Letter)
- prose_lint: 0 errors

## Deployment

Push to `main` and enable GitHub Pages from the repository root. The landing page embeds the PDF and links the Word download.
