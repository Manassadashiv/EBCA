#!/usr/bin/env python3
r"""
build_final_presentation.py — Precision Editorial, Scientific, Visual, and Structural Surgery
Produces:
  1. D:\ebca\310_Stage3_Updated_Final.pptx (and D:\310_Stage3_Updated_Final.pptx)
  2. D:\ebca\310_Stage3_Updated_Final_AUDIT.md

Strict Rules Applied:
  - Font: Times New Roman for EVERY visible text object.
  - Size: Absolute minimum 18 pt across the entire deck (titles 24-28 pt, body/captions/tables 18-20 pt).
  - Tables: Max 1 table per slide, native PowerPoint tables only (zero screenshots), plain white cells,
    simple 1pt black borders, black text, NO colored fills, title strictly ABOVE table.
  - Figures: Max 2 independent plots per slide, zero composite/dashboard figures (every visual plot
    is 1 independent graph with its own axes), figure captions strictly BELOW plot.
  - Zero alteration of scientific results, p-values, sample sizes, or certification values.
  - Architecture Section: Slide 14 simplified pipeline + MPPI annotation; Slide 15 simplified endocrine;
    Slide 16 deleted; Slide 17 simplified reflex override.
  - Slide 18: Replaced with 5-stage developmental architecture blocks + historical note.
  - Slide 21: Added compact callout with P0 metrics; Slide 22 deleted.
  - Stage 3 Hero Section: Rebuilt with native tables and independent single plots.
  - Master Status Ledger: Native plain table with 10 consolidated rows.
  - Work To Be Done: 3 clean sections, no duplicate bullets.
  - References: Times New Roman, >= 18 pt.
  - Slide numbers sequentially updated across all 46 slides.
"""

import sys
import os
import shutil
from pathlib import Path
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls

REPO_ROOT = Path(r"D:\ebca")
SRC_PPTX = REPO_ROOT / "310_Stage3_Updated.pptx"
OUT_PPTX_EBCA = REPO_ROOT / "310_Stage3_Updated_Final.pptx"
OUT_PPTX_DROOT = Path(r"D:\310_Stage3_Updated_Final.pptx")
AUDIT_MD_FILE = REPO_ROOT / "310_Stage3_Updated_Final_AUDIT.md"

PLOTS_DIR = REPO_ROOT / "evidence" / "independent_single_plots"
S31_DIR = REPO_ROOT / "evidence" / "stage3_1R"

FONT_NAME = "Times New Roman"
COLOR_BLACK = RGBColor(0, 0, 0)
COLOR_WHITE = RGBColor(255, 255, 255)
COLOR_DARK = RGBColor(17, 24, 39)
COLOR_MUTED = RGBColor(55, 65, 81)


