"""
build_final_dissertation.py
Definitive script to build D:\\carl major.docx strictly benchmarked against:
C:\\Users\\MANAS\\Downloads\\project_report_2.pdf

Key features:
1. Exact JNTUH thesis formatting: Left 1.25", Right/Top/Bottom 1.0", Times New Roman, 1.3 line spacing, 6pt after.
2. Every chapter starts on a brand NEW page.
3. Chapter 3 Literature Review formatted author-by-author chronologically followed by Section 3.2 Gap Identification.
4. ZERO compound, group, or dashboard images. Graph 8.8 deleted. Image collages replaced with single standalone plots.
5. All P0 numbers and parameter reconciliations applied.
6. Target page count: ~72-76 pages (streamlined academic prose).
"""

import os
import sys
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOC_PATH = r"D:\carl major.docx"
BACKUP_PATH = r"D:\carl major_PRE_BENCHMARK_BACKUP.docx"
MEDIA_DIR = r"D:\ebca\scratch\docx_media"

print("Starting dissertation generation...")
