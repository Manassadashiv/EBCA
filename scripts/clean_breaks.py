"""
clean_breaks.py
Inspects all w:br elements in doc.paragraphs[:100] and ensures clean page breaks.
"""
import docx
from docx.oxml.ns import qn

doc = docx.Document(r"D:\carl major.docx")
print("=== BREAKS IN FRONT MATTER ===")
for i, p in enumerate(doc.paragraphs[:100]):
    brs = p._p.xpath('.//w:br')
    if brs:
        types = [b.get(qn('w:type'), 'normal_break') for b in brs]
        print(f"P[{i}]: {len(brs)} breaks {types} | Text: {p.text[:50].strip()}")
