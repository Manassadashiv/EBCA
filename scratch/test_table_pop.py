import sys
sys.stdout.reconfigure(encoding='utf-8')
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

FONT_SERIF = "Times New Roman"
BLACK = RGBColor(0x00, 0x00, 0x00)
DARK_GRAY = RGBColor(0x22, 0x22, 0x22)
VERY_LIGHT_GRAY = RGBColor(0xF6, 0xF7, 0xF9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

def populate_table(tbl, rows_data):
    """
    rows_data is a list of tuples: (author, title, methodology, key_finding, role_in_carl)
    """
    for r_idx, data in enumerate(rows_data):
        row_cells = tbl.rows[r_idx + 1].cells
        for c_idx, text in enumerate(data):
            cell = row_cells[c_idx]
            cell.fill.solid()
            cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.06)
            cell.margin_bottom = Inches(0.06)
            
            tf = cell.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.text = text
            p.font.name = FONT_SERIF
            p.font.size = Pt(10.5)
            p.font.color.rgb = BLACK
            if c_idx == 0:
                p.font.bold = True

print("populate_table defined successfully!")
