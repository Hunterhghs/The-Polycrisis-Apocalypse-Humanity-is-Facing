#!/usr/bin/env python3
"""
build_site.py — The Polycrisis Apocalypse Humanity Is Facing
Builds index.html as a digitalreports.hheuristics.com-style digital report
(masthead caption, sticky nav, exec-grid, stat-grid, chart-container,
pull-quote, callout, data-table, ref-list, report footer) from sections/*.md.
"""
import html
import re
import subprocess
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
SECTIONS = sorted((DIR / "sections").glob("*.md"))

INTERACTIVE = {
    "fig3_trapped_share": "chart3",
    "fig4_africa_rise": "chart4",
    "fig5_world_share_2100": "chart5",
    "fig7_haiti_collapse": "chart7",
}

TABLE_CAPTIONS = {
    1: "Habitability tiers and their 2050 populations",
    2: "Regional demographic projections, 2024\u20132100",
    3: "Haiti collapse timeline, 1804\u20132025",
    4: "Three long-run scenarios to 2300",
}

DEKS = {
    "Executive Summary": "The apocalypse is not a blast. It is a re-sorting of the species into survivability risk regions, a stabilization at unsafe levels, and a long decay \u2014 unless the loops are broken now.",
    "1. The Polycrisis Apocalypse Frame": "The slow apocalypse is the probable branch \u2014 and it hides in plain sight.",
    "2. Survivability Risk Regions: The Majority's Destination": "Habitable but harmful: the four tiers and the six vectors that trap the majority.",
    "3. The Long Degradation Arc: Centuries to Extinction": "Collapse runs for centuries. The length of the arc measures the suffering, not the warning.",
    "4. Demographic Tectonics: Africa's Ascent, the West's Decline": "Africa adds 2.3 billion people this century while Europe contracts. The centre of gravity shifts south.",
    "5. The Middle-50% Hypothesis: The Average Human in 2200": "The median human of 2200 is a child in a risk region \u2014 unless this century changes that.",
    "6. Case Study: The Collapse of Haiti": "Haiti is the preview: a trapped population, a hollow state, and criminal governance.",
    "7. Advanced Weapons and the Threat Multiplier": "Arsenals are modernising while the capacity for violence diffuses downward.",
    "8. Societal Turmoil and Instability Cascades": "Shocks do not stay in one system. Prices, migration, and violence cascade.",
    "9. The Diaspora-Dominance Collapse Trajectory": "Three scenarios diverge on one variable: whether the risk regions develop first.",
    "10. Counter-Forces and Stabilizers": "The stabilisers exist. They are currently losing.",
    "11. The Apocalypse Is a Choice, Not a Schedule": "The apocalypse is a choice, not a schedule.",
    "12. References": "Every quantitative claim is attributed inline. Principal sources are collected here.",
}

PULL_QUOTES = [
    ("exec", "\u201cThe apocalypse is not written in the population\u2019s ancestry. It is written in the failure to build.\u201d", "Chapter 9"),
    ("2", "\u201cThe risk region is not a margin of the map. It is the centre of the human distribution.\u201d", "Chapter 2"),
    ("6", "\u201cCollapse is a governance event before it is an environmental one.\u201d", "Chapter 6"),
]

figure_count = 0
table_count = 0


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def md_to_html(md_text):
    p = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html5", "--wrap=none"],
        input=md_text, capture_output=True, text=True,
    )
    if p.returncode != 0:
        sys.exit(f"pandoc failed: {p.stderr}")
    return p.stdout.strip()


def process_fig(m):
    global figure_count
    figure_count += 1
    name, caption = m.group(1), m.group(2)
    num = figure_count
    cap = html.escape(caption)
    if name in INTERACTIVE:
        cid = INTERACTIVE[name]
        inner = f'<div class="chart-frame"><canvas id="{cid}" aria-label="{cap}"></canvas></div>'
    else:
        inner = f'<div class="chart-frame"><img src="figures/{name}.png" alt="{cap}" loading="lazy"></div>'
    return (
        f'<div class="chart-container">'
        f'<p class="chart-label">Figure {num} \u2014 {cap}</p>'
        f'{inner}'
        f'<p class="chart-caption">{cap}.</p>'
        f'</div>'
    )


