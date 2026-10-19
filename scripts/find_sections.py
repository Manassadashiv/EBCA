"""
find_sections.py
Finds where section breaks exist in D:\carl major.docx
"""
import docx

doc = docx.Document(r"D:\carl major.docx")
body = doc._body._body
elements = list(body)

sect_pr_list = body.xpath('.//w:sectPr')
print(f"Total w:sectPr elements: {len(sect_pr_list)}")

for i, p in enumerate(doc.paragraphs):
    pPr = p._p.xpath('./w:pPr/w:sectPr')
    if pPr:
        print(f"Section break after P[{i}]: \"{p.text[:60].strip()}\"")

# Also check last element
if body.xpath('./w:sectPr'):
    print("Final section break on document root.")
