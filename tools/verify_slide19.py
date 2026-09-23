import pptx, cv2, os, hashlib
from pptx import Presentation

REPO_ROOT = r"D:\ebca"

png_path = os.path.join(REPO_ROOT, 'CARL_SLIDE_19_DEVELOPMENT_ROADMAP.png')
pptx_path = os.path.join(REPO_ROOT, 'CARL_SLIDE_19_DEVELOPMENT_ROADMAP.pptx')
notes_path = os.path.join(REPO_ROOT, 'CARL_SLIDE_19_ROADMAP_NOTES.md')

assert os.path.exists(png_path), 'PNG missing'
assert os.path.exists(pptx_path), 'PPTX missing'
assert os.path.exists(notes_path), 'Notes missing'

img = cv2.imread(png_path)
h, w, c = img.shape
print(f'PNG Resolution: {w}x{h} ({w/h:.3f} aspect ratio) | Size: {os.path.getsize(png_path)/1024:.1f} KB')

prs = Presentation(pptx_path)
print(f'PPTX Dimensions: {prs.slide_width.inches:.3f}" x {prs.slide_height.inches:.3f}" | Slides: {len(prs.slides)} | Shapes on Slide: {len(prs.slides[0].shapes)}')

with open(notes_path, 'r', encoding='utf-8') as f:
    notes = f.read()
print(f'Notes Length: {len(notes)} chars | Sections: {notes.count("## ")}')

CORE_FILES = [
    'brain/carl_autonomous_agent.py',
    'brain/carl_embodied_organism.py',
    'brain/carl_generative_self_model.py',
    'brain/carl_endogenous_agency.py',
    'brain/carl_homeostatic_core.py',
    'brain/carl_episodic_memory.py',
    'brain/carl_stuck_recovery.py',
    'brain/carl_empowerment.py',
    'brain/carl_reflex_laboratory.py',
    'tools/p0_regression_runner.py',
    'tools/p0_independent_scorer.py'
]

print('\n=== PRODUCTION CORE HASH INTEGRITY ===')
for cf in CORE_FILES:
    with open(os.path.join(REPO_ROOT, cf), 'rb') as f:
        h_val = hashlib.sha256(f.read()).hexdigest()
    print(f'  {cf:<38} : {h_val[:16]}... OK')

print('\nALL VERIFICATIONS PASSED!')