def add_table_captions(fragment):
    global table_count
    def repl(m):
        global table_count
        table_count += 1
        cap = TABLE_CAPTIONS.get(table_count, f"Table {table_count}")
        tag = m.group(0).replace("<table", '<table class="data-table"')
        return f'<p class="table-caption">Table {table_count} \u2014 {cap}</p>\n{tag}'
    return re.sub(r"<table[^>]*>", repl, fragment)


def section_body(md):
    lines = md.split("\n")
    title = ""
    body_lines = []
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("# "):
            title = line[2:].strip()
            continue
        body_lines.append(line)
    body = "\n".join(body_lines)
    body = re.sub(r"^FIG\|([^|]+)\|(.*)$", process_fig, body, flags=re.M)
    frag = md_to_html(body)
    frag = add_table_captions(frag)
    # remap markdown H2 -> h3 (section title is the h2); handle pandoc id attrs
    frag = frag.replace("<h2 ", "<h3 ").replace("<h2>", "<h3>")
    frag = frag.replace("</h2>", "</h3>")
    return title, frag


def ref_list(md):
    lines = md.split("\n")
    items = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)\s*[\u2014-]\s*(.*)$", line)
        if m:
            label, url, note = m.group(1), m.group(2), m.group(3)
            items.append(
                f'<li><span class="ref-org">{html.escape(label)}</span>'
                f'<a href="{html.escape(url)}" rel="noopener" target="_blank">{html.escape(label)}</a>'
                f' \u2014 {html.escape(note)}</li>'
            )
        elif line and not line.startswith("["):
            items.append(f'<li class="ref-note">{html.escape(line)}</li>')
    return '<ul class="ref-list">\n' + "\n".join(items) + "\n</ul>"


