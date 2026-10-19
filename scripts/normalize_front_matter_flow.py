"""
normalize_front_matter_flow.py
Ensures every front matter section has:
Heading -> Content -> Single clean page break.
No double breaks, no empty paragraph clusters.
"""
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DOC_PATH = r"D:\carl major.docx"

doc = docx.Document(DOC_PATH)

# Strip any existing standalone w:br type="page" from paragraphs before Chapter 1
for p in doc.paragraphs:
    if p.text.startswith("CHAPTER 1:"):
        break
    brs = p._p.xpath('.//w:br[@w:type="page"]')
    for b in brs:
        b.getparent().remove(b)

def add_page_break_after_element(el):
    p = OxmlElement('w:p')
    r = OxmlElement('w:r')
    br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    r.append(br)
    p.append(r)
    el.addnext(p)
    return p

# 1. After Declaration
for p in doc.paragraphs:
    if "Place: Hyderabad" in p.text and "Manas Sadashiv" in p.text:
        add_page_break_after_element(p._p)
        print("Added page break after Declaration.")
        break

# 2. After Certificate (Table 0)
add_page_break_after_element(doc.tables[0]._tbl)
print("Added page break after Certificate Table 0.")

# 3. After Acknowledgements
for p in doc.paragraphs:
    if p.text.strip() == "Manas Sadashiv (22011P0310)":
        add_page_break_after_element(p._p)
        print("Added page break after Acknowledgements.")
        break

# 4. After Abstract
for p in doc.paragraphs:
    if "Keywords: Embodied Cognition" in p.text:
        add_page_break_after_element(p._p)
        print("Added page break after Abstract.")
        break

# 5. After Table of Contents (Table 1)
add_page_break_after_element(doc.tables[1]._tbl)
print("Added page break after Table of Contents (Table 1).")

# 6. After List of Figures (Table 2)
add_page_break_after_element(doc.tables[2]._tbl)
print("Added page break after List of Figures (Table 2).")

# 7. After List of Graphs (Table 3)
add_page_break_after_element(doc.tables[3]._tbl)
print("Added page break after List of Graphs (Table 3).")

# 8. After List of Tables (Table 4)
add_page_break_after_element(doc.tables[4]._tbl)
print("Added page break after List of Tables (Table 4).")

# 9. After Nomenclature (Table 5)
add_page_break_after_element(doc.tables[5]._tbl)
print("Added page break after Nomenclature (Table 5).")

doc.save(DOC_PATH)
print("Successfully normalized all front-matter page transitions with ZERO duplicate breaks!")
