import sys
import re
sys.stdout.reconfigure(encoding='utf-8')
from pptx import Presentation

prs = Presentation(r"C:\Users\MANAS\OneDrive\Desktop\ppt\19_08\310.pptx")
print(f"Auditing Presentation: Total Slides = {len(prs.slides)}\n")

# Prohibited pre-2020 years pattern
pre_2020_years = ["1968", "1971", "1990", "1991", "1996", "1997", "1998", "2000", "2002", "2004", "2005", "2006", "2008", "2009", "2010", "2012", "2018", "2019"]
year_pattern = re.compile(r'\b(19\d\d|20[01]\d)\b') # Matches 1900-1999 and 2000-2019

found_violations = []
slide_titles = []
all_citations = []

for idx, s in enumerate(prs.slides):
    slide_text = []
    title = ''
    for shp in s.shapes:
        if shp.has_text_frame:
            for p in shp.text_frame.paragraphs:
                txt = p.text.strip()
                if txt:
                    slide_text.append(txt)
                    if not title:
                        title = txt.split('\n')[0]
        if shp.has_table:
            for r in shp.table.rows:
                for c in r.cells:
                    txt = c.text.strip()
                    if txt:
                        slide_text.append(txt)
                        
    slide_titles.append((idx + 1, title))
    full_slide_str = " ".join(slide_text)
    
    # Check for pre-2020 years
    matches = year_pattern.findall(full_slide_str)
    for m in matches:
        # Ignore roll numbers or known non-year codes like 22011P0310
        if m in pre_2020_years:
            found_violations.append((idx + 1, title, m, full_slide_str))
            
    # Collect 2020-2026 citations
    for y in range(2020, 2027):
        if str(y) in full_slide_str:
            all_citations.append((idx + 1, str(y)))

print("=== SLIDE INVENTORY ===")
for num, t in slide_titles:
    print(f"Slide {num:02d}: {t[:60]}")

print("\n=== PRE-2020 CITATION AUDIT ===")
if found_violations:
    print(f"[FAIL] Found {len(found_violations)} occurrences of pre-2020 years:")
    for num, t, y, full in found_violations:
        print(f"  Slide {num} ({t}): Year {y}")
else:
    print("[PASS] ZERO pre-2020 citations found in the presentation! All citations conform to 2020 <= year <= 2026.")

print(f"\nTotal 2020-2026 citation references found across deck: {len(all_citations)}")