def set_run(run, text, size_pt=18, bold=False, italic=False, color=COLOR_BLACK):
    run.text = text
    run.font.name = FONT_NAME
    run.font.size = Pt(max(18.0, float(size_pt)))
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def set_plain_cell_border(cell, color="000000", width="12700"):
    """Applies a simple 1pt solid black border to all 4 edges of a cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    for border_name in ['lnL', 'lnR', 'lnT', 'lnB']:
        ln = parse_xml(f'<a:{border_name} {nsdecls("a")} w="{width}" cmpd="s"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:{border_name}>')
        tcPr.append(ln)


def add_plain_table(slide, left, top, width, height, headers, rows, col_widths=None, font_size=18):
    """
    Creates a native PowerPoint table:
    - White background cells
    - Simple 1pt black borders on every cell
    - Black Times New Roman text at font_size (>= 18 pt)
    """
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    tbl = table_shape.table

    if col_widths and len(col_widths) == num_cols:
        for idx, w in enumerate(col_widths):
            tbl.columns[idx].width = w

    # Headers
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_WHITE
        set_plain_cell_border(cell, color="000000", width="12700")
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        set_run(r, h, size_pt=font_size, bold=True, color=COLOR_BLACK)

    # Rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_WHITE
            set_plain_cell_border(cell, color="000000", width="12700")
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            if c_idx in [0, 4] or len(str(val)) <= 15:
                p.alignment = PP_ALIGN.CENTER
            else:
                p.alignment = PP_ALIGN.LEFT
            r = p.add_run()
            bold = True if any(kw in str(val) for kw in ["PASS", "CERTIFIED", "FAIL", "ACTIVE", "VALIDATED"]) else False
            set_run(r, str(val), size_pt=font_size, bold=bold, color=COLOR_BLACK)

    return table_shape


def create_standard_slide(prs, title_text, subtitle_text=""):
    """Creates a base slide with standard title, subtitle, and divider line."""
    slide = prs.slides.add_slide(prs.slide_layouts[0])

    # Title box
    tb = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_bottom = Inches(0)

    p1 = tf.paragraphs[0]
    p1.space_after = Pt(2)
    r1 = p1.add_run()
    set_run(r1, title_text, size_pt=24, bold=True, color=COLOR_BLACK)

    if subtitle_text:
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        set_run(r2, subtitle_text, size_pt=18, bold=False, italic=True, color=COLOR_MUTED)

    # Black divider line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    return slide


def add_bullet_p(tf, text, size_pt=18, bold=False, space_after=6, bullet=True):
    p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
    p.space_after = Pt(space_after)
    clean_text = text.strip()
    while clean_text.startswith("•") or clean_text.startswith("-") or clean_text.startswith("*"):
        clean_text = clean_text.lstrip("•-* ").strip()
    prefix = "•  " if bullet else ""
    r = p.add_run()
    set_run(r, prefix + clean_text, size_pt=size_pt, bold=bold, color=COLOR_BLACK)
    return p


def add_card_box(slide, left, top, width, height, title, subtitle=None, items=None):
    """Creates a structured rounded rectangle card with Times New Roman text >= 18 pt."""
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = COLOR_WHITE
    box.line.color.rgb = COLOR_BLACK
    box.line.width = Pt(1.5)

    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_right = Inches(0.18)
    tf.margin_top = Inches(0.12)
    tf.margin_bottom = Inches(0.10)

    p0 = tf.paragraphs[0]
    p0.space_after = Pt(2)
    r_t = p0.add_run()
    set_run(r_t, title, size_pt=19, bold=True, color=COLOR_BLACK)

    if subtitle:
        p_sub = tf.add_paragraph()
        p_sub.space_after = Pt(6)
        r_s = p_sub.add_run()
        set_run(r_s, subtitle, size_pt=18, italic=True, color=COLOR_MUTED)

    if items:
        for it in items:
            p_it = tf.add_paragraph()
            p_it.space_after = Pt(4)
            clean_it = it.strip()
            while clean_it.startswith("•") or clean_it.startswith("-") or clean_it.startswith("*"):
                clean_it = clean_it.lstrip("•-* ").strip()
            if ":" in clean_it and not clean_it.startswith("http"):
                part_title, part_desc = clean_it.split(":", 1)
                r_prefix = p_it.add_run()
                set_run(r_prefix, f"•  {part_title}:", size_pt=18, bold=True, color=COLOR_BLACK)
                r_body = p_it.add_run()
                set_run(r_body, part_desc, size_pt=18, bold=False, color=COLOR_BLACK)
            else:
                r_body = p_it.add_run()
                set_run(r_body, f"•  {clean_it}", size_pt=18, bold=False, color=COLOR_BLACK)

    return box


NUMERICAL_FIXES = [
    # Terminology typos
    ("Stage 21A/21B", "Stage 2.1A / 2.1B"),
    ("Stage 21A", "Stage 2.1A"),
    ("Stage 21B", "Stage 2.1B"),
    ("Stage 21 Spatial Architecture & Multi Seed Scorecard", "Stage 2.1 Spatial Architecture & Multi-Seed Scorecard"),
    ("Stage 21 Spatial Architecture", "Stage 2.1 Spatial Architecture"),
    ("Stage 22 predictive world model", "Stage 2.2 predictive world model"),
    ("Stage 22", "Stage 2.2"),
    ("Stage 23 discrete deliberation", "Stage 2.3 discrete deliberation"),
    ("Stage 23", "Stage 2.3"),

    # Slide 22: Dynamical Stability
    ("01–05 m/s", "0.1–0.5 m/s"),
    ("01-05 m/s", "0.1–0.5 m/s"),
    ("02–15 rad/s", "0.2–1.5 rad/s"),
    ("02-15 rad/s", "0.2–1.5 rad/s"),

    # Slide 23: Parameter Discovery
    ("μ = 035", "μ = 0.35"),
    ("u = 035", "μ = 0.35"),

    # Slide 24: Friction Sweep & Odometric Drift
    ("μ ∈ [005, 10]", "μ ∈ [0.05, 1.0]"),
    ("u ∈ [005, 10]", "μ ∈ [0.05, 1.0]"),
    ("μ = 005–025", "μ = 0.05–0.25"),
    ("μ = 005-025", "μ = 0.05–0.25"),
    ("982%", "98.2%"),
    ("μ = 050–10", "μ = 0.50–1.0"),
    ("μ = 050-10", "μ = 0.50–1.0"),
    ("241%", "24.1%"),

    # Slide 26: CANN Physical Reality vs Self-Model
    ("drift = 00650 m", "drift = 0.0650 m"),
    ("drift = 00570 m", "drift = 0.0570 m"),
    ("within 022 m", "within 0.22 m"),
    ("(022 m gate)", "(within 0.22 m target gate)"),

    # Slide 27: Multi-Seed Scorecard
    ("homing error = 0065 m", "homing error = 0.065 m"),
    ("homing error = 0071 m", "homing error = 0.071 m"),
    ("homing error = 0062 m", "homing error = 0.062 m"),
    ("homing error = 0059 m", "homing error = 0.059 m"),
    ("homing error = 0057 m", "homing error = 0.057 m"),
    ("Target < 022 m", "Target < 0.22 m"),
    ("drift < 002 rad/s", "drift < 0.02 rad/s"),

    # Slide 28: 7-Gate Table Values (backup)
    ("≥ 090", "≥ 0.90"),
    ("R² = 09613", "R² = 0.9613"),
    ("≥ 080", "≥ 0.80"),
    ("R² = 08466", "R² = 0.8466"),
    ("≥ 050", "≥ 0.50"),
    ("R² = 05377", "R² = 0.5377"),
    ("ROC AUC = 0995", "ROC-AUC = 0.995"),
    ("ROC AUC", "ROC-AUC"),
    ("< 150%", "< 15.0%"),
    ("Drift = 818%", "Drift = 8.18%"),
    ("> 035", "> 0.35"),
    ("Δ = 0442", "Δ = 0.442"),
    ("≤ 100 ms", "≤ 10.0 ms"),
    ("≤ 100 ", "≤ 10.0 "),
    ("212 ms", "2.12 ms"),
    ("212 ", "2.12 "),

    # Slide 29: World Model Evidence
    ("Δ ≥ +030 m", "Δ ≥ +0.30 m"),
    ("R² ≥ 050", "R² ≥ 0.50"),
    ("mean R² = 0772", "mean R² = 0.772"),
]


def fix_corrupted_number_string(text):
    for bad, good in NUMERICAL_FIXES:
        if bad in text:
            text = text.replace(bad, good)
    return text


def normalize_text_in_shape(sh):
    """Recursively normalizes all text in any shape or table to Times New Roman and >= 18 pt, fixing notation."""
    # Clamp overflow bounding boxes
    try:
        if sh.left.inches < 0.10:
            sh.left = Inches(0.50)
        if (sh.left.inches + sh.width.inches) > 13.20:
            sh.width = Inches(max(1.0, 13.20 - sh.left.inches))
        if (sh.top.inches + sh.height.inches) > 7.35:
            sh.height = Inches(max(0.4, 7.30 - sh.top.inches))
    except Exception:
        pass

    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.text = fix_corrupted_number_string(r.text)
                r.font.name = FONT_NAME
                cur_sz = r.font.size.pt if r.font.size else 18.0
                r.font.size = Pt(max(18.0, cur_sz))
    elif sh.has_table:
        tbl = sh.table
        for row in tbl.rows:
            for cell in row.cells:
                cell.fill.solid()
                cell.fill.fore_color.rgb = COLOR_WHITE
                set_plain_cell_border(cell, color="000000", width="12700")
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.text = fix_corrupted_number_string(r.text)
                        r.font.name = FONT_NAME
                        cur_sz = r.font.size.pt if r.font.size else 18.0
                        r.font.size = Pt(max(18.0, cur_sz))
                        r.font.color.rgb = COLOR_BLACK


def build_slide14_architecture(slide):
    """Rebuilds Slide 14 as the primary conceptual architecture pipeline."""
    shapes_to_delete = []
    for sh in slide.shapes:
        if sh.has_text_frame and any(kw in sh.text_frame.text for kw in ["DIGITAL TWIN", "14"]):
            continue
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    blocks = [
        ("Sensory Layer", "12 Sonars (30° Cones) • Head Retina Camera • Wheel Encoders • 6-Axis IMU"),
        ("Sensor Fusion", "Ego-Centric Body Frame Alignment • Odometry Integration • Velocity Filtering"),
        ("Neuromorphic Internal State", "2,114-Unit CANN Attractor Network (64-HD + 1,024-Grid Torus) • 500-Neuron LSM"),
        ("Deliberation & Trajectory", "Continuous Model Predictive Path Integral [MPPI (M=128, H=15) — Stage 3.3]"),
        ("Motor Command Generation", "Continuous Wheel Velocities u = [u_L, u_R] ∈ [-1.0, 1.0]² • Acceleration Clamping"),
        ("Physical Response & Twin", "MuJoCo 30 Hz Rigid-Body Physics Twin • Ground Surface Traction & Kinematic Slip")
    ]

    top_start = 1.45
    block_h = 0.72
    gap = 0.16

    for idx, (b_title, b_desc) in enumerate(blocks):
        top_pos = top_start + idx * (block_h + gap)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.80), Inches(top_pos), Inches(11.73), Inches(block_h))
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_WHITE
        box.line.color.rgb = COLOR_BLACK
        box.line.width = Pt(1.5)

        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.20)
        tf.margin_top = Inches(0.08)
        p = tf.paragraphs[0]
        r1 = p.add_run()
        set_run(r1, f"{idx+1}. {b_title}: ", size_pt=18, bold=True, color=COLOR_BLACK)
        r2 = p.add_run()
        bold_desc = True if "MPPI" in b_desc else False
        set_run(r2, b_desc, size_pt=18, bold=bold_desc, color=COLOR_BLACK)

        if idx < len(blocks) - 1:
            arrow = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(6.50), Inches(top_pos + block_h), Inches(0.33), Inches(gap))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = COLOR_BLACK
            arrow.line.fill.background()


def build_slide15_endocrine(slide):
    """Rebuilds Slide 15 emphasizing Endocrine Modulation with 2 clean structured cards."""
    shapes_to_delete = []
    for sh in slide.shapes:
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    tb_t = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, "COMPLETE CONTROL LOOP & ENDOCRINE MODULATION PATHWAYS", size_pt=24, bold=True, color=COLOR_BLACK)
    p2 = tf_t.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, "Dynamic Neuromodulatory Kinetics & Deliberative Gain Control [Stages 1.4 & 3.5]", size_pt=18, italic=True, color=COLOR_MUTED)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    # Left Card: Hormone Kinetics
    hormone_items = [
        "Dopamine (DA): Encodes appetitive reward expectation; promotes forward goal-seeking persistence.",
        "Norepinephrine (NE): Modulates exploration noise scale (σ) and vigilance under sensory uncertainty.",
        "Serotonin (5-HT): Sets temporal discounting horizon and motor behavioral inhibition.",
        "Cortisol: Emergency stress hormone; contracts safe obstacle clearance margins under threat."
    ]
    add_card_box(slide, Inches(0.80), Inches(1.45), Inches(5.75), Inches(5.15),
                 "Neuromodulatory Hormone Kinetics",
                 "Four Circulating Virtual Hormones Regulating Cognitive Modes",
                 hormone_items)

    # Right Card: Deliberation & Safety Coupling
    coupling_items = [
        "Online Gain Adaptation: Hormone concentrations dynamically scale MPPI exploration temperature λ.",
        "Stress-Gated Precision: High Cortisol tightens swept-cone safety margins in hazardous regimes.",
        "Sensorimotor Grounding: Chemical kinetics are grounded in physical topological constraints.",
        "Deterministic Homeostasis: Closed-loop synthesis and decay stabilize long-horizon behavior."
    ]
    add_card_box(slide, Inches(6.78), Inches(1.45), Inches(5.75), Inches(5.15),
                 "Deliberation & Safety Coupling",
                 "Hierarchical Integration with Continuous Action Optimization",
                 coupling_items)


def build_slide17_reflex(slide):
    """Rebuilds Slide 17 (final Slide 16) communicating Spiking Reflex Safety Override."""
    shapes_to_delete = []
    for sh in slide.shapes:
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    tb_t = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, "CONTROL LOGIC FLOW: REFLEX MODE", size_pt=24, bold=True, color=COLOR_BLACK)
    p2 = tf_t.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, "Sub-Millisecond Spiking Neural Network (LIF) Emergency Pre-emption", size_pt=18, italic=True, color=COLOR_MUTED)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    steps = [
        ("1. Hazard Detection", "Near-field ultrasonic sensors detect imminent obstacle violation (distance d ≤ 0.15 m)."),
        ("2. SNN Spiking Reflex", "Sub-millisecond Leaky Integrate-and-Fire (LIF) reflex layer fires emergency burst (< 1.0 ms)."),
        ("3. Motor Pre-emption", "Direct motor mixer pre-empts cognitive deliberation and executes decisive aversive repulsion.")
    ]

    top_start = 1.45
    box_w = Inches(3.60)
    box_h = Inches(2.20)
    gap = Inches(0.66)

    for idx, (st_title, st_desc) in enumerate(steps):
        left_pos = Inches(0.60) + idx * (box_w + gap)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(top_start), box_w, box_h)
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_WHITE
        box.line.color.rgb = COLOR_BLACK
        box.line.width = Pt(1.5)

        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.18)
        tf.margin_right = Inches(0.18)
        tf.margin_top = Inches(0.18)

        p = tf.paragraphs[0]
        r1 = p.add_run()
        set_run(r1, st_title + "\n", size_pt=20, bold=True, color=COLOR_BLACK)

        p2 = tf.add_paragraph()
        p2.space_before = Pt(8)
        r2 = p2.add_run()
        set_run(r2, st_desc, size_pt=18, bold=False, color=COLOR_BLACK)

        if idx < len(steps) - 1:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left_pos + box_w + Inches(0.15), Inches(top_start + 0.85), Inches(0.36), Inches(0.45))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = COLOR_BLACK
            arrow.line.fill.background()

    safety_items = [
        "Zero Cognitive Delay: Bypasses MPPI optimization and world model rollouts when safety margins are breached.",
        "Asymmetric Repulsion: SNN generates maximum angular velocity away from the closest detected obstacle vector.",
        "Verified Invariant: Over 150 physical challenge trials executed with 0.00% uncontrolled collisions."
    ]
    add_card_box(slide, Inches(0.60), Inches(3.95), Inches(12.13), Inches(2.65),
                 "Key Safety Properties of the Spiking Reflex Architecture",
                 "Autonomous Pre-emptive Safety Guarantee",
                 safety_items)


def build_slide18_roadmap(slide):
    """Replaces Slide 18 (final Slide 17) with the 5-Stage Developmental Architecture blocks + historical note."""
    shapes_to_delete = []
    for sh in slide.shapes:
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    tb_t = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, "CARL DEVELOPMENTAL ROADMAP — 5-STAGE ARCHITECTURE", size_pt=24, bold=True, color=COLOR_BLACK)
    p2 = tf_t.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, "Sequential Developmental Progression from Sensorimotor Grounding to Metacognition", size_pt=18, italic=True, color=COLOR_MUTED)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    stages = [
        ("Stage 1", "Sensorimotor Grounding & Body Babbling", "Learn My Body", "COMPLETED & CERTIFIED ✅"),
        ("Stage 2", "Generative World & Self Modeling", "Learn My World", "COMPLETED & CERTIFIED ✅"),
        ("Stage 3", "Continuous Action Synthesis & Behavioral Discovery", "Learn How to Behave", "CURRENT ACTIVE MILESTONE ⏳"),
        ("Stage 4", "Autopoietic / Lifelong Memory & Persistence", "Remember & Develop", "FUTURE MILESTONE 🔮"),
        ("Stage 5", "Metacognition & Permission-Gated Self-Modification", "Understand Myself & Improve", "FINAL MATURITY 🔮")
    ]

    top_start = 1.45
    block_h = 0.85
    gap = 0.15

    for idx, (st_num, st_name, st_theme, st_status) in enumerate(stages):
        top_pos = top_start + idx * (block_h + gap)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.80), Inches(top_pos), Inches(11.73), Inches(block_h))
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_WHITE
        box.line.color.rgb = COLOR_BLACK
        box.line.width = Pt(1.5)

        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.20)
        tf.margin_top = Inches(0.08)

        p = tf.paragraphs[0]
        r_num = p.add_run()
        set_run(r_num, f"{st_num} — {st_name} (\"{st_theme}\")\n", size_pt=18, bold=True, color=COLOR_BLACK)

        p_sub = tf.add_paragraph()
        r_stat = p_sub.add_run()
        set_run(r_stat, f"Status: {st_status}", size_pt=18, bold=True, color=COLOR_BLACK)

    tb_note = slide.shapes.add_textbox(Inches(0.80), Inches(6.50), Inches(11.73), Inches(0.40))
    p_note = tb_note.text_frame.paragraphs[0]
    p_note.alignment = PP_ALIGN.CENTER
    r_n = p_note.add_run()
    set_run(r_n, "Historical Note: Original development phases 0–8 were consolidated into the unified 5-stage architecture as the project matured.", size_pt=18, italic=True, color=COLOR_MUTED)


def build_slide19_stage1_foundation(slide):
    """Rebuilds Slide 19 (final Slide 18) as Stage 1 Sensorimotor Grounding & Body Babbling."""
    shapes_to_delete = []
    for sh in slide.shapes:
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    tb_t = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, "STAGE 1 — SENSORIMOTOR GROUNDING & BODY BABBLING", size_pt=24, bold=True, color=COLOR_BLACK)
    p2 = tf_t.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, "Embodied Sensorimotor Foundations & Baseline Qualification [Historical: Phase 0]", size_pt=18, italic=True, color=COLOR_MUTED)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    card_w = Inches(5.75)
    card_h = Inches(2.35)
    left1 = Inches(0.80)
    left2 = Inches(6.78)
    top1 = Inches(1.40)
    top2 = Inches(3.90)

    c1_items = [
        "MuJoCo 30 Hz Physics: Real-time closed-loop rigid-body simulation twin.",
        "Ground Traction Dynamics: Kinematic slip, wheel chatter, and friction response.",
        "Sensory Modalities: 12 ultrasonic sonar cones, 6-axis IMU, and odometry."
    ]
    add_card_box(slide, left1, top1, card_w, card_h,
                 "1. Embodied Digital Twin Environment",
                 "Physics Grounding & Sensorimotor Interface",
                 c1_items)

    c2_items = [
        "6-Channel Motor Babbling: Autonomous exploration discovering physical limits.",
        "Kinematic Characterization: Linear momentum and angular turn-rate mapping.",
        "Actuator Lag Identification: Discovered unmodeled drive dynamics."
    ]
    add_card_box(slide, left2, top1, card_w, card_h,
                 "2. Motor Babbling & Topology Discovery",
                 "Unsupervised Autonomous Sensorimotor Mapping",
                 c2_items)

    c3_items = [
        "Spiking Reflex Layer: LIF spiking network fires emergency burst (< 1.0 ms).",
        "3-Tier Recovery Machine: Deterministic progressive stuck recovery maneuvers.",
        "Operational Safety Veto: Swept-cone collision margin prevents impacts."
    ]
    add_card_box(slide, left1, top2, card_w, card_h,
                 "3. Reflex Architecture & Operational Safety",
                 "Sub-Millisecond Pre-emption & Stuck Recovery",
                 c3_items)

    c4_items = [
        "81/81 Benchmark Runs Cleared: 100% success across structured maze tasks.",
        "0.00% Uncontrolled Collisions: Zero impact events across all test fixtures.",
        "Permanent Regression Baseline: Locked SHA-256 baseline certified."
    ]
    add_card_box(slide, left2, top2, card_w, card_h,
                 "4. Qualification & Baseline Certification",
                 "Empirical Zero-Collision Verification Suite",
                 c4_items)

    tb_note = slide.shapes.add_textbox(Inches(0.80), Inches(6.45), Inches(11.73), Inches(0.40))
    p_n = tb_note.text_frame.paragraphs[0]
    p_n.alignment = PP_ALIGN.CENTER
    r_n = p_n.add_run()
    set_run(r_n, "Historical Note: Formerly designated Phase 0 in preliminary development; certified as Stage 1 substrate.", size_pt=18, italic=True, color=COLOR_MUTED)


def build_slide20_stage1_demo(slide):
    """Updates Slide 20 (final Slide 19) title to Stage 1 Live Demonstration."""
    for sh in slide.shapes:
        normalize_text_in_shape(sh)
        if sh.has_text_frame and "LIVE DEMONSTRATION" in sh.text_frame.text:
            tf = sh.text_frame
            p = tf.paragraphs[0]
            p.text = ""
            r = p.add_run()
            set_run(r, "STAGE 1 LIVE DEMONSTRATION [HISTORICAL: PHASE 0]", size_pt=24, bold=True, color=COLOR_BLACK)


def build_slide21_stage1_evidence(slide):
    """Updates Slide 21 (final Slide 20) title to Stage 1 Validation Evidence and adds callout."""
    for sh in slide.shapes:
        normalize_text_in_shape(sh)
        if sh.has_text_frame and "VALIDATION EVIDENCE" in sh.text_frame.text:
            tf = sh.text_frame
            p = tf.paragraphs[0]
            p.text = ""
            r = p.add_run()
            set_run(r, "STAGE 1 VALIDATION EVIDENCE [HISTORICAL: PHASE 0]", size_pt=24, bold=True, color=COLOR_BLACK)

    callout = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.80), Inches(5.85), Inches(11.73), Inches(0.75))
    callout.fill.solid()
    callout.fill.fore_color.rgb = COLOR_WHITE
    callout.line.color.rgb = COLOR_BLACK
    callout.line.width = Pt(1.5)

    tf = callout.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    set_run(r, "81/81 runs passed • 0 collisions • 0 uncontrolled recovery failures • STAGE 1 CERTIFIED [P0 COMPLETE]", size_pt=18, bold=True, color=COLOR_BLACK)


def build_slide23_stage1_1_adaptation(slide):
    """Rebuilds Slide 23 (final Slide 21) as Stage 1.1 Individual Emergence & Adaptive Learning."""
    shapes_to_delete = []
    for sh in slide.shapes:
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    tb_t = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, "STAGE 1.1 — INDIVIDUAL EMERGENCE & ADAPTIVE SENSORIMOTOR LEARNING", size_pt=24, bold=True, color=COLOR_BLACK)
    p2 = tf_t.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, "Experience-Driven Internal Adaptation Beyond Predefined Behaviors [Historical: Phase 1]", size_pt=18, italic=True, color=COLOR_MUTED)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    card_w = Inches(11.73)
    card_h = Inches(1.50)
    top_start = Inches(1.40)
    gap = Inches(0.18)

    c1_items = [
        "Adaptive Friction Mapping: Online tracking across surface transitions (μ ∈ [0.2, 1.0]).",
        "Chatter Detection: IMU and encoder divergence flags instantaneous loss of surface traction."
    ]
    add_card_box(slide, Inches(0.80), top_start, card_w, card_h,
                 "1. Dynamic Friction Gradient Adaptation",
                 "Online Slip Detection & Traction State Estimation",
                 c1_items)

    c2_items = [
        "Systematic Velocity Sweeps: Linear v ∈ [0.1, 0.5] m/s, angular ω ∈ [0.2, 1.5] rad/s.",
        "Boundary Mapping: Empirical stability envelope prevents dynamic rollover and skidding."
    ]
    add_card_box(slide, Inches(0.80), top_start + card_h + gap, card_w, card_h,
                 "2. Dynamical Stability Envelope Mapping",
                 "Safe Operating Boundary Discovery Across 150 Physical Trials",
                 c2_items)

    c3_items = [
        "Adaptive Plasticity: Agent modifies internal sensorimotor representations from experience.",
        "Physical Grounding: Verified on physical MuJoCo surfaces under dynamic friction drops."
    ]
    add_card_box(slide, Inches(0.80), top_start + (card_h + gap) * 2, card_w, card_h,
                 "3. Emergent Individual Adaptation Outcome",
                 "Transition from Static Control to Experience-Driven Plasticity",
                 c3_items)

    tb_note = slide.shapes.add_textbox(Inches(0.80), Inches(6.45), Inches(11.73), Inches(0.40))
    p_n = tb_note.text_frame.paragraphs[0]
    p_n.alignment = PP_ALIGN.CENTER
    r_n = p_n.add_run()
    set_run(r_n, "Historical Note: Formerly designated Phase 1 in preliminary development; certified as Stage 1.1 substrate.", size_pt=18, italic=True, color=COLOR_MUTED)


def build_slide27_stage2_spatial(slide):
    """Rebuilds Slide 27 (final Slide 25) as Stage 2 Generative World & Self Modeling."""
    shapes_to_delete = []
    for sh in slide.shapes:
        shapes_to_delete.append(sh)
    for sh in shapes_to_delete:
        sp = sh._element
        sp.getparent().remove(sp)

    tb_t = slide.shapes.add_textbox(Inches(0.60), Inches(0.35), Inches(12.13), Inches(0.80))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    r1 = p1.add_run()
    set_run(r1, "STAGE 2 — GENERATIVE WORLD & SELF MODELING", size_pt=24, bold=True, color=COLOR_BLACK)
    p2 = tf_t.add_paragraph()
    r2 = p2.add_run()
    set_run(r2, "Internal Spatial Representations & Prospective Deliberation Substrate [Historical: Phase 2]", size_pt=18, italic=True, color=COLOR_MUTED)

    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_BLACK
    line.line.fill.background()

    card_w = Inches(5.75)
    card_h = Inches(2.35)
    left1 = Inches(0.80)
    left2 = Inches(6.78)
    top1 = Inches(1.40)
    top2 = Inches(3.90)

    c1_items = [
        "64-HD Attractor Ring: Continuous attractor network tracking heading angle.",
        "1,024-Grid Cell Torus: 2D spatial periodic representation for path integration.",
        "LSM Reservoir Coupling: 500-neuron recurrent network provides temporal memory."
    ]
    add_card_box(slide, left1, top1, card_w, card_h,
                 "1. 2,114-Unit Spatial Attractor Networks",
                 "Grounded Head Direction & Grid Space Representation",
                 c1_items)

    c2_items = [
        "1-Step Dynamics Model: Grounded predictive forward model with R² = 0.97.",
        "Sensory Anticipation: Predicts next-step sonar readings and collision boundaries.",
        "Counterfactual Rollouts: Simulates prospective branch trajectories in real time."
    ]
    add_card_box(slide, left2, top1, card_w, card_h,
                 "2. Decoupled Generative World Model",
                 "Prospective Forward Dynamics Simulation (R² = 0.97)",
                 c2_items)

    c3_items = [
        "Allocentric Raster Grid: 2D occupancy memory persisting obstacle locations.",
        "Ray-Traced Shadow Casting: Eliminates phantom updates behind solid geometry.",
        "Temporal Occlusion Persistence: Retains obstacle bounds when sensors look away."
    ]
    add_card_box(slide, left1, top2, card_w, card_h,
                 "3. Allocentric Occupancy Memory",
                 "2D Spatial Memory Grid with Shadow Casting",
                 c3_items)

    c4_items = [
        "Prospective Trajectory Evaluation: Continuous swept-cone collision evaluation.",
        "Scope-Bounded Certified: 40/40 challenge mazes cleared with 0.00% collisions.",
        "Stage 3 Carryover: CANN causal coupling & memory necessity proven in Stage 3."
    ]
    add_card_box(slide, left2, top2, card_w, card_h,
                 "4. Deliberation Substrate Certification",
                 "Scope-Bounded Acceptance Suite: 40/40 Mazes Cleared",
                 c4_items)

    tb_note = slide.shapes.add_textbox(Inches(0.80), Inches(6.45), Inches(11.73), Inches(0.40))
    p_n = tb_note.text_frame.paragraphs[0]
    p_n.alignment = PP_ALIGN.CENTER
    r_n = p_n.add_run()
    set_run(r_n, "Historical Note: Formerly designated Phase 2 in preliminary development; certified as Stage 2 substrate.", size_pt=18, italic=True, color=COLOR_MUTED)


def build_slide28_seven_gates_table(slide):
    """Explicitly populates Slide 28 Seven-Gate table with exact canonical metrics."""
    gate_data = [
        ("Gate 1: Body Proprioception", "Forward Velocity (v) R²", "≥ 0.90", "R² = 0.9613", "PASS"),
        ("Gate 2: Angular Gyroscope", "Rotational Velocity (ω) R²", "≥ 0.80", "R² = 0.8466", "PASS"),
        ("Gate 3: Dynamic Sonar Range", "Virtual Rays Range R²", "≥ 0.50", "R² = 0.5377", "PASS"),
        ("Gate 4: Collision Prediction", "Imminent Contact ROC-AUC", "≥ 0.90", "ROC-AUC = 0.995", "PASS"),
        ("Gate 5: Multi-Step Stability", "5-Step Rollout Drift", "< 15.0%", "Drift = 8.18%", "PASS"),
        ("Gate 6: Causal Sensitivity", "Action Intervention Δ", "> 0.35", "Δ = 0.442", "PASS"),
        ("Gate 7: Compute Latency", "Inference Cycle Time", "≤ 10.0 ms", "2.12 ms", "PASS"),
    ]
    for sh in slide.shapes:
        if sh.has_table and len(sh.table.rows) == 8:
            tbl = sh.table
            for r_idx, row in enumerate(gate_data):
                for c_idx, val in enumerate(row):
                    cell = tbl.cell(r_idx + 1, c_idx)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = COLOR_WHITE
                    set_plain_cell_border(cell, color="000000", width="12700")
                    tf = cell.text_frame
                    tf.word_wrap = True
                    p = tf.paragraphs[0]
                    p.text = ""
                    r = p.add_run()
                    bold = (c_idx == 4 or "R²" in val or "ROC" in val or "Drift" in val)
                    set_run(r, val, size_pt=18, bold=bold, color=COLOR_BLACK)
                    if c_idx in [0, 4] or len(val) <= 12:
                        p.alignment = PP_ALIGN.CENTER
                    else:
                        p.alignment = PP_ALIGN.LEFT


def delete_slide(prs, index):
    """Cleanly deletes a slide from presentation by index and drops XML relation."""
    sldId = prs.slides._sldIdLst[index]
    rId = sldId.rId
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[index]


def build_final_deck():
    print(f"Loading presentation from: {SRC_PPTX}")
    prs = pptx.Presentation(SRC_PPTX)
    print(f"Original slide count: {len(prs.slides)}")

    # 1. Update Slide 14 (Primary Architecture)
    print("Rebuilding Slide 14 (Primary Architecture Pipeline)...")
    build_slide14_architecture(prs.slides[13])

    # 2. Update Slide 15 (Endocrine Modulation)
    print("Rebuilding Slide 15 (Endocrine Modulation)...")
    build_slide15_endocrine(prs.slides[14])

    # 3. Update Slide 17 (Reflex Mode)
    print("Rebuilding Slide 17 (Reflex Mode Safety Override)...")
    build_slide17_reflex(prs.slides[16])

    # 4. Update Slide 18 (5-Stage Roadmap)
    print("Rebuilding Slide 18 (5-Stage Roadmap)...")
    build_slide18_roadmap(prs.slides[17])

    # 5. Update Slide 19 (Stage 1 Sensorimotor Grounding & Body Babbling - former Phase 0)
    print("Rebuilding Slide 19 (Stage 1 Sensorimotor Grounding & Body Babbling)...")
    build_slide19_stage1_foundation(prs.slides[18])

    # 6. Update Slide 20 (Stage 1 Live Demonstration)
    print("Updating Slide 20 (Stage 1 Live Demonstration)...")
    build_slide20_stage1_demo(prs.slides[19])

    # 7. Update Slide 21 (Stage 1 Validation Evidence + Callout)
    print("Updating Slide 21 (Stage 1 Validation Evidence + Callout)...")
    build_slide21_stage1_evidence(prs.slides[20])

    # 8. Update Slide 23 (Stage 1.1 Individual Emergence - former Phase 1)
    print("Rebuilding Slide 23 (Stage 1.1 Individual Emergence & Adaptive Learning)...")
    build_slide23_stage1_1_adaptation(prs.slides[22])

    # 9. Update Slide 27 (Stage 2 Generative World & Self Modeling - former Phase 2)
    print("Rebuilding Slide 27 (Stage 2 Generative World & Self Modeling)...")
    build_slide27_stage2_spatial(prs.slides[26])

    # 10. Update Slide 28 Seven-Gate Table (former Slide 30, index 29)
    print("Populating Slide 28 (Predictive World Model 7-Gate Certification Table)...")
    build_slide28_seven_gates_table(prs.slides[29])

    # 6. Clean Deletions in Descending Order:
    # First delete everything from Slide 33 (index 32) to end of presentation:
    print("Deleting all old Stage 3 and legacy end slides (indices 32 onwards)...")
    for idx in range(len(prs.slides) - 1, 31, -1):
        delete_slide(prs, idx)

    # Delete slide 22 (index 21)
    print("Deleting redundant Slide 22 (P0 Evidence Duplicate)...")
    delete_slide(prs, 21)

    # Delete slide 16 (index 15)
    print("Deleting redundant Slide 16 (Normal Mode)...")
    delete_slide(prs, 15)

    print(f"Base slides cleanly retained: {len(prs.slides)} (Expected: exactly 30 slides, indices 0..29)")

    # 7. Normalize all base slides from 1 to 30 (indices 0..29)
    print("Normalizing typography and tables across base slides 1 to 30...")
    for idx in range(len(prs.slides)):
        s = prs.slides[idx]
        for sh in s.shapes:
            normalize_text_in_shape(sh)

    # Save to intermediate clean base presentation and reload to refresh package parts
    temp_base = REPO_ROOT / "temp_clean_base.pptx"
    prs.save(temp_base)
    prs = pptx.Presentation(temp_base)
    print(f"Reloaded clean base presentation! Current slides count: {len(prs.slides)}")

    # =========================================================================
    # RECONSTRUCT STAGE 3 HERO SECTION (SLIDES 31 to 41)
    # =========================================================================

    # -------------------------------------------------------------------------
    # SLIDE 31: STAGE 3 SECTION OVERVIEW
    # -------------------------------------------------------------------------
    s31 = create_standard_slide(prs, "STAGE 3 : CONTINUOUS ACTION SYNTHESIS & BEHAVIORAL DISCOVERY",
                                "Autonomous Deliberation, Continuous Trajectory Optimization & Active Inference")
    tb31 = s31.shapes.add_textbox(Inches(0.60), Inches(1.50), Inches(12.13), Inches(5.20))
    tf31 = tb31.text_frame
    tf31.word_wrap = True
    add_bullet_p(tf31, "Core Technical Capabilities Constructed in Stage 3:", size_pt=20, bold=True, space_after=10, bullet=False)
    add_bullet_p(tf31, "Pre-Flight Integrity (Stage 3.0): 100% clean AST anti-cheat scan guaranteeing zero simulator leaks.", size_pt=18, space_after=8)
    add_bullet_p(tf31, "CANN Causal Verification (Stage 3.1): 4-arm ablation battery proving 2,114-unit network causally drives actions.", size_pt=18, space_after=8)
    add_bullet_p(tf31, "Trajectory Fidelity (Stage 3.2): Air-gapped world model rollouts validated against MuJoCo physics steps (≤ 0.08 m error).", size_pt=18, space_after=8)
    add_bullet_p(tf31, "Memory Necessity (Stage 3.2): Proven strictly necessary across 5 non-line-of-sight task families (Δu = 0.47 divergence).", size_pt=18, space_after=8)
    add_bullet_p(tf31, "Continuous MPPI (Stage 3.3): 128 candidates evaluated across 15-step horizon at 30 Hz (Mean 1.36 ms latency).", size_pt=18, space_after=8)
    add_bullet_p(tf31, "Active Inference (Stage 3.4): Expected Free Energy (Pragmatic + Epistemic) driving autonomous behavioral discovery.", size_pt=18, space_after=8)
    add_bullet_p(tf31, "Scientific Integrity: Zero-tolerance governance, permanent fail-closed records, and unprivileged forensic remediation.", size_pt=18, space_after=8)

    # -------------------------------------------------------------------------
    # SLIDE 32: STAGE 3.0 PRE-FLIGHT INTEGRITY (NATIVE POWERPOINT TABLE)
    # -------------------------------------------------------------------------
    s32 = create_standard_slide(prs, "STAGE 3.0 PRE-FLIGHT INTEGRITY & DECISION PIPELINE HYGIENE",
                                "Zero-Simulator-Coordinate Anti-Cheat Enforcement & Code Hygiene Verification")

    tb_cap32 = s32.shapes.add_textbox(Inches(0.60), Inches(1.35), Inches(12.13), Inches(0.40))
    r_cap32 = tb_cap32.text_frame.paragraphs[0].add_run()
    set_run(r_cap32, "Table 1. Stage 3.0 Pre-Flight Anti-Cheat AST Isolation Scan Results", size_pt=18, bold=True)

    headers_32 = ["Target Module", "Examined Pipeline", "Prohibited AST Nodes", "Detected Leaks", "Integrity Verdict"]
    rows_32 = [
        ["carl_autonomous_agent.py", "Cognitive Decision Loop", "qpos, qvel, geom_xpos, mj_ray", "0 Leaks", "PASS ✅"],
        ["carl_mppi_deliberation.py", "Trajectory Optimization", "qpos, qvel, geom_xpos, mj_ray", "0 Leaks", "PASS ✅"],
        ["carl_grid_space_ring.py", "Spatial Memory Torus", "qpos, qvel, geom_xpos, mj_ray", "0 Leaks", "PASS ✅"],
        ["carl_cann_attractor.py", "Heading Ring Attractor", "qpos, qvel, geom_xpos, mj_ray", "0 Leaks", "PASS ✅"],
        ["carl_embodied_organism.py", "Embodied Action Synthesizer", "qpos, qvel, geom_xpos, mj_ray", "0 Leaks", "PASS ✅"]
    ]
    col_w_32 = [Inches(2.8), Inches(2.6), Inches(3.2), Inches(1.8), Inches(1.73)]
    add_plain_table(s32, Inches(0.60), Inches(1.80), Inches(12.13), Inches(3.60), headers_32, rows_32, col_w_32, font_size=18)

    tb32_b = s32.shapes.add_textbox(Inches(0.60), Inches(5.60), Inches(12.13), Inches(1.40))
    tf32_b = tb32_b.text_frame
    tf32_b.word_wrap = True
    add_bullet_p(tf32_b, "Decision-Pipeline Isolation: Prohibits simulator coordinates from leaking into cognitive decisions.", size_pt=18, space_after=6)
    add_bullet_p(tf32_b, "Physical Grounding: Agent perceives world strictly through emulated noisy sonars, camera, and odometry.", size_pt=18, space_after=6)

    # -------------------------------------------------------------------------
    # SLIDE 33: STAGE 3.1 CANN CAUSAL ABLATION (2 SINGLE PLOTS)
    # -------------------------------------------------------------------------
    s33 = create_standard_slide(prs, "STAGE 3.1 CANN CAUSAL ABLATION: ACTION DIVERGENCE & SAFETY",
                                "Stage 3.1-R Certified: Proving Neural Spatial System Causally Dictates Action")
    f33_left = S31_DIR / "plot1_stage3_1R_action_divergence.png"
    f33_right = S31_DIR / "plot3_stage3_1R_collision_rates.png"
    s33.shapes.add_picture(str(f33_left), Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.20))
    s33.shapes.add_picture(str(f33_right), Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.20))

    tb33_c1 = s33.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb33_c1.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 1. Action Divergence ||Δu|| Across Ablation Arms", size_pt=18, bold=True)

    tb33_c2 = s33.shapes.add_textbox(Inches(6.80), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb33_c2.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 2. Collision Rates: Intact vs Ablated Conditions", size_pt=18, bold=True)

    tb33_b = s33.shapes.add_textbox(Inches(0.60), Inches(5.25), Inches(12.13), Inches(1.60))
    tf33_b = tb33_b.text_frame
    tf33_b.word_wrap = True
    add_bullet_p(tf33_b, "Action Divergence: Zeroed CANN Δu = 0.563, Shuffled CANN Δu = 0.582 (Wilcoxon p < 10⁻¹⁶, d = 1.12).", size_pt=18, space_after=6)
    add_bullet_p(tf33_b, "Collision Increase: Intact baseline 4.0% vs Zeroed 31.0% (7.75× worse) and Shuffled 32.0% (8.0× worse).", size_pt=18, space_after=6)

    # -------------------------------------------------------------------------
    # SLIDE 34: STAGE 3.2 COUNTERFACTUAL TRAJECTORY FIDELITY (2 SINGLE PLOTS)
    # -------------------------------------------------------------------------
    s34 = create_standard_slide(prs, "STAGE 3.2 COUNTERFACTUAL TRAJECTORY FIDELITY VALIDATION",
                                "Stage 3.2-R Certified: Validating World Model Rollouts Against Physical MuJoCo Steps")
    f34_left = PLOTS_DIR / "fig_stage3_2_terminal_error.png"
    f34_right = PLOTS_DIR / "fig_stage3_2_path_rmse.png"
    s34.shapes.add_picture(str(f34_left), Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.20))
    s34.shapes.add_picture(str(f34_right), Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.20))

    tb34_c1 = s34.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb34_c1.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 3. Terminal Error by Profile (Threshold ≤ 0.080 m)", size_pt=18, bold=True)

    tb34_c2 = s34.shapes.add_textbox(Inches(6.80), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb34_c2.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 4. Path RMSE by Profile (Threshold ≤ 0.050 m)", size_pt=18, bold=True)

    tb34_b = s34.shapes.add_textbox(Inches(0.60), Inches(5.25), Inches(12.13), Inches(1.60))
    tf34_b = tb34_b.text_frame
    tf34_b.word_wrap = True
    add_bullet_p(tf34_b, "Fidelity Certification: Rollouts closely match physical MuJoCo steps across 100% of tested profiles.", size_pt=18, space_after=6)
    add_bullet_p(tf34_b, "High Dynamic Precision: Mean terminal error = 0.048 m, Path RMSE = 0.024 m (both well below ceilings).", size_pt=18, space_after=6)

    # -------------------------------------------------------------------------
    # SLIDE 35: STAGE 3.2 SPATIAL MEMORY NECESSITY (2 SINGLE PLOTS)
    # -------------------------------------------------------------------------
    s35 = create_standard_slide(prs, "STAGE 3.2 SPATIAL MEMORY NECESSITY ACROSS 5 NON-LOS TASKS",
                                "Stage 3.2-R Certified: Proving Occupancy Memory Provides Information Unrecoverable from Sonar Alone")
    f35_left = PLOTS_DIR / "fig_stage3_2_success_by_arm.png"
    f35_right = PLOTS_DIR / "fig_stage3_2_action_divergence_hist.png"
    s35.shapes.add_picture(str(f35_left), Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.20))
    s35.shapes.add_picture(str(f35_right), Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.20))

    tb35_c1 = s35.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb35_c1.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 5. Task Family Success Rate Across Experimental Arms", size_pt=18, bold=True)

    tb35_c2 = s35.shapes.add_textbox(Inches(6.80), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb35_c2.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 6. Decision Divergence Under Identical Local Sonar", size_pt=18, bold=True)

    tb35_b = s35.shapes.add_textbox(Inches(0.60), Inches(5.25), Inches(12.13), Inches(1.60))
    tf35_b = tb35_b.text_frame
    tf35_b.word_wrap = True
    add_bullet_p(tf35_b, "Memory Necessity Proven: Intact Arm achieves 96% success vs 69% in Amnesic Arm (Δ = 27%, p < 10⁻¹²).", size_pt=18, space_after=6)
    add_bullet_p(tf35_b, "Action Divergence at T_crit: Mean ||Δu|| = 0.47 m/s under identical local sensor views.", size_pt=18, space_after=6)

    # -------------------------------------------------------------------------
    # SLIDE 36: STAGE 3.3 MPPI TRAJECTORY OPTIMIZATION (NATIVE TABLE)
    # -------------------------------------------------------------------------
    s36 = create_standard_slide(prs, "STAGE 3.3 MPPI CONTINUOUS TRAJECTORY SYNTHESIS CERTIFICATION",
                                "Stage 3.3 Certified: Model Predictive Path Integral 5-Gate Acceptance Battery")

    tb_cap36 = s36.shapes.add_textbox(Inches(0.60), Inches(1.35), Inches(12.13), Inches(0.40))
    r_cap36 = tb_cap36.text_frame.paragraphs[0].add_run()
    set_run(r_cap36, "Table 2. Stage 3.3 MPPI Trajectory Synthesis 5-Gate Certification Results", size_pt=18, bold=True)

    headers_36 = ["Gate", "Evaluation Metric", "Acceptance Threshold", "Measured Value", "Verdict"]
    rows_36 = [
        ["Gate 1", "Action Smoothness", "Mean ‖Δu‖ ≤ 0.35", "0.060", "PASS ✅"],
        ["Gate 2", "Cycle Latency", "Mean ≤ 20 ms, p95 ≤ 45 ms", "Mean 1.36 ms, p95 2.14 ms", "PASS ✅"],
        ["Gate 3", "Collision Reduction", "≥ 50% vs Discrete Stage 2", "50.0% (15.0% → 7.5%)", "PASS ✅"],
        ["Gate 4", "CANN Multi-Objective", "Spearman rank correlation ρ ≥ 0.30", "ρ = 0.34", "PASS ✅"],
        ["Gate 5", "AST Anti-Cheat Scan", "100% clean isolation scan", "100% Clean (0 Leaks)", "PASS ✅"]
    ]
    col_w_36 = [Inches(1.5), Inches(3.2), Inches(3.4), Inches(2.3), Inches(1.73)]
    add_plain_table(s36, Inches(0.60), Inches(1.80), Inches(12.13), Inches(4.30), headers_36, rows_36, col_w_36, font_size=18)

    tb36_f = s36.shapes.add_textbox(Inches(0.60), Inches(6.25), Inches(12.13), Inches(0.50))
    r = tb36_f.text_frame.paragraphs[0].add_run()
    set_run(r, "• Evaluates 128 rollouts over 15-step horizon (0.45 s) at 30 Hz with zero-copy shared memory.", size_pt=18, bold=False)

    # -------------------------------------------------------------------------
    # SLIDE 37: STAGE 3.3 MPPI PERFORMANCE & OBSTACLE NEGOTIATION (2 SINGLE PLOTS)
    # -------------------------------------------------------------------------
    s37 = create_standard_slide(prs, "STAGE 3.3 MPPI PERFORMANCE: CYCLE LATENCY & HULL CLEARANCE",
                                "Stage 3.3 Evidence: Real-Time Vectorized Trajectory Optimization & Physical Margin Gain")
    f37_left = PLOTS_DIR / "fig_stage3_3_cycle_latency.png"
    f37_right = PLOTS_DIR / "fig_stage3_3_hull_clearance.png"
    s37.shapes.add_picture(str(f37_left), Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.20))
    s37.shapes.add_picture(str(f37_right), Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.20))

    tb37_c1 = s37.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb37_c1.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 7. Vectorized Latency Distribution (p95 = 2.14 ms)", size_pt=18, bold=True)

    tb37_c2 = s37.shapes.add_textbox(Inches(6.80), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb37_c2.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 8. Mean Minimum Hull Clearance Margin Gain", size_pt=18, bold=True)

    tb37_b = s37.shapes.add_textbox(Inches(0.60), Inches(5.25), Inches(12.13), Inches(1.60))
    tf37_b = tb37_b.text_frame
    tf37_b.word_wrap = True
    add_bullet_p(tf37_b, "Real-Time Vectorized Execution: p95 latency of 2.14 ms consumes only 6.4% of the 33.3 ms budget.", size_pt=18, space_after=6)
    add_bullet_p(tf37_b, "Hull Margin Gain: +18.7% physical clearance gain (ΔC_hull = +0.0273 m) vs discrete action baseline.", size_pt=18, space_after=6)

    # -------------------------------------------------------------------------
    # SLIDE 38: STAGE 3.4 ACTIVE INFERENCE & EXPECTED FREE ENERGY
    # -------------------------------------------------------------------------
    s38 = create_standard_slide(prs, "AUTONOMOUS BEHAVIORAL DISCOVERY UNDER ACTIVE INFERENCE",
                                "Stage 3.4: Expected Free Energy Minimization (G = G_pragmatic + G_epistemic)")
    f38_plot = PLOTS_DIR / "fig_stage3_3_action_continuity.png"
    s38.shapes.add_picture(str(f38_plot), Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.20))

    tb38_c = s38.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb38_c.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 9. Action Continuity & Step Delta Distribution", size_pt=18, bold=True)

    tb38_r = s38.shapes.add_textbox(Inches(6.80), Inches(1.40), Inches(5.80), Inches(5.20))
    tf38_r = tb38_r.text_frame
    tf38_r.word_wrap = True
    add_bullet_p(tf38_r, "Expected Free Energy Formulation:", size_pt=20, bold=True, space_after=10, bullet=False)
    add_bullet_p(tf38_r, "G(π) = G_pragmatic(π) + G_epistemic(π)", size_pt=20, bold=True, space_after=12, bullet=False)
    add_bullet_p(tf38_r, "• Pragmatic Term: Maximizes wall clearance, enforces forward progress, and penalizes motor acceleration jerk.", size_pt=18, space_after=8, bullet=False)
    add_bullet_p(tf38_r, "• Epistemic Term: Information gain driving autonomous exploration into novel unvisited occupancy cells.", size_pt=18, space_after=8, bullet=False)
    add_bullet_p(tf38_r, "• Emergent Maneuvers: Multi-step reversals and pivot turns emerge naturally without handcoded rule tables.", size_pt=18, space_after=8, bullet=False)

    # -------------------------------------------------------------------------
    # SLIDE 39: STAGE 3.4-R3 200-EPISODE ADJUDICATION (HONEST FAIL-CLOSED RECORD)
    # -------------------------------------------------------------------------
    s39 = create_standard_slide(prs, "STAGE 3.4-R3: 200-EPISODE CERTIFICATION (FAIL-CLOSED RECORD)",
                                "Scientific Integrity: Pre-Registered Adjudication & Permanent Fail-Closed Documentation")

    tb_cap39 = s39.shapes.add_textbox(Inches(0.60), Inches(1.35), Inches(12.13), Inches(0.40))
    r_cap39 = tb_cap39.text_frame.paragraphs[0].add_run()
    set_run(r_cap39, "Table 3. Stage 3.4-R3 Pre-Registered 200-Episode Certification Battery Adjudication", size_pt=18, bold=True)

    headers_39 = ["Gate", "Evaluation Metric", "Acceptance Threshold", "Measured R3", "Verdict"]
    rows_39 = [
        ["Gate 1", "Autonomous Escape Rate", "ARM-A ≥ 80%, Collision ≤ 10%", "Escape 0%, Collision 18%", "FAIL ❌"],
        ["Gate 2", "Composite Sequence Rate", "≥ 75% complete sequence", "2.0% (1 of 50 trials)", "FAIL ❌"],
        ["Gate 3", "Epistemic Necessity", "Δ ≥ 40% (Env 2), p < 0.001", "Δ = 0.0%, p = 1.0", "FAIL ❌"],
        ["Gate 4", "Latency Budget", "Mean ≤ 20 ms, p95 ≤ 45 ms", "Mean 12.18 ms, p95 22.3 ms", "PASS ✅"],
        ["Gate 5", "AST Anti-Cheat Scan", "100% clean isolation scan", "7/7 Clean (0 Leaks)", "PASS ✅"]
    ]
    col_w_39 = [Inches(1.5), Inches(3.2), Inches(3.4), Inches(2.3), Inches(1.73)]
    add_plain_table(s39, Inches(0.60), Inches(1.80), Inches(12.13), Inches(4.30), headers_39, rows_39, col_w_39, font_size=18)

    tb39_f = s39.shapes.add_textbox(Inches(0.60), Inches(6.25), Inches(12.13), Inches(0.50))
    r = tb39_f.text_frame.paragraphs[0].add_run()
    set_run(r, "• Fail-Closed Governance: Failures permanently recorded; initiated forensic R4 root-cause analysis.", size_pt=18, bold=True)

    # -------------------------------------------------------------------------
    # SLIDE 40: STAGE 3.4-R4 FORENSIC ROOT CAUSE ANALYSIS (2 SINGLE PLOTS)
    # -------------------------------------------------------------------------
    s40 = create_standard_slide(prs, "FORENSIC ROOT-CAUSE: SONAR HEADING CORRUPTION AT JUNCTIONS",
                                "Stage 3.4-R4 Remediation: Diagnosing Phantom Sensor Returns & Corner Gating")
    f40_left = PLOTS_DIR / "fig_stage3_4_heading_error_config22.png"
    f40_right = PLOTS_DIR / "fig_stage3_4_heading_reduction_summary.png"
    s40.shapes.add_picture(str(f40_left), Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.20))
    s40.shapes.add_picture(str(f40_right), Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.20))

    tb40_c1 = s40.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb40_c1.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 10. Dynamic Heading Error: R4.1 vs R4.2 (Config 22)", size_pt=18, bold=True)

    tb40_c2 = s40.shapes.add_textbox(Inches(6.80), Inches(4.70), Inches(5.80), Inches(0.40))
    r = tb40_c2.text_frame.paragraphs[0].add_run()
    set_run(r, "Figure 11. Peak Heading Error Slashed Across Configs 20–24", size_pt=18, bold=True)

    tb40_b = s40.shapes.add_textbox(Inches(0.60), Inches(5.25), Inches(12.13), Inches(1.60))
    tf40_b = tb40_b.text_frame
    tf40_b.word_wrap = True
    add_bullet_p(tf40_b, "Root Cause Discovered: Perpendicular wall reflections generated phantom heading returns (31° to 61° error).", size_pt=18, space_after=6)
    add_bullet_p(tf40_b, "Unprivileged Remediation: Sonar validity gating slashes heading error by 35% to 60% without ground-truth cheats.", size_pt=18, space_after=6)

    # -------------------------------------------------------------------------
    # SLIDE 41: STAGE 3.4-R4.3 REMEDIATION SCREENING BENCHMARK (NATIVE TABLE)
    # -------------------------------------------------------------------------
    s41 = create_standard_slide(prs, "STAGE 3.4-R4.3: SCREENING BENCHMARK & PROGRESS",
                                "Active Remediation Results: 100% Env 1 Escape, 60% Env 2 Escape, 0% Collisions")

    tb_cap41 = s41.shapes.add_textbox(Inches(0.60), Inches(1.35), Inches(12.13), Inches(0.40))
    r_cap41 = tb_cap41.text_frame.paragraphs[0].add_run()
    set_run(r_cap41, "Table 4. Stage 3.4-R4.3 Diagnostic Screening Benchmark Across Test Mazes", size_pt=18, bold=True)

    headers_41 = ["Environment", "Maze Geometry", "Configs Tested", "Escape Rate", "Collision Rate", "Timeouts"]
    rows_41 = [
        ["Env 1", "L-Shaped Dead-End Corridor", "5 Configs (0–4)", "5/5 (100.0%)", "0/5 (0.0%)", "0/5 (0.0%)"],
        ["Env 2", "Asymmetric T-Junction Maze", "5 Configs (20–24)", "3/5 (60.0%)", "0/5 (0.0%)", "2/5 (40.0%)"]
    ]
    col_w_41 = [Inches(1.5), Inches(3.4), Inches(2.2), Inches(1.8), Inches(1.7), Inches(1.53)]
    add_plain_table(s41, Inches(0.60), Inches(1.80), Inches(12.13), Inches(2.60), headers_41, rows_41, col_w_41, font_size=18)

    tb41_b = s41.shapes.add_textbox(Inches(0.60), Inches(4.60), Inches(12.13), Inches(2.10))
    tf41_b = tb41_b.text_frame
    tf41_b.word_wrap = True
    add_bullet_p(tf41_b, "Progression Narrative: Slashed collision from 18% to 0.0%, achieved 100% escape in Env 1 and 60% in Env 2.", size_pt=18, space_after=8)
    add_bullet_p(tf41_b, "Active Subproblem: Rotational hull clearance at narrow (0.65 m) channel entries under geodesic repair.", size_pt=18, space_after=8)
    add_bullet_p(tf41_b, "Next Milestone: Geodesic gradient projection fix to achieve 100% escape across all configurations.", size_pt=18, space_after=8)

    # -------------------------------------------------------------------------
    # SLIDE 42: MASTER STATUS LEDGER (NATIVE TABLE)
    # -------------------------------------------------------------------------
    s42 = create_standard_slide(prs, "CARL MASTER STATUS LEDGER & VIVA COMPLIANCE",
                                "Comprehensive Verification Audit Across All Developmental Stages")

    tb_cap42 = s42.shapes.add_textbox(Inches(0.60), Inches(1.30), Inches(12.13), Inches(0.35))
    r_cap42 = tb_cap42.text_frame.paragraphs[0].add_run()
    set_run(r_cap42, "Table 5. Master Architecture Verification Status Across Stages 1 to 3", size_pt=18, bold=True)

    headers_42 = ["Stage", "Architectural Component", "Verification Metric", "Empirical Finding", "Viva Status"]
    rows_42 = [
        ["Stage 1", "MuJoCo 30 Hz Kinematics Twin", "Dynamical Stability", "Zero tip-over in 150 trials", "VALIDATED ✅"],
        ["Stage 1.1", "Traction & Slip Observer", "Slip vs Friction", "σ reaches 98.2% on ice", "VALIDATED ✅"],
        ["Stage 2A/B", "2,114-Unit CANN Attractor", "Homing Drift Gate", "Mean drift = 0.062 m", "VALIDATED ✅"],
        ["Stage 2.1", "7-Gate Predictive World Model", "Multi-Step Prediction", "7/7 Gates Passed (R²=0.96)", "VALIDATED ✅"],
        ["Stage 2.3", "Prospective Trajectory Veto", "40 Challenge Mazes", "40/40 Cleared, 0.0% Coll.", "CERTIFIED ✅"],
        ["Stage 3.0", "Decision-Pipeline Hygiene", "AST Anti-Cheat Scan", "7/7 Clean (0 Leaks)", "VALIDATED ✅"],
        ["Stage 3.1", "4-Arm CANN Ablation Battery", "Action Divergence Δu", "Δu = 0.56, p < 10⁻¹⁶", "VALIDATED ✅"],
        ["Stage 3.2", "5 Non-LOS Task Families", "Spatial Memory Necessity", "Δu = 0.47 Divergence Proven", "VALIDATED ✅"],
        ["Stage 3.3", "Continuous MPPI Trajectory", "Smoothness & Latency", "Δu = 0.060, p95 2.14 ms", "CERTIFIED ✅"],
        ["Stage 3.4", "Active Inference Discovery", "200-Episode Battery", "100% Env 1, Heading -59%", "ACTIVE ⏳"]
    ]
    col_w_42 = [Inches(1.5), Inches(3.2), Inches(2.5), Inches(3.2), Inches(1.73)]
    add_plain_table(s42, Inches(0.60), Inches(1.70), Inches(12.13), Inches(5.10), headers_42, rows_42, col_w_42, font_size=18)

    # -------------------------------------------------------------------------
    # SLIDE 43: WORK TO BE DONE
    # -------------------------------------------------------------------------
    s43 = create_standard_slide(prs, "WORK TO BE DONE & IMMEDIATE NEXT STEPS",
                                "Current Active Subproblems and Long-Term Developmental Roadmap")
    tb43 = s43.shapes.add_textbox(Inches(0.60), Inches(1.40), Inches(12.13), Inches(5.30))
    tf43 = tb43.text_frame
    tf43.word_wrap = True

    add_bullet_p(tf43, "Completed & Certified Milestones (Stages 1, 2, 3.0–3.3):", size_pt=20, bold=True, space_after=8, bullet=False)
    add_bullet_p(tf43, "• Stage 1 & 2: Embodied sensorimotor grounding, CANN spatial memory, and 7-gate world model.", size_pt=18, space_after=6, bullet=False)
    add_bullet_p(tf43, "• Stage 3.1 & 3.2: Formal proofs of CANN causal coupling (p < 10⁻¹⁶) and non-LOS memory necessity.", size_pt=18, space_after=6, bullet=False)
    add_bullet_p(tf43, "• Stage 3.3: MPPI continuous trajectory optimization certified (50% collision reduction, 2.14 ms latency).", size_pt=18, space_after=10, bullet=False)

    add_bullet_p(tf43, "Active & Immediate Next Steps (Stage 3.4–3.7):", size_pt=20, bold=True, space_after=8, bullet=False)
    add_bullet_p(tf43, "• Stage 3.4 Active: Resolve rotational hull clearance at narrow (0.65 m) channel entries for 100% escape.", size_pt=18, space_after=6, bullet=False)
    add_bullet_p(tf43, "• Stage 3.5: Physical perturbation adaptation (friction drops μ=0.2, torque loss, and wheel slip recovery).", size_pt=18, space_after=6, bullet=False)
    add_bullet_p(tf43, "• Stage 3.6: Behavioral synergy formation & Physarum plasmodial flow routing to prune dead-ends.", size_pt=18, space_after=10, bullet=False)

    add_bullet_p(tf43, "Long-Term Developmental Roadmap (Stages 4–5 & Hardware):", size_pt=20, bold=True, space_after=8, bullet=False)
    add_bullet_p(tf43, "• Stage 4: Autopoietic lifelong memory via online R-STDP synaptic plasticity & Holographic HDC vectors.", size_pt=18, space_after=6, bullet=False)
    add_bullet_p(tf43, "• Stage 5: Metacognitive self-reflection via \"The Witness\" (causal attribution & permission-gated self-modification).", size_pt=18, space_after=6, bullet=False)
    add_bullet_p(tf43, "• Hardware Transfer: Zero-shot sim-to-real transfer to Orange Pi 5 (6.0 TOPS) + ESP32 dual-board chassis.", size_pt=18, space_after=6, bullet=False)

    # -------------------------------------------------------------------------
    # SLIDE 44: REFERENCES PART 1
    # -------------------------------------------------------------------------
    s44 = create_standard_slide(prs, "KEY REFERENCES & THEORETICAL FOUNDATIONS (PART 1)",
                                "Peer-Reviewed Foundations: Neuromorphic Computing & Spatial Cognition")
    tb44 = s44.shapes.add_textbox(Inches(0.60), Inches(1.40), Inches(12.13), Inches(5.30))
    tf44 = tb44.text_frame
    tf44.word_wrap = True
    add_bullet_p(tf44, "1. Maass, W., Natschläger, T., & Markram, H. (2002). Real-time computing without stable states: A new framework for neural computation based on perturbations. Neural Computation, 14(11), 2531-2560.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf44, "2. Zhang, K. (1996). Representation of spatial orientation by the intrinsic dynamics of the head-direction cell system: a formation of continuous attractor networks. Journal of Neuroscience, 16(6), 2112-2126.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf44, "3. Fiete, I. R., Burak, Y., & Brookings, T. (2008). What grid cells convey about rat location. Journal of Neuroscience, 28(27), 6858-6871.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf44, "4. Friston, K. (2010). The free-energy principle: a unified brain theory?. Nature Reviews Neuroscience, 11(2), 127-138.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf44, "5. Williams, G., Aldrich, A., & Theodorou, E. (2017). Model predictive path integral control: Formulations, generalizations and applications. ICRA, IEEE.", size_pt=18, space_after=10, bullet=False)

    # -------------------------------------------------------------------------
    # SLIDE 45: REFERENCES PART 2
    # -------------------------------------------------------------------------
    s45 = create_standard_slide(prs, "KEY REFERENCES & THEORETICAL FOUNDATIONS (PART 2)",
                                "Peer-Reviewed Foundations: Active Inference, Motor Control & Validation")
    tb45 = s45.shapes.add_textbox(Inches(0.60), Inches(1.40), Inches(12.13), Inches(5.30))
    tf45 = tb45.text_frame
    tf45.word_wrap = True
    add_bullet_p(tf45, "6. Todorov, E., Erez, T., & Tassa, Y. (2012). MuJoCo: A physics engine for model-based control. In IEEE/RSJ IROS (pp. 5026-5033).", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf45, "7. Kanerva, P. (2009). Hyperdimensional computing: An introduction to computing in distributed representation with high-dimensional random vectors. Cognitive Computation, 1(2), 139-159.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf45, "8. Tero, A., Takagi, S., Saigusa, T., Ito, K., Bebber, D. P., Fricker, M. D., ... & Nakagaki, T. (2010). Rules for biologically inspired adaptive network design. Science, 327(5964), 439-442.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf45, "9. Bi, G. Q., & Poo, M. M. (1998). Synaptic modifications in cultured hippocampal neurons: dependence on spike timing and biophysical properties. Journal of Neuroscience, 18(24), 10464-10472.", size_pt=18, space_after=10, bullet=False)
    add_bullet_p(tf45, "10. Ha, D., & Schmidhuber, J. (2018). Recurrent world models facilitate policy evolution. Advances in Neural Information Processing Systems (NeurIPS), 31.", size_pt=18, space_after=10, bullet=False)

    # -------------------------------------------------------------------------
    # SLIDE 46: THANK YOU
    # -------------------------------------------------------------------------
    s46 = create_standard_slide(prs, "THANK YOU", "CARL-DX: Embodied Biomimetic Cognitive Architecture — Research Viva")
    tb46 = s46.shapes.add_textbox(Inches(0.60), Inches(2.20), Inches(12.13), Inches(3.50))
    tf46 = tb46.text_frame
    tf46.word_wrap = True
    p_th = tf46.paragraphs[0]
    p_th.alignment = PP_ALIGN.CENTER
    r_th1 = p_th.add_run()
    set_run(r_th1, "Questions & Discussion\n\n", size_pt=28, bold=True, color=COLOR_BLACK)

    p_th2 = tf46.add_paragraph()
    p_th2.alignment = PP_ALIGN.CENTER
    r_th2 = p_th2.add_run()
    set_run(r_th2, "CARL-DX: Continuous Action Synthesis & Autonomous Behavioral Discovery\n", size_pt=20, bold=True, color=COLOR_DARK)
    r_th3 = p_th2.add_run()
    set_run(r_th3, "Repository: https://github.com/Manassadashiv/EBCA\nCertified Substrates: Stages 1, 2, 3.0, 3.1, 3.2, 3.3 | Active: Stage 3.4", size_pt=18, italic=True, color=COLOR_MUTED)

    # =========================================================================
    # REGENERATE SLIDE NUMBERS ON ALL SLIDES (1..N)
    # =========================================================================
    total_slides = len(prs.slides)
    print(f"\nRegenerating sequential slide numbers across all {total_slides} slides...")
    for idx, slide in enumerate(prs.slides):
        slide_num = idx + 1
        num_shapes = []
        for sh in slide.shapes:
            if sh.has_text_frame:
                txt = sh.text_frame.text.strip()
                if txt.isdigit() and len(txt) <= 2:
                    num_shapes.append(sh)
                elif "Slide " in txt and len(txt) <= 10:
                    num_shapes.append(sh)
        for sh in num_shapes:
            sp = sh._element
            sp.getparent().remove(sp)

        num_box = slide.shapes.add_textbox(Inches(11.50), Inches(7.00), Inches(1.30), Inches(0.40))
        tf_num = num_box.text_frame
        p_num = tf_num.paragraphs[0]
        p_num.alignment = PP_ALIGN.RIGHT
        r_num = p_num.add_run()
        set_run(r_num, f"{slide_num}", size_pt=18, bold=True, color=COLOR_MUTED)

    # Final Strict Typography Enforcement Across All Slides
    print("Executing final strict typography enforcement across entire presentation...")
    for idx, slide in enumerate(prs.slides):
        for sh in slide.shapes:
            normalize_text_in_shape(sh)

    # Save to both locations
    print(f"\nSaving final presentation to: {OUT_PPTX_EBCA}")
    prs.save(OUT_PPTX_EBCA)
    print(f"Duplicating to: {OUT_PPTX_DROOT}")
    shutil.copy2(OUT_PPTX_EBCA, OUT_PPTX_DROOT)
    temp_base = REPO_ROOT / "temp_clean_base.pptx"
    if temp_base.exists():
        os.remove(temp_base)
    print(f"Presentation surgery completed successfully! Total Slides: {len(prs.slides)}")


if __name__ == "__main__":
    build_final_deck()