def build():
    global figure_count, table_count
    body = []
    toc_items = []

    for idx, path in enumerate(SECTIONS):
        md = path.read_text(encoding="utf-8")
        title = md.split("\n", 1)[0].lstrip("# ").strip()
        slug = slugify(title)
        label = title
        if label.startswith("Executive Summary"):
            label = "Executive Summary"
        if label.startswith("12."):
            label = "References"
        toc_items.append(f'<a href="#{slug}">{html.escape(label)}</a>')

        dek = DEKS.get(title, "")
        if idx == 0:
            # Executive summary: house-style exec grid + stat grid + prose + pull quote
            _, frag = section_body(md)
            pq = next((q for q in PULL_QUOTES if q[0] == "exec"), None)
            pull = f'<div class="pull-quote">{pq[1]}<span class="attribution">{pq[2]}</span></div>' if pq else ""
            body.append(
                f'<section id="{slug}">'
                f'<h2>{html.escape(title)}</h2>'
                f'<p class="section-dek">{dek}</p>'
                f'<div class="exec-grid">'
                f'<div class="exec-card"><div class="exec-num">FINDING 01</div><p class="exec-title">The apocalypse is a plateau, not a blast</p><p class="exec-body">A majority of humanity is being re-sorted into survivability risk regions \u2014 habitable but harmful \u2014 where conditions stabilise at unsafe levels and then decay over centuries, not in one event.</p></div>'
                f'<div class="exec-card"><div class="exec-num">FINDING 02</div><p class="exec-title">Demography moves the median human south</p><p class="exec-body">Africa grows from 1.5 billion to 3.8 billion people by 2100 while Europe contracts; the middle of the human distribution enters Africa in the 22nd century.</p></div>'
                f'<div class="exec-card"><div class="exec-num">FINDING 03</div><p class="exec-title">Collapse is a governance failure, not destiny</p><p class="exec-body">Haiti shows the mechanism \u2014 extractive legacy, hollow institutions, criminal governance, a trapped population. The Dominican comparison refutes any demographic-determinist reading.</p></div>'
                f'<div class="exec-card"><div class="exec-num">FINDING 04</div><p class="exec-title">Weapons and turmoil convert slow decline into fast collapse</p><p class="exec-body">Roughly 9,600 nuclear warheads sit in military stockpiles while autonomy diffuses downward; price, migration and violence cascades run through every risk region.</p></div>'
                f'</div>'
                f'<div class="stat-grid">'
                f'<div class="stat-card"><div class="stat-value">4.2 B</div><div class="stat-label">People in the Survivability Risk Zone by 2050</div><div class="stat-source">H Heuristics survivability model, 2026</div></div>'
                f'<div class="stat-card"><div class="stat-value">3.8 B</div><div class="stat-label">Africa\u2019s projected population by 2100</div><div class="stat-source">UN World Population Prospects 2024</div></div>'
                f'<div class="stat-card"><div class="stat-value">37%</div><div class="stat-label">Africa\u2019s projected share of humanity by 2100</div><div class="stat-source">UN World Population Prospects 2024</div></div>'
                f'<div class="stat-card"><div class="stat-value">9,600+</div><div class="stat-label">Nuclear warheads in military stockpiles, January 2025</div><div class="stat-source">SIPRI Yearbook 2025</div></div>'
                f'<div class="stat-card"><div class="stat-value">~90%</div><div class="stat-label">Of Port-au-Prince under gang control, 2025</div><div class="stat-source">UN News / BINUH / FEWS NET</div></div>'
                f'</div>'
                f'{frag}{pull}'
                f'</section>'
            )
        elif idx == len(SECTIONS) - 1:
            # References
            refs = ref_list(md)
            body.append(
                f'<section id="{slug}">'
                f'<h2>{html.escape(title)}</h2>'
                f'<p class="section-dek">{dek}</p>'
                f'{refs}'
                f'</section>'
            )
        else:
            _, frag = section_body(md)
            pull = ""
            for key, text, attr in PULL_QUOTES:
                if key == title.split(".")[0]:
                    pull = f'<div class="pull-quote">{text}<span class="attribution">{attr}</span></div>'
                    break
            body.append(
                f'<section id="{slug}">'
                f'<h2>{html.escape(title)}</h2>'
                f'<p class="section-dek">{dek}</p>'
                f'{frag}{pull}'
                f'</section>'
            )

    sections_html = '\n<hr class="section-rule">\n'.join(body)
    toc_html = "\n".join(toc_items)
    page = TEMPLATE.replace("__TOC__", toc_html).replace("__SECTIONS__", sections_html)
    (DIR / "index.html").write_text(page, encoding="utf-8")
    print(f"index.html written: {len(page):,} bytes, {len(SECTIONS)} sections, "
          f"{figure_count} figures ({len(INTERACTIVE)} interactive), {table_count} tables")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Polycrisis Apocalypse Humanity Is Facing — H Heuristics Digital Report</title>
<meta name="description" content="Survivability risk regions, demographic tectonics, and the long road to human extinction — a scenario analysis. Hunter Hughes, H Heuristics, October 2026.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Public+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
/* ===========================================================================
   Theme — "The Polycrisis Apocalypse Humanity Is Facing"
   Aesthetic: risk dossier. White ground, H Heuristics navy structure, orange
   rulings, hairline rules everywhere. Source Serif 4 carries the prose,
   Public Sans the argument, IBM Plex Mono the citations. Built to match the
   digitalreports.hheuristics.com house format.
   =========================================================================== */
