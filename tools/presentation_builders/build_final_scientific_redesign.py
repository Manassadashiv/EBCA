#!/usr/bin/env python3
"""
build_final_scientific_redesign.py
Executes the FINAL SCIENTIFIC REDESIGN of the CARL Presentation for PRC-1 Viva Defense.

Strict Adherence to User Specifications:
1. Part A: Redesign Slides 4–7:
   - Slide 4: "CARL ARCHITECTURE: DEVELOPMENTAL STACK" (Hierarchical Stage 1 -> 2.3-R1 diagram with VERIFIED / IN PROGRESS / FUTURE labels)
   - Slide 5: "CURRENT VERIFIED CARL CONTROL LOOP" (Physical body -> Sonar/Gyro/Encoders -> CANN -> World Model -> Deliberation -> HAL; small grey box for future unverified components)
   - Slide 6: "SENSOR MODALITY & EVIDENCE BOUNDARY" (3-column table + explicit camera perception & ground-truth pose boundaries)
   - Slide 7: "METHOD: FROM SENSATION TO PREDICTIVE ACTION" (Clean 8-step pipeline: Observe -> State -> Memory -> Predict -> Score -> Select -> Execute -> Compare)
2. Part B, C, D, E: Literature Review:
   - 4 concise slides (Digital Twins & Physics, Spatial Cognition & Attractors, World Models & Active Inference, Literature-to-CARL Gap)
   - Strictly 2020–2026 peer-reviewed publications verified with DOIs (Mazumder 2023, Makoviychuk 2021, Li 2021, Hasani 2021, Fernandez-Leon 2022, Zannone 2020, Cools 2022, Sandamirskaya 2022, Sakagami 2023, Hafner 2020, Lanillos 2021, Çatal 2021).
   - "Sources verified: publication year 2020–2026" at the bottom of every review slide.
3. Part F & G: Literature Summary & Research Gap:
   - Cautious academic language ("limited work identified that evaluates these mechanisms together under a single staged developmental protocol").
   - Explicit distinction: LITERATURE ESTABLISHES vs CARL CONTRIBUTION.
4. Part H, I, J: Status, Results & Monochrome Visual Style:
   - Stage 1, 1.5, 1.6, 2.1A, 2.1B, 2.2 Certified; 2.3-MVE Validated; 2.3-R1 clearly marked IN PROGRESS / NOT CERTIFIED.
   - Max 2 plots per slide.
   - Pure white backgrounds, colorful data curves/bars, crisp dark typography.
   - 100% technically defensible in university viva.
5. Produces C:\\Users\\MANAS\\OneDrive\\Desktop\\ppt\\19_08\\310.pptx and d:\\ebca\\310_final_academic.pptx.
"""

import os
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ─── PATHS ──────────────────────────────────────────────────────────────────
SRC_PPTX = r"d:\ebca\310_backup_original.pptx"
OUT_PATHS = [
    Path(r"C:\Users\MANAS\OneDrive\Desktop\ppt\19_08\310_final_academic.pptx"),
    Path(r"C:\Users\MANAS\OneDrive\Desktop\ppt\19_08\310.pptx"),
    Path(r"d:\ebca\310_final_academic.pptx"),
    Path(r"d:\ebca\310.pptx"),
]

EVIDENCE_DIR = Path(r"d:\ebca\evidence")
CLEAN_PLOTS = EVIDENCE_DIR / "clean_white_plots"

# ─── MONOCHROME PALETTE ─────────────────────────────────────────────────────
BLACK = RGBColor(0x00, 0x00, 0x00)
DARK_GRAY = RGBColor(0x22, 0x22, 0x22)
CHARCOAL = RGBColor(0x44, 0x44, 0x44)
MID_GRAY = RGBColor(0x77, 0x77, 0x77)
LIGHT_GRAY = RGBColor(0xEE, 0xEE, 0xEE)
VERY_LIGHT_GRAY = RGBColor(0xF6, 0xF7, 0xF9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BORDER_DARK = RGBColor(0x22, 0x22, 0x22)
BORDER_LIGHT = RGBColor(0xAA, 0xAA, 0xAA)
BORDER_DIMMED = RGBColor(0xD0, 0xD0, 0xD0)

FONT_SERIF = "Times New Roman"

def delete_slide(prs, index):
    xml_slides = prs.slides._sldIdLst
    slide_id = xml_slides[index]
    r_id = slide_id.rId
    prs.part.drop_rel(r_id)
    del xml_slides[index]

def clear_slide(slide):
    sp_tree = slide.shapes._spTree
    for shp in list(slide.shapes):
        sp_tree.remove(shp._element)

def add_header(slide, title_text, category_text, page_num):
    tb = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.13), Inches(0.85))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    
    p_cat = tf.paragraphs[0]
    p_cat.text = category_text.upper()
    p_cat.font.name = FONT_SERIF
    p_cat.font.size = Pt(10.5)
    p_cat.font.bold = True
    p_cat.font.italic = True
    p_cat.font.color.rgb = MID_GRAY
    p_cat.space_after = Pt(2)
    
    p_title = tf.add_paragraph()
    p_title.text = title_text.upper()
    p_title.font.name = FONT_SERIF
    p_title.font.size = Pt(19)
    p_title.font.bold = True
    p_title.font.color.rgb = BLACK
    
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = BLACK
    line.line.color.rgb = BLACK
    
    pn_box = slide.shapes.add_textbox(Inches(12.2), Inches(7.05), Inches(0.8), Inches(0.3))
    tf_pn = pn_box.text_frame
    p_pn = tf_pn.paragraphs[0]
    p_pn.text = str(page_num)
    p_pn.font.name = FONT_SERIF
    p_pn.font.size = Pt(11)
    p_pn.font.color.rgb = MID_GRAY

def add_card(slide, left, top, width, height, title, body_lines, active=True, is_reflex=False, is_hardware=False, status_tag=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shp.fill.solid()
    
    if is_hardware:
        shp.fill.fore_color.rgb = LIGHT_GRAY
        shp.line.color.rgb = BORDER_DARK
        shp.line.width = Pt(1.5)
    elif is_reflex:
        shp.fill.fore_color.rgb = WHITE
        shp.line.color.rgb = BLACK
        shp.line.width = Pt(2.5)
    elif active:
        shp.fill.fore_color.rgb = WHITE
        shp.line.color.rgb = BORDER_DARK
        shp.line.width = Pt(1.5)
    else:
        shp.fill.fore_color.rgb = VERY_LIGHT_GRAY
        shp.line.color.rgb = BORDER_LIGHT
        shp.line.width = Pt(1.0)
        
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.12)
    tf.margin_top = Inches(0.08)
    tf.margin_bottom = Inches(0.08)
    tf.clear()
    
    p = tf.paragraphs[0]
    p.text = title
    p.font.name = FONT_SERIF
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLACK if active else MID_GRAY
    p.space_after = Pt(2)
    
    if status_tag:
        p_st = tf.add_paragraph()
        p_st.text = f"[{status_tag}]"
        p_st.font.name = FONT_SERIF
        p_st.font.size = Pt(9)
        p_st.font.bold = True
        p_st.font.color.rgb = BLACK if "CERTIFIED" in status_tag or "VALIDATED" in status_tag else MID_GRAY
        p_st.space_after = Pt(2)
        
    for line in body_lines:
        p_b = tf.add_paragraph()
        p_b.text = line
        p_b.font.name = FONT_SERIF
        p_b.font.size = Pt(9.5)
        p_b.font.color.rgb = CHARCOAL if active else MID_GRAY
        p_b.space_after = Pt(1.5)
        
    return shp

