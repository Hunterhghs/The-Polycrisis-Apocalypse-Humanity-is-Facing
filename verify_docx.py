#!/usr/bin/env python3
"""Veles Phase-4 verification gate for the built .docx."""
import re
import sys
import zipfile
import html

DOCX = "Confronting_the_Global_Polycrisis.docx"

failures = []

with zipfile.ZipFile(DOCX) as z:
    bad = z.testzip()
    if bad:
        failures.append(f"zip integrity: bad member {bad}")

    media = [n for n in z.namelist() if n.startswith("word/media/") and not n.endswith("/")]
    print(f"images embedded: {len(media)}")
    if len(media) != 13:
        failures.append(f"expected 13 media files, found {len(media)}")

    doc = z.read("word/document.xml").decode("utf-8")
    styles = z.read("word/styles.xml").decode("utf-8")
    rels = z.read("word/_rels/document.xml.rels").decode("utf-8")

    # Headings present with outline levels
    h1 = len(re.findall(r'<w:outlineLvl w:val="0"', styles))
    h2 = len(re.findall(r'<w:outlineLvl w:val="1"', styles))
    h3 = len(re.findall(r'<w:outlineLvl w:val="2"', styles))
    h1p = len(re.findall(r'<w:pStyle w:val="Heading1"', doc))
    h2p = len(re.findall(r'<w:pStyle w:val="Heading2"', doc))
    h3p = len(re.findall(r'<w:pStyle w:val="Heading3"', doc))
    print(f"heading styles: H1={h1} H2={h2} H3={h3}; heading paragraphs: H1={h1p} H2={h2p} H3={h3p}")
    if h1 < 1 or h2 < 1:
        failures.append("heading outline levels missing")
    if h1p < 10 or h2p < 20:
        failures.append(f"too few heading paragraphs (H1={h1p}, H2={h2p})")

    # TOC field present
    if "TOC" not in doc:
        failures.append("TOC field missing")

    # Word count from document.xml
    text = html.unescape(re.sub(r"<[^>]+>", " ", doc))
    words = len(text.split())
    print(f"document.xml word count: {words}")

    # CJK check
    cjk = re.findall(r"[\u4e00-\u9fff]", doc)
    print(f"CJK characters: {len(cjk)}")
    if cjk:
        failures.append(f"CJK characters found: {cjk[:5]}")

    # Hyperlink targets: no literal parens, no truncation
    targets = re.findall(r'Target="(http[^"]+)"', rels)
    bad_targets = [t for t in targets if "(" in t or t.endswith("\\") or len(t) < 10]
    print(f"hyperlink targets: {len(targets)}, suspicious: {len(bad_targets)}")
    if bad_targets:
        failures.append(f"suspicious targets: {bad_targets[:5]}")

    # docPr id duplicates
    ids = re.findall(r'<wp:docPr[^>]*\bid="(\d+)"', doc)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    print(f"docPr ids: {len(ids)}, duplicates: {len(dupes)}")
    if dupes:
        failures.append(f"duplicate docPr ids: {dupes[:5]}")

    # Image EMU sizes sanity: width/height within page bounds (12240 x 15840 EMU)
    extents = re.findall(r'<wp:extent cx="(\d+)" cy="(\d+)"', doc)
    oversized = [e for e in extents if int(e[0]) > 9000000 or int(e[1]) > 11000000]
    print(f"image extents: {len(extents)}, oversized: {len(oversized)}")
    if oversized:
        failures.append(f"oversized images: {oversized[:3]}")

print()
if failures:
    print("FAIL")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("PASS — all Veles docx gate checks green")