:root{
  --bg:#ffffff;
  --bg-card:#fbfcfe;
  --bg-accent:#eef3f9;
  --bg-dark:#0a1628;
  --bg-dark-2:#060d1a;
  --text:#191f28;
  --text-secondary:#38424f;
  --text-muted:#66717f;
  --text-inverse:#f2f6fb;
  --primary:#0F4D92;
  --primary-light:#3775BA;
  --accent:#E67E22;
  --accent-light:#f0a04b;
  --border:#d8dee5;
  --border-light:#e7ebf0;
  --rule:#b9c3cf;
  --chart-blue:#0F4D92;
  --chart-blue-light:#3775BA;
  --chart-gold:#E67E22;
  --chart-red:#C0392B;
  --chart-teal:#2E86AB;
  --chart-gray:#8b93a1;
  --chart-orange:#E67E22;
  --chart-green:#27AE60;
  --serif:"Source Serif 4","Iowan Old Style",Georgia,serif;
  --sans:"Public Sans",-apple-system,BlinkMacSystemFont,"system-ui",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --gutter:clamp(16px,4vw,40px);
  --max-width:960px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{background:var(--bg);color:var(--text);font-family:var(--serif);font-size:1.02rem;line-height:1.72;margin:0;}
::selection{background:rgba(15,77,146,.16);}
a{color:var(--primary);text-decoration:underline;text-underline-offset:2px;}
a:hover{color:var(--accent);}
:where(a,button,[tabindex]):focus-visible{outline:2px solid var(--primary);outline-offset:2px;}
.progress{position:fixed;top:0;left:0;right:0;height:3px;background:transparent;z-index:60;}
.progress__bar{height:100%;width:0;background:var(--primary);}
.skip-link{position:absolute;left:-9999px;top:0;background:var(--primary);color:#fff;padding:.6rem 1rem;font-family:var(--sans);font-size:.8rem;z-index:70;}
.skip-link:focus{left:0;}

/* --- masthead -------------------------------------------------------------- */
.masthead{background:var(--bg);border-top:8px solid var(--primary);border-bottom:1px solid var(--border);padding:2.4rem var(--gutter) 0;max-width:var(--max-width);margin:0 auto;}
.masthead .overline{display:inline-block;border:1px solid var(--rule);color:var(--text-muted);background:var(--bg-card);padding:.42rem .75rem;font-family:var(--mono);font-size:.56rem;font-weight:500;letter-spacing:.18em;text-transform:uppercase;margin-bottom:1.5rem;}
.masthead h1{font-family:var(--serif);font-size:clamp(1.95rem,5vw,2.85rem);font-weight:700;letter-spacing:-.02em;line-height:1.1;max-width:20ch;color:var(--primary);}
.masthead .subtitle{font-family:var(--serif);font-style:italic;color:var(--text-secondary);font-size:clamp(1.05rem,2.4vw,1.35rem);margin-top:.9rem;max-width:56ch;}
.masthead .strapline{border-left:4px solid var(--accent);padding:.2rem 0 .2rem 1rem;color:var(--text-secondary);font-family:var(--sans);font-style:normal;font-size:1rem;margin-top:1.4rem;max-width:60ch;}
.masthead .meta-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(136px,1fr));gap:0 1px;margin-top:2.2rem;background:var(--border-light);font-family:var(--mono);font-size:.7rem;color:var(--text-secondary);}
.masthead .meta-row div{background:var(--bg-card);border-top:3px solid var(--accent);padding:.8rem .9rem 1.1rem 0;}
.masthead .meta-row strong{display:block;color:var(--accent);font-family:var(--mono);font-size:.58rem;font-weight:500;letter-spacing:.14em;margin-bottom:.3rem;text-transform:uppercase;}

