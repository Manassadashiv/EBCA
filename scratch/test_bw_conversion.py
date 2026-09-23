import sys
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE

prs = Presentation(r'd:\ebca\310_backup_original.pptx')

# Mapping of colorful fills to elegant monochrome academic fills
# Dark or saturated colors in legend swatches
SWATCH_MAP = {
    '2E86C1': RGBColor(0xFF, 0xFF, 0xFF), # Raw sensory: White fill, black border
    'B7950B': RGBColor(0xEE, 0xEE, 0xEE), # Signal prep: Light gray
    'E67E22': RGBColor(0xD0, 0xD0, 0xD0), # Endocrine: Medium-light gray
    '8E44AD': RGBColor(0xA0, 0xA0, 0xA0), # Cognitive: Medium gray
    'E74C3C': RGBColor(0x50, 0x50, 0x50), # Reflex path: Dark gray
    '229954': RGBColor(0x80, 0x80, 0x80), # Motor output: Neutral gray
    'B0B7BE': RGBColor(0xF5, 0xF5, 0xF5), # Auxiliary: Off-white
}

# Flowchart box background fills
BOX_MAP = {
    'D6EAF8': RGBColor(0xFF, 0xFF, 0xFF), # Sensory box -> White
    'FCF3CF': RGBColor(0xF4, 0xF4, 0xF4), # Preproc box -> Very light gray
    'FDEBD0': RGBColor(0xEA, 0xEA, 0xEA), # Endocrine box -> Light gray
    'EBDEF0': RGBColor(0xDE, 0xDE, 0xDE), # Cognitive box -> Soft gray
    'FADBD8': RGBColor(0xD0, 0xD0, 0xD0), # Reflex box -> Medium-light gray
    'D5F5E3': RGBColor(0xE5, 0xE5, 0xE5), # Motor box -> Light gray
    'CFF5E5': RGBColor(0xE5, 0xE5, 0xE5), # Motor box -> Light gray
    'EAEDED': RGBColor(0xF8, 0xF9, 0xFA), # Inactive/aux -> Clean off-white
    'EDF0F2': RGBColor(0xF0, 0xF2, 0xF4), # Inactive/aux -> Light gray
    'F7F9FA': RGBColor(0xFA, 0xFA, 0xFA), # Legend background container
}

# Convert slides 4, 5, 6, 7
for s_idx in [3, 4, 5, 6]:
    slide = prs.slides[s_idx]
    for shp in slide.shapes:
        # Check text
        if shp.has_text_frame:
            for p in shp.text_frame.paragraphs:
                # Update subtitle if red
                for r in p.runs:
                    if r.font.color and r.font.color.type is not None:
                        try:
                            # If reddish subtitle text, make it black/dark gray
                            if str(r.font.color.rgb) in ['B7472A', '2E86C1']:
                                r.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                        except Exception:
                            pass
            # Update title of legend
            if "COLOR LEGEND" in shp.text_frame.text:
                shp.text_frame.text = shp.text_frame.text.replace("COLOR LEGEND", "SUBSYSTEM ARCHITECTURE LEGEND")

        # Check fill
        if hasattr(shp, 'fill') and shp.fill.type is not None:
            try:
                rgb_str = str(shp.fill.fore_color.rgb)
                if rgb_str in SWATCH_MAP:
                    shp.fill.solid()
                    shp.fill.fore_color.rgb = SWATCH_MAP[rgb_str]
                elif rgb_str in BOX_MAP:
                    shp.fill.solid()
                    shp.fill.fore_color.rgb = BOX_MAP[rgb_str]
            except Exception:
                pass

        # Check line / border
        if hasattr(shp, 'line') and shp.line is not None:
            try:
                line_rgb = str(shp.line.color.rgb)
                # If colored line, convert to black or dark charcoal
                if line_rgb in ['2E86C1', 'B7950B', 'E67E22', '8E44AD', 'E74C3C', '229954']:
                    shp.line.color.rgb = RGBColor(0x22, 0x22, 0x22)
            except Exception:
                pass

# Convert Slide 19 (Roadmap)
s19 = prs.slides[18]
ROADMAP_MAP = {
    'E8F5E9': RGBColor(0xEE, 0xEE, 0xEE), # P0 Complete -> Light gray
    'FFF3E0': RGBColor(0xE0, 0xE0, 0xE0), # P1 Next -> Medium-light gray
    'E3F2FD': RGBColor(0xFF, 0xFF, 0xFF), # P2-P8 Roadmap -> White
    'AEB6C2': RGBColor(0xCC, 0xCC, 0xCC), # Badges -> Neutral gray
}
for shp in s19.shapes:
    if hasattr(shp, 'fill') and shp.fill.type is not None:
        try:
            rgb_str = str(shp.fill.fore_color.rgb)
            if rgb_str in ROADMAP_MAP:
                shp.fill.solid()
                shp.fill.fore_color.rgb = ROADMAP_MAP[rgb_str]
        except Exception:
            pass
    if hasattr(shp, 'line') and shp.line is not None:
        try:
            shp.line.color.rgb = RGBColor(0x33, 0x33, 0x33)
        except Exception:
            pass

prs.save(r'd:\ebca\test_bw_output.pptx')
print("Saved d:\\ebca\\test_bw_output.pptx successfully!")
