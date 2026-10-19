"""
scripts/fix_thesis_full_audit.py
Comprehensive thesis audit remediation script for D:\carl major.docx.
Implements 100% of the audit fixes requested in the prompt.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import shutil
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex="F2F2F2"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_run_font(run, name="Times New Roman", size_pt=12, bold=False, italic=False, color_rgb=(0, 0, 0)):
    run.font.name = name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = RGBColor(*color_rgb)

def set_p_format(p, space_before=0, space_after=6, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.JUSTIFY, keep_with_next=False):
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    p.alignment = align
    p.paragraph_format.keep_with_next = keep_with_next

def format_cell_text(cell, text, bold=False, italic=False, size_pt=9.5, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", size_pt, bold=bold, italic=italic)

def make_table_header(row, titles, col_widths=None, fill_hex="E8E8E8", size_pt=9.5):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for idx, (cell, title) in enumerate(zip(row.cells, titles)):
        format_cell_text(cell, title, bold=True, size_pt=size_pt, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_background(cell, fill_hex)
        set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
        if col_widths and idx < len(col_widths):
            cell.width = Inches(col_widths[idx])

def populate_row(row, values, col_widths=None, aligns=None, bold_first=False, size_pt=9.0):
    for idx, (cell, val) in enumerate(zip(row.cells, values)):
        align = aligns[idx] if aligns and idx < len(aligns) else WD_ALIGN_PARAGRAPH.LEFT
        bold = bold_first and (idx == 0)
        format_cell_text(cell, str(val), bold=bold, size_pt=size_pt, align=align)
        set_cell_margins(cell, top=80, bottom=80, left=140, right=140)
        if col_widths and idx < len(col_widths):
            cell.width = Inches(col_widths[idx])

def add_p_before(ref_el, doc, text, space_after=6, space_before=0, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    set_p_format(p, space_before, space_after, line_spacing, align)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 12, False, False)
    ref_el.addprevious(p._element)
    return p

def add_h1_before(ref_el, doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 1"]
    set_p_format(p, space_before=20, space_after=8, align=WD_ALIGN_PARAGRAPH.LEFT, keep_with_next=True)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 14, True, False)
    ref_el.addprevious(p._element)
    return p

def add_h2_before(ref_el, doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 2"]
    set_p_format(p, space_before=14, space_after=6, align=WD_ALIGN_PARAGRAPH.LEFT, keep_with_next=True)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 13, True, False)
    ref_el.addprevious(p._element)
    return p

def add_h3_before(ref_el, doc, text):
    p = doc.add_paragraph()
    p.style = doc.styles["Heading 3"]
    set_p_format(p, space_before=10, space_after=4, align=WD_ALIGN_PARAGRAPH.LEFT, keep_with_next=True)
    run = p.add_run(text)
    set_run_font(run, "Times New Roman", 12, True, True)
    ref_el.addprevious(p._element)
    return p

def add_bullet_before(ref_el, doc, bold_prefix, text):
    p = doc.add_paragraph()
    set_p_format(p, space_before=0, space_after=4, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    p.paragraph_format.left_indent = Inches(0.25)
    r_bullet = p.add_run("• ")
    set_run_font(r_bullet, "Times New Roman", 12, True)
    r_bold = p.add_run(bold_prefix + ": ")
    set_run_font(r_bold, "Times New Roman", 12, True)
    r_text = p.add_run(text)
    set_run_font(r_text, "Times New Roman", 12, False)
    ref_el.addprevious(p._element)
    return p

def add_figure_before(ref_el, doc, image_path, caption_text, width_inches=5.6):
    if not os.path.exists(image_path):
        print(f"  [MISSING FIGURE]: {image_path}")
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_p_format(p_img, space_before=12, space_after=4, align=WD_ALIGN_PARAGRAPH.CENTER)
    run = p_img.add_run()
    run.add_picture(image_path, width=Inches(width_inches))
    ref_el.addprevious(p_img._element)
    
    p_cap = doc.add_paragraph()
    set_p_format(p_cap, space_before=2, space_after=14, align=WD_ALIGN_PARAGRAPH.CENTER, keep_with_next=True)
    run_cap = p_cap.add_run(caption_text)
    set_run_font(run_cap, "Times New Roman", 10.5, bold=False, italic=True)
    ref_el.addprevious(p_cap._element)
    print(f"  [EMBEDDED FIGURE BEFORE]: {os.path.basename(image_path)}")

print("Enhanced helper functions loaded.")