/* --- sticky nav ------------------------------------------------------------ */
.sticky-nav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.97);border-bottom:2px solid var(--primary);}
.nav-inner{max-width:var(--max-width);margin:0 auto;padding:.55rem var(--gutter);display:flex;gap:1.15rem;overflow-x:auto;white-space:nowrap;scrollbar-width:none;}
.nav-inner::-webkit-scrollbar{display:none;}
.nav-inner a{color:var(--text-muted);font-family:var(--mono);font-size:.66rem;text-decoration:none;letter-spacing:.02em;padding-bottom:.25rem;border-bottom:2px solid transparent;}
.nav-inner a:hover{color:var(--primary);}
.nav-inner a.is-active{color:var(--primary);border-bottom-color:var(--accent);}

/* --- layout ---------------------------------------------------------------- */
main{max-width:var(--max-width);margin:0 auto;padding:2.6rem var(--gutter) 4rem;}
section > h2{font-family:var(--serif);font-size:1.7rem;font-weight:700;letter-spacing:-.015em;color:var(--primary);border-bottom:3px double var(--primary);padding-bottom:.55rem;margin-bottom:.4rem;}
section > .section-dek{font-style:italic;font-family:var(--serif);color:var(--text-muted);font-size:1rem;max-width:66ch;margin:0 0 1.6rem;}
section > h3{font-family:var(--serif);font-weight:600;font-size:1.18rem;letter-spacing:-.01em;color:var(--text);margin:2.4rem 0 .7rem;}
section > h4{color:var(--accent);font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;margin:1.8rem 0 .5rem;}
section p{margin:0 0 1.1rem;}
section strong{color:var(--primary);font-weight:600;}
section ul,section ol{margin:0 0 1.2rem 1.4rem;}
section li{margin-bottom:.45rem;}
.section-rule{border:0;border-top:1px solid var(--rule);margin:3.2rem 0;}

/* --- exec grid ------------------------------------------------------------- */
.exec-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:1.4rem 0 2rem;}
.exec-card{background:var(--bg-card);border:1px solid var(--border);border-top:4px solid var(--primary);padding:1.3rem 1.35rem;}
.exec-card .exec-num{font-family:var(--mono);font-size:.6rem;font-weight:500;letter-spacing:.14em;color:var(--accent);line-height:1;}
.exec-card .exec-title{font-family:var(--serif);font-weight:700;font-size:1.1rem;letter-spacing:-.015em;color:var(--primary);margin:.8rem 0 .5rem;}
.exec-card .exec-body{font-size:.95rem;color:var(--text-secondary);line-height:1.6;margin:0;}

/* --- stat grid ------------------------------------------------------------- */
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:1.6rem 0 2rem;}
.stat-card{background:var(--bg-card);border:1px solid var(--border);border-top:4px solid var(--accent);padding:1.1rem 1.2rem;}
.stat-card .stat-value{font-family:var(--serif);font-weight:700;font-size:1.8rem;letter-spacing:-.03em;color:var(--primary);line-height:1;}
.stat-card .stat-label{color:var(--text-secondary);font-size:.82rem;margin-top:.4rem;line-height:1.45;}
.stat-card .stat-source{font-family:var(--mono);font-size:.6rem;color:var(--text-muted);letter-spacing:.02em;margin-top:.55rem;}

/* --- charts ---------------------------------------------------------------- */
.chart-container{background:var(--bg-card);border:1px solid var(--border);padding:1.25rem 1.35rem;margin:1.8rem 0;}
.chart-container .chart-label{font-family:var(--mono);color:var(--primary);font-weight:500;font-size:.62rem;letter-spacing:.02em;text-transform:uppercase;padding-bottom:.7rem;border-bottom:1px solid var(--border-light);}
.chart-frame{margin-top:.9rem;}
.chart-frame canvas{max-height:440px;width:100% !important;}
.chart-frame img{max-width:100%;height:auto;display:block;margin:0 auto;}
.chart-container .chart-caption{border-top:1px solid var(--border-light);padding-top:.7rem;color:var(--text-muted);font-family:var(--sans);font-size:.82rem;font-style:normal;line-height:1.55;}