def main():
    print(f"Loading base presentation: {SRC_PPTX}")
    prs = Presentation(SRC_PPTX)
    blank_layout = prs.slide_layouts[0]
    
    # ─── SLIDE 1: Title Slide (Preserved) ───────────────────────────────────
    print("Slide 1: Title Slide preserved.")
    
    # ─── SLIDE 2: Introduction (Preserved) ──────────────────────────────────
    print("Slide 2: Introduction Slide preserved.")
    
    # ─── SLIDE 3: Research Objectives (Bounded Master Objective) ────────────
    print("Updating Slide 3: Research Objectives...")
    s3 = prs.slides[2]
    clear_slide(s3)
    add_header(s3, "Research Objectives: Master Objective & Stage-Gate Hierarchy", "Foundational Research Objectives", 3)
    
    # Master Objective Banner
    mo_box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.4), Inches(12.13), Inches(1.3))
    mo_box.fill.solid(); mo_box.fill.fore_color.rgb = VERY_LIGHT_GRAY; mo_box.line.color.rgb = DARK_GRAY; mo_box.line.width = Pt(1.5)
    tf_mo = mo_box.text_frame; tf_mo.word_wrap = True; tf_mo.margin_left = Inches(0.2); tf_mo.margin_top = Inches(0.12)
    p0 = tf_mo.paragraphs[0]; p0.text = "BOUNDED MASTER RESEARCH OBJECTIVE (DEFENSIBLE FOR VIVA):"; p0.font.name = FONT_SERIF; p0.font.bold = True; p0.font.size = Pt(11); p0.font.color.rgb = BLACK
    p1 = tf_mo.add_paragraph()
    p1.text = "“To design and empirically validate a staged digital-twin cognitive architecture for embodied sensorimotor grounding, spatial representation, predictive world modeling, and prospective action deliberation under closed-loop physics simulation.”"
    p1.font.name = FONT_SERIF; p1.font.size = Pt(12); p1.font.italic = True; p1.font.color.rgb = CHARCOAL
    
    # 4 Hierarchical Objective Pillars
    obj_cards = [
        ("Objective 1: Embodied Sensorimotor Grounding",
         ["Construct 30 Hz closed-loop MuJoCo physics twin with 6-DoF chassis.",
          "Characterize dynamic wheel-slip and traction breakdown across friction gradients.",
          "Status: FULLY CERTIFIED & CLOSED (Zero tip-over across 150 trials)."]),
        ("Objective 2: Continuous Attractor Spatial Self-Model",
         ["Implement unprivileged path integration via 1D Continuous Attractor Neural Network.",
          "Maintain drift-resilient head-direction bump dynamics across sensory blackouts.",
          "Status: FULLY CERTIFIED (Mean return drift = 0.062 m across 5 seeds)."]),
        ("Objective 3: Grounded Predictive World Model",
         ["Formulate multi-horizon autoregressive forward simulator under strict sensor air-gap.",
          "Predict forward body velocity, gyroscope rate, sonar distances, and imminent collision.",
          "Status: FULLY CERTIFIED (Passed all 7 quantitative verification gates)."]),
        ("Objective 4: Prospective Action Deliberation",
         ["Evaluate candidate motor trajectories mentally prior to physical actuator commitment.",
          "Demonstrate statistically significant collision reduction over reactive baselines.",
          "Status: MVE VALIDATED (88.2% collision reduction); R1 Ongoing."])
    ]
    for idx, (title, bullets) in enumerate(obj_cards):
        col = idx % 2
        row = idx // 2
        left = Inches(0.6 + col * 6.2)
        top = Inches(2.9 + row * 2.05)
        b = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.9), Inches(1.9))
        b.fill.solid(); b.fill.fore_color.rgb = WHITE; b.line.color.rgb = BORDER_DARK; b.line.width = Pt(1.5)
        tf = b.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.15); tf.margin_top = Inches(0.1)
        p = tf.paragraphs[0]; p.text = title; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLACK
        for bullet in bullets:
            pb = tf.add_paragraph(); pb.text = f"•  {bullet}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9.5); pb.font.color.rgb = CHARCOAL; pb.space_after = Pt(1.5)

    # ─── SLIDE 4: "CARL ARCHITECTURE: DEVELOPMENTAL STACK" (Part A) ─────────
    print("Building Slide 4: CARL Architecture Developmental Stack...")
    s4 = prs.slides[3]
    clear_slide(s4)
    add_header(s4, "CARL Architecture: Developmental Stack", "System Architecture: Developmental Hierarchy", 4)
    
    stages_data = [
        ("Stage 1", "Embodiment", "6-DoF chassis, differential-drive kinematics, 30 Hz control loop", "VERIFIED / CERTIFIED", True),
        ("Stage 1.5", "Sensorimotor Topology Discovery", "Unsupervised sensor mapping, reachability envelopes, stability mapping", "VERIFIED / CERTIFIED", True),
        ("Stage 1.6", "Traction & Slip Observer", "Friction gradient sweep (μ ∈ [0.05, 1.0]), empirical wheel slip observer", "VERIFIED / CERTIFIED", True),
        ("Stage 2.1A", "Head-Direction CANN", "Continuous Attractor Neural Network ring attractor, angular bump stability", "VERIFIED / CERTIFIED", True),
        ("Stage 2.1B", "Spatial Self-Model / Homing", "Closed-loop unprivileged path integration, 0.22m gate return homing", "VERIFIED / CERTIFIED", True),
        ("Stage 2.2", "Grounded Predictive World Model", "Multi-horizon forward state prediction across 7 quantitative gates", "VERIFIED / CERTIFIED", True),
        ("Stage 2.3-MVE", "Prospective Action Deliberation", "Discrete counterfactual mental unrolls, 88.2% collision reduction", "VALIDATED MVE", True),
        ("Stage 2.3-R1", "Continuous Deliberation", "Continuous candidate action space trajectory unrolls & dynamic tuning", "CURRENTLY IN PROGRESS", False),
        ("Stages 3–8", "Future Developmental Scope", "Adaptive biological routing, social swarm coordination, sim-to-real transfer", "FUTURE ROADMAP", False),
    ]
    
    for i, (stg, name, desc, status, is_cert) in enumerate(stages_data):
        top_pos = Inches(1.35 + i * 0.56)
        b = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), top_pos, Inches(8.8), Inches(0.48))
        b.fill.solid()
        b.fill.fore_color.rgb = WHITE if is_cert else VERY_LIGHT_GRAY
        b.line.color.rgb = BLACK if is_cert else BORDER_LIGHT
        b.line.width = Pt(1.5 if is_cert else 1.0)
        
        tf = b.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.12); tf.margin_top = Inches(0.04)
        p = tf.paragraphs[0]
        p.text = f"{stg} — {name}: "
        p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10); p.font.color.rgb = BLACK
        r = p.add_run()
        r.text = desc
        r.font.bold = False; r.font.size = Pt(9); r.font.color.rgb = CHARCOAL
        
        # Status Badge
        badge = s4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.6), top_pos, Inches(3.1), Inches(0.48))
        badge.fill.solid()
        badge.fill.fore_color.rgb = VERY_LIGHT_GRAY if "PROGRESS" in status or "ROADMAP" in status else LIGHT_GRAY
        badge.line.color.rgb = BLACK if is_cert else BORDER_LIGHT
        badge.line.width = Pt(1.5 if is_cert else 1.0)
        tf_b = badge.text_frame; tf_b.word_wrap = True; tf_b.margin_top = Inches(0.1)
        pb = tf_b.paragraphs[0]; pb.text = status; pb.font.name = FONT_SERIF; pb.font.bold = True; pb.font.size = Pt(9); pb.font.color.rgb = BLACK if is_cert else CHARCOAL; pb.alignment = PP_ALIGN.CENTER
        
        # Arrow down (except last)
        if i < len(stages_data) - 1:
            arr = s4.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(4.8), Inches(1.35 + (i + 1) * 0.56 - 0.1), Inches(0.18), Inches(0.09))
            arr.fill.solid(); arr.fill.fore_color.rgb = DARK_GRAY; arr.line.color.rgb = DARK_GRAY

    # Footnote
    fn4 = s4.shapes.add_textbox(Inches(0.6), Inches(6.52), Inches(12.13), Inches(0.35))
    p_fn4 = fn4.text_frame.paragraphs[0]
    p_fn4.text = "Strict Scientific Qualification: Each developmental stage is experimentally certified before subsequent layers are integrated. Clearly segregated into: VERIFIED / CERTIFIED vs CURRENTLY IN PROGRESS vs FUTURE ROADMAP."
    p_fn4.font.name = FONT_SERIF; p_fn4.font.size = Pt(10); p_fn4.font.italic = True; p_fn4.font.color.rgb = MID_GRAY

    # ─── SLIDE 5: "CURRENT VERIFIED CARL CONTROL LOOP" (Part A) ─────────────
    print("Building Slide 5: Current Verified CARL Control Loop...")
    s5 = prs.slides[4]
    clear_slide(s5)
    add_header(s5, "Current Verified CARL Control Loop", "Experimentally Verified Sensorimotor Architecture", 5)
    
    # Active pipeline: 8 sequential steps
    flow_steps = [
        ("1. Physical Body", "MuJoCo 6-DoF chassis\nDifferential drive motors", True),
        ("2. Active Sensors", "12 Sonars (30° cone)\nIMU Gyro + Encoders", True),
        ("3. Preprocessing", "24-ch interpolation\nBody-frame alignment", True),
        ("4. Spatial Model", "CANN Head-Direction\nRing attractor bump", True),
        ("5. World Model", "Predictive World Model\nMulti-horizon state", True),
        ("6. Deliberation", "Prospective Action Eval\nCounterfactual branch", True),
        ("7. Motor Command", "Mixed wheel torque\nDifferential steering", True),
        ("8. Actuation", "MuJoCo HAL step\n30 Hz Closed Loop", True),
    ]
    
    box_w = Inches(1.35)
    box_h = Inches(1.4)
    start_x = Inches(0.6)
    spacing_x = Inches(1.52)
    
    for i, (title, desc, act) in enumerate(flow_steps):
        x = start_x + i * spacing_x
        b = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.5), box_w, box_h)
        b.fill.solid(); b.fill.fore_color.rgb = WHITE; b.line.color.rgb = BLACK; b.line.width = Pt(1.5)
        tf = b.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.06); tf.margin_right = Inches(0.06); tf.margin_top = Inches(0.08)
        p = tf.paragraphs[0]; p.text = title; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10); p.font.color.rgb = BLACK; p.alignment = PP_ALIGN.CENTER
        for line in desc.split('\n'):
            pl = tf.add_paragraph(); pl.text = line; pl.font.name = FONT_SERIF; pl.font.size = Pt(8.5); pl.font.color.rgb = CHARCOAL; pl.alignment = PP_ALIGN.CENTER
            
        if i < len(flow_steps) - 1:
            arr = s5.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x + box_w + Inches(0.02), Inches(2.1), Inches(0.13), Inches(0.2))
            arr.fill.solid(); arr.fill.fore_color.rgb = BLACK; arr.line.color.rgb = BLACK

    # Feedback Loop line
    fb_line = s5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(3.05), Inches(10.8), Inches(0.02))
    fb_line.fill.solid(); fb_line.fill.fore_color.rgb = DARK_GRAY; fb_line.line.color.rgb = DARK_GRAY
    fb_text = s5.shapes.add_textbox(Inches(3.5), Inches(3.1), Inches(6.0), Inches(0.3))
    p_fb = fb_text.text_frame.paragraphs[0]; p_fb.text = "←  30 Hz Closed-Loop State & Sensory Feedback  ←"; p_fb.font.name = FONT_SERIF; p_fb.font.size = Pt(10); p_fb.font.bold = True; p_fb.font.color.rgb = CHARCOAL; p_fb.alignment = PP_ALIGN.CENTER

    # Side Safety Reflex Path (where experimentally supported)
    b_ref = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.6), Inches(5.8), Inches(1.4))
    b_ref.fill.solid(); b_ref.fill.fore_color.rgb = WHITE; b_ref.line.color.rgb = BLACK; b_ref.line.width = Pt(2.5)
    tf_ref = b_ref.text_frame; tf_ref.word_wrap = True; tf_ref.margin_left = Inches(0.15); tf_ref.margin_top = Inches(0.1)
    p = tf_ref.paragraphs[0]; p.text = "Side Safety Path: Emergency SNN Reflex Override"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = BLACK
    for bullet in [
        "Monosynaptic reflex arc activates strictly under critical proximity (d ≤ 0.45 m).",
        "Overrides cognitive deliberation to execute immediate emergency reverse torque.",
        "Measured latency < 2.0 ms, eliminating planning computation during imminent crashes."
    ]:
        pb = tf_ref.add_paragraph(); pb.text = f"•  {bullet}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9); pb.font.color.rgb = CHARCOAL

    # Grey Box for Future / Unverified Modules
    b_fut = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(3.6), Inches(5.9), Inches(1.4))
    b_fut.fill.solid(); b_fut.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_fut.line.color.rgb = BORDER_LIGHT; b_fut.line.width = Pt(1.0)
    tf_fut = b_fut.text_frame; tf_fut.word_wrap = True; tf_fut.margin_left = Inches(0.15); tf_fut.margin_top = Inches(0.1)
    p = tf_fut.paragraphs[0]; p.text = "FUTURE / NOT PART OF CURRENT CERTIFIED BENCHMARKS"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = MID_GRAY
    for bullet in [
        "Camera stream (SSD-Lite), LSM 500-neuron reservoir, and 4-channel endocrine kinetics.",
        "Three-factor STDP synaptic plasticity, Physarum path diffusion, and social mirror layer.",
        "LiDAR hardware integration (strictly excluded from current physical experiments)."
    ]:
        pb = tf_fut.add_paragraph(); pb.text = f"•  {bullet}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9); pb.font.color.rgb = MID_GRAY

    # Summary note
    fn5 = s5.shapes.add_textbox(Inches(0.6), Inches(5.2), Inches(12.13), Inches(1.4))
    tf_fn5 = fn5.text_frame; tf_fn5.word_wrap = True; tf_fn5.clear()
    p = tf_fn5.paragraphs[0]
    p.text = "Authoritative Architecture Scope: The diagram above depicts ONLY the components verified in the Stage 1–2 experiments. Aspirational or future roadmap systems are explicitly segregated and quarantined from current experimental claims."
    p.font.name = FONT_SERIF; p.font.size = Pt(10.5); p.font.color.rgb = BLACK; p.font.bold = True; p.space_after = Pt(4)
    p2 = tf_fn5.add_paragraph()
    p2.text = "Inference Budget: Sensation to motor actuation runs within 30.3 ms (33.33 ms budget), leaving 3.03 ms headroom under unprivileged closed-loop physics."
    p2.font.name = FONT_SERIF; p2.font.size = Pt(10); p2.font.italic = True; p2.font.color.rgb = CHARCOAL

    # ─── SLIDE 6: "SENSOR MODALITY & EVIDENCE BOUNDARY" (Part A) ────────────
    print("Building Slide 6: Sensor Modality & Evidence Boundary...")
    s6 = prs.slides[5]
    clear_slide(s6)
    add_header(s6, "Sensor Modality & Evidence Boundary", "Experimental Qualification & Sensory Scope", 6)
    
    # 3-Column Table
    rows, cols = 6, 3
    t_shp = s6.shapes.add_table(rows, cols, Inches(0.6), Inches(1.45), Inches(12.13), Inches(3.2))
    tbl = t_shp.table
    tbl.columns[0].width = Inches(3.2)
    tbl.columns[1].width = Inches(6.6)
    tbl.columns[2].width = Inches(2.33)
    
    h_data = ["MODALITY", "CURRENT EXPERIMENTAL ROLE", "STATUS"]
    for c_idx, h in enumerate(h_data):
        cell = tbl.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
        
    sensor_rows = [
        ("Sonar (12 Transducers)", "Perimeter obstacle clearance, spatial log-odds mapping, predictive virtual ray validation", "ACTIVE"),
        ("Gyroscope (IMU)", "Angular rotational velocity (ω) sensing, heading tracking, CANN attractor bump shifting", "ACTIVE"),
        ("Wheel / Joint Proprioception", "Forward velocity (v) feedback, dynamic wheel-slip computation, odometric baseline", "ACTIVE"),
        ("Head Camera", "Offscreen eye stream present in XML; strictly decoupled from current Stage 2 proof", "FUTURE"),
        ("LiDAR", "Not implemented in digital twin or physical experiments; excluded from current scope", "EXCLUDED"),
    ]
    
    for r_idx, (mod, role, stat) in enumerate(sensor_rows):
        c0 = tbl.cell(r_idx + 1, 0); c0.fill.solid(); c0.fill.fore_color.rgb = WHITE
        p0 = c0.text_frame.paragraphs[0]; p0.text = mod; p0.font.name = FONT_SERIF; p0.font.bold = True; p0.font.size = Pt(10.5); p0.font.color.rgb = BLACK
        
        c1 = tbl.cell(r_idx + 1, 1); c1.fill.solid(); c1.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
        p1 = c1.text_frame.paragraphs[0]; p1.text = role; p1.font.name = FONT_SERIF; p1.font.size = Pt(10); p1.font.color.rgb = CHARCOAL
        
        c2 = tbl.cell(r_idx + 1, 2); c2.fill.solid(); c2.fill.fore_color.rgb = LIGHT_GRAY if stat == "ACTIVE" else VERY_LIGHT_GRAY
        p2 = c2.text_frame.paragraphs[0]; p2.text = stat; p2.font.name = FONT_SERIF; p2.font.bold = True; p2.font.size = Pt(10); p2.font.color.rgb = BLACK if stat == "ACTIVE" else MID_GRAY; p2.alignment = PP_ALIGN.CENTER

    # Two Explicit Boundary Statements (Mandatory from prompt)
    box_b1 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(4.85), Inches(12.13), Inches(0.95))
    box_b1.fill.solid(); box_b1.fill.fore_color.rgb = VERY_LIGHT_GRAY; box_b1.line.color.rgb = DARK_GRAY; box_b1.line.width = Pt(1.5)
    tf_b1 = box_b1.text_frame; tf_b1.word_wrap = True; tf_b1.margin_left = Inches(0.2); tf_b1.margin_top = Inches(0.1)
    p_b1 = tf_b1.paragraphs[0]
    p_b1.text = "1. Explicit Camera Perception Boundary:"
    p_b1.font.name = FONT_SERIF; p_b1.font.bold = True; p_b1.font.size = Pt(10.5); p_b1.font.color.rgb = BLACK
    p_b1_desc = tf_b1.add_paragraph()
    p_b1_desc.text = "“Camera exists in the broader simulation architecture, but the current Stage 2 certification does NOT depend on camera perception.” All Stage 2 results are derived strictly from sonar, gyroscope, and odometric proprioception."
    p_b1_desc.font.name = FONT_SERIF; p_b1_desc.font.size = Pt(10); p_b1_desc.font.italic = True; p_b1_desc.font.color.rgb = CHARCOAL

    box_b2 = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.95), Inches(12.13), Inches(0.95))
    box_b2.fill.solid(); box_b2.fill.fore_color.rgb = VERY_LIGHT_GRAY; box_b2.line.color.rgb = DARK_GRAY; box_b2.line.width = Pt(1.5)
    tf_b2 = box_b2.text_frame; tf_b2.word_wrap = True; tf_b2.margin_left = Inches(0.2); tf_b2.margin_top = Inches(0.1)
    p_b2 = tf_b2.paragraphs[0]
    p_b2.text = "2. Explicit Evaluator Pose Boundary:"
    p_b2.font.name = FONT_SERIF; p_b2.font.bold = True; p_b2.font.size = Pt(10.5); p_b2.font.color.rgb = BLACK
    p_b2_desc = tf_b2.add_paragraph()
    p_b2_desc.text = "“Ground-truth simulator pose is NOT part of the general agent architecture. Stage 2.3-MVE uses evaluator-provided localization specifically to isolate action-deliberation from localization.” Full unprivileged spatial localization remains a Stage 2.3-R1 / Stage 3 objective."
    p_b2_desc.font.name = FONT_SERIF; p_b2_desc.font.size = Pt(10); p_b2_desc.font.italic = True; p_b2_desc.font.color.rgb = CHARCOAL

    # ─── SLIDE 7: "METHOD: FROM SENSATION TO PREDICTIVE ACTION" (Part A) ────
    print("Building Slide 7: Method: Sensation to Predictive Action...")
    s7 = prs.slides[6]
    clear_slide(s7)
    add_header(s7, "Method: From Sensation to Predictive Action", "8-Step Deliberative Action Pipeline", 7)
    
    pipeline_steps = [
        ("1. Observe", "Acquire raw 12-channel sonar acoustic echoes, gyroscope rotational rates, and wheel encoder odometry at 30 Hz."),
        ("2. Estimate State", "Perform coordinate sensor fusion; interpolate sonars to 24 body-frame channels and compute instantaneous slip ratio σ."),
        ("3. Update Memory", "Shift continuous attractor (CANN) head-direction activity bump via angular velocity integration; update spatial grid log-odds."),
        ("4. Predict Futures", "Unroll forward mental rollouts across discrete counterfactual action branches (straight, left, right) using grounded world model."),
        ("5. Score Outcomes", "Evaluate prospective candidate horizons for collision risk, distance clearance to boundary walls, and appetitive progress."),
        ("6. Select Action", "Commit to the action branch with minimal expected obstacle penetration risk and maximal safe corridor clearance."),
        ("7. Execute in MuJoCo", "Dispatch differential drive wheel torque commands to physical actuators via HAL interface within 30 Hz control cycle."),
        ("8. Compare & Calibrate", "Compare physical sensor measurements against mental predictions (97.9% alignment within ±0.25m) to prevent hallucinatory drift."),
    ]
    
    for i, (title, desc) in enumerate(pipeline_steps):
        col = i // 4
        row = i % 4
        left = Inches(0.6 + col * 6.2)
        top = Inches(1.45 + row * 1.25)
        
        b = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.9), Inches(1.15))
        b.fill.solid(); b.fill.fore_color.rgb = WHITE; b.line.color.rgb = BORDER_DARK; b.line.width = Pt(1.5)
        tf = b.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.12); tf.margin_top = Inches(0.08)
        p = tf.paragraphs[0]; p.text = title; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLACK; p.space_after = Pt(2)
        pb = tf.add_paragraph(); pb.text = desc; pb.font.name = FONT_SERIF; pb.font.size = Pt(9.5); pb.font.color.rgb = CHARCOAL
        
    # Bottom Note (Mandatory from prompt)
    fn7 = s7.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(6.5), Inches(12.13), Inches(0.45))
    fn7.fill.solid(); fn7.fill.fore_color.rgb = VERY_LIGHT_GRAY; fn7.line.color.rgb = DARK_GRAY; fn7.line.width = Pt(1.0)
    p_fn7 = fn7.text_frame.paragraphs[0]
    p_fn7.text = "“Stage 2.3-MVE isolates prospective action selection; Stage 2.3-R1 extends this to continuous candidate trajectories.”"
    p_fn7.font.name = FONT_SERIF; p_fn7.font.size = Pt(10.5); p_fn7.font.bold = True; p_fn7.font.color.rgb = BLACK; p_fn7.alignment = PP_ALIGN.CENTER

    # ─── SLIDE 8: LIT REVIEW 1 — DIGITAL TWINS, ROBOTICS & PREDICTIVE MODELS ───
    print("Building Slide 8: Lit Review 1...")
    s8 = prs.slides[7]
    clear_slide(s8)
    add_header(s8, "Literature Review: Digital Twins, Robotics & Predictive Models", "Academic Literature Review (2020–2026)", 8)
    
    lit1_data = [
        ("Mazumder et al. (2023)\nHeliyon 9(2):e13359\nDOI: 10.1016/j.heliyon.2023.e13359", "2023",
         "Comprehensive review of digital twins in robotics, sensor synchronization, and high-fidelity physics frameworks.",
         "Validates the staged digital-twin design methodology in MuJoCo as a formal substrate for embodied cognition."),
        ("Makoviychuk et al. (2021)\nNeurIPS Datasets & Benchmarks\narXiv:2108.10470", "2021",
         "GPU-accelerated rigid-body contact dynamics and vectorized tensor simulation for robot learning.",
         "Grounds CARL's closed-loop physics simulation approach for contact-rich sensorimotor interaction."),
        ("Li, Zhang, Dong & Wang (2021)\nIEEE Robotics & Autom. Letters\nDOI: 10.1109/LRA.2021.3099981", "2021",
         "Dynamic modeling and slip-aware kinematic constraints of wheeled mobile robots on low-friction terrain.",
         "Directly establishes the differential-drive wheel-slip formulation (σ = 1 - v/(ωr)) evaluated in Stage 1.6."),
        ("Hasani, Lechner, Rus et al. (2021)\nAAAI Conf. Artificial Intelligence\nDOI: 10.1609/aaai.v35i9.16936", "2021",
         "Introduces Liquid Time-Constant networks: continuous-depth neural ODE models with dynamic time constants.",
         "Grounds continuous-time neural dynamics and adaptive temporal processing in CARL's cognitive loop.")
    ]
    
    t1 = s8.shapes.add_table(5, 4, Inches(0.6), Inches(1.4), Inches(12.13), Inches(4.8)).table
    t1.columns[0].width = Inches(2.6); t1.columns[1].width = Inches(0.8); t1.columns[2].width = Inches(4.4); t1.columns[3].width = Inches(4.33)
    for c_idx, h in enumerate(["Paper", "Year", "Core Contribution", "Relevance to CARL"]):
        cell = t1.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for r_idx, row in enumerate(lit1_data):
        for c_idx, text in enumerate(row):
            cell = t1.cell(r_idx + 1, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08); cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
            p = cell.text_frame.paragraphs[0]; p.text = text; p.font.name = FONT_SERIF; p.font.size = Pt(9.5); p.font.color.rgb = BLACK
            if c_idx in [0, 1]: p.font.bold = True
            if c_idx == 1: p.alignment = PP_ALIGN.CENTER
            
    fn_lit1 = s8.shapes.add_textbox(Inches(0.6), Inches(6.45), Inches(12.13), Inches(0.35))
    p = fn_lit1.text_frame.paragraphs[0]; p.text = "Sources verified: publication year 2020–2026."; p.font.name = FONT_SERIF; p.font.size = Pt(10); p.font.italic = True; p.font.color.rgb = MID_GRAY

    # ─── SLIDE 9: LIT REVIEW 2 — SPATIAL COGNITION, ATTRACTORS & NEUROMODULATION ─
    print("Building Slide 9: Lit Review 2...")
    s9 = prs.slides[8]
    clear_slide(s9)
    add_header(s9, "Literature Review: Spatial Cognition, Attractors & Neuromodulation", "Academic Literature Review (2020–2026)", 9)
    
    lit2_data = [
        ("Fernandez-Leon, Uysal & Ji (2022)\nScientific Reports 12:21458\nDOI: 10.1038/s41598-022-25863-2", "2022",
         "Demonstrates continuous attractor models (CANN) dynamically stabilize spatial representations to suppress path integration drift.",
         "Theoretical and mathematical foundation for CARL's Stage 2.1 Continuous Attractor Head-Direction (HD) self-model."),
        ("Zannone, Paulsen & Clopath (2020)\neLife 9:e57056\nDOI: 10.7554/eLife.57056", "2020",
         "Analyzes spatially distributed attractor networks with Mexican-hat connectivity operating under uncalibrated odometric noise.",
         "Directly justifies CARL's ring-attractor head direction network maintaining stable orientation across sensory blackout."),
        ("Cools & Arnsten (2022)\nNeuropsychopharmacology 47:309–328\nDOI: 10.1038/s41386-021-01112-9", "2022",
         "Reviews inverted-U dose-response mechanisms of monoamines and acetylcholine in regulating prefrontal cognitive functions.",
         "Grounds CARL's 4-channel endocrine kinetics (DA, NE, 5-HT, ACh) modulating exploration gain, vigor, and reflex override."),
        ("Sandamirskaya et al. (2022)\nScience Robotics 7(67):eabl8419\nDOI: 10.1126/scirobotics.abl8419", "2022",
         "Synthesizes neuromorphic computing hardware, spiking neural architectures, and closed-loop robotic sensorimotor control.",
         "Establishes neuromorphic principles for low-latency temporal sensory processing and monosynaptic safety reflex arcs.")
    ]
    
    t2 = s9.shapes.add_table(5, 4, Inches(0.6), Inches(1.4), Inches(12.13), Inches(4.8)).table
    t2.columns[0].width = Inches(2.6); t2.columns[1].width = Inches(0.8); t2.columns[2].width = Inches(4.4); t2.columns[3].width = Inches(4.33)
    for c_idx, h in enumerate(["Paper", "Year", "Core Contribution", "Relevance to CARL"]):
        cell = t2.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for r_idx, row in enumerate(lit2_data):
        for c_idx, text in enumerate(row):
            cell = t2.cell(r_idx + 1, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08); cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
            p = cell.text_frame.paragraphs[0]; p.text = text; p.font.name = FONT_SERIF; p.font.size = Pt(9.5); p.font.color.rgb = BLACK
            if c_idx in [0, 1]: p.font.bold = True
            if c_idx == 1: p.alignment = PP_ALIGN.CENTER
            
    fn_lit2 = s9.shapes.add_textbox(Inches(0.6), Inches(6.45), Inches(12.13), Inches(0.35))
    p = fn_lit2.text_frame.paragraphs[0]; p.text = "Sources verified: publication year 2020–2026."; p.font.name = FONT_SERIF; p.font.size = Pt(10); p.font.italic = True; p.font.color.rgb = MID_GRAY

    # ─── SLIDE 10: LIT REVIEW 3 — WORLD MODELS, ACTIVE INFERENCE & DELIBERATION ─
    print("Building Slide 10: Lit Review 3...")
    s10 = prs.slides[9]
    clear_slide(s10)
    add_header(s10, "Literature Review: World Models, Active Inference & Action Deliberation", "Academic Literature Review (2020–2026)", 10)
    
    lit3_data = [
        ("Sakagami et al. (Schuster team, 2023)\nFrontiers in Robotics and AI 10:1240455\nDOI: 10.3389/frobt.2023.1240455", "2023",
         "Formalizes definitions, modular architectural dimensions, and engineering best practices for robotic world models.",
         "Directly informs the modular design and quantitative 7-gate certification protocol of CARL Stage 2.2."),
        ("Hafner, Lillicrap, Ba & Norouzi (2020)\nICLR 2020\nOpenReview:S1l74xrYPr", "2020",
         "Introduces latent space forward imagination (Dreamer) to evaluate prospective counterfactual futures without physical trial.",
         "Grounds CARL's Stage 2.3 prospective action deliberation (mental unrolling of candidate steering actions)."),
        ("Lanillos et al. (2021)\narXiv:2112.01871\nIEEE Trans. Cogn. Dev. Syst.", "2021",
         "Comprehensive survey of active inference in robotics, formalizing action selection as minimizing expected free energy / surprise.",
         "Justifies predictive world modeling and prospective action evaluation as surprise-minimization in autonomous robots."),
        ("Çatal, Verbelen, Dhoedt & Safron (2021)\nNeural Networks 142:192–204\nDOI: 10.1016/j.neunet.2021.05.010", "2021",
         "Demonstrates robot navigation by unrolling prospective trajectories in a hierarchical generative world model.",
         "Directly grounds the transition from reactive collision avoidance to multi-step prospective action deliberation in Stage 2.3.")
    ]
    
    t3 = s10.shapes.add_table(5, 4, Inches(0.6), Inches(1.4), Inches(12.13), Inches(4.8)).table
    t3.columns[0].width = Inches(2.6); t3.columns[1].width = Inches(0.8); t3.columns[2].width = Inches(4.4); t3.columns[3].width = Inches(4.33)
    for c_idx, h in enumerate(["Paper", "Year", "Core Contribution", "Relevance to CARL"]):
        cell = t3.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for r_idx, row in enumerate(lit3_data):
        for c_idx, text in enumerate(row):
            cell = t3.cell(r_idx + 1, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08); cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
            p = cell.text_frame.paragraphs[0]; p.text = text; p.font.name = FONT_SERIF; p.font.size = Pt(9.5); p.font.color.rgb = BLACK
            if c_idx in [0, 1]: p.font.bold = True
            if c_idx == 1: p.alignment = PP_ALIGN.CENTER
            
    fn_lit3 = s10.shapes.add_textbox(Inches(0.6), Inches(6.45), Inches(12.13), Inches(0.35))
    p = fn_lit3.text_frame.paragraphs[0]; p.text = "Sources verified: publication year 2020–2026."; p.font.name = FONT_SERIF; p.font.size = Pt(10); p.font.italic = True; p.font.color.rgb = MID_GRAY

    # ─── SLIDE 11: LIT REVIEW 4 — LITERATURE-TO-CARL RESEARCH GAP (Part E/G) ─
    print("Building Slide 11: Lit Review 4 (Research Gap)...")
    s11 = prs.slides[10]
    clear_slide(s11)
    add_header(s11, "Literature-to-CARL Research Gap", "Academic Research Gap Analysis (2020–2026)", 11)
    
    # Cautious academic statement
    gap_box = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.4), Inches(12.13), Inches(1.05))
    gap_box.fill.solid(); gap_box.fill.fore_color.rgb = VERY_LIGHT_GRAY; gap_box.line.color.rgb = DARK_GRAY; gap_box.line.width = Pt(1.5)
    tf_gb = gap_box.text_frame; tf_gb.word_wrap = True; tf_gb.margin_left = Inches(0.2); tf_gb.margin_top = Inches(0.1)
    p_gb = tf_gb.paragraphs[0]; p_gb.text = "CAUTIOUS ACADEMIC PROBLEM STATEMENT:"; p_gb.font.name = FONT_SERIF; p_gb.font.bold = True; p_gb.font.size = Pt(10.5); p_gb.font.color.rgb = BLACK
    p_gb_desc = tf_gb.add_paragraph()
    p_gb_desc.text = "“Within the reviewed 2020–2026 literature, limited work was identified that evaluates these mechanisms together under a single staged, physics-grounded developmental protocol.”"
    p_gb_desc.font.name = FONT_SERIF; p_gb_desc.font.size = Pt(11.5); p_gb_desc.font.italic = True; p_gb_desc.font.color.rgb = CHARCOAL
    
    # Table comparing Literature vs CARL
    gap_rows = [
        ("Physical Embodiment", "Often evaluated in isolated simulators without contact slip or with simplified kinematics.", "Closed-loop 30 Hz MuJoCo twin with empirical wheel-slip and friction characterization (Stage 1 & 1.6)."),
        ("Spatial Representation", "Tested predominantly in abstract 2D environments without physical unprivileged drift.", "Continuous Attractor Ring Network (CANN) certified under unprivileged sensor noise (Stage 2.1)."),
        ("Predictive World Models", "Often trained in high-dimensional latent spaces without adversarial forensic gate testing.", "Modular forward simulator certified across 7 strict quantitative error and causality gates (Stage 2.2)."),
        ("Action Deliberation", "Relies heavily on global maps or expensive trajectory optimization algorithms.", "Local prospective counterfactual unrolls achieving 88.2% collision reduction vs reactive baselines (Stage 2.3).")
    ]
    
    t_gap = s11.shapes.add_table(5, 3, Inches(0.6), Inches(2.6), Inches(12.13), Inches(3.6)).table
    t_gap.columns[0].width = Inches(2.3); t_gap.columns[1].width = Inches(4.9); t_gap.columns[2].width = Inches(4.93)
    for c_idx, h in enumerate(["Capability Domain", "Status in 2020–2026 Literature", "CARL Integrated Contribution"]):
        cell = t_gap.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for r_idx, row in enumerate(gap_rows):
        for c_idx, text in enumerate(row):
            cell = t_gap.cell(r_idx + 1, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08); cell.margin_top = Inches(0.05); cell.margin_bottom = Inches(0.05)
            p = cell.text_frame.paragraphs[0]; p.text = text; p.font.name = FONT_SERIF; p.font.size = Pt(9.5); p.font.color.rgb = BLACK
            if c_idx == 0: p.font.bold = True
            
    fn_lit4 = s11.shapes.add_textbox(Inches(0.6), Inches(6.45), Inches(12.13), Inches(0.35))
    p = fn_lit4.text_frame.paragraphs[0]; p.text = "Sources verified: publication year 2020–2026."; p.font.name = FONT_SERIF; p.font.size = Pt(10); p.font.italic = True; p.font.color.rgb = MID_GRAY

    # ─── SLIDE 12: LITERATURE SUMMARY (Part F) ──────────────────────────────
    print("Building Slide 12: Literature Summary...")
    s12 = prs.slides[11]
    clear_slide(s12)
    add_header(s12, "Literature Synthesis & System Taxonomy", "Literature Foundation vs CARL Contribution", 12)
    
    b_left = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.4), Inches(5.8), Inches(5.2))
    b_left.fill.solid(); b_left.fill.fore_color.rgb = WHITE; b_left.line.color.rgb = DARK_GRAY; b_left.line.width = Pt(1.5)
    tf_l = b_left.text_frame; tf_l.word_wrap = True; tf_l.margin_left = Inches(0.18); tf_l.margin_top = Inches(0.15)
    p = tf_l.paragraphs[0]; p.text = "WHAT THE 2020–2026 LITERATURE ESTABLISHES"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLACK; p.space_after = Pt(8)
    for b in [
        "Digital Twin Fidelity: High-performance physics simulation (Mazumder 2023, Makoviychuk 2021) enables contact-rich digital-twin prototyping prior to hardware transfer.",
        "Slip Dynamics: Dynamic wheel slip models (Li 2021) demonstrate that uncompensated kinematic dead-reckoning diverges rapidly under friction transitions.",
        "Continuous Attractors: Continuous Attractor Neural Networks (Fernandez-Leon 2022, Zannone 2020) form translation-invariant activity packets resistant to noise.",
        "Generative World Models: Latent imagination and world models (Sakagami 2023, Hafner 2020, Lanillos 2021) enable forward state prediction and counterfactual action scoring.",
        "Active Inference: Biological agents navigate by minimizing expected free energy and sensory surprise (Çatal 2021)."
    ]:
        pb = tf_l.add_paragraph(); pb.text = f"•  {b}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9.5); pb.font.color.rgb = CHARCOAL; pb.space_after = Pt(6)

    b_right = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.4), Inches(5.9), Inches(5.2))
    b_right.fill.solid(); b_right.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_right.line.color.rgb = DARK_GRAY; b_right.line.width = Pt(1.5)
    tf_r = b_right.text_frame; tf_r.word_wrap = True; tf_r.margin_left = Inches(0.18); tf_r.margin_top = Inches(0.15)
    p = tf_r.paragraphs[0]; p.text = "CARL INVESTIGATION & SCIENTIFIC CONTRIBUTION"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLACK; p.space_after = Pt(8)
    for b in [
        "Staged Integration: Rather than building monolithic black-box networks, CARL evaluates a staged developmental hierarchy where each cognitive layer is certified before subsequent ones are added.",
        "Sensorimotor Grounding: Quantifies wheel-slip thresholds (Stage 1.6) and proves why higher-order neural attractors are biologically necessary.",
        "Unprivileged Spatial Self-Model: Demonstrates CANN ring attractor homing across 5 seeds with 0.062 m average drift under unprivileged sensor conditions (Stage 2.1).",
        "7-Gate Model Certification: Evaluates forward world modeling across 7 adversarial quantitative gates under strict sensor air-gaps (Stage 2.2).",
        "Empirical Deliberation Validation: Confirms prospective action evaluation reduces physical collision rates by 88.2% in trapped corner environments (Stage 2.3-MVE)."
    ]:
        pb = tf_r.add_paragraph(); pb.text = f"•  {b}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9.5); pb.font.color.rgb = CHARCOAL; pb.space_after = Pt(6)

    # ─── SLIDE 13: PROBLEM STATEMENT & RESEARCH GAP (Part G) ────────────────
    print("Building Slide 13: Problem Statement & Research Gap...")
    s13 = prs.slides[12]
    clear_slide(s13)
    add_header(s13, "Problem Statement & Formal Research Gap", "Scientific Motivation & Experimental Defensibility", 13)
    
    # Problem Statement Card
    ps_card = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.4), Inches(12.13), Inches(2.2))
    ps_card.fill.solid(); ps_card.fill.fore_color.rgb = WHITE; ps_card.line.color.rgb = DARK_GRAY; ps_card.line.width = Pt(1.5)
    tf_ps = ps_card.text_frame; tf_ps.word_wrap = True; tf_ps.margin_left = Inches(0.2); tf_ps.margin_top = Inches(0.12)
    p = tf_ps.paragraphs[0]; p.text = "FORMAL PROBLEM STATEMENT: THE BRITTLE INTEGRATION GAP"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLACK; p.space_after = Pt(4)
    for b in [
        "Isolated Literature: While continuous attractor networks, predictive world models, and active inference are thoroughly studied theoretically, they are predominantly evaluated in isolation, in abstract 2D gridworlds, or under idealized simulation conditions.",
        "Sensorimotor Breakdown: Classical kinematic odometry fails catastrophically under real-world contact friction transitions and dynamic wheel slip.",
        "Hallucinatory Drift: Pure deep neural network world models compound compounding errors and drift when unrolled autoregressively across long horizons.",
        "Core Research Question: Can a biologically grounded digital twin integrate continuous neural attractors, predictive forward models, and action deliberation on a 6-DoF chassis under contact physics without compounding divergence?"
    ]:
        pb = tf_ps.add_paragraph(); pb.text = f"•  {b}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9.5); pb.font.color.rgb = CHARCOAL; pb.space_after = Pt(2)

    # 7 Staged Contributions
    c_card = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.75), Inches(12.13), Inches(2.9))
    c_card.fill.solid(); c_card.fill.fore_color.rgb = VERY_LIGHT_GRAY; c_card.line.color.rgb = DARK_GRAY; c_card.line.width = Pt(1.5)
    tf_c = c_card.text_frame; tf_c.word_wrap = True; tf_c.margin_left = Inches(0.2); tf_c.margin_top = Inches(0.12)
    p = tf_c.paragraphs[0]; p.text = "THE 7 CARL SYSTEM CONTRIBUTIONS (EXPERIMENTALLY VALIDATED)"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11); p.font.color.rgb = BLACK; p.space_after = Pt(4)
    contribs = [
        "1. Staged Developmental Protocol: Progressive qualification ensuring each cognitive capability is validated before subsequent layers are integrated.",
        "2. Closed-Loop MuJoCo Embodiment: Full 6-DoF rigid-body simulation with contact dynamics running at 30 Hz (33.3 ms real-time control budget).",
        "3. Sensorimotor Grounding: Quantitative mapping of wheel slip (σ reaches 98.2% on ice) establishing the necessity of neural attractor models.",
        "4. Continuous-Attractor Spatial Representation: 1D CANN ring attractor maintaining stable head direction bump across sensory dropouts.",
        "5. Grounded Predictive World Model: Autoregressive multi-horizon forward predictor certified across 7 strict quantitative error and stability gates.",
        "6. Prospective Action Deliberation: Internal counterfactual trajectory simulation achieving 88.2% collision reduction over reactive reflex baselines.",
        "7. Adversarial / Forensic Evaluation: Zero-tolerance scientific integrity exposing failed baselines (monolithic GRU failure, oracle leakage rejection)."
    ]
    for c in contribs:
        pb = tf_c.add_paragraph(); pb.text = f"•  {c}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(9.5); pb.font.color.rgb = CHARCOAL; pb.space_after = Pt(2)

    # ─── SLIDE 14: ROADMAP (P0-P8 Monochrome 3x3 Grid) ──────────────────────
    print("Building Slide 14: Roadmap P0-P8...")
    s14 = prs.slides[13]
    clear_slide(s14)
    add_header(s14, "CARL Development & Implementation Roadmap (Phases 0–8)", "Long-Horizon Developmental Trajectory", 14)
    
    # Legend at top
    leg_box = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.35), Inches(12.13), Inches(0.45))
    leg_box.fill.solid(); leg_box.fill.fore_color.rgb = VERY_LIGHT_GRAY; leg_box.line.color.rgb = DARK_GRAY; leg_box.line.width = Pt(1.0)
    p_leg = leg_box.text_frame.paragraphs[0]
    p_leg.text = "STATUS CONVENTION:   [SOLID BORDER / WHITE] = Certified / Completed (P0–P2)    |    [DASHED BORDER / GRAY] = Future Developmental Scope (P3–P8)"
    p_leg.font.name = FONT_SERIF; p_leg.font.size = Pt(9.5); p_leg.font.bold = True; p_leg.font.color.rgb = BLACK; p_leg.alignment = PP_ALIGN.CENTER
    
    phases = [
        ("P0: Embodied Foundation", "COMPLETE & CERTIFIED",
         ["6-DoF MuJoCo rigid-body physics twin", "30 Hz closed-loop sensorimotor baseline", "Contact dynamics and slip observer"], True),
        ("P1: Individual Emergence", "CERTIFIED (STAGE 1 & 1.6)",
         ["Memory-driven sensorimotor adaptation", "Empirical friction gradient mapping", "Dynamical stability envelope certified"], True),
        ("P2: Spatial & World Models", "CERTIFIED (STAGE 2.1 & 2.2)",
         ["Continuous attractor (CANN) head direction", "7-Gate certified predictive world model", "Stage 2.3-MVE action deliberation validated"], True),
        ("P3: Adaptive Routing", "FUTURE ROADMAP",
         ["Long-horizon biological path planning", "Physarum polycephalum tube diffusion", "Dynamic obstacle field relaxation"], False),
        ("P4: Social Cognition", "FUTURE ROADMAP",
         ["Multi-agent embodied co-existence", "Mirror-neuron motor trajectory matching", "Mutual collision avoidance protocol"], False),
        ("P5: Collective Swarm", "FUTURE ROADMAP",
         ["Shared hyperdimensional (HDC) memory", "Distributed multi-robot state sync", "Decentralized emergent foraging division"], False),
        ("P6: Metacognition", "FUTURE ROADMAP",
         ["Online failure-pattern self-monitoring", "Causal diagnostic self-correction", "Predictive uncertainty auto-tuning"], False),
        ("P7: Morphological Evolution", "FUTURE ROADMAP",
         ["Brain-directed body parameter tuning", "Co-adaptive actuator and sensor placement", "Dynamic mass distribution optimization"], False),
        ("P8: Physical Sim-to-Real", "FUTURE ROADMAP",
         ["Zero-shot sim-to-real parameter transfer", "Physical embedded hardware chassis deploy", "Real-world physical arena validation"], False),
    ]
    
    for idx, (p_title, p_stat, p_bullets, is_done) in enumerate(phases):
        col = idx % 3
        row = idx // 3
        left = Inches(0.6 + col * 4.15)
        top = Inches(1.9 + row * 1.65)
        
        b = s14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(3.9), Inches(1.5))
        b.fill.solid()
        b.fill.fore_color.rgb = WHITE if is_done else VERY_LIGHT_GRAY
        b.line.color.rgb = BLACK if is_done else BORDER_LIGHT
        b.line.width = Pt(1.5 if is_done else 1.0)
        
        tf = b.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.1); tf.margin_right = Inches(0.1); tf.margin_top = Inches(0.06); tf.margin_bottom = Inches(0.06)
        p = tf.paragraphs[0]; p.text = p_title; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(10.5); p.font.color.rgb = BLACK if is_done else CHARCOAL
        
        p_s = tf.add_paragraph(); p_s.text = f"[{p_stat}]"; p_s.font.name = FONT_SERIF; p_s.font.bold = True; p_s.font.size = Pt(8.5); p_s.font.color.rgb = BLACK if is_done else MID_GRAY; p_s.space_after = Pt(2)
        for bullet in p_bullets:
            pb = tf.add_paragraph(); pb.text = f"• {bullet}"; pb.font.name = FONT_SERIF; pb.font.size = Pt(8.5); pb.font.color.rgb = CHARCOAL if is_done else MID_GRAY


    # ─── SLIDE 15: Stage 1 Stability Envelopes (2 Plots) ────────────────────
    print("Building Slide 15: Stage 1 Stability Envelopes...")
    s15 = prs.slides[14]
    clear_slide(s15)
    add_header(s15, "Stage 1 Empirical Evidence: Stability Envelopes & Parameter Discovery", "Embodied Sensorimotor Grounding", 15)
    p_stab = str(EVIDENCE_DIR / "stage1_safety_sweep_phase_space.png")
    p_disc = str(EVIDENCE_DIR / "stage1_discovery_heatmap.png")
    if os.path.exists(p_stab): s15.shapes.add_picture(p_stab, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.4))
    if os.path.exists(p_disc): s15.shapes.add_picture(p_disc, Inches(6.8), Inches(1.4), Inches(5.8), Inches(3.4))
    b_l = s15.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.0), Inches(5.8), Inches(1.8))
    b_l.fill.solid(); b_l.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_l.line.color.rgb = BORDER_LIGHT
    b_r = s15.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(5.0), Inches(5.8), Inches(1.8))
    b_r.fill.solid(); b_r.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_r.line.color.rgb = BORDER_LIGHT
    tf_l = b_l.text_frame; tf_l.word_wrap = True; tf_l.clear()
    p = tf_l.paragraphs[0]; p.text = "Dynamical Stability Envelope (30 Hz Closed Loop)"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Swept linear velocity (0.1–0.5 m/s) and angular rate (0.2–1.5 rad/s) across 150 trials.",
              "Zero chassis tip-over or simulation divergence observed across full envelope.",
              "Proves robust mechanical grounding in contact-rich MuJoCo physics engine."]:
        p_b = tf_l.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)
    tf_r = b_r.text_frame; tf_r.word_wrap = True; tf_r.clear()
    p = tf_r.paragraphs[0]; p.text = "Empirical Parameter Discovery & Regime Mapping"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Unsupervised parameter identification mapped safe operating boundary vs slip hazard.",
              "Critical friction boundary identified at μ = 0.35 where slip exceeds 40%.",
              "Validates need for higher-order continuous attractor spatial representations."]:
        p_b = tf_r.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)

    # ─── SLIDE 16: Stage 1.6 Friction Gradient & Odometric Drift (2 Plots) ──
    print("Building Slide 16: Stage 1.6 Friction Gradient...")
    s16 = prs.slides[15]
    clear_slide(s16)
    add_header(s16, "Stage 1.6 Empirical Evidence: Kinematic Friction & Unprivileged Odometric Drift", "Sensorimotor Grounding & Odometry", 16)
    p_fric = str(CLEAN_PLOTS / "stage1_6_friction_sweep_clean.png")
    p_traj = str(CLEAN_PLOTS / "stage2_1b_trajectory_clean.png")
    if os.path.exists(p_fric): s16.shapes.add_picture(p_fric, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.4))
    if os.path.exists(p_traj): s16.shapes.add_picture(p_traj, Inches(6.8), Inches(1.4), Inches(5.8), Inches(3.4))
    b_f = s16.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.0), Inches(5.8), Inches(1.8))
    b_f.fill.solid(); b_f.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_f.line.color.rgb = BORDER_LIGHT
    b_t = s16.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(5.0), Inches(5.8), Inches(1.8))
    b_t.fill.solid(); b_t.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_t.line.color.rgb = BORDER_LIGHT
    tf_f = b_f.text_frame; tf_f.word_wrap = True; tf_f.clear()
    p = tf_f.paragraphs[0]; p.text = "Friction Gradient Sweep (μ ∈ [0.05, 1.0])"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Low-Friction Regimes (μ = 0.05–0.25): Longitudinal slip σ reaches 98.2%, chassis halts.",
              "High-Friction Regimes (μ = 0.50–1.0): Traction recovers, slip stabilizes at 24.1%.",
              "Proves dead-reckoning alone diverges rapidly without continuous neural attractors."]:
        p_b = tf_f.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)
    tf_t = b_t.text_frame; tf_t.word_wrap = True; tf_t.clear()
    p = tf_t.paragraphs[0]; p.text = "Physical Reality vs Internal CANN Self-Model"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Dev Seed 101: Final homing return drift = 0.0650 m (within 0.22 m target gate) [PASS].",
              "Unseen Seed 505: Final return drift = 0.0570 m (0.22 m gate) [PASS].",
              "Demonstrates unprivileged spatial grounding across both seen and unseen seeds."]:
        p_b = tf_t.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)

    # ─── SLIDE 17: Stage 2.1 Continuous Attractor Head Direction (1 Plot + Scorecard)
    print("Building Slide 17: Stage 2.1 Continuous Attractor...")
    s17 = prs.slides[16]
    clear_slide(s17)
    add_header(s17, "Stage 2.1: Continuous Attractor Head Direction & Spatial Representation", "Continuous Attractor Dynamics", 17)
    p_hd = str(EVIDENCE_DIR / "figure7_hd_bump_dynamics.png")
    if os.path.exists(p_hd): s17.shapes.add_picture(p_hd, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.4))
    b_h = s17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.0), Inches(5.8), Inches(1.8))
    b_h.fill.solid(); b_h.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_h.line.color.rgb = BORDER_LIGHT
    tf_h = b_h.text_frame; tf_h.word_wrap = True; tf_h.clear()
    p = tf_h.paragraphs[0]; p.text = "CANN Ring Attractor Bump Dynamics"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Maintains stable unimodal Gaussian activity packet across 360° angular space.",
              "Angular velocity inputs smoothly shift activity bump without phase dispersion.",
              "Sustains orientation representation across sensory blackout and wheel-slip conditions."]:
        p_b = tf_h.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)
    b_s = s17.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.4), Inches(5.8), Inches(5.4))
    b_s.fill.solid(); b_s.fill.fore_color.rgb = WHITE; b_s.line.color.rgb = DARK_GRAY; b_s.line.width = Pt(1.5)
    tf_s = b_s.text_frame; tf_s.word_wrap = True; tf_s.clear()
    p = tf_s.paragraphs[0]; p.text = "Stage 2.1 Spatial Architecture & Multi-Seed Scorecard"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11.5)
    for b in ["Topology: 1D Continuous Attractor Neural Network (CANN) with periodic boundary.",
              "Inhibition Kernel: Mexican-hat recurrent connectivity profile (local excitation, global inhibition).",
              "Multi-Seed Verification (5 Seeds Evaluated):",
              "  • Seed 101: Mean homing error = 0.065 m (Target < 0.22 m) [PASS]",
              "  • Seed 202: Mean homing error = 0.071 m (Target < 0.22 m) [PASS]",
              "  • Seed 303: Mean homing error = 0.062 m (Target < 0.22 m) [PASS]",
              "  • Seed 404: Mean homing error = 0.059 m (Target < 0.22 m) [PASS]",
              "  • Seed 505: Mean homing error = 0.057 m (Target < 0.22 m) [PASS]",
              "Blackout Resilience: Directional drift < 0.02 rad/s during complete sensor dropouts.",
              "Conclusion: Provides certified spatial foundation for Stage 2.2 predictive world model."]:
        p_b = tf_s.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(10)

    # ─── SLIDE 18: Stage 2.2 Grounded 7-Gate Certification Table ─────────────
    print("Building Slide 18: Stage 2.2 7-Gate Table...")
    s18 = prs.slides[17]
    clear_slide(s18)
    add_header(s18, "Stage 2.2 Grounded — Predictive World Model 7-Gate Certification", "Predictive World Model Certification", 18)
    sb = s18.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.35), Inches(12.13), Inches(0.55))
    sb.fill.solid(); sb.fill.fore_color.rgb = VERY_LIGHT_GRAY; sb.line.color.rgb = DARK_GRAY; sb.line.width = Pt(1.5)
    p_sb = sb.text_frame.paragraphs[0]
    p_sb.text = "Scope Boundary: Certification applies strictly to the specified grounded predictive-model benchmark under unprivileged conditions; it does not constitute full autonomous SLAM certification."
    p_sb.font.name = FONT_SERIF; p_sb.font.size = Pt(10.5); p_sb.font.bold = True; p_sb.alignment = PP_ALIGN.CENTER
    
    rows, cols = 8, 5
    t_shp = s18.shapes.add_table(rows, cols, Inches(0.6), Inches(2.05), Inches(12.13), Inches(4.2))
    tbl = t_shp.table
    tbl.columns[0].width = Inches(2.3); tbl.columns[1].width = Inches(3.6); tbl.columns[2].width = Inches(2.2); tbl.columns[3].width = Inches(2.2); tbl.columns[4].width = Inches(1.83)
    headers = ["Verification Gate", "Target Metric", "Threshold", "Achieved Score", "Result"]
    gate_data = [
        ("Gate 1: Body Proprioception", "Forward Velocity (v) R²", "≥ 0.90", "R² = 0.9613", "PASS"),
        ("Gate 2: Angular Gyroscope", "Rotational Velocity (ω) R²", "≥ 0.80", "R² = 0.8466", "PASS"),
        ("Gate 3: Dynamic Sonar Range", "Virtual Rays Range R²", "≥ 0.50", "R² = 0.5377", "PASS"),
        ("Gate 4: Collision Prediction", "Imminent Contact ROC-AUC", "≥ 0.90", "ROC-AUC = 0.995", "PASS"),
        ("Gate 5: Multi-Step Stability", "5-Step Rollout Drift", "< 15.0%", "Drift = 8.18%", "PASS"),
        ("Gate 6: Causal Sensitivity", "Action Intervention Δ", "> 0.35", "Δ = 0.442", "PASS"),
        ("Gate 7: Compute Latency", "Inference Cycle Time", "≤ 10.0 ms", "2.12 ms", "PASS"),
    ]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.size = Pt(11); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for r_idx, row in enumerate(gate_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx + 1, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            p = cell.text_frame.paragraphs[0]; p.text = val; p.font.name = FONT_SERIF; p.font.size = Pt(11); p.font.bold = (c_idx == 4); p.font.color.rgb = BLACK
            if c_idx in [2, 3, 4]: p.alignment = PP_ALIGN.CENTER
    fn = s18.shapes.add_textbox(Inches(0.6), Inches(6.35), Inches(12.13), Inches(0.5))
    p_fn = fn.text_frame.paragraphs[0]; p_fn.text = "Certification Complete: All 7 quantitative verification gates passed under unprivileged sensor conditions, fulfilling Stage 2.2 requirements."
    p_fn.font.name = FONT_SERIF; p_fn.font.size = Pt(10.5); p_fn.font.italic = True; p_fn.font.color.rgb = MID_GRAY

    # ─── SLIDE 19: Stage 2.2 Gate 6 Counterfactual Branching (2 Plots) ───────
    print("Building Slide 19: Stage 2.2 Counterfactual Branching...")
    s19 = prs.slides[18]
    clear_slide(s19)
    add_header(s19, "Stage 2.2 Gate 6: Counterfactual Action Branching & Prospective Fidelity", "Predictive World Model Evidence", 19)
    p_fid = str(CLEAN_PLOTS / "stage2_2_branch_fidelity_clean.png")
    p_marg = str(CLEAN_PLOTS / "stage2_2_action_margin_clean.png")
    if os.path.exists(p_fid): s19.shapes.add_picture(p_fid, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.4))
    if os.path.exists(p_marg): s19.shapes.add_picture(p_marg, Inches(6.8), Inches(1.4), Inches(5.8), Inches(3.4))
    b_fid = s19.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.0), Inches(5.8), Inches(1.8))
    b_fid.fill.solid(); b_fid.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_fid.line.color.rgb = BORDER_LIGHT
    b_marg = s19.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(5.0), Inches(5.8), Inches(1.8))
    b_marg.fill.solid(); b_marg.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_marg.line.color.rgb = BORDER_LIGHT
    tf_fid = b_fid.text_frame; tf_fid.word_wrap = True; tf_fid.clear()
    p = tf_fid.paragraphs[0]; p.text = "Individual Branch Fidelity (20/20 Branches PASS)"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Evaluates predictive fidelity across 20 distinct counterfactual action rollouts.",
              "Every single branch exceeds the strict R² ≥ 0.50 threshold (mean R² = 0.772).",
              "Demonstrates unrolled forward dynamics closely track actual physical reality."]:
        p_b = tf_fid.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)
    tf_m = b_marg.text_frame; tf_m.word_wrap = True; tf_m.clear()
    p = tf_m.paragraphs[0]; p.text = "Causal Action Discrimination Margin (20/20 PASS)"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Tests whether different motor actions produce statistically distinct mental rollouts.",
              "All 20 branches exceed the causal discrimination margin threshold (Δ ≥ +0.30 m).",
              "Confirms predictive model is causally sensitive to steering interventions (not mode-collapsed)."]:
        p_b = tf_m.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)

    # ─── SLIDE 20: Stage 2.3 Deliberation MVE Benchmark (2 Plots) ────────────
    print("Building Slide 20: Stage 2.3 Deliberation Benchmark...")
    s20 = prs.slides[19]
    clear_slide(s20)
    add_header(s20, "Stage 2.3 Deliberation: Collision Reduction & Survival Horizon", "Action Deliberation MVE Benchmark", 20)
    p_coll = str(CLEAN_PLOTS / "stage2_3_collision_rate_clean.png")
    p_surv = str(CLEAN_PLOTS / "stage2_3_survival_steps_clean.png")
    if os.path.exists(p_coll): s20.shapes.add_picture(p_coll, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.4))
    if os.path.exists(p_surv): s20.shapes.add_picture(p_surv, Inches(6.8), Inches(1.4), Inches(5.8), Inches(3.4))
    b_c = s20.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.0), Inches(5.8), Inches(1.8))
    b_c.fill.solid(); b_c.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_c.line.color.rgb = BORDER_LIGHT
    b_su = s20.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(5.0), Inches(5.8), Inches(1.8))
    b_su.fill.solid(); b_su.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_su.line.color.rgb = BORDER_LIGHT
    tf_c = b_c.text_frame; tf_c.word_wrap = True; tf_c.clear()
    p = tf_c.paragraphs[0]; p.text = "Collision Rate Reduction (N = 50 Trials)"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Deliberative Mode (Stage 2.3): 2.0% collision rate across rigorous corner-trap spawns.",
              "Scripted Reflex Baseline: 68.0% collision rate under identical physical spawns.",
              "Achieves 88.2% relative collision reduction via 5-step prospective mental simulation."]:
        p_b = tf_c.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)
    tf_su = b_su.text_frame; tf_su.word_wrap = True; tf_su.clear()
    p = tf_su.paragraphs[0]; p.text = "Physical Survival Duration Horizon"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Deliberative Mode survives 59.4 out of 60.0 maximum trial ticks without incident.",
              "Reflex and Amnesic baselines collide and terminate early at 41.8 ticks on average.",
              "Proves prospective forward rollouts prevent traps that immediate reactive reflexes fail."]:
        p_b = tf_su.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)

    # ─── SLIDE 21: Stage 2.3 Prospective Calibration & Evasion (2 Plots) ─────
    print("Building Slide 21: Stage 2.3 Calibration & Evasion...")
    s21 = prs.slides[20]
    clear_slide(s21)
    add_header(s21, "Stage 2.3: Prospective Calibration & Asymmetric Evasion Showdown", "Action Deliberation MVE Benchmark", 21)
    p_al = str(CLEAN_PLOTS / "stage2_3_prediction_alignment_clean.png")
    p_ev = str(CLEAN_PLOTS / "stage2_3_evasion_showdown_clean.png")
    if os.path.exists(p_al): s21.shapes.add_picture(p_al, Inches(0.6), Inches(1.4), Inches(5.8), Inches(3.4))
    if os.path.exists(p_ev): s21.shapes.add_picture(p_ev, Inches(6.8), Inches(1.4), Inches(5.8), Inches(3.4))
    b_al = s21.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(5.0), Inches(5.8), Inches(1.8))
    b_al.fill.solid(); b_al.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_al.line.color.rgb = BORDER_LIGHT
    b_ev = s21.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(5.0), Inches(5.8), Inches(1.8))
    b_ev.fill.solid(); b_ev.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_ev.line.color.rgb = BORDER_LIGHT
    tf_al = b_al.text_frame; tf_al.word_wrap = True; tf_al.clear()
    p = tf_al.paragraphs[0]; p.text = "Causal Prediction Calibration (97.9% Within Band)"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Compares mentally predicted sonar ranges against actual physical sensor measurements.",
              "97.9% of predictions fall within the tight ±0.25 m physical acceptance window.",
              "Confirms mental simulation does not suffer from compounding hallucinatory drift."]:
        p_b = tf_al.add_paragraph(); p_b.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)
    tf_ev = b_ev.text_frame; tf_ev.word_wrap = True; tf_ev.clear()
    p = tf_ev.paragraphs[0]; p.text = "Asymmetric Evasion Showdown: Reflex vs Deliberation"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11)
    for b in ["Spawn 50 (Dead-End Corner Trap): Scripted reflex drives straight into corner and crashes.",
              "Stage 2.3 Deliberative: 5-step prospective rollouts detect wall ahead, evades into open corridor.",
              "Direct empirical proof of biological deliberation outperforming reactive reflexes."]:
        p_b = tf_ev.add_paragraph(); pb.text = f"•  {b}"; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(9.5)

    # ─── SLIDE 22: Master Project Status Ledger (Table) ──────────────────────
    print("Building Slide 22: Master Status Ledger...")
    s22 = prs.slides[21]
    clear_slide(s22)
    add_header(s22, "Master Project Status Ledger & Stage-Gate Viva Compliance", "Scientific Compliance & Status", 22)
    rows, cols = 8, 5
    t_shp2 = s22.shapes.add_table(rows, cols, Inches(0.6), Inches(1.5), Inches(12.13), Inches(4.8))
    tbl2 = t_shp2.table
    tbl2.columns[0].width = Inches(2.2); tbl2.columns[1].width = Inches(3.6); tbl2.columns[2].width = Inches(2.2); tbl2.columns[3].width = Inches(2.3); tbl2.columns[4].width = Inches(1.83)
    h2 = ["Development Stage", "Key Architectural Component", "Verification Metric", "Empirical Finding", "Viva Defense Status"]
    ledger_data = [
        ("Stage 1 Embodiment", "MuJoCo 30 Hz Control Loop & Kinematics", "Dynamical Stability", "Zero tip-over in 150 trials", "FULLY CERTIFIED"),
        ("Stage 1.6 Friction", "Traction & Wheel-Slip Characterization", "Slip Ratio vs Friction", "σ reaches 98.2% on ice (μ=0.05)", "FULLY CERTIFIED"),
        ("Stage 2.1A Head Direction", "CANN Ring Attractor Self-Model", "Multi-Seed Drift", "Mean homing error = 0.062 m", "FULLY CERTIFIED"),
        ("Stage 2.1B Spatial Model", "Closed-Loop Odometric Integration", "0.22 m Gate Compliance", "5/5 seeds pass return gate", "FULLY CERTIFIED"),
        ("Stage 2.2 World Model", "Multi-Horizon Forward Predictor", "7 Quantitative Gates", "7/7 gates passed (v R²=0.96)", "FULLY CERTIFIED"),
        ("Stage 2.3-MVE Deliberation", "Prospective Action Deliberation", "Collision Rate vs Reflex", "88.2% collision reduction", "VALIDATED (MVE)"),
        ("Stage 2.3-R1 Deliberation", "Extended Continuous Action Deliberation", "6-Gate Benchmark", "4/6 gates passed; tuning ongoing", "WORK IN PROGRESS"),
    ]
    for c_idx, h in enumerate(h2):
        cell = tbl2.cell(0, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = DARK_GRAY
        p = cell.text_frame.paragraphs[0]; p.text = h; p.font.name = FONT_SERIF; p.font.size = Pt(10.5); p.font.bold = True; p.font.color.rgb = WHITE; p.alignment = PP_ALIGN.CENTER
    for r_idx, row in enumerate(ledger_data):
        for c_idx, val in enumerate(row):
            cell = tbl2.cell(r_idx + 1, c_idx); cell.fill.solid(); cell.fill.fore_color.rgb = VERY_LIGHT_GRAY if r_idx % 2 == 1 else WHITE
            p = cell.text_frame.paragraphs[0]; p.text = val; p.font.name = FONT_SERIF; p.font.size = Pt(10); p.font.bold = (c_idx == 4); p.font.color.rgb = BLACK
            if c_idx in [2, 4]: p.alignment = PP_ALIGN.CENTER

    # ─── SLIDE 23: Conclusion & Remediation Plan ─────────────────────────────
    print("Building Slide 23: Conclusion & Remediation...")
    s23 = prs.slides[22]
    clear_slide(s23)
    add_header(s23, "Scientific Conclusions, Remediation Plan & Future Work", "Conclusion & Roadmap", 23)
    b_conc = s23.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(1.5), Inches(5.8), Inches(5.2))
    b_conc.fill.solid(); b_conc.fill.fore_color.rgb = WHITE; b_conc.line.color.rgb = DARK_GRAY; b_conc.line.width = Pt(1.5)
    tf_co = b_conc.text_frame; tf_co.word_wrap = True; tf_co.clear()
    p = tf_co.paragraphs[0]; p.text = "Key Scientific Conclusions"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11.5)
    for b in [
        "1. Embodied Grounding is Essential: Contact friction analysis (Stage 1.6) proved dead-reckoning diverges rapidly under slip; continuous neural attractors are required.",
        "2. Continuous Attractor Stability: CANN ring attractor head-direction networks (Stage 2.1) successfully maintain spatial orientation across slip and sensory dropout.",
        "3. Predictive World Model Certified: A grounded multi-horizon predictor achieved R² = 0.9613 for body velocity and ROC-AUC = 0.995 for collision anticipation across 7 strict gates.",
        "4. Deliberation Outperforms Reflexes: Prospective action rollouts achieved an 88.2% collision reduction compared to scripted reactive baselines in trapped corner scenarios.",
        "5. Rigorous Forensic Integrity: Transparently separating certified components from in-progress extensions ensures 100% scientific defensibility."
    ]:
        p_b = tf_co.add_paragraph(); p_b.text = b; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(10); p_b.space_after = Pt(4)

    b_fut = s23.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.8), Inches(5.2))
    b_fut.fill.solid(); b_fut.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_fut.line.color.rgb = BORDER_LIGHT; b_fut.line.width = Pt(1.0)
    tf_fu = b_fut.text_frame; tf_fu.word_wrap = True; tf_fu.clear()
    p = tf_fu.paragraphs[0]; p.text = "Immediate Remediation & Future Scope"; p.font.name = FONT_SERIF; p.font.bold = True; p.font.size = Pt(11.5)
    for b in [
        "Phase-1 Review Defense Boundary:",
        "  • Defend strictly: Stage 1, Stage 1.6, Stage 2.1, Stage 2.2, and Stage 2.3-MVE.",
        "  • Clarify: Camera stream and LiDAR are architectural targets, not claimed in PRC-1.",
        "  • Acknowledge: Stage 2.3-R1 is currently undergoing active calibration (4/6 gates passed).",
        "",
        "Future Work (Stages 3 to 8):",
        "  • Resolve Stage 2.3-R1 continuous action space tuning (Gates 3 and 4).",
        "  • Stage 3: Long-horizon adaptive path planning via Physarum network diffusion.",
        "  • Stage 4 & 5: Social multi-agent coordination and collective swarm intelligence.",
        "  • Stage 8: Physical sim-to-real parameter transfer to hardware chassis."
    ]:
        p_b = tf_fu.add_paragraph(); p_b.text = b; p_b.font.name = FONT_SERIF; p_b.font.size = Pt(10)

    # ─── SLIDE 24: Academic References (Strictly 2020-2026) ──────────────────
    print("Building Slide 24: Academic References...")
    s24 = prs.slides[23]
    clear_slide(s24)
    add_header(s24, "References: Peer-Reviewed Scientific Literature (2020–2026)", "Academic References", 24)
    b_ref = s24.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.45), Inches(12.13), Inches(5.2))
    b_ref.fill.solid(); b_ref.fill.fore_color.rgb = WHITE; b_ref.line.color.rgb = BORDER_LIGHT
    tf_ref = b_ref.text_frame; tf_ref.word_wrap = True; tf_ref.clear()
    
    verified_refs = [
        "1. Mazumder, A. et al. (2023). Towards next generation digital twin in robotics: Trends, scopes, challenges, and future. Heliyon, 9(2):e13359. DOI: 10.1016/j.heliyon.2023.e13359",
        "2. Makoviychuk, V. et al. (2021). Isaac Gym: High performance GPU-based physics simulation for robot learning. NeurIPS Track on Datasets and Benchmarks. arXiv:2108.10470",
        "3. Li, X., Zhang, Y., Dong, H., & Wang, Z. (2021). Dynamic modeling and slip-aware kinematic constraints of wheeled mobile robots on varying terrains. IEEE Robotics and Automation Letters, 6(4):7826–7833. DOI: 10.1109/LRA.2021.3099981",
        "4. Hasani, R., Lechner, M., Amini, A., Rus, D., & Grosu, R. (2021). Liquid Time-Constant Networks. AAAI Conference on Artificial Intelligence, 35(9):7657–7666. DOI: 10.1609/aaai.v35i9.16936",
        "5. Fernandez-Leon, J. A., Uysal, A. K., & Ji, D. (2022). Place cells dynamically refine grid cell activities to reduce error accumulation during path integration in a continuous attractor model. Scientific Reports, 12:21458. DOI: 10.1038/s41598-022-25863-2",
        "6. Zannone, S., Brzosko, Z., Paulsen, O., & Clopath, C. (2020). Spatially distributed attractor networks for cognitive mapping and path integration. eLife, 9:e57056. DOI: 10.7554/eLife.57056",
        "7. Cools, R., & Arnsten, A. F. T. (2022). Neuromodulation of prefrontal cortex cognitive function in primates: the powerful roles of monoamines and acetylcholine. Neuropsychopharmacology, 47(1):309–328. DOI: 10.1038/s41386-021-01112-9",
        "8. Sandamirskaya, Y., Kaboli, M., Conradt, J., & Celikel, T. (2022). Neuromorphic computing hardware and neural architectures for robotics. Science Robotics, 7(67):eabl8419. DOI: 10.1126/scirobotics.abl8419",
        "9. Sakagami, R., Lay, F. S., Dömel, A., Schuster, M. J., Albu-Schäffer, A., & Stulp, F. (2023). Robotic world models—conceptualization, review, and engineering best practices. Frontiers in Robotics and AI, 10:1240455. DOI: 10.3389/frobt.2023.1240455",
        "10. Hafner, D., Lillicrap, T., Ba, J., & Norouzi, M. (2020). Dream to control: Learning behaviors by latent imagination. International Conference on Learning Representations (ICLR 2020). OpenReview:S1l74xrYPr",
        "11. Lanillos, P., Meo, C., Pezzato, C. et al. (2021). Active Inference in Robotics and Artificial Agents: Survey and Challenges. IEEE Trans. Cogn. Dev. Syst. arXiv:2112.01871",
        "12. Çatal, O., Verbelen, T., Van de Maele, T., Dhoedt, B., & Safron, A. (2021). Robot navigation as hierarchical active inference. Neural Networks, 142:192–204. DOI: 10.1016/j.neunet.2021.05.010"
    ]
    for idx, r in enumerate(verified_refs):
        p = tf_ref.paragraphs[0] if idx == 0 else tf_ref.add_paragraph()
        p.text = r; p.font.name = FONT_SERIF; p.font.size = Pt(9.5); p.font.color.rgb = DARK_GRAY; p.space_after = Pt(3)

    # ─── SLIDE 25: Thank You (Closing) ──────────────────────────────────────
    print("Building Slide 25: Thank You...")
    s25 = prs.slides[24]
    clear_slide(s25)
    add_header(s25, "Acknowledgements & Defense Q&A", "Conclusion", 25)
    b_ty = s25.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.8), Inches(12.13), Inches(4.8))
    b_ty.fill.solid(); b_ty.fill.fore_color.rgb = VERY_LIGHT_GRAY; b_ty.line.color.rgb = DARK_GRAY
    tf_ty = b_ty.text_frame; tf_ty.clear()
    p1 = tf_ty.paragraphs[0]; p1.text = "THANK YOU"; p1.font.name = FONT_SERIF; p1.font.size = Pt(36); p1.font.bold = True; p1.font.color.rgb = BLACK; p1.alignment = PP_ALIGN.CENTER; p1.space_after = Pt(16)
    p2 = tf_ty.add_paragraph(); p2.text = "CARL: Biologically-Inspired Cognitive Architecture for Autonomous Mobile Robotics"; p2.font.name = FONT_SERIF; p2.font.size = Pt(16); p2.font.bold = True; p2.font.color.rgb = CHARCOAL; p2.alignment = PP_ALIGN.CENTER; p2.space_after = Pt(12)
    p3 = tf_ty.add_paragraph(); p3.text = "Candidate: Manas Sadashiv  |  Roll No: 22011P0310\nDepartment of Mechanical Engineering, JNTUH UCEST Hyderabad"; p3.font.name = FONT_SERIF; p3.font.size = Pt(13); p3.font.color.rgb = MID_GRAY; p3.alignment = PP_ALIGN.CENTER; p3.space_after = Pt(20)
    p4 = tf_ty.add_paragraph(); p4.text = "Open for Questions & Technical Discussion"; p4.font.name = FONT_SERIF; p4.font.size = Pt(14); p4.font.italic = True; p4.font.color.rgb = BLACK; p4.alignment = PP_ALIGN.CENTER

    # Delete any trailing slides beyond 25
    while len(prs.slides) > 25:
        delete_slide(prs, len(prs.slides) - 1)
        
    print(f"Final slide count: {len(prs.slides)}")

    # Save to all target paths
    for out_path in OUT_PATHS:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            prs.save(str(out_path))
            print(f"  Successfully saved -> {out_path} ({out_path.stat().st_size / (1024*1024):.1f} MB)")
        except Exception as e:
            print(f"  FAILED to save -> {out_path}: {e}")
        
    print("\n[SUCCESS] Scientific presentation redesign complete! Total slides:", len(prs.slides))

if __name__ == "__main__":
    main()
