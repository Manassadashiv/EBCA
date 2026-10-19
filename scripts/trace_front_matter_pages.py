"""
trace_front_matter_pages.py
Traces every page break and heading in Section 1.
"""
import docx
from docx.oxml.ns import qn

doc = docx.Document(r"D:\carl major.docx")
print("=== SECTION 1 BREAKDOWN ===")

for i in range(23, 71):
    p = doc.paragraphs[i]
    brs = p._p.xpath('.//w:br[@w:type="page"]')
    text = p.text.strip().replace('\n', ' ')
    if p.style.name.startswith('Heading') or brs or len(text) > 0:
        print(f"P[{i}] (Style: {p.style.name}): {text[:60]} | PageBreaks: {len(brs)}")