/* --- pull quote ------------------------------------------------------------ */
.pull-quote{position:relative;background:var(--bg-card);border:1px solid var(--border);border-left:6px double var(--accent);padding:1.7rem 1.8rem 1.5rem 2.3rem;margin:2.6rem 0;font-family:var(--serif);font-style:italic;font-weight:600;font-size:clamp(1.15rem,2.6vw,1.42rem);line-height:1.4;letter-spacing:-.01em;color:var(--text);max-width:46ch;}
.pull-quote::before{content:"\201C";position:absolute;left:.9rem;top:.35rem;font-size:3.2rem;line-height:1;color:var(--accent);font-style:normal;font-family:var(--serif);}
.pull-quote .attribution{display:block;font-family:var(--mono);font-style:normal;font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-top:1rem;font-weight:500;}

/* --- callouts -------------------------------------------------------------- */
.callout{background:var(--bg-card);border:1px solid var(--border);border-left:5px solid var(--accent);padding:1.3rem 1.45rem;margin:1.8rem 0;}
.callout .callout-title{color:var(--accent);font-family:var(--mono);font-weight:500;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.4rem;}
.callout strong{color:var(--primary);}
.callout--warn{border-left-color:var(--chart-red);}
.callout--warn .callout-title{color:var(--chart-red);}

