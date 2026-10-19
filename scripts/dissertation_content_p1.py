"""
dissertation_content_p1.py
Contains Front Matter and Chapters 1, 2, 3 for CARL-DX Dissertation.
Strictly compliant with JNTUH-UCESTH guidelines and project_report_2.pdf benchmark.
British spelling throughout.
"""

import docx
from docx.shared import Inches, Pt, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dissertation_helpers import (
    add_page_break, add_chapter_title, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_equation_p, add_image_figure,
    add_table_caption, add_clean_table, set_cell_margins
)

def add_front_matter(doc):
    # -------------------------------------------------------------
    # PAGE 1: OUTER COVER (Center-justified, NO Guide Name per Rule 3)
    # -------------------------------------------------------------
    p0 = doc.add_paragraph()
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(36)
    p0.paragraph_format.space_after = Pt(20)
    r0 = p0.add_run("DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS")
    r0.font.name = 'Times New Roman'
    r0.font.size = Pt(18)
    r0.font.bold = True
    
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(40)
    p1.paragraph_format.space_after = Pt(12)
    r1 = p1.add_run("A Dissertation Submitted in Partial Fulfilment of the Requirements\nfor the Award of the Degree of")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(12)
    r1.font.italic = True
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(40)
    r2 = p2.add_run("MASTER OF TECHNOLOGY\nIN\nADVANCED MANUFACTURING SYSTEMS")
    r2.font.name = 'Times New Roman'
    r2.font.size = Pt(14)
    r2.font.bold = True
    
    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p3.paragraph_format.space_after = Pt(4)
    r3 = p3.add_run("By\n")
    r3.font.name = 'Times New Roman'
    r3.font.size = Pt(12)
    r3b = p3.add_run("MANAS SADASHIV\n(Regd. No. 22011P0310)")
    r3b.font.name = 'Times New Roman'
    r3b.font.size = Pt(14)
    r3b.font.bold = True
    
    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p4.paragraph_format.space_before = Pt(64)
    p4.paragraph_format.space_after = Pt(0)
    r4 = p4.add_run(
        "DEPARTMENT OF MECHANICAL ENGINEERING\n"
        "JNTUH UNIVERSITY COLLEGE OF ENGINEERING, SCIENCE AND TECHNOLOGY HYDERABAD (AUTONOMOUS)\n"
        "KUKATPALLY, HYDERABAD – 500085, TELANGANA, INDIA\n"
        "OCTOBER, 2026"
    )
    r4.font.name = 'Times New Roman'
    r4.font.size = Pt(11)
    r4.font.bold = True

    # -------------------------------------------------------------
    # PAGE 2: BLANK PAGE (Per Rule 1)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_blank = doc.add_paragraph()
    p_blank.paragraph_format.space_before = Pt(200)
    p_blank.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_blk = p_blank.add_run("[This page is intentionally left blank]")
    r_blk.font.name = 'Times New Roman'
    r_blk.font.size = Pt(10)
    r_blk.font.italic = True

    # -------------------------------------------------------------
    # PAGE 3: INNER COVER PAGE (Third page per Guideline 2)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_in_t = doc.add_paragraph()
    p_in_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_in_t.paragraph_format.space_before = Pt(24)
    p_in_t.paragraph_format.space_after = Pt(20)
    r_in_t = p_in_t.add_run("DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS")
    r_in_t.font.name = 'Times New Roman'
    r_in_t.font.size = Pt(16)
    r_in_t.font.bold = True
    
    p_in_sub = doc.add_paragraph()
    p_in_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_in_sub.paragraph_format.space_after = Pt(12)
    r_in_sub = p_in_sub.add_run(
        "Dissertation submitted in partial fulfillment of the requirement for the award of the degree of\n"
        "Master of Technology in Advanced Manufacturing Systems\n\n"
        "BY\n"
        "MANAS SADASHIV\n"
        "(Regd. No. 22011P0310)\n\n"
        "Under the Guidance and Supervision of\n"
        "Dr. M. INDIRA RANI\n"
        "Professor of Mechanical Engineering"
    )
    r_in_sub.font.name = 'Times New Roman'
    r_in_sub.font.size = Pt(12)
    
    p_in_foot = doc.add_paragraph()
    p_in_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_in_foot.paragraph_format.space_before = Pt(70)
    r_in_foot = p_in_foot.add_run(
        "DEPARTMENT OF MECHANICAL ENGINEERING\n"
        "JNTUH UNIVERSITY COLLEGE OF ENGINEERING, SCIENCE AND TECHNOLOGY HYDERABAD (AUTONOMOUS)\n"
        "KUKATPALLY, HYDERABAD – 500085, TELANGANA, INDIA\n"
        "OCTOBER, 2026"
    )
    r_in_foot.font.name = 'Times New Roman'
    r_in_foot.font.size = Pt(11)
    r_in_foot.font.bold = True

    # -------------------------------------------------------------
    # PAGE 4: CERTIFICATE (Fourth page per Guideline 3)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_cert_head = doc.add_paragraph()
    p_cert_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cert_head.paragraph_format.space_before = Pt(18)
    p_cert_head.paragraph_format.space_after = Pt(18)
    r_ch = p_cert_head.add_run("CERTIFICATE")
    r_ch.font.name = 'Times New Roman'
    r_ch.font.size = Pt(14)
    r_ch.font.bold = True
    
    p_cert_b = doc.add_paragraph()
    p_cert_b.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cert_b.paragraph_format.line_spacing = 1.5
    p_cert_b.paragraph_format.space_after = Pt(40)
    r_cb = p_cert_b.add_run(
        'This is to certify that the thesis / dissertation entitled "DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS" '
        'that is being submitted by Sri Manas Sadashiv (Regd. No: 22011P0310) in partial fulfillment for the award of Master of Technology in Advanced Manufacturing Systems, '
        'to the Department of Mechanical Engineering, JNTUH University College of Engineering, Science and Technology Hyderabad (Autonomous), '
        'is a record of bonafide work carried out by him under our guidance and supervision.\n\n'
        'The results embodied in this thesis have not been submitted to any other University or Institute for the award of any degree or diploma.'
    )
    r_cb.font.name = 'Times New Roman'
    r_cb.font.size = Pt(12)
    
    tbl_cert = doc.add_table(rows=1, cols=2)
    tbl_cert.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    c_h, c_s = tbl_cert.rows[0].cells
    c_h.width = Inches(3.2)
    c_s.width = Inches(3.2)
    
    p_s = c_s.paragraphs[0]
    p_s.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_s = p_s.add_run(
        "Signature of Supervisor\n\n\n\n"
        "Dr. M. INDIRA RANI\n"
        "Professor of Mechanical Engineering\n"
        "Department of Mechanical Engineering\n"
        "JNTUH-UCESTH, Hyderabad"
    )
    r_s.font.name = 'Times New Roman'
    r_s.font.size = Pt(11)
    
    p_h = c_h.paragraphs[0]
    p_h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_h = p_h.add_run(
        "Signature of Head of Department\n\n\n\n"
        "Dr. S. NAGA SARADA\n"
        "Professor and Head\n"
        "Department of Mechanical Engineering\n"
        "JNTUH-UCESTH, Hyderabad"
    )
    r_h.font.name = 'Times New Roman'
    r_h.font.size = Pt(11)

    # -------------------------------------------------------------
    # PAGE 5: DECLARATION (Fifth page per Guideline 4)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_dec_head = doc.add_paragraph()
    p_dec_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dec_head.paragraph_format.space_before = Pt(18)
    p_dec_head.paragraph_format.space_after = Pt(18)
    r_dh = p_dec_head.add_run("DECLARATION\nby the P.G. (M.Tech) Student")
    r_dh.font.name = 'Times New Roman'
    r_dh.font.size = Pt(13)
    r_dh.font.bold = True
    
    p_dec_b = doc.add_paragraph()
    p_dec_b.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_dec_b.paragraph_format.line_spacing = 1.5
    p_dec_b.paragraph_format.space_after = Pt(36)
    r_db = p_dec_b.add_run(
        'I hereby declare that the Report of the P.G. Project Work entitled "DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS" '
        'which is being submitted to the Jawaharlal Nehru Technological University Hyderabad, in partial fulfillment of the requirements for the award of the Degree of '
        'Master of Technology in Advanced Manufacturing Systems, Department of Mechanical Engineering, is a bonafide report of the work carried out by me. '
        'The material contained in this Report has not been submitted to any University or Institution for the award of any degree or diploma.'
    )
    r_db.font.name = 'Times New Roman'
    r_db.font.size = Pt(12)
    
    p_dec_meta = doc.add_paragraph()
    p_dec_meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_dec_meta.paragraph_format.line_spacing = 1.3
    r_dm = p_dec_meta.add_run(
        "Register Number: 22011P0310\n"
        "Name: Manas Sadashiv\n"
        "Signature of Student: _____________________________\n"
        "Phone No: +91 94901 00000\n"
        "E-mail I.D: manas.sadashiv@jntuh.ac.in\n"
        "Department of Mechanical Engineering\n"
        "Place: JNTUH-UCESTH, Hyderabad\n"
        "Date:  19-10-2026"
    )
    r_dm.font.name = 'Times New Roman'
    r_dm.font.size = Pt(11)

    # -------------------------------------------------------------
    # PAGE 6: ACKNOWLEDGEMENT (Sixth page per Guideline 5)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_ack_head = doc.add_paragraph()
    p_ack_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ack_head.paragraph_format.space_before = Pt(18)
    p_ack_head.paragraph_format.space_after = Pt(16)
    r_ah = p_ack_head.add_run("ACKNOWLEDGEMENT")
    r_ah.font.name = 'Times New Roman'
    r_ah.font.size = Pt(13)
    r_ah.font.bold = True
    
    add_body_p(doc, "The completion of this Master of Technology dissertation project represents an intellectually stimulating and rigorous journey. I express my profound gratitude to everyone who contributed their invaluable technical expertise, academic critique, and mentorship.")
    add_body_p(doc, "I record my deepest sense of gratitude to my research supervisor, Dr. M. Indira Rani, Professor of Mechanical Engineering, JNTUH University College of Engineering, Science and Technology Hyderabad, for her visionary guidance, acute scientific judgment, and meticulous scrutiny throughout the developmental trajectory of this work.")
    add_body_p(doc, "I am sincerely grateful to Dr. S. Naga Sarada, Professor and Head, Department of Mechanical Engineering, JNTUH-UCESTH, for facilitating seamless access to university simulation workstations and robotics laboratory resources.")
    add_body_p(doc, "Finally, I extend my heartfelt gratitude to my family and colleagues for their constant encouragement and enduring patience throughout the tenure of this post-graduate research.")
    
    p_asig = doc.add_paragraph()
    p_asig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_asig.paragraph_format.space_before = Pt(24)
    r_as = p_asig.add_run("MANAS SADASHIV\n(Regd. No. 22011P0310)")
    r_as.font.name = 'Times New Roman'
    r_as.font.size = Pt(12)
    r_as.font.bold = True

    # -------------------------------------------------------------
    # PAGE 7: ABSTRACT (Seventh page per Guideline 6)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_abs_head = doc.add_paragraph()
    p_abs_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_abs_head.paragraph_format.space_before = Pt(18)
    p_abs_head.paragraph_format.space_after = Pt(14)
    r_abh = p_abs_head.add_run("ABSTRACT")
    r_abh.font.name = 'Times New Roman'
    r_abh.font.size = Pt(13)
    r_abh.font.bold = True
    
    add_body_p(doc, "Contemporary autonomous mobile robotics is constrained by a profound methodological divide. On one hand, deep reinforcement learning frameworks operate as compute-intensive black boxes requiring millions of training samples, yet exhibit severe catastrophic forgetting when transferred outside their training distributions. On the other hand, classical navigation pipelines (e.g. ROS MoveBase, SLAM, TEB planners) rely on privileged global coordinate frames, artificial Cartesian obstacle inflation, and rigid pre-programmed routines that lack introspective self-awareness. This dissertation presents CARL-DX (Cognitive Autonomous Robotic Lifelong Digital-eXperiment), a 2,114-unit neuromorphic computational architecture integrated within a high-fidelity contact-physics digital twin and engineered for ultra-frugal embedded execution.")
    add_body_p(doc, "The key research contributions and empirical findings developed in this dissertation include:")
    add_bullet_p(doc, "Autonomous Sensorimotor Grounding (Stage 1)", "Elimination of kinematic hand-tuning via 6-channel anonymous motor babbling, discovering directional momentum and empirical wheel-slip thresholds without simulator coordinate access.")
    add_bullet_p(doc, "Topological Attractor Self-Modelling (Stage 2)", "Formulation of a 2,114-unit Continuous Attractor Neural Network (64-HD ring, 1,024-grid torus, 1,026 reservoir) coupled to log-odds allocentric occupancy memory, achieving 100% collision-free navigation across 40 challenge mazes.")
    add_bullet_p(doc, "Continuous Action Synthesis & Active Inference (Stage 3)", "Implementation of Model Predictive Path Integral (MPPI) control driven by Expected Free Energy minimization, successfully resolving dead ends, surface friction drops (mu=0.20), and 40% motor drag with sub-28 ms cycle latency.")
    add_bullet_p(doc, "Autopoiesis & Metacognitive Repair (Stages 4–5)", "Reward-modulated STDP, 2,048-D holographic memory, and an introspective 7-channel 'Witness' organ arbitrating Drosophila PFL2 escape maneuvers with an 81.5% causal recovery advantage.")
    add_bullet_p(doc, "Cross-Embodiment & Hardware Prototyping (Stage 6)", "Demonstrated zero-retraining morphological transfer across 4 mechanical tiers (including Google DeepMind Franka Panda) and execution on an ESP32 hardware platform within 33.6 KB SRAM.")
    add_bullet_p(doc, "Zero-Cheat Architectural Quarantine", "Rigorous Abstract Syntax Tree (AST) static analysis verifying complete mathematical isolation between simulator physics and the cognitive decision loop.")

    # -------------------------------------------------------------
    # PAGES 8-10: TOC, LIST OF TABLES, LIST OF FIGURES, NOTATION
    # -------------------------------------------------------------
    add_page_break(doc)
    p_toc_head = doc.add_paragraph()
    p_toc_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_head.paragraph_format.space_before = Pt(14)
    p_toc_head.paragraph_format.space_after = Pt(12)
    r_th = p_toc_head.add_run("TABLE OF CONTENTS")
    r_th.font.name = 'Times New Roman'
    r_th.font.size = Pt(13)
    r_th.font.bold = True
    
    toc_data = [
        ("CERTIFICATE", "ii"),
        ("DECLARATION", "iii"),
        ("ACKNOWLEDGEMENT", "iv"),
        ("ABSTRACT", "v"),
        ("TABLE OF CONTENTS", "vii"),
        ("LIST OF TABLES", "ix"),
        ("LIST OF FIGURES", "x"),
        ("NOTATION AND ABBREVIATIONS", "xii"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("    1.1  Background and Motivation", "1"),
        ("    1.2  Problem Statement and Research Challenges", "2"),
        ("    1.3  Developmental Architecture Overview", "3"),
        ("    1.4  Objectives of Present Work", "4"),
        ("    1.5  Organization of the Thesis", "4"),
        ("CHAPTER 2: THEORETICAL FOUNDATIONS AND EMBODIED BACKGROUND", "5"),
        ("    2.1  Sensorimotor Grounding and Embodied Cognition", "5"),
        ("    2.2  Continuous Attractor Neural Networks", "6"),
        ("    2.3  Active Inference and Free Energy Principle", "8"),
        ("    2.4  Model Predictive Path Integral Control", "9"),
        ("    2.5  Bio-Physical Fluid Flux Dynamics", "11"),
        ("CHAPTER 3: LITERATURE REVIEW", "12"),
        ("    3.1  Literature Survey", "12"),
        ("    3.2  Gap Identification", "16"),
        ("CHAPTER 4: PLATFORM DESIGN AND SIMULATION METHODOLOGY", "17"),
        ("    4.1  Mechatronic Architecture and Specifications", "17"),
        ("    4.2  MuJoCo Contact-Rich Multi-Body Digital Twin", "19"),
        ("    4.3  Decision-Pipeline AST Quarantine Barrier", "22"),
        ("CHAPTER 5: SENSORIMOTOR GROUNDING AND MOTOR BABBLING (STAGE 1)", "25"),
        ("    5.1  Autonomous Motor Babbling and Topology Discovery", "25"),
        ("    5.2  Sensorimotor Contingency Discovery", "26"),
        ("    5.3  Dynamical Stability and Slip Estimation", "27"),
        ("CHAPTER 6: GENERATIVE WORLD AND SELF-MODELING (STAGE 2)", "29"),
        ("    6.1  2,114-Unit Continuous Attractor Neural Network", "29"),
        ("    6.2  Grounded World Model and Allocentric Occupancy Memory", "31"),
        ("    6.3  Prospective Deliberation and Swept-Cone Veto", "33"),
        ("CHAPTER 7: CONTINUOUS ACTION SYNTHESIS AND ACTIVE INFERENCE (STAGE 3)", "35"),
        ("    7.1  CANN Causal Coupling Battery", "35"),
        ("    7.2  Counterfactual Rollout Fidelity and Memory Necessity", "37"),
        ("    7.3  Continuous MPPI Action Synthesis", "39"),
        ("    7.4  Autonomous Active Inference and Exploration", "41"),
        ("    7.5  Physical Perturbation and Environmental Adaptation", "43"),
        ("    7.6  Bio-Physical Flux Routing and Motor Synergies", "45"),
        ("    7.7  Multi-Modal Retinal Vision and Gaze Dynamics", "46"),
        ("CHAPTER 8: EXPERIMENTAL RESULTS AND BENCHMARK VALIDATION", "49"),
        ("    8.1  Empirical Performance Analysis", "49"),
        ("    8.2  Real-Time Latency and Computational Complexity Profile", "51"),
        ("    8.3  Environmental Adaptation under Extreme Perturbations", "53"),
        ("    8.4  Bio-Physical Flux Routing and Motor Synergies", "54"),
        ("    8.5  Multi-Modal Perception and Efference Copy Dynamics", "55"),
        ("    8.6  Causal Necessity and Ablation Effect Sizes", "56"),
        ("    8.7  AST Anti-Cheat Decision-Pipeline Quarantine Audit", "57"),
        ("CHAPTER 9: ENGINEERING SYNTHESIS AND CONTRIBUTIONS", "59"),
        ("    9.1  Summary of Core Engineering Contributions", "59"),
        ("    9.2  Validation of Foundational Architectural Invariants", "60"),
        ("    9.3  Comparative Analysis with State-of-the-Art Robotic Stacks", "61"),
        ("CHAPTER 10: AUTOPOIETIC LIFELONG MEMORY AND PERSISTENCE (STAGE 4)", "63"),
        ("    10.1 Reward-Modulated STDP Synaptic Plasticity", "63"),
        ("    10.2 2,048-D FHRR Holographic Associative Memory", "64"),
        ("    10.3 SWR Reverse Replay and Sleep Consolidation", "65"),
        ("    10.4 Autopoietic Lifelong Persistence (GIS-901 Atomic WAL)", "66"),
        ("CHAPTER 11: METACOGNITION AND SELF-MODIFICATION (STAGE 5)", "67"),
        ("    11.1 Introspective Failure Telemetry Monitoring", "67"),
        ("    11.2 Abductive Causal Attribution and PFL2 Steering", "68"),
        ("    11.3 Permission-Gated Self-Modification & Turrigiano Scaling", "69"),
        ("    11.4 40-Episode Adversarial Acceptance Battery", "70"),
        ("CHAPTER 12: FOREIGN EMBODIMENT AND PHYSICAL PROTOTYPING (STAGE 6)", "71"),
        ("    12.1 Cross-Embodiment Transfer Across Diverse Morphologies", "71"),
        ("    12.2 Heavy 3D Clutter Arena Stress Benchmark", "72"),
        ("    12.3 Frugal ESP32 Embedded Prototype Design", "73"),
        ("    12.4 Neuromorphic Authenticity Verification & Council Verdict", "74"),
        ("CHAPTER 13: CONCLUSIONS AND FUTURE SCOPE (STAGE 7 FUTURE WORK)", "75"),
        ("    13.1 Conclusions", "75"),
        ("    13.2 Limitations", "75"),
        ("    13.3 Future Scope: Stage 7 Physical Deployment and Swarm Systems", "76"),
        ("REFERENCES", "77"),
        ("APPENDIX A: COMPLETE MATHEMATICAL FORMULATIONS", "81"),
        ("APPENDIX B: HYPERPARAMETER AND CONFIGURATION TABLES", "83")
    ]
    
    tbl_t = doc.add_table(rows=len(toc_data) + 1, cols=2)
    tbl_t.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl_t.rows[0]
    hdr.cells[0].text = "TITLE"
    hdr.cells[1].text = "PAGE NO."
    hdr.cells[0].paragraphs[0].runs[0].font.bold = True
    hdr.cells[1].paragraphs[0].runs[0].font.bold = True
    hdr.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hdr.cells[0].width = Inches(5.6)
    hdr.cells[1].width = Inches(1.0)
    
    for idx, (title, pg) in enumerate(toc_data):
        row = tbl_t.rows[idx + 1]
        c0, c1 = row.cells
        c0.width = Inches(5.6)
        c1.width = Inches(1.0)
        c0.text = title
        c1.text = str(pg)
        p0 = c0.paragraphs[0]
        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p0.runs[0].font.name = 'Times New Roman'
        p1.runs[0].font.name = 'Times New Roman'
        p0.runs[0].font.size = Pt(10)
        p1.runs[0].font.size = Pt(10)
        if "CHAPTER" in title or title in ["CERTIFICATE", "DECLARATION", "ACKNOWLEDGEMENT", "ABSTRACT", "REFERENCES", "APPENDIX A", "APPENDIX B"]:
            p0.runs[0].font.bold = True
            p1.runs[0].font.bold = True
        set_cell_margins(c0, top=20, bottom=20, left=35, right=35)
        set_cell_margins(c1, top=20, bottom=20, left=35, right=35)

    # -------------------------------------------------------------
    # LIST OF TABLES (Guideline 7, Page ix)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_lot_head = doc.add_paragraph()
    p_lot_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot_head.paragraph_format.space_before = Pt(14)
    p_lot_head.paragraph_format.space_after = Pt(12)
    r_lth = p_lot_head.add_run("LIST OF TABLES")
    r_lth.font.name = 'Times New Roman'
    r_lth.font.size = Pt(13)
    r_lth.font.bold = True
    
    tables_list = [
        ("Table 4.1", "Master Physical and Kinematic Parameters of the CARL Mobile Platform", "18"),
        ("Table 4.2", "Mechatronic Hardware and Sensor Specifications", "19"),
        ("Table 4.3", "MuJoCo Multi-Body Simulation Digital Twin Parameters", "21"),
        ("Table 5.1", "Stage 1 Sensorimotor Contingency Discovery & Dynamics", "26"),
        ("Table 6.1", "Stage 2 Topological Representation Parameters", "29"),
        ("Table 6.2", "Stage 2 Grounded World Model Accuracy Metrics", "32"),
        ("Table 6.3", "Stage 2.3 Deliberative Lookahead Benchmark Results", "33"),
        ("Table 7.1", "Stage 3.1 Pre-Registered CANN Causal Ablation Battery Results", "36"),
        ("Table 7.2", "Stage 3.2 Counterfactual Trajectory Rollout Fidelity Benchmark", "37"),
        ("Table 7.3", "Stage 3.2 Non-LOS Spatial Memory Necessity Ablation Across 5 Task Families", "39"),
        ("Table 7.4", "Stage 3.3 Continuous MPPI Algorithmic Configuration", "40"),
        ("Table 7.5", "Stage 3.4 Autonomous Active Inference Performance (50 Episodes)", "42"),
        ("Table 7.6", "Real-Time Cycle Latency Breakdown by Cognitive Organ", "43"),
        ("Table 7.7", "Stage 3.5 Physical Perturbation and Environmental Adaptation Results", "44"),
        ("Table 7.8", "Stage 3 Final Adversarial Acceptance Suite (50 Episodes)", "47"),
        ("Table 8.1", "Master Comparative Developmental Progression Matrix (Stages 1 through 6)", "50"),
        ("Table 8.2", "Real-Time Latency and Computational Complexity Profile", "52"),
        ("Table 8.3", "Causal Necessity and Ablation Effect Sizes Across Developmental Stages", "57"),
        ("Table 8.4", "AST Anti-Cheat Decision-Pipeline Quarantine Audit Across 14 Code Modules", "58"),
        ("Table 12.1", "Stage 6.2 Cross-Embodiment Transfer Performance Across 4 Morphological Tiers", "72"),
        ("Table 12.2", "Stage 6.4 ₹2,150 ESP32 Embedded Prototype Bill of Materials (BOM)", "74"),
        ("Table B.1", "Complete Hyperparameter and Configuration Index", "83")
    ]
    
    tbl_lot = doc.add_table(rows=len(tables_list) + 1, cols=3)
    tbl_lot.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl_lot.rows[0]
    hdr.cells[0].text = "TABLE NO."
    hdr.cells[1].text = "TITLE"
    hdr.cells[2].text = "PAGE NO."
    for c in hdr.cells:
        c.paragraphs[0].runs[0].font.bold = True
    hdr.cells[0].width = Inches(1.3)
    hdr.cells[1].width = Inches(4.5)
    hdr.cells[2].width = Inches(0.8)
    hdr.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    for idx, (tnum, title, pg) in enumerate(tables_list):
        row = tbl_lot.rows[idx + 1]
        c0, c1, c2 = row.cells
        c0.width = Inches(1.3)
        c1.width = Inches(4.5)
        c2.width = Inches(0.8)
        c0.text = tnum
        c1.text = title
        c2.text = str(pg)
        c0.paragraphs[0].runs[0].font.name = 'Times New Roman'
        c1.paragraphs[0].runs[0].font.name = 'Times New Roman'
        c2.paragraphs[0].runs[0].font.name = 'Times New Roman'
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)
        c2.paragraphs[0].runs[0].font.size = Pt(9.5)
        c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_cell_margins(c0, top=20, bottom=20, left=35, right=35)
        set_cell_margins(c1, top=20, bottom=20, left=35, right=35)
        set_cell_margins(c2, top=20, bottom=20, left=35, right=35)

    # -------------------------------------------------------------
    # LIST OF FIGURES (Guideline 7, Page x)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_lof_head = doc.add_paragraph()
    p_lof_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof_head.paragraph_format.space_before = Pt(14)
    p_lof_head.paragraph_format.space_after = Pt(12)
    r_lfh = p_lof_head.add_run("LIST OF FIGURES")
    r_lfh.font.name = 'Times New Roman'
    r_lfh.font.size = Pt(13)
    r_lfh.font.bold = True
    
    figures_list = [
        ("Fig. 4.1", "Master mechatronic schematic and CAD architecture of CARL", "18"),
        ("Fig. 4.2", "2D differential-drive kinematic schematic showing wheelbase and axle geometry", "19"),
        ("Fig. 4.3", "MuJoCo multi-body simulation digital twin render with contact geometries", "21"),
        ("Fig. 4.4", "Master embodied architecture of CARL, detailing zero-copy sensory pipeline", "23"),
        ("Fig. 4.5", "Cognitive isolation barrier and AST anti-cheat quarantine boundary", "24"),
        ("Fig. 5.1", "Stage 1 sensorimotor grounding architecture and 6-channel motor babbling", "25"),
        ("Fig. 5.2", "Stage 1.1 empirical sensorimotor contingency cross-correlation matrix", "27"),
        ("Fig. 5.3", "Stage 1.1 10,000-tick dynamical stability phase space trajectory", "28"),
        ("Fig. 5.4", "Stage 1.1 friction gradient response and kinematic wheel-slip tracking", "28"),
        ("Fig. 6.1", "Physical reality vs internal CANN self-model homing trajectory", "30"),
        ("Fig. 6.2", "CANN 1D ring attractor activity packet and angular bump dynamics", "31"),
        ("Fig. 6.3", "2D grid cell torus (1,024 units) spatial activation profile", "31"),
        ("Fig. 6.4", "Allocentric raster occupancy memory field generated via inverse sonar model", "32"),
        ("Fig. 6.5", "Model-based prospective trajectory evaluation and rotational swept-cone veto", "34"),
        ("Fig. 6.6", "Stage 2 canonical maze navigation clearance trajectory across challenge mazes", "34"),
        ("Fig. 7.1", "Stage 3.1 CANN causal ablation battery: action divergence distributions", "36"),
        ("Fig. 7.2", "Stage 3.1 candidate trajectory rank correlation distributions", "36"),
        ("Fig. 7.3", "Stage 3.2 individual counterfactual branch fidelity vs physical MuJoCo steps", "38"),
        ("Fig. 7.4", "Stage 3.2 non-LOS spatial memory necessity evaluation across 5 challenge families", "38"),
        ("Fig. 7.5", "Stage 3.3 continuous MPPI trajectory rollout and sampling distribution", "40"),
        ("Fig. 7.6", "Stage 3.3 autonomous corridor escape and target acquisition", "41"),
        ("Fig. 8.1", "Stage 3.3 empirical performance benchmarks from master defense trials", "50"),
        ("Fig. 8.2", "Real-time cognitive cycle latency distribution across 50 episodes", "52"),
        ("Fig. 8.3", "Stage 3.5 empirical performance matrix and endocrine adaptation to friction drops", "53"),
        ("Fig. 8.4", "Stage 3.6 Physarum plasmodial streamlines and fluid flux concentration", "54"),
        ("Fig. 8.5", "Stage 3.6 2,048-D Hyperdimensional Computing (HDC) motor synergy clustering", "55"),
        ("Fig. 8.6", "Stage 3.7 Retinal 64x64 RGB vision, spatial feature maps and attention saliency", "56"),
        ("Fig. 8.7", "Stage 3.7 Active head gaze dynamics and efference copy reafference cancellation", "56"),
        ("Fig. 10.1", "Stage 4.1 Reward-Modulated STDP (R-STDP) online synaptic weight matrix evolution", "64"),
        ("Fig. 11.1", "Stage 5.1 & 5.2 'The Witness' 7-channel introspective telemetry signal traces", "68"),
        ("Fig. 11.2", "Stage 5.4 Physical trajectory recovery comparison under motor drag failure", "70"),
        ("Fig. 12.1", "Stage 6.2 Foreign Embodiment Transfer — Google DeepMind MuJoCo Franka Panda arm", "71"),
        ("Fig. 12.2", "Stage 6.2 Foreign Embodiment Transfer — Skid-Steer Rover and Holonomic Omni-base", "72"),
        ("Fig. 12.3", "Stage 6.3 Dense 4-chamber Heavy 3D Clutter Arena environment", "73"),
        ("Fig. 12.4", "Stage 6.3 Multi-Chamber Trajectory Clearance Heatmap across 20 trials", "74")
    ]
    
    tbl_lof = doc.add_table(rows=len(figures_list) + 1, cols=3)
    tbl_lof.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl_lof.rows[0]
    hdr.cells[0].text = "FIGURE NO."
    hdr.cells[1].text = "TITLE"
    hdr.cells[2].text = "PAGE NO."
    for c in hdr.cells:
        c.paragraphs[0].runs[0].font.bold = True
    hdr.cells[0].width = Inches(1.3)
    hdr.cells[1].width = Inches(4.5)
    hdr.cells[2].width = Inches(0.8)
    hdr.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    for idx, (fnum, title, pg) in enumerate(figures_list):
        row = tbl_lof.rows[idx + 1]
        c0, c1, c2 = row.cells
        c0.width = Inches(1.3)
        c1.width = Inches(4.5)
        c2.width = Inches(0.8)
        c0.text = fnum
        c1.text = title
        c2.text = str(pg)
        c0.paragraphs[0].runs[0].font.name = 'Times New Roman'
        c1.paragraphs[0].runs[0].font.name = 'Times New Roman'
        c2.paragraphs[0].runs[0].font.name = 'Times New Roman'
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)
        c2.paragraphs[0].runs[0].font.size = Pt(9.5)
        c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_cell_margins(c0, top=20, bottom=20, left=35, right=35)
        set_cell_margins(c1, top=20, bottom=20, left=35, right=35)
        set_cell_margins(c2, top=20, bottom=20, left=35, right=35)

    # -------------------------------------------------------------
    # NOTATION AND ABBREVIATIONS (Guideline 7, Page xii)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_nom_t = doc.add_paragraph()
    p_nom_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_nom_t.paragraph_format.space_before = Pt(14)
    p_nom_t.paragraph_format.space_after = Pt(12)
    r_nom_t = p_nom_t.add_run("NOTATION AND ABBREVIATIONS")
    r_nom_t.font.name = 'Times New Roman'
    r_nom_t.font.size = Pt(13)
    r_nom_t.font.bold = True
    
    p_ns1 = doc.add_paragraph()
    r_n1 = p_ns1.add_run("Mathematical Notations and Symbols")
    r_n1.font.name = 'Times New Roman'
    r_n1.font.size = Pt(11.5)
    r_n1.font.bold = True
    
    symbols_data = [
        ("u", "Control vector [u_L, u_R]^T representing normalized wheel motor commands in [-1.0, 1.0]"),
        ("v, omega", "Linear forward velocity (m/s) and angular rotational velocity (rad/s)"),
        ("theta_pan", "Active head gaze pan angle (rad) commanded within [-0.85, +0.85] rad"),
        ("mu", "Tire-ground contact friction coefficient (nominal 0.85, perturbed low-friction 0.20)"),
        ("G", "Expected Free Energy (EFE) functional minimized in Active Inference"),
        ("G_pragmatic", "Pragmatic value component of EFE driving progress toward goal states"),
        ("G_epistemic", "Epistemic information-gain value component of EFE driving curiosity and exploration"),
        ("lambda", "Temperature hyperparameter in MPPI trajectory importance weighting (lambda = 0.250)"),
        ("sigma_u", "Exploration noise covariance in MPPI control perturbations (sigma_u = 0.250)"),
        ("D_ij", "Hydraulic conductivity between nodes i and j in Physarum flux dynamics (D in [1e-5, 50.0])"),
        ("dt_ctrl", "Organism discrete cognitive control cycle timestep (0.030 s = 30 ms, 33.3 Hz)"),
        ("T_budget", "Maximum real-time hardware execution deadline per control step (30.0 ms)")
    ]
    for sym, desc in symbols_data:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.space_after = Pt(2)
        r_s = p.add_run(f"{sym:15s}: ")
        r_s.font.name = 'Times New Roman'
        r_s.font.size = Pt(10)
        r_s.font.bold = True
        r_d = p.add_run(desc)
        r_d.font.name = 'Times New Roman'
        r_d.font.size = Pt(10)
        
    p_ns2 = doc.add_paragraph()
    p_ns2.paragraph_format.space_before = Pt(8)
    r_n2 = p_ns2.add_run("Abbreviations and Acronyms")
    r_n2.font.name = 'Times New Roman'
    r_n2.font.size = Pt(11.5)
    r_n2.font.bold = True
    
    abbrevs_data = [
        ("AST", "Abstract Syntax Tree (code verification quarantine mechanism)"),
        ("BOM", "Bill of Materials"),
        ("CANN", "Continuous Attractor Neural Network"),
        ("CARL", "Cognitive Autonomous Robotic Lifelong (organism architecture)"),
        ("EFE", "Expected Free Energy (Active Inference objective)"),
        ("FHRR", "Fractional Holographic Reduced Representation"),
        ("HAL", "Hardware Abstraction Layer"),
        ("HDC", "Hyperdimensional Computing"),
        ("LOS", "Line of Sight"),
        ("MPPI", "Model Predictive Path Integral Control"),
        ("PFL2", "Protocerebral Bridge to Fan-Shaped Body Layer 2 (insect steering neurons)"),
        ("R-STDP", "Reward-Modulated Spike-Timing-Dependent Plasticity"),
        ("SHY", "Synaptic Homeostasis Hypothesis"),
        ("SWR", "Sharp-Wave Ripple (hippocampal replay mechanism)"),
        ("WAL", "Write-Ahead Log (atomic persistence engine)")
    ]
    for abb, desc in abbrevs_data:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.space_after = Pt(2)
        r_a = p.add_run(f"{abb:10s}: ")
        r_a.font.name = 'Times New Roman'
        r_a.font.size = Pt(10)
        r_a.font.bold = True
        r_d = p.add_run(desc)
        r_d.font.name = 'Times New Roman'
        r_d.font.size = Pt(10)


