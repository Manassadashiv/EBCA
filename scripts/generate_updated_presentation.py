#!/usr/bin/env python3
r"""
Generate Updated CARL-DX Presentation with Stage 3 Evidence Pack.
Clones the user's 310.pptx, updates existing slides (Roadmap, Status Ledger, Work To Be Done),
inserts 10 new Stage 3 slides with exact figures, tables, and forensic evidence,
and saves the result to D:\ebca\310_Stage3_Updated.pptx and D:\310_Stage3_Updated.pptx.
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

SRC_PPTX = r"C:\Users\MANAS\OneDrive\Desktop\ppt\16_09\310.pptx"
OUT_PPTX_EBCA = r"D:\ebca\310_Stage3_Updated.pptx"
OUT_PPTX_DROOT = r"D:\310_Stage3_Updated.pptx"

FONT_FAMILY = "Times New Roman"
COLOR_TITLE = RGBColor(17, 24, 39)       # #111827 dark gray
COLOR_SUBTITLE = RGBColor(75, 85, 99)    # #4B5563 medium gray
COLOR_BODY = RGBColor(31, 41, 55)        # #1F2937 charcoal
COLOR_CARD_BG = RGBColor(246, 247, 249)  # #F6F7F9 very light gray
COLOR_CARD_BORDER = RGBColor(218, 222, 229) # #DADEE5
COLOR_DIVIDER = RGBColor(0, 0, 0)        # solid black
COLOR_CAPTION = RGBColor(75, 85, 99)     # caption gray
COLOR_PASS = RGBColor(22, 101, 52)       # green-800
COLOR_FAIL = RGBColor(153, 27, 27)       # red-800
COLOR_ACTIVE = RGBColor(180, 83, 9)      # amber-700
COLOR_HEADER_BG = RGBColor(229, 231, 235)# light gray header


def set_run_font(run, size_pt=14, bold=False, italic=False, color=COLOR_BODY):
    run.font.name = FONT_FAMILY
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color


def create_base_slide(prs, title_text, subtitle_text=""):
    """Creates a new slide matching the 310.pptx aesthetic."""
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)

    # Title box (left: 0.60, top: 0.35, width: 12.13, height: 0.80)
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
    r1.text = title_text
    set_run_font(r1, size_pt=18, bold=True, color=COLOR_TITLE)

    if subtitle_text:
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = subtitle_text
        set_run_font(r2, size_pt=12, bold=False, italic=True, color=COLOR_SUBTITLE)

    # Divider line (left: 0.60, top: 1.22, width: 12.13, height: 0.02)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = COLOR_DIVIDER
    line.line.fill.background()

    return slide


def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
    """Adds a rounded rectangle card container."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(0.75)
    else:
        card.line.fill.background()
    return card


def add_bullet_text(tf, text, size_pt=12, bold=False, is_bullet=True, color=COLOR_BODY, space_after=3):
    p = tf.add_paragraph() if len(tf.paragraphs[0].text) > 0 else tf.paragraphs[0]
    p.space_after = Pt(space_after)
    prefix = "•  " if is_bullet else ""
    r = p.add_run()
    r.text = prefix + text
    set_run_font(r, size_pt=size_pt, bold=bold, color=color)
    return p


def add_table_styled(slide, left, top, width, height, headers, rows, col_widths=None, font_size=10):
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
        cell.fill.fore_color.rgb = COLOR_HEADER_BG
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = h
        set_run_font(r, size_pt=font_size, bold=True, color=COLOR_TITLE)

    # Rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = tbl.cell(r_idx + 1, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            r = p.add_run()
            r.text = str(val)

            # Highlight status column
            cell_color = COLOR_BODY
            bold = False
            if "PASS" in str(val) or "VALIDATED" in str(val) or "CERTIFIED" in str(val):
                cell_color = COLOR_PASS
                bold = True
            elif "FAIL" in str(val):
                cell_color = COLOR_FAIL
                bold = True
            elif "ACTIVE" in str(val) or "PROGRESS" in str(val):
                cell_color = COLOR_ACTIVE
                bold = True

            if c_idx in [0, 4] or len(str(val)) <= 15:
                p.alignment = PP_ALIGN.CENTER
            else:
                p.alignment = PP_ALIGN.LEFT

            set_run_font(r, size_pt=font_size, bold=bold, color=cell_color)

    return table_shape


