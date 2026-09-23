#!/usr/bin/env python3
import pptx
from pptx.enum.shapes import MSO_SHAPE_TYPE
import re
from pathlib import Path

path = Path(r"C:\Users\MANAS\OneDrive\Desktop\ppt\23_09\310.pptx")
if not path.exists():
    print(f"File not found: {path}")
    exit(1)

prs = pptx.Presentation(path)

print("=== COMPREHENSIVE AUDIT OF USER FINAL PPTX ===")
print(f"File: {path}")
print(f"Total Slides: {len(prs.slides)}")
print(f"Widescreen: {prs.slide_width.inches:.3f}\" x {prs.slide_height.inches:.3f}\"")

small_text = []
non_tnr = []
double_bullets = []
suspicious_numbers = []
tables_per_slide = {}
images_per_slide = {}

suspicious_patterns = [
    r"\b00\d+", r"\b022\b", r"\b09613\b", r"\b08466\b", r"\b05377\b", 
    r"\b0995\b", r"\b818%\b", r"\b00570\b", r"\b0065\b", r"\b0057\b",
    r"Stage 21\b", r"Stage 22\b"
]

for idx, slide in enumerate(prs.slides):
    s_num = idx + 1
    t_cnt = 0
    i_cnt = 0
    
    for sh in slide.shapes:
        if sh.has_table:
            t_cnt += 1
            for r_idx, row in enumerate(sh.table.rows):
                for c_idx, cell in enumerate(row.cells):
                    for p in cell.text_frame.paragraphs:
                        if "• •" in p.text or "•  •" in p.text:
                            double_bullets.append((s_num, p.text.strip()[:40]))
                        for pat in suspicious_patterns:
                            if re.search(pat, p.text):
                                suspicious_numbers.append((s_num, f"Table cell: {p.text.strip()}"))
                        for r in p.runs:
                            if r.font.name and r.font.name != "Times New Roman":
                                non_tnr.append((s_num, r.font.name, r.text.strip()[:30]))
                            if r.font.size and r.font.size.pt < 17.5:
                                small_text.append((s_num, r.font.size.pt, r.text.strip()[:30]))
        elif sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                if "• •" in p.text or "•  •" in p.text:
                    double_bullets.append((s_num, p.text.strip()[:40]))
                for pat in suspicious_patterns:
                    if re.search(pat, p.text):
                        suspicious_numbers.append((s_num, f"Text: {p.text.strip()}"))
                for r in p.runs:
                    if r.font.name and r.font.name != "Times New Roman":
                        non_tnr.append((s_num, r.font.name, r.text.strip()[:30]))
                    if r.font.size and r.font.size.pt < 17.5:
                        small_text.append((s_num, r.font.size.pt, r.text.strip()[:30]))
        elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            i_cnt += 1
            
    tables_per_slide[s_num] = t_cnt
    images_per_slide[s_num] = i_cnt

with open(r"d:\ebca\scratch\user_deck_audit_results.txt", "w", encoding="utf-8") as out:
    out.write(f"Non-Times New Roman runs: {len(non_tnr)}\n")
    out.write(f"Double bullet occurrences: {len(double_bullets)}\n")
    out.write(f"Suspicious number occurrences: {len(suspicious_numbers)}\n")
    for s_num, desc in suspicious_numbers:
        out.write(f"  Slide {s_num}: {desc}\n")

    out.write(f"\nSlides with > 1 table: {[s for s, c in tables_per_slide.items() if c > 1]}\n")
    out.write(f"Slides with > 2 images: {[s for s, c in images_per_slide.items() if c > 2]}\n")

    slides_with_small = sorted(list(set(s for s, pt, txt in small_text)))
    out.write(f"\nSlides with text < 18 pt: {len(slides_with_small)} slides -> {slides_with_small}\n")

print("Saved audit results to d:\\ebca\\scratch\\user_deck_audit_results.txt")

with open(r"d:\ebca\scratch\user_small_text_summary.txt", "w", encoding="utf-8") as f:
    f.write(f"Total small text runs: {len(small_text)}\n")
    for s_num, pt, txt in small_text:
        f.write(f"Slide {s_num:02d} ({pt} pt): {txt}\n")
print("Saved small text details to d:\\ebca\\scratch\\user_small_text_summary.txt")