def add_chapter_1(doc):
    # -------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION
    # -------------------------------------------------------------
    add_chapter_title(doc, 1, "INTRODUCTION")
    
    add_heading_2(doc, "1.1", "Background and Motivation")
    add_body_p(doc, "The quest to develop truly autonomous mobile machines capable of purposeful navigation, persistent learning, and resilient physical adaptation in unstructured environments represents one of the foundational frontiers of modern robotics and advanced manufacturing. For decades, the dominant engineering paradigm has relied on modular, decoupled pipelines: perception via dense metric Simultaneous Localisation and Mapping (SLAM), global path planning via graph search algorithms (such as A* or Dijkstra), and local trajectory tracking via deterministic controllers (such as the Timed Elastic Band or Dynamic Window Approach). While these classical frameworks have achieved commendable industrial success in structured, highly predictable settings, they exhibit severe vulnerabilities when exposed to novel kinematic slip, severe hardware degradation, unexpected obstacle geometry, and dynamic physical perturbations.")
    add_body_p(doc, "Concurrently, the emergence of deep reinforcement learning (DRL) promised end-to-end sensorimotor synthesis directly from high-dimensional sensory inputs. However, deep RL methods introduce substantial liabilities: extreme sample inefficiency requiring hundreds of millions of environmental interactions, opaque black-box representations that resist formal safety verification, catastrophic forgetting of previously acquired behavioural repertoires upon distribution shift, and excessive computational demands that necessitate power-hungry workstation GPUs. Biological organisms—from simple slime moulds and insects to mammals—navigate complex physical worlds with remarkable energy efficiency, zero catastrophic forgetting, and immediate, graceful adaptation to limb trauma or surface changes, operating under stringent physiological and metabolic constraints.")
    add_body_p(doc, "This profound performance disparity indicates that biological autonomy does not arise from brute-force statistical curve-fitting over Cartesian coordinates. Instead, biological intelligence is inherently grounded in recurrent topological inductive biases, prospective continuous deliberation, active epistemic inference, and homeostatic plasticity. Developing a computational architecture that embodies these principles within an unprivileged contact-rich physics digital twin—whilst remaining rigorously deployable on ultra-low-cost embedded microcontrollers—constitutes the central motivation of this dissertation.")

    add_heading_2(doc, "1.2", "Problem Statement and Research Challenges")
    add_body_p(doc, "The overarching research problem addressed in this dissertation is the systematic synthesis, empirical validation, and cross-embodiment evaluation of a fully grounded, 2,114-unit neuromorphic computational architecture for mobile robotics, designated CARL-DX (Cognitive Autonomous Robotic Lifelong Digital-eXperiment). Specifically, this research investigates:")
    add_bullet_p(doc, "Sensorimotor Grounding without Priors", "Can an autonomous mobile agent discover its bodily kinematics, actuator polarity, and linear forward momentum purely through anonymous motor babbling, without pre-programmed kinematic models or access to simulator pose coordinates?")
    add_bullet_p(doc, "Causal Spatial Necessity", "Does a recurrent Continuous Attractor Neural Network (CANN) coupled with allocentric occupancy memory provide measurable causal necessity in navigation, or can equivalent performance be attained through purely reactive sonar reflex rules?")
    add_bullet_p(doc, "Continuous Active Inference", "Can Model Predictive Path Integral (MPPI) stochastic trajectory optimization driven by Expected Free Energy (EFE) minimization discover multi-phase escape maneuvers and adapt online to severe physical perturbations (e.g. 76% friction drops and unilateral 40% motor drag)?")
    add_bullet_p(doc, "Autopoiesis and Metacognitive Repair", "How can an embodied agent autonomously detect internal performance degradation ('The Witness') and execute permission-gated homeostatic synaptic modifications without catastrophic divergence?")
    add_bullet_p(doc, "Zero-Cheat Architectural Quarantine", "How can a simulated digital twin be engineered to guarantee, via formal Abstract Syntax Tree (AST) static analysis, that zero privileged simulator coordinates (qpos, qvel, geom_xpos) leak into the active decision loop?")

    add_heading_2(doc, "1.3", "Developmental Architecture Overview")
    add_body_p(doc, "To ensure methodical scientific progression without premature capability inheritance, CARL-DX is structured across six sequential, cumulative developmental stages:")
    add_bullet_p(doc, "Stage 1 (Sensorimotor Grounding)", "Anonymous motor babbling across 6 motor primitives, discovering directionality, velocity bounds, and empirical wheel-slip thresholds.")
    add_bullet_p(doc, "Stage 2 (Generative World and Self-Modelling)", "Coupling a 2,114-unit CANN (64-unit head-direction ring, 1,024-unit grid torus, 1,026-unit reservoir) with an allocentric occupancy grid and prospective trajectory lookahead.")
    add_bullet_p(doc, "Stage 3 (Continuous Action Synthesis)", "Continuous MPPI action synthesis under Active Inference, physical caster spring-damper stabilization, Physarum hydrodynamic routing, and retinal vision with efference copy.")
    add_bullet_p(doc, "Stage 4 (Autopoietic Lifelong Memory)", "Reward-modulated STDP plasticity, 2,048-D holographic associative memory, sharp-wave ripple (SWR) replay, and write-ahead log (WAL) persistence.")
    add_bullet_p(doc, "Stage 5 (Metacognition & Introspection)", "The 7-channel 'Witness' failure telemetry organ, abductive causal attribution, and permission-gated self-repair via Drosophila PFL2 steering.")
    add_bullet_p(doc, "Stage 6 (Cross-Embodiment & Hardware)", "Morphological transfer across four mechanical embodiments (including Google DeepMind Franka Panda) and physical prototyping on an ESP32 microcontroller.")

    add_heading_2(doc, "1.4", "Objectives of Present Work")
    add_body_p(doc, "The specific engineering and scientific objectives of this research are:")
    add_bullet_p(doc, "Objective 1", "To design and simulate a high-fidelity contact-rich digital twin of the CARL mobile platform in MuJoCo 3.3.0, incorporating spring-damper suspension and unprivileged sensor emulation.")
    add_bullet_p(doc, "Objective 2", "To implement and mathematically formalize the 2,114-unit neuromorphic CANN architecture for topological path integration and allocentric spatial memory.")
    add_bullet_p(doc, "Objective 3", "To formulate a continuous MPPI trajectory optimization engine governed by Active Inference Expected Free Energy (EFE = G_pragmatic - w_epistemic * G_epistemic).")
    add_bullet_p(doc, "Objective 4", "To validate biological routing via Physarum polycephalum flux dynamics and motor synergies via Hyperdimensional Computing (HDC).")
    add_bullet_p(doc, "Objective 5", "To conduct pre-registered causal ablation batteries proving the statistical necessity of CANN representations and spatial memory across non-line-of-sight challenge tasks.")
    add_bullet_p(doc, "Objective 6", "To demonstrate autopoietic self-repair, cross-embodiment generalization, and frugal embedded execution within a strict 30 ms real-time cycle budget.")

    add_heading_2(doc, "1.5", "Organization of the Thesis")
    add_body_p(doc, "The remainder of this dissertation is organized as follows:")
    add_body_p(doc, "In Chapter 2, the theoretical foundations of embodied cognition, attractor networks, Active Inference, stochastic optimal control, and biological flux networks are presented.")
    add_body_p(doc, "In Chapter 3, a comprehensive chronological review of existing literature is conducted, followed by the explicit identification of existing research gaps and project contributions.")
    add_body_p(doc, "In Chapter 4, the mechatronic platform design, MuJoCo multi-body digital twin, and AST anti-cheat quarantine architecture are described in detail.")
    add_body_p(doc, "In Chapter 5, Chapter 6, and Chapter 7, the core developmental progression is presented: Stage 1 sensorimotor grounding, Stage 2 attractor self-modelling, and Stage 3 continuous MPPI action synthesis with active gaze vision.")
    add_body_p(doc, "In Chapter 8 and Chapter 9, comprehensive empirical results, real-time latency profiles, causal ablation batteries, and engineering synthesis are evaluated.")
    add_body_p(doc, "In Chapter 10, Chapter 11, and Chapter 12, autopoietic lifelong memory (Stage 4), metacognitive introspective repair (Stage 5), and cross-embodiment transfer / embedded prototyping (Stage 6) are demonstrated.")
    add_body_p(doc, "In Chapter 13, overarching conclusions, system limitations, and future directions for physical Stage 7 deployment and swarm coordination are discussed.")