/* --- tables ---------------------------------------------------------------- */
.table-caption{color:var(--accent);font-family:var(--mono);font-weight:500;font-size:.62rem;letter-spacing:.02em;text-transform:uppercase;margin:1.8rem 0 .6rem;}
.data-table{border-collapse:collapse;width:100%;margin:0 0 1.4rem;font-family:var(--sans);font-size:.85rem;}
.data-table thead{background:var(--primary);color:#fff;}
.data-table thead th{font-family:var(--mono);font-size:.6rem;letter-spacing:.02em;padding:.65rem .8rem;text-align:left;text-transform:uppercase;}
.data-table tbody td{border:1px solid var(--border);padding:.6rem .8rem;vertical-align:top;line-height:1.5;}
.data-table tbody tr:nth-child(even){background:var(--bg-accent);}
.data-table tbody tr:hover{background:rgba(230,126,34,.07);}

/* --- references ------------------------------------------------------------ */
.ref-list{list-style:none;margin:1.4rem 0 0;}
.ref-list li{border-top:1px solid var(--border-light);padding:.75rem 0;font-family:var(--sans);font-size:.9rem;line-height:1.6;}
.ref-list .ref-org{display:block;color:var(--accent);font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.15rem;}
.ref-list a{font-weight:500;}

/* --- footer ---------------------------------------------------------------- */
.report-footer{background:var(--bg-dark);color:var(--text-inverse);border-top:6px solid var(--primary);margin-top:4rem;padding:3rem var(--gutter);}
.footer-inner{max-width:var(--max-width);margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:2rem;}
.footer-inner h3{font-family:var(--serif);color:#fff;font-weight:700;font-size:1.2rem;letter-spacing:-.01em;margin-bottom:.6rem;}
.footer-inner p{font-family:var(--sans);font-size:.85rem;color:rgba(242,246,251,.8);}
.footer-inner a{color:#fff;text-decoration:underline;}
.cite-box{border-left:3px solid var(--accent-light);padding-left:1.1rem;}
.cite-box code{font-family:var(--mono);font-size:.72rem;color:rgba(242,246,251,.85);display:block;line-height:1.7;}
@media (max-width:760px){
  .masthead .meta-row div{padding-right:.6rem;}
  .nav-inner a{font-size:.62rem;}
  .pull-quote{padding-left:2rem;}
  .footer-inner{grid-template-columns:1fr;}
}
@media print{
  .progress,.sticky-nav{display:none;}
  .masthead{border-top:4px solid #333;}
  .pull-quote{background:#fafafa !important;border-left-color:#666;color:#000 !important;}
  .pull-quote::before{color:#666;}
}
</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"><div class="progress__bar" id="progressBar"></div></div>

<header class="masthead">
  <span class="overline">H Heuristics · Digital Report · 2026-10</span>
  <h1>The Polycrisis Apocalypse Humanity Is Facing</h1>
  <p class="subtitle">Survivability risk regions, demographic tectonics, and the long road to human extinction</p>
  <p class="strapline">A scenario analysis: a majority of humanity moves into survivability risk regions, stabilises at unsafe levels, and then decays over centuries unless the compounding loops are broken now.</p>
  <div class="meta-row">
    <div><strong>Author</strong>Hunter Hughes</div>
    <div><strong>Institution</strong>H Heuristics</div>
    <div><strong>Published</strong>October 2026</div>
    <div><strong>Format</strong>38 pages · 12,000+ words</div>
    <div><strong>Files</strong>PDF · Word (.docx)</div>
  </div>
</header>

<nav class="sticky-nav" aria-label="Report sections">
  <div class="nav-inner">
__TOC__
  </div>
</nav>

<main id="main">
__SECTIONS__
</main>

<footer class="report-footer">
  <div class="footer-inner">
    <div>
      <h3>The Polycrisis Apocalypse Humanity Is Facing</h3>
      <p>H Heuristics · Hunter Hughes · October 2026. Built with Veles (Fable-5).</p>
      <p><a href="The_Polycrisis_Apocalypse_Humanity_Is_Facing.pdf" download>Download PDF</a> · <a href="The_Polycrisis_Apocalypse_Humanity_Is_Facing.docx" download>Download Word (.docx)</a> · <a href="https://github.com/Hunterhghs/The-Polycrisis-Apocalypse-Humanity-is-Facing" rel="noopener" target="_blank">GitHub</a> · <a href="https://hheuristics.com" rel="noopener" target="_blank">hheuristics.com</a></p>
    </div>
    <div class="cite-box">
      <p>Cite this report</p>
      <code>Hughes, H. (2026). The Polycrisis Apocalypse Humanity Is Facing. H Heuristics Digital Report 2026-10. digitalreports.hheuristics.com</code>
    </div>
  </div>
</footer>

<script>
(function(){
  // reading progress
  var bar=document.getElementById("progressBar");
  function onScroll(){
    var h=document.documentElement;
    var max=h.scrollHeight-h.clientHeight;
    bar.style.width=(max>0?(h.scrollTop/max*100):0)+"%";
    // scrollspy
    var links=document.querySelectorAll(".nav-inner a");
    var current="";
    document.querySelectorAll("main section[id]").forEach(function(s){
      if(s.getBoundingClientRect().top<=110) current=s.id;
    });
    links.forEach(function(a){
      a.classList.toggle("is-active", a.getAttribute("href")==="#"+current);
    });
  }
  document.addEventListener("scroll",onScroll,{passive:true}); onScroll();

  var NAVY="#0F4D92",BLUE="#3775BA",ORANGE="#E67E22",GREY="#66717F",RED="#C0392B",GREEN="#27AE60";
  if(typeof Chart==="undefined") return;
  Chart.defaults.font.family="Public Sans, -apple-system, system-ui, sans-serif";
  Chart.defaults.color=GREY;

  var c3=document.getElementById("chart3");
  if(c3){var t=[],a=[],b=[],c=[];
    for(var y=2025;y<=2300;y+=5){t.push(y);
      a.push(Math.max(28,Math.min(55,52*(1-0.45*(1-Math.exp(-(y-2025)/90)))-8*(y-2025)/275)));
      b.push(40+18*(1-Math.exp(-(y-2025)/55)));
      c.push(Math.max(40,Math.min(88,40+34*(1-Math.exp(-(y-2025)/60))+0.05*(y-2025))));
    }
    new Chart(c3,{type:"line",data:{labels:t,datasets:[
      {label:"Managed adaptation",data:a,borderColor:GREEN,backgroundColor:"rgba(39,174,96,.08)",fill:true,tension:.3,borderWidth:2.4,pointRadius:0},
      {label:"Trapped majority (unsafe plateau)",data:b,borderColor:BLUE,backgroundColor:"rgba(55,117,186,.08)",fill:true,tension:.3,borderWidth:2.4,pointRadius:0},
      {label:"Worsening (pessimistic)",data:c,borderColor:RED,backgroundColor:"rgba(192,57,43,.08)",fill:true,tension:.3,borderWidth:2.4,pointRadius:0}
    ]},options:{responsive:true,maintainAspectRatio:true,scales:{y:{min:0,max:100,title:{display:true,text:"Share of humanity in survivability risk regions (%)"}},x:{title:{display:true,text:"Year"}}},plugins:{legend:{position:"top",labels:{boxWidth:14,font:{size:11}}}}}});
  }

  var c4=document.getElementById("chart4");
  if(c4){var y4=[1950,1970,1990,2010,2024,2050,2075,2100];
    new Chart(c4,{type:"line",data:{labels:y4,datasets:[
      {label:"Africa",data:[0.23,0.37,0.64,1.06,1.51,2.5,3.2,3.81],borderColor:ORANGE,backgroundColor:"rgba(230,126,34,.12)",fill:true,tension:.25,borderWidth:3,pointRadius:3},
      {label:"Europe",data:[0.55,0.66,0.72,0.74,0.745,0.70,0.65,0.59],borderColor:BLUE,borderWidth:3,pointRadius:3,tension:.25},
      {label:"North America",data:[0.17,0.23,0.28,0.34,0.38,0.42,0.43,0.44],borderColor:GREY,borderWidth:3,pointRadius:3,tension:.25}
    ]},options:{responsive:true,maintainAspectRatio:true,scales:{y:{min:0,title:{display:true,text:"Population (billions)"}},x:{title:{display:true,text:"Year"}}},plugins:{legend:{position:"top",labels:{boxWidth:14,font:{size:11}}}}}});
  }

  var c5=document.getElementById("chart5");
  if(c5){new Chart(c5,{type:"bar",data:{labels:["Africa","Asia","Europe","Latin America & Caribbean","North America","Oceania"],datasets:[
      {label:"2024",data:[18.4,59.2,9.1,8.3,4.7,0.56],backgroundColor:BLUE,borderRadius:3},
      {label:"2100",data:[37.4,45.0,5.8,6.4,4.3,0.7],backgroundColor:ORANGE,borderRadius:3}
    ]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:true,scales:{x:{min:0,title:{display:true,text:"Share of world population (%)"}}},plugins:{legend:{position:"top",labels:{boxWidth:14,font:{size:11}}}}}});
  }

  var c7=document.getElementById("chart7");
  if(c7){new Chart(c7,{data:{labels:[2018,2019,2020,2021,2022,2023,2024,2025],datasets:[
      {type:"bar",label:"Reported killings (BINUH/OHCHR)",data:[1000,900,1200,1600,2200,4800,5600,5915],backgroundColor:"rgba(192,57,43,.8)",yAxisID:"y",borderRadius:2},
      {type:"line",label:"Gang control of Port-au-Prince (%)",data:[20,25,30,50,60,80,85,90],borderColor:ORANGE,backgroundColor:ORANGE,yAxisID:"y1",tension:.3,borderWidth:2.6,pointRadius:3}
    ]},options:{responsive:true,maintainAspectRatio:true,scales:{y:{beginAtZero:true,title:{display:true,text:"Reported killings"}},y1:{position:"right",min:0,max:100,title:{display:true,text:"Gang control (%)"},grid:{drawOnChartArea:false}},x:{title:{display:true,text:"Year"}}},plugins:{legend:{position:"top",labels:{boxWidth:14,font:{size:11}}}}}});
  }
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