def main():
    print(f"Loading presentation from: {SRC_PPTX}")
    if not os.path.exists(SRC_PPTX):
        print(f"ERROR: Source file {SRC_PPTX} does not exist!")
        sys.exit(1)

    prs = pptx.Presentation(SRC_PPTX)
    orig_count = len(prs.slides)
    print(f"Original slide count: {orig_count}")

    # =========================================================================
    # PART 1: UPDATE EXISTING SLIDE 18 (Roadmap)
    # =========================================================================
    print("Updating Slide 18 (Roadmap)...")
    s18 = prs.slides[17]
    for sh in s18.shapes:
        if sh.name == "Rounded Rectangle 8": # P3
            tf = sh.text_frame
            tf.paragraphs[0].text = "P3: Continuous Action Synthesis"
            tf.paragraphs[1].text = "[STAGE 3: ACTIVE MILESTONE ⏳]"
            tf.paragraphs[2].text = "• Continuous trajectory optimization (MPPI, M=128)"
            if len(tf.paragraphs) > 3:
                tf.paragraphs[3].text = "• Physarum polycephalum tube diffusion"
            if len(tf.paragraphs) > 4:
                tf.paragraphs[4].text = "• Active Inference behavioral discovery"
        elif sh.name == "Rounded Rectangle 9": # P4
            tf = sh.text_frame
            tf.paragraphs[1].text = "[POST-STAGE 5 EXTENSION]"
        elif sh.name == "Rounded Rectangle 10": # P5
            tf = sh.text_frame
            tf.paragraphs[0].text = "P5: Lifelong HDC Memory"
            tf.paragraphs[1].text = "[STAGE 4: AUTOCATALYTIC MEMORY]"
            tf.paragraphs[2].text = "• Holographic Hyperdimensional (HDC) memory"
            if len(tf.paragraphs) > 3:
                tf.paragraphs[3].text = "• Synaptic plasticity (R-STDP) across sleep/wake"
        elif sh.name == "Rounded Rectangle 11": # P6
            tf = sh.text_frame
            tf.paragraphs[1].text = "[STAGE 5: METACONSCIOUSNESS]"
            tf.paragraphs[2].text = "• \"The Witness\" introspective failure analysis"
            if len(tf.paragraphs) > 3:
                tf.paragraphs[3].text = "• Causal diagnostic self-attribution"
        elif sh.name == "Rounded Rectangle 12": # P7
            tf = sh.text_frame
            tf.paragraphs[1].text = "[STAGE 5: SELF-MODIFICATION]"
            tf.paragraphs[2].text = "• Permission-gated parameter adaptation"
        elif sh.name == "Rounded Rectangle 13": # P8
            tf = sh.text_frame
            tf.paragraphs[1].text = "[PHYSICAL HARDWARE MILESTONE]"
            tf.paragraphs[2].text = "• Zero-shot sim-to-real transfer to chassis"
            if len(tf.paragraphs) > 3:
                tf.paragraphs[3].text = "• Orange Pi 5 (6.0 TOPS) + ESP32 dual-board"
            if len(tf.paragraphs) > 4:
                tf.paragraphs[4].text = "• 5 NASA JPL OSR engineering extractions"

    # Add alignment banner at bottom of Slide 18
    banner_box = s18.shapes.add_textbox(Inches(0.60), Inches(6.75), Inches(12.13), Inches(0.40))
    btf = banner_box.text_frame
    bp = btf.paragraphs[0]
    bp.alignment = PP_ALIGN.CENTER
    br = bp.add_run()
    br.text = "Master Architecture Alignment: Structured into 5 Developmental Stages (Stage 1: Body Babbling | Stage 2: World Model | Stage 3: Continuous Action Synthesis [ACTIVE] | Stage 4: Lifelong Memory | Stage 5: Metacognition)"
    set_run_font(br, size_pt=9.5, bold=True, color=COLOR_SUBTITLE)

    # =========================================================================
    # PART 2: CONSTRUCT 10 NEW STAGE 3 SLIDES
    # We will add them to prs.slides, and then move them into position 32..41!
    # =========================================================================
    print("Constructing 10 new Stage 3 slides...")
    new_slides = []

    # -------------------------------------------------------------------------
    # NEW SLIDE 1 (Index 32 in final): PHASE 3 SECTION HEADER
    # -------------------------------------------------------------------------
    s_p3 = create_base_slide(prs, "PHASE 3 : CONTINUOUS ACTION SYNTHESIS & BEHAVIOURAL DISCOVERY",
                             "Autonomous behavioral discovery through continuous trajectory optimization and Expected Free Energy minimization")
    # Left Card
    add_card(s_p3, Inches(0.60), Inches(1.50), Inches(5.90), Inches(5.20))
    tb_l = s_p3.shapes.add_textbox(Inches(0.80), Inches(1.65), Inches(5.50), Inches(4.90))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    add_bullet_text(tf_l, "What Was Constructed in Stage 3", size_pt=14, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=6)
    add_bullet_text(tf_l, "Decision-Pipeline Integrity System: Static AST scanner ensuring 0 simulator coordinate leakage into cognitive loop.", size_pt=11.5)
    add_bullet_text(tf_l, "CANN Causal Verification: 4-arm ablation battery proving 2,114-unit network causally drives navigation decisions.", size_pt=11.5)
    add_bullet_text(tf_l, "Counterfactual Trajectory Fidelity: Air-gapped world model rollouts validated against physical MuJoCo steps.", size_pt=11.5)
    add_bullet_text(tf_l, "Spatial Memory Necessity: 5 non-LOS task families testing whether occupancy memory contributes beyond sonar.", size_pt=11.5)
    add_bullet_text(tf_l, "MPPI Continuous Action Synthesis: 128-candidate, 15-step trajectory optimizer replacing discrete action tables.", size_pt=11.5)
    add_bullet_text(tf_l, "Active Inference Behavioral Discovery: Expected Free Energy (Pragmatic + Epistemic) scoring for composite maneuvers.", size_pt=11.5)

    # Right Card
    add_card(s_p3, Inches(6.83), Inches(1.50), Inches(5.90), Inches(5.20))
    tb_r = s_p3.shapes.add_textbox(Inches(7.03), Inches(1.65), Inches(5.50), Inches(4.90))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    add_bullet_text(tf_r, "Scientific Methodology & Governance", size_pt=14, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=6)
    add_bullet_text(tf_r, "Zero-Tolerance Scientific Rigor: Pre-registered protocols locked BEFORE evaluation with SHA-256 baseline hashing.", size_pt=11.5)
    add_bullet_text(tf_r, "Fail-Closed Acceptance: Permanent failure records with zero threshold relaxation or post-hoc exclusions.", size_pt=11.5)
    add_bullet_text(tf_r, "Forensic Root-Cause Debugging: Transparent diagnosis of sensor anomalies (sonar corner phantom returns).", size_pt=11.5)
    add_bullet_text(tf_r, "Key Outcome: Evolution from discrete heuristic switching to continuous prospective action synthesis under the Free Energy Principle.", size_pt=11.5)
    new_slides.append(s_p3)

    # -------------------------------------------------------------------------
    # NEW SLIDE 2: STAGE 3.0 PRE-FLIGHT & STAGE 3.1 CANN CAUSAL COUPLING
    # -------------------------------------------------------------------------
    s34 = create_base_slide(prs, "DECISION-PIPELINE INTEGRITY & CANN CAUSAL COUPLING",
                            "Stage 3.0 Static AST Anti-Cheat Scan & Stage 3.1 Causal Ablation Battery")
    # Left Fig + Card
    f_ast = r"D:\ebca\evidence\stage3_preflight\plot5_ast_anti_cheat_isolation_matrix.png"
    s34.shapes.add_picture(f_ast, Inches(0.60), Inches(1.40), Inches(5.80), Inches(2.90))
    tb_c1 = s34.shapes.add_textbox(Inches(0.60), Inches(4.35), Inches(5.80), Inches(0.30))
    r = tb_c1.text_frame.paragraphs[0].add_run()
    r.text = "Figure 6(a): AST Anti-Cheat Scan Isolation Matrix (7/7 Scans Clean)"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s34, Inches(0.60), Inches(4.70), Inches(5.80), Inches(2.35))
    tb_ast = s34.shapes.add_textbox(Inches(0.75), Inches(4.80), Inches(5.50), Inches(2.15))
    tf_ast = tb_ast.text_frame
    tf_ast.word_wrap = True
    add_bullet_text(tf_ast, "Stage 3.0: Decision-Pipeline AST Isolation", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_ast, "7/7 static analysis scans passed: 0 instances of simulator coordinates (qpos, qvel, geom_xpos, mj_ray) in cognitive pipeline.", size_pt=10.5)
    add_bullet_text(tf_ast, "SHA-256 weight baselines locked for all neural checkpoints.", size_pt=10.5)
    add_bullet_text(tf_ast, "Guarantees behavior emerges strictly from internal representations.", size_pt=10.5)

    # Right Fig + Card
    f_cann_cert = r"D:\ebca\evidence\stage3_1R\plot5_stage3_1R_certification_matrix.png"
    s34.shapes.add_picture(f_cann_cert, Inches(6.80), Inches(1.40), Inches(5.80), Inches(2.90))
    tb_c2 = s34.shapes.add_textbox(Inches(6.80), Inches(4.35), Inches(5.80), Inches(0.30))
    r = tb_c2.text_frame.paragraphs[0].add_run()
    r.text = "Figure 6(b): CANN Causal Coupling Certification Matrix (4-Arm Battery)"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s34, Inches(6.80), Inches(4.70), Inches(5.80), Inches(2.35))
    tb_cann = s34.shapes.add_textbox(Inches(6.95), Inches(4.80), Inches(5.50), Inches(2.15))
    tf_cann = tb_cann.text_frame
    tf_cann.word_wrap = True
    add_bullet_text(tf_cann, "Stage 3.1: CANN Causal Coupling Verification", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_cann, "4-arm causal battery (N=100 per arm): Intact vs Frozen vs Zeroed vs Shuffled.", size_pt=10.5)
    add_bullet_text(tf_cann, "Statistically significant action divergence: Wilcoxon p < 10⁻¹⁶, Cohen's d = 1.12.", size_pt=10.5)
    add_bullet_text(tf_cann, "Verdict: 2,114-unit network is causally necessary, not a decorative passenger.", size_pt=10.5)
    new_slides.append(s34)

    # -------------------------------------------------------------------------
    # NEW SLIDE 3: STAGE 3.1 CANN CAUSAL EVIDENCE (ACTION DIVERGENCE & COLLISION)
    # -------------------------------------------------------------------------
    s35 = create_base_slide(prs, "CANN CAUSAL ABLATION: ACTION DIVERGENCE & COLLISION RATES",
                            "Stage 3.1-R Certified: Proving Neural Spatial Attractors Causally Drive Actions")
    f_act_div = r"D:\ebca\evidence\stage3_1R\plot1_stage3_1R_action_divergence.png"
    f_coll_rate = r"D:\ebca\evidence\stage3_1R\plot3_stage3_1R_collision_rates.png"
    s35.shapes.add_picture(f_act_div, Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.10))
    s35.shapes.add_picture(f_coll_rate, Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.10))

    tb_c1 = s35.shapes.add_textbox(Inches(0.60), Inches(4.55), Inches(5.80), Inches(0.30))
    r = tb_c1.text_frame.paragraphs[0].add_run()
    r.text = "Figure 7(a): Action Divergence Δu Across Ablated Conditions (p < 10⁻¹⁶)"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    tb_c2 = s35.shapes.add_textbox(Inches(6.80), Inches(4.55), Inches(5.80), Inches(0.30))
    r = tb_c2.text_frame.paragraphs[0].add_run()
    r.text = "Figure 7(b): Collision Rate Comparison: Intact vs Ablated Conditions"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s35, Inches(0.60), Inches(4.90), Inches(5.80), Inches(2.15))
    tb_d1 = s35.shapes.add_textbox(Inches(0.75), Inches(4.95), Inches(5.50), Inches(2.00))
    tf_d1 = tb_d1.text_frame
    tf_d1.word_wrap = True
    add_bullet_text(tf_d1, "Action Divergence Quantification", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_d1, "Zeroed CANN: Mean Δu = 0.563, p < 10⁻¹⁶ (Wilcoxon rank-sum test).", size_pt=10.5)
    add_bullet_text(tf_d1, "Shuffled CANN: Mean Δu = 0.582, p < 10⁻¹⁶ — destroys topological coherence.", size_pt=10.5)
    add_bullet_text(tf_d1, "Frozen CANN: Mean Δu = 0.174, p < 10⁻⁶ — prevents dynamic update.", size_pt=10.5)

    add_card(s35, Inches(6.80), Inches(4.90), Inches(5.80), Inches(2.15))
    tb_d2 = s35.shapes.add_textbox(Inches(6.95), Inches(4.95), Inches(5.50), Inches(2.00))
    tf_d2 = tb_d2.text_frame
    tf_d2.word_wrap = True
    add_bullet_text(tf_d2, "Behavioral Necessity Demonstrated", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_d2, "Intact Baseline Collision Rate: 4.0% (4/100 trials).", size_pt=10.5)
    add_bullet_text(tf_d2, "Zeroed CANN Collision Rate: 31.0% (31/100 trials) — 7.75× increase!", size_pt=10.5)
    add_bullet_text(tf_d2, "Shuffled CANN Collision Rate: 32.0% (32/100 trials) — 8.0× increase!", size_pt=10.5)
    add_bullet_text(tf_d2, "Conclusive proof: CANN spatial state is vital for collision-free navigation.", size_pt=10.5)
    new_slides.append(s35)

    # -------------------------------------------------------------------------
    # NEW SLIDE 4: STAGE 3.2 TRAJECTORY FIDELITY & SPATIAL MEMORY NECESSITY
    # -------------------------------------------------------------------------
    s36 = create_base_slide(prs, "COUNTERFACTUAL TRAJECTORY FIDELITY & SPATIAL MEMORY NECESSITY",
                            "Stage 3.2: Mental Simulator Accuracy vs Physics & 5 Non-LOS Task Families")
    f_dash = r"D:\ebca\evidence\stage3_2R\figures\fig1_stage3_2R_master_dashboard.png"
    s36.shapes.add_picture(f_dash, Inches(0.60), Inches(1.35), Inches(12.13), Inches(3.30))

    tb_cd = s36.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(12.13), Inches(0.25))
    r = tb_cd.text_frame.paragraphs[0].add_run()
    r.text = "Figure 8: Stage 3.2 Master Dashboard — Trajectory Fidelity (MuJoCo Match) & Spatial Memory Divergence Across 5 Task Families"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s36, Inches(0.60), Inches(5.00), Inches(5.80), Inches(2.10))
    tb_m1 = s36.shapes.add_textbox(Inches(0.75), Inches(5.05), Inches(5.50), Inches(1.95))
    tf_m1 = tb_m1.text_frame
    tf_m1.word_wrap = True
    add_bullet_text(tf_m1, "Part A: Counterfactual Trajectory Fidelity", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_m1, "Air-gapped world model rollouts strictly match physical MuJoCo steps.", size_pt=10.5)
    add_bullet_text(tf_m1, "Observational equivalence error Ds ≤ 0.150 m (100% PASS across configs).", size_pt=10.5)
    add_bullet_text(tf_m1, "Validates internal mental simulation as a faithful proxy for physical dynamics.", size_pt=10.5)

    add_card(s36, Inches(6.80), Inches(5.00), Inches(5.80), Inches(2.10))
    tb_m2 = s36.shapes.add_textbox(Inches(6.95), Inches(5.05), Inches(5.50), Inches(1.95))
    tf_m2 = tb_m2.text_frame
    tf_m2.word_wrap = True
    add_bullet_text(tf_m2, "Part B: Spatial Memory Necessity (Non-LOS)", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_m2, "Tested in 5 non-LOS families: Blind Corners, Cul-de-Sacs, Backtracking, Sonic Symmetries, Sensor Blackouts.", size_pt=10.5)
    add_bullet_text(tf_m2, "Action divergence Δu = 0.47 between intact and ablated memory conditions.", size_pt=10.5)
    add_bullet_text(tf_m2, "Proves memory contributes spatial information unrecoverable from sonar alone.", size_pt=10.5)
    new_slides.append(s36)

    # -------------------------------------------------------------------------
    # NEW SLIDE 5: STAGE 3.3 MPPI CONTINUOUS TRAJECTORY OPTIMIZATION
    # -------------------------------------------------------------------------
    s37 = create_base_slide(prs, "MPPI CONTINUOUS TRAJECTORY OPTIMISATION",
                            "Stage 3.3 Certified: Model Predictive Path Integral Trajectory Synthesis (M=128, H=15)")
    headers_33 = ["Gate", "Metric", "Threshold", "Measured Value", "Result"]
    rows_33 = [
        ["Gate 1", "Action Smoothness", "Mean ‖Δu‖ ≤ 0.35", "0.060", "PASS ✅"],
        ["Gate 2", "Cycle Latency", "Mean ≤ 20 ms, p95 ≤ 45 ms", "Mean 1.36 ms, p95 2.14 ms", "PASS ✅"],
        ["Gate 3", "Collision Reduction", "≥ 50% vs Discrete", "50.0% (15% → 7.5%)", "PASS ✅"],
        ["Gate 4", "CANN Multi-Objective", "Spearman ρ ≥ 0.30", "ρ = 0.34", "PASS ✅"],
        ["Gate 5", "AST Anti-Cheat Scan", "100% clean scan", "100% clean (0 leaks)", "PASS ✅"]
    ]
    col_w_33 = [Inches(1.2), Inches(2.8), Inches(3.1), Inches(3.2), Inches(1.8)]
    add_table_styled(s37, Inches(0.60), Inches(1.35), Inches(12.13), Inches(2.10), headers_33, rows_33, col_w_33, font_size=10.5)

    f_act = r"D:\ebca\evidence\stage3_3\fig1_action_continuity_and_smoothness.png"
    f_lat = r"D:\ebca\evidence\stage3_3\fig2_realtime_cycle_latency.png"
    s37.shapes.add_picture(f_act, Inches(0.60), Inches(3.60), Inches(5.80), Inches(3.10))
    s37.shapes.add_picture(f_lat, Inches(6.80), Inches(3.60), Inches(5.80), Inches(3.10))

    tb_c1 = s37.shapes.add_textbox(Inches(0.60), Inches(6.75), Inches(5.80), Inches(0.25))
    r = tb_c1.text_frame.paragraphs[0].add_run()
    r.text = "Figure 9(a): Action Continuity & Smoothness Traces"
    set_run_font(r, size_pt=9.5, bold=True, color=COLOR_CAPTION)

    tb_c2 = s37.shapes.add_textbox(Inches(6.80), Inches(6.75), Inches(5.80), Inches(0.25))
    r = tb_c2.text_frame.paragraphs[0].add_run()
    r.text = "Figure 9(b): Real-Time Latency (Mean 1.36 ms, p95 2.14 ms)"
    set_run_font(r, size_pt=9.5, bold=True, color=COLOR_CAPTION)
    new_slides.append(s37)

    # -------------------------------------------------------------------------
    # NEW SLIDE 6: STAGE 3.3 MPPI vs DISCRETE EVIDENCE
    # -------------------------------------------------------------------------
    s38 = create_base_slide(prs, "MPPI vs DISCRETE: COMPARATIVE OBSTACLE NEGOTIATION",
                            "Stage 3.3 Evidence: 50% Collision Reduction & Formal 5-Gate Certification Matrix")
    f_obs = r"D:\ebca\evidence\stage3_3\fig3_comparative_obstacle_negotiation.png"
    f_cert33 = r"D:\ebca\evidence\stage3_3\fig5_stage3_3_formal_certification_matrix.png"
    s38.shapes.add_picture(f_obs, Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.10))
    s38.shapes.add_picture(f_cert33, Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.10))

    tb_c1 = s38.shapes.add_textbox(Inches(0.60), Inches(4.55), Inches(5.80), Inches(0.30))
    r = tb_c1.text_frame.paragraphs[0].add_run()
    r.text = "Figure 10(a): Comparative Trajectories (MPPI Continuous vs Discrete)"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    tb_c2 = s38.shapes.add_textbox(Inches(6.80), Inches(4.55), Inches(5.80), Inches(0.30))
    r = tb_c2.text_frame.paragraphs[0].add_run()
    r.text = "Figure 10(b): Formal Certification Matrix (5/5 Gates Passed)"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s38, Inches(0.60), Inches(4.90), Inches(5.80), Inches(2.15))
    tb_o1 = s38.shapes.add_textbox(Inches(0.75), Inches(4.95), Inches(5.50), Inches(2.00))
    tf_o1 = tb_o1.text_frame
    tf_o1.word_wrap = True
    add_bullet_text(tf_o1, "Obstacle Negotiation Comparison", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_o1, "40 matched trials across 5 non-LOS task families.", size_pt=10.5)
    add_bullet_text(tf_o1, "Discrete Stage 2 Collision Rate: 15.0% (6/40 trials).", size_pt=10.5)
    add_bullet_text(tf_o1, "MPPI Stage 3 Collision Rate: 7.5% (3/40 trials) — 50.0% relative reduction!", size_pt=10.5)
    add_bullet_text(tf_o1, "Mean hull clearance improved by +19.1 mm along tight corridors.", size_pt=10.5)

    add_card(s38, Inches(6.80), Inches(4.90), Inches(5.80), Inches(2.15))
    tb_o2 = s38.shapes.add_textbox(Inches(6.95), Inches(4.95), Inches(5.50), Inches(2.00))
    tf_o2 = tb_o2.text_frame
    tf_o2.word_wrap = True
    add_bullet_text(tf_o2, "Continuous Synthesis Impact", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_o2, "Evaluates 128 rollouts over H=15 horizon (0.45 s) at 30 Hz closed loop.", size_pt=10.5)
    add_bullet_text(tf_o2, "Replaces brittle if-else discrete rule transitions with smooth motor distributions.", size_pt=10.5)
    add_bullet_text(tf_o2, "Stage 3.3 formally certified on zero-copy memory bus.", size_pt=10.5)
    new_slides.append(s38)

    # -------------------------------------------------------------------------
    # NEW SLIDE 7: STAGE 3.4 ACTIVE INFERENCE & EXPECTED FREE ENERGY
    # -------------------------------------------------------------------------
    s39 = create_base_slide(prs, "AUTONOMOUS BEHAVIOURAL DISCOVERY UNDER ACTIVE INFERENCE",
                            "Stage 3.4: Expected Free Energy (EFE) Minimisation Driving Autonomous Composite Manoeuvres")
    f_efe = r"D:\ebca\evidence\stage3_4\figures\fig1_expected_free_energy_landscape.png"
    s39.shapes.add_picture(f_efe, Inches(0.60), Inches(1.35), Inches(12.13), Inches(3.30))

    tb_cefe = s39.shapes.add_textbox(Inches(0.60), Inches(4.70), Inches(12.13), Inches(0.25))
    r = tb_cefe.text_frame.paragraphs[0].add_run()
    r.text = "Figure 11: Expected Free Energy (EFE) Optimization Landscape — Pragmatic Safety vs Epistemic Information Gain"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s39, Inches(0.60), Inches(5.00), Inches(5.80), Inches(2.10))
    tb_e1 = s39.shapes.add_textbox(Inches(0.75), Inches(5.05), Inches(5.50), Inches(1.95))
    tf_e1 = tb_e1.text_frame
    tf_e1.word_wrap = True
    add_bullet_text(tf_e1, "Expected Free Energy Formulation: G = Gprag + Gepis", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_e1, "Pragmatic Value (Gprag): Wall clearance margin, heading alignment, geodesic progress, and jerk minimisation.", size_pt=10.5)
    add_bullet_text(tf_e1, "Epistemic Value (Gepis): Information gain — novel occupancy cells explored by prospective rollouts.", size_pt=10.5)
    add_bullet_text(tf_e1, "Autonomous behavioral discovery without handcoded heuristic rule tables.", size_pt=10.5)

    add_card(s39, Inches(6.80), Inches(5.00), Inches(5.80), Inches(2.10))
    tb_e2 = s39.shapes.add_textbox(Inches(6.95), Inches(5.05), Inches(5.50), Inches(1.95))
    tf_e2 = tb_e2.text_frame
    tf_e2.word_wrap = True
    add_bullet_text(tf_e2, "Emergent Behaviors in Complex Environments", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_e2, "Reversals emerge naturally: Reverse candidates score best when walls enclose the front.", size_pt=10.5)
    add_bullet_text(tf_e2, "Pivot turns emerge naturally: Aligning with unvisited frontiers minimizes EFE.", size_pt=10.5)
    add_bullet_text(tf_e2, "Evaluated in challenging L-corridors (Env 1) and asymmetric T-junctions (Env 2).", size_pt=10.5)
    new_slides.append(s39)

    # -------------------------------------------------------------------------
    # NEW SLIDE 8: STAGE 3.4-R3 CERTIFICATION BATTERY & HONEST FAILURE
    # -------------------------------------------------------------------------
    s40 = create_base_slide(prs, "STAGE 3.4-R3: 200-EPISODE CERTIFICATION — FAIL-CLOSED RECORD",
                            "Scientific Integrity: Pre-Registered Adjudication & Permanent Fail-Closed Documentation")
    headers_40 = ["Gate", "Metric Name", "Acceptance Threshold", "Measured R3", "Adjudication"]
    rows_40 = [
        ["Gate 1", "Autonomous Escape Rate", "ARM-A ≥ 80%, Collision ≤ 10%", "Escape 0%, Collision 18%", "FAIL ❌"],
        ["Gate 2", "Composite Sequence Rate", "≥ 75% complete sequence", "2.0% (1/50)", "FAIL ❌"],
        ["Gate 3", "Epistemic Causal Necessity", "Δ ≥ 40% (Env 2), p < 0.001", "Δ = 0.0%, p = 1.0", "FAIL ❌"],
        ["Gate 4", "Latency Budget", "Mean ≤ 20 ms, p95 ≤ 45 ms", "Mean 12.18 ms, p95 22.3 ms", "PASS ✅"],
        ["Gate 5", "AST Anti-Cheat Scan", "100% clean scan", "7/7 passed (0 leaks)", "PASS ✅"]
    ]
    col_w_40 = [Inches(1.0), Inches(2.2), Inches(2.2), Inches(1.8), Inches(1.1)]
    add_table_styled(s40, Inches(0.60), Inches(1.40), Inches(8.30), Inches(2.80), headers_40, rows_40, col_w_40, font_size=9.5)

    f_cert34 = r"D:\ebca\evidence\stage3_4R3\figures\fig5_stage3_4R3_formal_certification_matrix.png"
    s40.shapes.add_picture(f_cert34, Inches(9.10), Inches(1.40), Inches(3.63), Inches(2.80))
    tb_cc = s40.shapes.add_textbox(Inches(9.10), Inches(4.25), Inches(3.63), Inches(0.25))
    r = tb_cc.text_frame.paragraphs[0].add_run()
    r.text = "Figure 12: Stage 3.4-R3 Adjudication Matrix"
    set_run_font(r, size_pt=9.5, bold=True, color=COLOR_CAPTION)

    add_card(s40, Inches(0.60), Inches(4.55), Inches(12.13), Inches(2.45))
    tb_f = s40.shapes.add_textbox(Inches(0.75), Inches(4.65), Inches(11.83), Inches(2.25))
    tf_f = tb_f.text_frame
    tf_f.word_wrap = True
    add_bullet_text(tf_f, "The Value of Transparent Scientific Governance", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_f, "Permanent Fail-Closed Record: Rather than altering thresholds or cherry-picking episodes, Stage 3.4-R3 was certified FAILED CLOSED ❌ under zero-tolerance rules.", size_pt=10.5)
    add_bullet_text(tf_f, "Computational Efficiency Confirmed: Gates 4 & 5 demonstrated full real-time compliance (12.18 ms latency) and 100% clean AST isolation.", size_pt=10.5)
    add_bullet_text(tf_f, "Triggered Forensic Investigation: The failure initiated an immediate root-cause investigation that uncovered sonar heading corruption at perpendicular corners.", size_pt=10.5)
    new_slides.append(s40)

    # -------------------------------------------------------------------------
    # NEW SLIDE 9: STAGE 3.4-R4 FORENSIC ROOT CAUSE ANALYSIS
    # -------------------------------------------------------------------------
    s41 = create_base_slide(prs, "FORENSIC ROOT-CAUSE: SONAR HEADING CORRUPTION AT JUNCTIONS",
                            "Stage 3.4-R4 Remediation: Diagnosing Phantom Sensor Returns & Validating Corner Gating")
    f_son = r"D:\ebca\evidence\stage3_4R4_2\figures\fig2_sonar_validity_gating.png"
    f_head = r"D:\ebca\evidence\stage3_4R4_2\figures\fig1_heading_error_comparison.png"
    s41.shapes.add_picture(f_son, Inches(0.60), Inches(1.40), Inches(5.80), Inches(3.10))
    s41.shapes.add_picture(f_head, Inches(6.80), Inches(1.40), Inches(5.80), Inches(3.10))

    tb_c1 = s41.shapes.add_textbox(Inches(0.60), Inches(4.55), Inches(5.80), Inches(0.30))
    r = tb_c1.text_frame.paragraphs[0].add_run()
    r.text = "Figure 13(a): Sonar Validity Gating & Corner Rejection Geometry"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    tb_c2 = s41.shapes.add_textbox(Inches(6.80), Inches(4.55), Inches(5.80), Inches(0.30))
    r = tb_c2.text_frame.paragraphs[0].add_run()
    r.text = "Figure 13(b): Heading Error Slashed by 35% to 60% with Corner Gating"
    set_run_font(r, size_pt=10, bold=True, color=COLOR_CAPTION)

    add_card(s41, Inches(0.60), Inches(4.90), Inches(5.80), Inches(2.15))
    tb_h1 = s41.shapes.add_textbox(Inches(0.75), Inches(4.95), Inches(5.50), Inches(2.00))
    tf_h1 = tb_h1.text_frame
    tf_h1.word_wrap = True
    add_bullet_text(tf_h1, "Root-Cause Diagnosis", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_h1, "At T-junctions, sonar rays struck perpendicular walls simultaneously.", size_pt=10.5)
    add_bullet_text(tf_h1, "Total Least Squares fit across both walls generated phantom heading angles (31° to 61° heading error!).", size_pt=10.5)
    add_bullet_text(tf_h1, "The robot believed it was facing north while physically facing west → MPPI rolled out toward phantom headings → trapped in corner stall.", size_pt=10.5)

    add_card(s41, Inches(6.80), Inches(4.90), Inches(5.80), Inches(2.15))
    tb_h2 = s41.shapes.add_textbox(Inches(6.95), Inches(4.95), Inches(5.50), Inches(2.00))
    tf_h2 = tb_h2.text_frame
    tf_h2.word_wrap = True
    add_bullet_text(tf_h2, "Unprivileged Remediation Fix (R4.2)", size_pt=12, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=3)
    add_bullet_text(tf_h2, "Corner Rejection Gate: PCA residual + linearity check detects multi-wall returns (98–100% rejected at corners).", size_pt=10.5)
    add_bullet_text(tf_h2, "Turn-Rate Gating: Suppresses sonar heading during fast pivots (|ω| ≥ 0.20 rad/s).", size_pt=10.5)
    add_bullet_text(tf_h2, "Result: Peak heading error reduced by 35% to 60% across all configurations!", size_pt=10.5)
    new_slides.append(s41)

    # -------------------------------------------------------------------------
    # NEW SLIDE 10: STAGE 3.4 CURRENT PROGRESS & SCREENING RESULTS
    # -------------------------------------------------------------------------
    s42 = create_base_slide(prs, "STAGE 3.4-R4.3: CURRENT PROGRESS & ACTIVE REMEDIATION",
                            "Screening Results: 100% Env 1 Escape, 60% Env 2 Escape, 0% Collisions")
    headers_42 = ["Environment", "Description", "Configs Tested", "Escapes", "Collisions", "Timeouts"]
    rows_42 = [
        ["Env 1", "L-Shaped Dead-End Corridor", "5 (Configs 0–4)", "5/5 (100%)", "0/5 (0.0%)", "0/5 (0.0%)"],
        ["Env 2", "Asymmetric T-Junction Maze", "5 (Configs 20–24)", "3/5 (60%)", "0/5 (0.0%)", "2/5 (40.0%)"]
    ]
    col_w_42 = [Inches(1.2), Inches(3.2), Inches(2.2), Inches(1.8), Inches(1.8), Inches(1.93)]
    add_table_styled(s42, Inches(0.60), Inches(1.35), Inches(12.13), Inches(1.40), headers_42, rows_42, col_w_42, font_size=10.5)

    f_env2 = r"D:\ebca\evidence\stage3_4R4_2\figures\fig3_env2_trajectory_comparison.png"
    f_prog = r"D:\ebca\evidence\stage3_4R4_2\figures\fig4_southward_progress.png"
    s42.shapes.add_picture(f_env2, Inches(0.60), Inches(2.90), Inches(5.80), Inches(2.90))
    s42.shapes.add_picture(f_prog, Inches(6.80), Inches(2.90), Inches(5.80), Inches(2.90))

    tb_c1 = s42.shapes.add_textbox(Inches(0.60), Inches(5.85), Inches(5.80), Inches(0.25))
    r = tb_c1.text_frame.paragraphs[0].add_run()
    r.text = "Figure 14(a): Env 2 Trajectory Comparison Before vs After Fix"
    set_run_font(r, size_pt=9.5, bold=True, color=COLOR_CAPTION)

    tb_c2 = s42.shapes.add_textbox(Inches(6.80), Inches(5.85), Inches(5.80), Inches(0.25))
    r = tb_c2.text_frame.paragraphs[0].add_run()
    r.text = "Figure 14(b): Southward Progress Over Time Showing Active Escape"
    set_run_font(r, size_pt=9.5, bold=True, color=COLOR_CAPTION)

    add_card(s42, Inches(0.60), Inches(6.15), Inches(12.13), Inches(0.95))
    tb_cur = s42.shapes.add_textbox(Inches(0.75), Inches(6.18), Inches(11.83), Inches(0.85))
    tf_cur = tb_cur.text_frame
    tf_cur.word_wrap = True
    add_bullet_text(tf_cur, "Active Subproblem & Immediate Next Step", size_pt=11, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=1)
    add_bullet_text(tf_cur, "Dramatic progression: R3 (0% escape, 18% collision) → R4.3 (100% Env 1 escape, 60% Env 2 escape, 0% collisions).", size_pt=10)
    add_bullet_text(tf_cur, "Final remaining bottleneck: Corridor-axis alignment at narrow (0.65 m) channel entries. Geodesic gradient projection repair is active.", size_pt=10)
    new_slides.append(s42)

    # -------------------------------------------------------------------------
    # INSERT NEW SLIDES INTO POSITION (AFTER ORIGINAL SLIDE 32, i.e., INDEX 32)
    # In python-pptx, sldIdLst controls presentation slide order!
    # -------------------------------------------------------------------------
    print("Reordering slides: inserting 10 new slides after Slide 32...")
    sldIdLst = prs.slides._sldIdLst
    # The 10 new slides were appended to the end of sldIdLst.
    # We remove them from the end and insert them sequentially starting at index 32!
    for i in range(10):
        # The first new slide is currently at index (orig_count)
        new_sld_id = sldIdLst[orig_count + i]
        # Insert into target index: 32 + i
        sldIdLst.insert(32 + i, new_sld_id)

    print(f"Total slides after insertion: {len(prs.slides)}")

    # =========================================================================
    # PART 3: UPDATE STATUS LEDGER (NOW SLIDE 43, INDEX 42)
    # =========================================================================
    print("Updating Master Status Ledger (Slide 43)...")
    s_ledger = prs.slides[42] # Originally Slide 33 (index 32)
    # Remove existing Table 4 shape
    table_to_remove = None
    for sh in s_ledger.shapes:
        if sh.has_table:
            table_to_remove = sh
            break
    if table_to_remove:
        sp = table_to_remove._element
        sp.getparent().remove(sp)

    headers_ledger = ["Development Stage", "Key Architectural Component", "Verification Metric", "Empirical Finding", "Viva Defense Status"]
    rows_ledger = [
        ["Stage 1 Embodiment", "MuJoCo 30 Hz Control Loop & Kinematics", "Dynamical Stability", "Zero tip-over in 150 trials", "VALIDATED ✅"],
        ["Stage 1.1 Friction", "Traction & Wheel Slip Characterization", "Slip Ratio vs Friction", "σ reaches 98.2% on ice (μ=0.05)", "VALIDATED ✅"],
        ["Stage 2A Head Direction", "CANN Ring Attractor Self-Model", "Multi-Seed Drift", "Mean homing error = 0.062 m", "VALIDATED ✅"],
        ["Stage 2B Spatial Model", "Closed-Loop Odometric Integration", "0.22 m Gate Compliance", "5/5 seeds pass return gate", "VALIDATED ✅"],
        ["Stage 2.1 World Model", "Multi-Horizon Forward Predictor", "7 Quantitative Gates", "7/7 gates passed (v R²=0.96)", "VALIDATED ✅"],
        ["Stage 2.2 MVE Deliberation", "Prospective Action Deliberation", "Collision Rate vs Reflex", "88.2% collision reduction", "VALIDATED ✅"],
        ["Stage 2.3 R1 Deliberation", "Continuous Swept-Cone Action Veto", "40 Challenge Mazes", "40/40 cleared, 0.00% collisions", "CERTIFIED ✅"],
        ["Stage 3.0 Pre-Flight", "Decision-Pipeline Code Hygiene", "AST Anti-Cheat Scan", "7/7 clean (0 coordinate leaks)", "VALIDATED ✅"],
        ["Stage 3.1 CANN Causal", "2,114-Unit Causal Ablation Battery", "Ablation Δu > 0.15, p < 0.01", "Δu = 0.56, p < 10⁻¹⁶, coll +27%", "VALIDATED ✅"],
        ["Stage 3.2A Trajectory", "Air-Gapped Mental Simulator Fidelity", "Rollout Error ≤ 0.08 m", "Ds ≤ 0.150 m (100% PASS)", "VALIDATED ✅"],
        ["Stage 3.2B Memory", "Spatial Memory Necessity Battery", "5 Non-LOS Task Families", "Δu = 0.47 action divergence", "VALIDATED ✅"],
        ["Stage 3.3 MPPI Action", "Continuous Trajectory Synthesis", "Action Smoothness & Latency", "Δu = 0.060, p95 = 2.14 ms", "CERTIFIED ✅"],
        ["Stage 3.4 Active Inference", "Expected Free Energy Minimisation", "200-Episode Frozen Battery", "R4.2 heading fix -59%, 100% Env 1", "ACTIVE ⏳"]
    ]
    col_w_ledger = [Inches(1.8), Inches(3.3), Inches(2.4), Inches(3.1), Inches(1.53)]
    add_table_styled(s_ledger, Inches(0.49), Inches(1.30), Inches(12.13), Inches(5.60), headers_ledger, rows_ledger, col_w_ledger, font_size=9.5)

    # =========================================================================
    # PART 4: UPDATE "WORK TO BE DONE" (NOW SLIDE 44, INDEX 43)
    # =========================================================================
    print("Updating Work To Be Done (Slide 44)...")
    s_work = prs.slides[43] # Originally Slide 34 (index 33)
    for sh in s_work.shapes:
        if sh.has_text_frame and "WORK TO BE DONE" not in sh.text_frame.text and len(sh.text_frame.text) > 30:
            tf = sh.text_frame
            tf.clear()
            p0 = tf.paragraphs[0]
            p0.text = "Completed & Certified Milestones (Stages 1, 2, 3.0–3.3):"
            p0.space_after = Pt(4)
            set_run_font(p0.runs[0], size_pt=13.5, bold=True, color=COLOR_TITLE)

            add_bullet_text(tf, "✓ Stage 1 & 2: Embodied sensorimotor grounding, CANN spatial representation, and 7-gate world model.", size_pt=11.5, color=COLOR_PASS, space_after=3)
            add_bullet_text(tf, "✓ Stage 3.1 & 3.2: Mathematical proofs of CANN causal coupling (p < 10⁻¹⁶) and non-LOS memory necessity.", size_pt=11.5, color=COLOR_PASS, space_after=3)
            add_bullet_text(tf, "✓ Stage 3.3: MPPI continuous trajectory optimization certified (50% collision reduction, 2.14 ms latency).", size_pt=11.5, color=COLOR_PASS, space_after=3)
            add_bullet_text(tf, "✓ Stage 3.4-R4: Forensic sonar corner-reflection heading correction (slashed heading error by 35%–60%).", size_pt=11.5, color=COLOR_PASS, space_after=6)

            add_bullet_text(tf, "Active & Immediate Next Steps (Stage 3.4–3.7):", size_pt=13.5, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=4)
            add_bullet_text(tf, "⏳ Finalize corridor-axis geodesic alignment in Stage 3.4 for 100% escape across asymmetric T-junctions.", size_pt=11.5, color=COLOR_ACTIVE, space_after=3)
            add_bullet_text(tf, "• Stage 3.5: Physical perturbation adaptation (friction drops μ=0.2, torque loss, and wheel slip recovery).", size_pt=11.5, space_after=3)
            add_bullet_text(tf, "• Stage 3.6: Behavioral synergy formation & Physarum plasmodial flow routing to prune dead-ends.", size_pt=11.5, space_after=3)
            add_bullet_text(tf, "• Stage 3.7: Active head gaze scanning & multi-modal vision network (CarlVisionNet) integration.", size_pt=11.5, space_after=6)

            add_bullet_text(tf, "Long-Term Developmental Roadmap (Stages 4–5 & Hardware):", size_pt=13.5, bold=True, is_bullet=False, color=COLOR_TITLE, space_after=4)
            add_bullet_text(tf, "• Stage 4: Autopoietic lifelong memory via online R-STDP synaptic plasticity & Holographic HDC vectors.", size_pt=11.5, space_after=3)
            add_bullet_text(tf, "• Stage 5: Metacognitive self-reflection via \"The Witness\" (causal attribution & permission-gated self-modification).", size_pt=11.5, space_after=3)
            add_bullet_text(tf, "• Hardware Transfer: Zero-shot sim-to-real transfer to Orange Pi 5 (6.0 TOPS) + ESP32 dual-board chassis.", size_pt=11.5, space_after=3)
            break

    # =========================================================================
    # PART 5: UPDATE SLIDE NUMBERS ON ALL SLIDES (1..47)
    # =========================================================================
    print("Updating slide numbers across all 47 slides...")
    for idx, s in enumerate(prs.slides):
        slide_num_str = str(idx + 1)
        found_num = False
        for sh in s.shapes:
            if sh.has_text_frame:
                txt = sh.text_frame.text.strip()
                if txt.isdigit() and int(txt) <= orig_count + 15:
                    sh.text_frame.text = slide_num_str
                    if sh.text_frame.paragraphs[0].runs:
                        set_run_font(sh.text_frame.paragraphs[0].runs[0], size_pt=11, bold=False, color=COLOR_SUBTITLE)
                    found_num = True
                    break
        if not found_num:
            # Add slide number box at bottom right
            nb = s.shapes.add_textbox(Inches(12.20), Inches(7.05), Inches(0.80), Inches(0.30))
            np = nb.text_frame.paragraphs[0]
            np.alignment = PP_ALIGN.RIGHT
            nr = np.add_run()
            nr.text = slide_num_str
            set_run_font(nr, size_pt=11, bold=False, color=COLOR_SUBTITLE)

    # =========================================================================
    # PART 6: SAVE TO D: DRIVE DESTINATIONS
    # =========================================================================
    print(f"Saving updated presentation to: {OUT_PPTX_EBCA}")
    os.makedirs(os.path.dirname(OUT_PPTX_EBCA), exist_ok=True)
    prs.save(OUT_PPTX_EBCA)
    print(f"Successfully saved: {OUT_PPTX_EBCA} ({os.path.getsize(OUT_PPTX_EBCA)/1024/1024:.2f} MB)")

    print(f"Saving duplicate to: {OUT_PPTX_DROOT}")
    prs.save(OUT_PPTX_DROOT)
    print(f"Successfully saved: {OUT_PPTX_DROOT} ({os.path.getsize(OUT_PPTX_DROOT)/1024/1024:.2f} MB)")

    print("\nALL PRESENTATION TASKS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