def add_chapter_2(doc):
    # -------------------------------------------------------------
    # CHAPTER 2: THEORETICAL FOUNDATIONS
    # -------------------------------------------------------------
    add_chapter_title(doc, 2, "THEORETICAL FOUNDATIONS AND EMBODIED BACKGROUND")
    
    add_heading_2(doc, "2.1", "Sensorimotor Grounding and Embodied Cognition")
    add_body_p(doc, "Classical cognitive science long operated under the computationalist hypothesis, positing that intelligence consists of formal symbol manipulation over abstract, amodal representations disconnected from physical embodiment. However, the physical grounding hypothesis (Brooks, 1991) and enactive cognitive science demonstrated that intelligence is deeply inseparable from the physical body and its dynamic sensorimotor interaction with the environment. An embodied agent does not solve an abstract mathematical puzzle; it couples its sensory receptors and physical effectors to maintain homeostatic equilibrium within a dynamic world.")
    add_body_p(doc, "Under this paradigm, meaning and spatial understanding emerge from sensorimotor contingencies—stable, predictable covariations between self-generated motor commands and subsequent sensory state changes. Rather than presuming an innate Cartesian coordinate frame, an organism must babble its actuators, establish empirical contingencies, and ground its internal representations in the physical physics of contact, friction, and inertia.")

    add_heading_2(doc, "2.2", "Continuous Attractor Neural Networks")
    add_body_p(doc, "A Continuous Attractor Neural Network (CANN) is a recurrent neural circuit with symmetric, translationally invariant synaptic connectivity capable of maintaining a continuous manifold of stable steady states (attractors) in the absence of external sensory input (Amari, 1977). In neurobiology, CANNs provide the foundational computational substrate for spatial orientation and path integration in the mammalian head-direction and grid-cell systems (Taube et al., 1990; Hafting et al., 2005).")
    add_body_p(doc, "For a 1D ring attractor comprising N_hd = 64 neurons encoding heading angle theta in [-pi, pi], the synaptic weight W_ij between neuron i (with preferred heading theta_i) and neuron j (with preferred heading theta_j) is given by:")
    add_equation_p(doc, "W_ij^hd = J_0 + J_1 * cos(theta_i - theta_j) + J_v * omega_z * sin(theta_i - theta_j)", "2.1")
    add_body_p(doc, "where J_0 represents uniform global inhibition, J_1 governs local recurrent excitation, and J_v modulates an asymmetric weight component proportional to angular velocity omega_z, which shifts the stable Gaussian activity bump along the ring in real time.")
    add_body_p(doc, "Similarly, a 2D toroidal attractor network comprising N_grid = 1,024 units encodes 2D translational position (x, y) through recurrent inhibitory and excitatory connections arranged on a periodic torus, integrating forward velocity to update position coordinates without drift.")

    add_heading_2(doc, "2.3", "Active Inference and Free Energy Principle")
    add_body_p(doc, "Active Inference (Friston et al., 2006, 2017; Parr et al., 2022) is a normative neurocomputational framework derived from the Free Energy Principle, asserting that self-organizing biological agents survive by minimizing variational free energy—an upper bound on sensory surprise. When planning prospective actions into the future, the agent selects policies pi that minimize the Expected Free Energy (EFE), denoted G(pi):")
    add_equation_p(doc, "G(pi) = sum_{tau=t+1}^{t+H} G(pi, tau)", "2.2")
    add_body_p(doc, "The Expected Free Energy at each lookahead step tau decomposes naturally into a pragmatic (instrumental) value and an epistemic (information-seeking) value:")
    add_equation_p(doc, "G(pi, tau) = G_pragmatic(pi, tau) - w_epistemic * G_epistemic(pi, tau)", "2.3")
    add_body_p(doc, "where G_pragmatic quantifies the deviation of predicted future states from the agent's preferred goal distribution (penalizing collisions and rewarding target approach), while G_epistemic reflects the anticipated reduction in state uncertainty (rewarding exploration of unvisited, high-entropy spatial cells). The negative sign ensures that minimizing G simultaneously maximizes epistemic discovery and minimizes goal distance.")

    add_heading_2(doc, "2.4", "Model Predictive Path Integral Control")
    add_body_p(doc, "Model Predictive Path Integral (MPPI) control (Williams et al., 2017) is an advanced stochastic optimal control method based on the path integral formulation of the dynamic programming equation. Rather than computing gradients through non-smooth contact dynamics, MPPI samples M parallel candidate control trajectories, rolls them forward using a learned or simulated world model, evaluates their cumulative trajectory costs, and computes an importance-weighted control update.")
    add_body_p(doc, "Given a baseline nominal action sequence u = {u_0, ..., u_{H-1}} over horizon H, MPPI samples M noise perturbations delta u_m ~ N(0, Sigma). The importance weight w_m for candidate trajectory m is computed as:")
    add_equation_p(doc, "w_m = exp(-1/lambda * (S_m - min_k S_k)) / sum_{j=1}^M exp(-1/lambda * (S_j - min_k S_k))", "2.4")
    add_body_p(doc, "where S_m is the cumulative EFE cost of candidate trajectory m, and lambda is the temperature parameter. The optimal synthesized control action u_0^* executed at the current timestep is given by:")
    add_equation_p(doc, "u_0^* = u_0 + sum_{m=1}^M w_m * delta u_{m,0}", "2.5")

    add_heading_2(doc, "2.5", "Bio-Physical Fluid Flux Dynamics and HDC")
    add_body_p(doc, "To resolve cul-de-sacs and mazes without combinatorial graph expansion, biological systems utilize hydrodynamic network dynamics. The plasmodial slime mould Physarum polycephalum optimizes its tubule network by adjusting the hydraulic conductivity D_ij of tubule (i, j) in response to fluid flux Q_ij according to Hagen-Poiseuille law (Nakagaki et al., 2000; Tero et al., 2010):")
    add_equation_p(doc, "d/dt D_ij = gamma * |Q_ij|^alpha - r * D_ij", "2.6")
    add_body_p(doc, "Tubes experiencing high flux dilate (increasing conductivity), while tubes leading into closed dead ends suffer flux stagnation and atrophy. In CARL-DX, this hydrodynamic mechanism is coupled to a 2,048-dimensional Hyperdimensional Computing (HDC) vector symbolic space (Kanerva, 2009), binding sensory states and motor synergies into quasi-orthogonal hypervectors that resist noise and prevent catastrophic forgetting.")


def add_chapter_3(doc):
    # -------------------------------------------------------------
    # CHAPTER 3: LITERATURE REVIEW (Strictly compliant with benchmark)
    # -------------------------------------------------------------
    add_chapter_title(doc, 3, "LITERATURE REVIEW")
    
    add_body_p(doc, "This chapter presents a comprehensive, chronological review of existing literature relevant to embodied cognitive robotics, continuous attractor networks, active inference, stochastic optimal control, and biological routing mechanisms. Following the survey, existing research gaps are identified to contextualize the scientific contributions of this dissertation.")

    add_heading_2(doc, "3.1", "Literature Survey")
    
    add_body_p(doc, "Brooks (1991) introduced the subsumption architecture and the physical grounding hypothesis, arguing that true autonomous intelligence does not require abstract symbolic representation, but rather tight, direct coupling between sensors and actuators through layered, asynchronous behavioural competencies.")
    
    add_body_p(doc, "Taube et al. (1990) discovered head-direction (HD) cells in the rat postsubiculum, demonstrating that mammalian spatial orientation is governed by internally generated neural activity packets that track angular heading even in complete darkness, establishing the biological blueprint for continuous ring attractors.")
    
    add_body_p(doc, "Amari (1977) formulated the mathematical foundations of Continuous Attractor Neural Networks (CANNs) in lateral-inhibition neural fields, proving that recurrent neural rings with Mexican-hat synaptic connectivity sustain stable, localized activity bumps capable of smooth continuous tracking.")
    
    add_body_p(doc, "Nakagaki et al. (2000) demonstrated that the plasmodial slime mould Physarum polycephalum could solve maze routing problems by optimizing fluid flux through tubule networks, providing biological evidence for decentralized, non-Cartesian path optimization.")
    
    add_body_p(doc, "Hafting et al. (2005) discovered grid cells in the dorsomedial entorhinal cortex, showing that spatial position is encoded in a periodic, triangular lattice across multiple spatial scales, validating theoretical models of toroidal continuous attractor manifolds for path integration.")
    
    add_body_p(doc, "Friston et al. (2006, 2017) formalized the Free Energy Principle and Active Inference, demonstrating that biological perception, action, and learning can be unified under a single normative drive: minimizing variational and expected free energy to bound sensory surprise and entropy.")
    
    add_body_p(doc, "Turrigiano (2008) established homeostatic synaptic scaling as a fundamental negative-feedback mechanism in neural circuits, showing that biological neurons dynamically adjust their total synaptic strength to maintain stable firing rates despite continuous Hebbian potentiation.")
    
    add_body_p(doc, "Kanerva (2009) introduced Hyperdimensional Computing (HDC) and Vector Symbolic Architectures, proving that computing with high-dimensional (D >= 1,024) quasi-orthogonal vectors provides exceptional robustness against noise, instant one-shot associative binding, and mathematical resistance to catastrophic forgetting.")
    
    add_body_p(doc, "Theodorou et al. (2010) formulated path integral policy improvement from first-principles stochastic optimal control, demonstrating that optimal control policies can be computed via forward trajectory sampling without explicitly calculating Hessian matrices or resolving non-smooth dynamic gradients.")
    
    add_body_p(doc, "Tero et al. (2010) developed mathematical models of Physarum tubule flux dynamics under Hagen-Poiseuille resistance, demonstrating that decentralized adaptive tube networks achieve routing efficiency comparable to engineered railway infrastructures.")
    
    add_body_p(doc, "Todorov et al. (2012) developed the MuJoCo physics engine, providing a convex, contact-rich multi-body dynamics simulator capable of resolving complex frictional contact constraints and terrain interactions at faster-than-real-time rates.")
    
    add_body_p(doc, "Williams et al. (2016, 2017) introduced Model Predictive Path Integral (MPPI) control for autonomous ground vehicles operating at extreme dynamical limits, demonstrating real-time GPU-accelerated trajectory synthesis across complex obstacle fields.")
    
    add_body_p(doc, "Stone et al. (2017) and Green et al. (2017) identified the neural circuit architecture of the insect central complex, showing that Drosophila PFL2 and PFL3 neurons act as direct steering comparators between internal heading attractors and visual goal cues, inspiring frugal biological steering mechanisms.")
    
    add_body_p(doc, "Parr et al. (2022) consolidated Active Inference into an executable computational framework, proving that Expected Free Energy minimization naturally unifies goal-directed exploitation (pragmatic value) with curiosity-driven exploration (epistemic value) in continuous robotic domains.")

    add_heading_2(doc, "3.2", "Gap Identification")
    add_body_p(doc, "From the survey of existing literature, research in autonomous robotic navigation remains severely fragmented across two disparate, mutually isolated paradigms:")
    add_body_p(doc, "First, classical engineering navigation systems (such as ROS MoveBase, AMCL, and DWA) rely entirely on globally privileged Cartesian coordinates, artificial obstacle inflation layers, and static deterministic routines. These systems possess zero introspective awareness: when encountering novel kinematic slip, caster vibration, or sensor occlusion, they fail silently or enter irrecoverable recovery rotations.")
    add_body_p(doc, "Second, contemporary deep reinforcement learning and end-to-end neural network approaches treat navigation as an ungrounded black-box regression problem. They require prohibitive compute clusters, exhibit extreme sensitivity to hyperparameter initialization, suffer from catastrophic forgetting upon encountering new environments, and completely lack verifiable code-execution boundaries.")
    add_body_p(doc, "Furthermore, while individual theoretical neurobiology models—such as CANN head-direction rings, grid-cell tori, Physarum flux networks, and STDP plasticity—have been simulated in isolation as academic toy models, almost no research integrates these multi-organ biological principles into a single, unified, embodied cognitive organism operating under strict contact physics and real-time embedded constraints.")
    add_body_p(doc, "This dissertation directly bridges that gap by engineering CARL-DX: a unified, 2,114-unit neuromorphic computational architecture that integrates continuous topological attractor networks, active inference MPPI trajectory synthesis, Physarum hydrodynamic routing, and permission-gated introspective self-modification. By enforcing a formal Abstract Syntax Tree (AST) anti-cheat quarantine, CARL-DX proves that biological autonomy can be achieved purely through grounded sensorimotor contingencies without privileged simulator coordinates, while executing within 30 ms on embedded hardware.")

    print("Front matter and Chapters 1-3 ready.")
