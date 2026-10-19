"""
dissertation_front_matter.py
Generates the complete Front Matter matching JNTUH project_report_2.pdf format.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dissertation_helpers import add_page_break, set_cell_margins

def build_front_matter(doc):
    # -------------------------------------------------------------
    # 1. TITLE / COVER PAGE
    # -------------------------------------------------------------
    p0 = doc.add_paragraph()
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p0.paragraph_format.space_before = Pt(12)
    p0.paragraph_format.space_after = Pt(4)
    r = p0.add_run("A Major Project Report\non")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(14)
    r_title = p_title.add_run("DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS")
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(16)
    r_title.font.bold = True
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(4)
    r_sub = p_sub.add_run("Submitted in partial fulfilment of the requirements for the\naward of the degree of")
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    
    p_deg = doc.add_paragraph()
    p_deg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_deg.paragraph_format.space_after = Pt(12)
    r_deg = p_deg.add_run("BACHELOR OF TECHNOLOGY & MASTER OF TECHNOLOGY (IDP)\nIn\nMECHANICAL ENGINEERING")
    r_deg.font.name = 'Times New Roman'
    r_deg.font.size = Pt(13)
    r_deg.font.bold = True
    
    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_after = Pt(2)
    r_by = p_by.add_run("By")
    r_by.font.name = 'Times New Roman'
    r_by.font.size = Pt(12)
    
    p_name = doc.add_paragraph()
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_name.paragraph_format.space_after = Pt(10)
    r_name = p_name.add_run("Manas Sadashiv               22011P0310\nV B. Tech\nB. Tech + M. Tech (IDP - AMS)")
    r_name.font.name = 'Times New Roman'
    r_name.font.size = Pt(12)
    r_name.font.bold = True
    
    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_after = Pt(8)
    r_guide = p_guide.add_run("Under the Guidance of\nDr. M Indira Rani\nProfessor of Mechanical Engineering")
    r_guide.font.name = 'Times New Roman'
    r_guide.font.size = Pt(12)
    r_guide.font.bold = True
    
    logo_path = r"D:\ebca\scratch\docx_media\image1.png"
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_before = Pt(4)
        p_logo.paragraph_format.space_after = Pt(8)
        r_logo = p_logo.add_run()
        r_logo.add_picture(logo_path, width=Inches(1.2))
        
    p_dept = doc.add_paragraph()
    p_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept.paragraph_format.space_after = Pt(2)
    r_dept = p_dept.add_run("DEPARTMENT OF MECHANICAL ENGINEERING\nJNTUH UNIVERSITY COLLEGE OF ENGINEERING, SCIENCE AND TECHNOLOGY\nHYDERABAD (AUTONOMOUS)\nKUKATPALLY, HYDERABAD-500085, TELANGANA, INDIA\n2025-2026")
    r_dept.font.name = 'Times New Roman'
    r_dept.font.size = Pt(11)
    r_dept.font.bold = True

    # -------------------------------------------------------------
    # 2. DECLARATION (Page i)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_h = doc.add_paragraph()
    p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_h.paragraph_format.space_before = Pt(12)
    p_h.paragraph_format.space_after = Pt(18)
    r_h = p_h.add_run("JNTUH UNIVERSITY COLLEGE OF ENGINEERING, SCIENCE AND TECHNOLOGY\nKUKATPALLY, HYDERABAD-500085\nDepartment of Mechanical Engineering\n\nDECLARATION")
    r_h.font.name = 'Times New Roman'
    r_h.font.size = Pt(12)
    r_h.font.bold = True
    
    p_dec = doc.add_paragraph()
    p_dec.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_dec.paragraph_format.line_spacing = 1.3
    p_dec.paragraph_format.space_after = Pt(36)
    r_dec = p_dec.add_run('I, Manas Sadashiv (22011P0310), hereby declare that this major project report entitled "DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS" submitted to the JNTUH University College of Engineering, Science and Technology, Hyderabad in partial fulfilment of the requirements for the award of the degree of Bachelor of Technology & Master of Technology (Integrated Dual Degree Programme) in Mechanical Engineering is a record of original, bona fide work carried out by me under the supervision and guidance of Dr. M Indira Rani, Professor of Mechanical Engineering, and that it has not formed the basis for the award of any Degree, Diploma, Fellowship, or other similar titles to any candidate in this or any other university.')
    r_dec.font.name = 'Times New Roman'
    r_dec.font.size = Pt(11.5)
    
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sig = p_sig.add_run("Manas Sadashiv\n22011P0310\nDepartment of Mechanical Engineering\nJNTUH-UCESTH")
    r_sig.font.name = 'Times New Roman'
    r_sig.font.size = Pt(11.5)
    r_sig.font.bold = True

    # -------------------------------------------------------------
    # 3. CERTIFICATE (Page ii)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_ch = doc.add_paragraph()
    p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ch.paragraph_format.space_before = Pt(12)
    p_ch.paragraph_format.space_after = Pt(18)
    r_ch = p_ch.add_run("JNTUH UNIVERSITY COLLEGE OF ENGINEERING, SCIENCE AND TECHNOLOGY\nKUKATPALLY, HYDERABAD-500085\nDepartment of Mechanical Engineering\n\nCERTIFICATE")
    r_ch.font.name = 'Times New Roman'
    r_ch.font.size = Pt(12)
    r_ch.font.bold = True
    
    p_crt = doc.add_paragraph()
    p_crt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_crt.paragraph_format.line_spacing = 1.3
    p_crt.paragraph_format.space_after = Pt(60)
    r_crt = p_crt.add_run('This is to certify that the major project report entitled "DESIGN AND DEVELOPMENT OF A DIGITAL TWIN FRAMEWORK FOR BIOLOGICALLY INSPIRED COGNITIVE ROBOTIC SYSTEMS", submitted by Manas Sadashiv (22011P0310) in partial fulfilment of the requirements for the award of the degree of BACHELOR OF TECHNOLOGY & MASTER OF TECHNOLOGY (IDP) in Mechanical Engineering from JNTUH University College of Engineering, Science and Technology, Hyderabad during the academic year 2025-2026, is a record of bona fide work carried out under our supervision and guidance.')
    r_crt.font.name = 'Times New Roman'
    r_crt.font.size = Pt(11.5)
    
    tbl_cert = doc.add_table(rows=1, cols=2)
    tbl_cert.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    c1, c2 = tbl_cert.rows[0].cells
    c1.width = Inches(3.2)
    c2.width = Inches(3.2)
    
    p_c1 = c1.paragraphs[0]
    p_c1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r_c1 = p_c1.add_run("Dr. M Indira Rani\nInternal Guide & Supervisor\nProfessor of Mechanical Engineering\nDept. of Mechanical Engineering\nJNTUH-UCESTH")
    r_c1.font.name = 'Times New Roman'
    r_c1.font.size = Pt(11)
    r_c1.font.bold = True
    
    p_c2 = c2.paragraphs[0]
    p_c2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_c2 = p_c2.add_run("Dr. S Naga Sarada\nHead of the Department\nProfessor of Mechanical Engineering\nDept. of Mechanical Engineering\nJNTUH-UCESTH")
    r_c2.font.name = 'Times New Roman'
    r_c2.font.size = Pt(11)
    r_c2.font.bold = True

    # -------------------------------------------------------------
    # 4. ACKNOWLEDGEMENT (Page iii)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_ak_t = doc.add_paragraph()
    p_ak_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ak_t.paragraph_format.space_before = Pt(14)
    p_ak_t.paragraph_format.space_after = Pt(16)
    r_ak_t = p_ak_t.add_run("ACKNOWLEDGEMENT")
    r_ak_t.font.name = 'Times New Roman'
    r_ak_t.font.size = Pt(13)
    r_ak_t.font.bold = True
    
    p_ak1 = doc.add_paragraph()
    p_ak1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ak1.paragraph_format.line_spacing = 1.3
    p_ak1.paragraph_format.space_after = Pt(8)
    r_ak1 = p_ak1.add_run("The satisfaction and euphoria that accompany the successful completion of this major research project would be incomplete without expressing my sincere gratitude to the mentors and guides whose constant encouragement, scientific rigor, and academic support made it possible.")
    r_ak1.font.name = 'Times New Roman'
    r_ak1.font.size = Pt(11.5)
    
    p_ak2 = doc.add_paragraph()
    p_ak2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ak2.paragraph_format.line_spacing = 1.3
    p_ak2.paragraph_format.space_after = Pt(8)
    r_ak2 = p_ak2.add_run("I profoundly thank my supervisor, Dr. M Indira Rani, Professor, Department of Mechanical Engineering, JNTUH University College of Engineering, Science and Technology, Hyderabad, for her visionary guidance, insightful critique, and continuous technical support throughout the conception, modeling, and validation phases of this research.")
    r_ak2.font.name = 'Times New Roman'
    r_ak2.font.size = Pt(11.5)
    
    p_ak3 = doc.add_paragraph()
    p_ak3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ak3.paragraph_format.line_spacing = 1.3
    p_ak3.paragraph_format.space_after = Pt(24)
    r_ak3 = p_ak3.add_run("I express my sincere thanks to Dr. S Naga Sarada, Professor and Head, Department of Mechanical Engineering, JNTUH-UCESTH, for providing access to computing and laboratory infrastructure. Finally, I extend my heartfelt gratitude to my family, colleagues, and peers for their unwavering patience and support.")
    r_ak3.font.name = 'Times New Roman'
    r_ak3.font.size = Pt(11.5)
    
    p_ak_sig = doc.add_paragraph()
    p_ak_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_aks = p_ak_sig.add_run("Manas Sadashiv\n(22011P0310)")
    r_aks.font.name = 'Times New Roman'
    r_aks.font.size = Pt(11.5)
    r_aks.font.bold = True

    # -------------------------------------------------------------
    # 5. ABSTRACT (Page iv)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_ab_t = doc.add_paragraph()
    p_ab_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ab_t.paragraph_format.space_before = Pt(14)
    p_ab_t.paragraph_format.space_after = Pt(14)
    r_ab_t = p_ab_t.add_run("ABSTRACT")
    r_ab_t.font.name = 'Times New Roman'
    r_ab_t.font.size = Pt(13)
    r_ab_t.font.bold = True
    
    p_ab1 = doc.add_paragraph()
    p_ab1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ab1.paragraph_format.line_spacing = 1.3
    p_ab1.paragraph_format.space_after = Pt(6)
    r_ab1 = p_ab1.add_run("Autonomous mobile robotics faces a fundamental divide between compute-intensive deep reinforcement learning stacks—which operate as ungrounded black boxes prone to catastrophic forgetting—and rigid classical navigation systems that require privileged simulator state and non-biological global coordinate transforms. This dissertation presents CARL-DX (Cognitive Autonomous Robotic Lifelong Digital-eXperiment), a 2,114-unit neuromorphic computational architecture integrated with a contact-rich multi-body physics digital twin and demonstrated to be deployable on ultra-frugal embedded microcontrollers.")
    r_ab1.font.name = 'Times New Roman'
    r_ab1.font.size = Pt(11.5)
    
    p_ab2 = doc.add_paragraph()
    p_ab2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_ab2.paragraph_format.line_spacing = 1.3
    p_ab2.paragraph_format.space_after = Pt(6)
    r_ab2 = p_ab2.add_run("CARL-DX develops through a rigorously certified six-stage developmental continuum. In Stage 1, anonymous motor babbling autonomously derives sensorimotor contingencies, linear forward momentum, and kinematic wheel-slip tracking without kinematic priors. In Stage 2, a 2,114-unit Continuous Attractor Neural Network (CANN)—comprising a 64-unit head-direction ring, a 1,024-unit grid-cell torus, and a 1,026-unit recurrent reservoir—is coupled to an allocentric log-odds occupancy memory, achieving prospective trajectory deliberation with 0.00% collisions across 40 complex mazes. Stage 3 synthesizes continuous action via Model Predictive Path Integral (MPPI) control under Active Inference (Expected Free Energy minimization), overcoming dead ends, friction drops (mu=0.20), and motor drag perturbations with 100% escape rates and sub-28 ms cycle latency. Stage 4 introduces reward-modulated STDP plasticity and 2,048-D holographic memory. Stage 5 incorporates an introspective 'Witness' organ and Drosophila PFL2 steering for permission-gated self-repair. Stage 6 validates cross-embodiment transfer across four diverse mechanical morphologies and demonstrates frugal execution on an ESP32 hardware platform (33.6 KB SRAM). Throughout, an Abstract Syntax Tree (AST) anti-cheat barrier mathematically guarantees zero leakage of privileged simulation state into the cognitive loop.")
    r_ab2.font.name = 'Times New Roman'
    r_ab2.font.size = Pt(11.5)

    # -------------------------------------------------------------
    # 6. TABLE OF CONTENTS (Page v - vi)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_toc_t = doc.add_paragraph()
    p_toc_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_t.paragraph_format.space_before = Pt(14)
    p_toc_t.paragraph_format.space_after = Pt(12)
    r_toc_t = p_toc_t.add_run("TABLE OF CONTENTS")
    r_toc_t.font.name = 'Times New Roman'
    r_toc_t.font.size = Pt(13)
    r_toc_t.font.bold = True
    
    toc_items = [
        ("DECLARATION", "i"),
        ("CERTIFICATE", "ii"),
        ("ACKNOWLEDGEMENT", "iii"),
        ("ABSTRACT", "iv"),
        ("LIST OF FIGURES AND GRAPHS", "viii"),
        ("LIST OF TABLES", "x"),
        ("NOMENCLATURE AND SYMBOLS", "xi"),
        ("ABBREVIATIONS AND ACRONYMS", "xii"),
        ("CHAPTER-1    INTRODUCTION", "1"),
        ("    1.1  Background & Motivation", "1"),
        ("    1.2  Problem Statement & Research Challenges", "2"),
        ("    1.3  Developmental Architecture Overview", "3"),
        ("    1.4  Objectives of Present Work", "4"),
        ("    1.5  Organization of the Dissertation", "4"),
        ("CHAPTER-2    THEORETICAL FOUNDATIONS AND EMBODIED BACKGROUND", "5"),
        ("    2.1  Sensorimotor Grounding and Embodied Cognition", "5"),
        ("    2.2  Continuous Attractor Neural Networks (CANNs)", "6"),
        ("    2.3  Active Inference and Expected Free Energy", "8"),
        ("    2.4  Model Predictive Path Integral (MPPI) Control", "9"),
        ("    2.5  Bio-Physical Flux Routing and Hyperdimensional Computing", "11"),
        ("CHAPTER-3    LITERATURE REVIEW", "12"),
        ("    3.1  Literature Survey", "12"),
        ("    3.2  Gap Identification", "16"),
        ("CHAPTER-4    PLATFORM DESIGN AND SIMULATION METHODOLOGY", "17"),
        ("    4.1  Mechatronic Architecture and Hardware Specifications", "17"),
        ("    4.2  MuJoCo Contact-Rich Multi-Body Digital Twin", "19"),
        ("    4.3  Architectural Invariants and Decision-Pipeline AST Quarantine", "22"),
        ("CHAPTER-5    SENSORIMOTOR GROUNDING AND MOTOR BABBLING (STAGE 1)", "25"),
        ("    5.1  Autonomous Motor Babbling and Topology Discovery", "25"),
        ("    5.2  Sensorimotor Contingency Discovery", "26"),
        ("    5.3  Dynamical Stability and Slip Estimation", "27"),
        ("CHAPTER-6    GENERATIVE WORLD AND SELF-MODELING (STAGE 2)", "29"),
        ("    6.1  2,114-Unit Continuous Attractor Neural Network", "29"),
        ("    6.2  Grounded World Model and Allocentric Occupancy Memory", "31"),
        ("    6.3  Prospective Deliberation and Rotational Swept-Cone Veto", "33"),
        ("CHAPTER-7    CONTINUOUS ACTION SYNTHESIS AND ACTIVE INFERENCE (STAGE 3)", "35"),
        ("    7.1  CANN Causal Coupling Battery", "35"),
        ("    7.2  Counterfactual Rollout Fidelity and Non-LOS Memory Necessity", "37"),
        ("    7.3  Continuous MPPI Action Synthesis", "39"),
        ("    7.4  Autonomous Active Inference and Exploration", "41"),
        ("    7.5  Physical Perturbation and Environmental Adaptation", "43"),
        ("    7.6  Bio-Physical Flux Routing and HDC Motor Synergies", "45"),
        ("    7.7  Multi-Modal Retinal Vision and Gaze Dynamics", "46"),
        ("CHAPTER-8    EXPERIMENTAL RESULTS AND BENCHMARK VALIDATION", "49"),
        ("    8.1  Empirical Performance Analysis", "49"),
        ("    8.2  Real-Time Latency and Computational Complexity Profile", "51"),
        ("    8.3  Environmental Adaptation under Extreme Perturbations", "53"),
        ("    8.4  Bio-Physical Flux Routing and Motor Synergies", "54"),
        ("    8.5  Multi-Modal Perception and Efference Copy Dynamics", "55"),
        ("    8.6  Causal Necessity and Ablation Effect Sizes", "56"),
        ("    8.7  AST Anti-Cheat Decision-Pipeline Quarantine Audit", "57"),
        ("CHAPTER-9    ENGINEERING SYNTHESIS AND CONTRIBUTIONS", "59"),
        ("    9.1  Summary of Core Engineering Contributions", "59"),
        ("    9.2  Validation of Foundational Architectural Invariants", "60"),
        ("    9.3  Comparative Analysis with State-of-the-Art Robotic Stacks", "61"),
        ("CHAPTER-10   AUTOPOIETIC LIFELONG MEMORY AND PERSISTENCE (STAGE 4)", "63"),
        ("    10.1 Reward-Modulated STDP Synaptic Plasticity", "63"),
        ("    10.2 2,048-D FHRR Holographic Associative Memory", "64"),
        ("    10.3 SWR Reverse Replay and Sleep Consolidation", "65"),
        ("    10.4 Autopoietic Lifelong Persistence (GIS-901 Atomic WAL)", "66"),
        ("CHAPTER-11   METACOGNITION AND PERMISSION-GATED SELF-MODIFICATION (STAGE 5)", "67"),
        ("    11.1 Introspective Failure Telemetry Monitoring", "67"),
        ("    11.2 Abductive Causal Attribution & Drosophila PFL2 Steering", "68"),
        ("    11.3 Permission-Gated Self-Modification & Turrigiano Homeostasis", "69"),
        ("    11.4 40-Episode Adversarial Acceptance Battery", "70"),
        ("CHAPTER-12   FOREIGN EMBODIMENT AND PHYSICAL PROTOTYPING (STAGE 6)", "71"),
        ("    12.1 Cross-Embodiment Transfer Across Diverse Morphologies", "71"),
        ("    12.2 Heavy 3D Clutter Arena Stress Benchmark", "72"),
        ("    12.3 Frugal ESP32 Embedded Prototype Design", "73"),
        ("    12.4 Neuromorphic Authenticity Verification & Council Verdict", "74"),
        ("CHAPTER-13   CONCLUSIONS AND FUTURE SCOPE (STAGE 7 FUTURE WORK)", "75"),
        ("    13.1 Conclusions", "75"),
        ("    13.2 Limitations", "75"),
        ("    13.3 Future Scope: Stage 7 Physical Deployment and Swarm Extensions", "76"),
        ("REFERENCES", "77"),
        ("APPENDIX A   COMPLETE MATHEMATICAL FORMULATIONS", "81"),
        ("APPENDIX B   HYPERPARAMETER AND CONFIGURATION TABLES", "83")
    ]
    
    tbl_toc = doc.add_table(rows=len(toc_items) + 1, cols=2)
    tbl_toc.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    hdr = tbl_toc.rows[0]
    hdr.cells[0].text = "TITLE"
    hdr.cells[1].text = "Page No."
    hdr.cells[0].paragraphs[0].runs[0].font.bold = True
    hdr.cells[1].paragraphs[0].runs[0].font.bold = True
    hdr.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hdr.cells[0].width = Inches(5.6)
    hdr.cells[1].width = Inches(1.0)
    
    for idx, (title, pg) in enumerate(toc_items):
        row = tbl_toc.rows[idx + 1]
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
        if "CHAPTER" in title or title in ["DECLARATION", "CERTIFICATE", "ACKNOWLEDGEMENT", "ABSTRACT", "REFERENCES", "APPENDIX A", "APPENDIX B"]:
            p0.runs[0].font.bold = True
            p1.runs[0].font.bold = True
        set_cell_margins(c0, top=25, bottom=25, left=40, right=40)
        set_cell_margins(c1, top=25, bottom=25, left=40, right=40)

    # -------------------------------------------------------------
    # 7. LIST OF FIGURES & GRAPHS (Page vii)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_lof_t = doc.add_paragraph()
    p_lof_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lof_t.paragraph_format.space_before = Pt(14)
    p_lof_t.paragraph_format.space_after = Pt(12)
    r_lof_t = p_lof_t.add_run("LIST OF FIGURES AND GRAPHS")
    r_lof_t.font.name = 'Times New Roman'
    r_lof_t.font.size = Pt(13)
    r_lof_t.font.bold = True
    
    figures_list = [
        ("Figure 4.1", "Master mechatronic schematic and CAD architecture of CARL", "18"),
        ("Figure 4.2", "2D differential-drive kinematic schematic showing wheelbase and axle geometry", "19"),
        ("Figure 4.3", "MuJoCo multi-body simulation digital twin render with contact geometries", "21"),
        ("Figure 4.4", "Master embodied architecture of CARL, detailing zero-copy sensory pipeline", "23"),
        ("Figure 4.5", "Cognitive isolation barrier and AST anti-cheat quarantine boundary", "24"),
        ("Figure 5.1", "Stage 1 sensorimotor grounding architecture and 6-channel motor babbling", "25"),
        ("Graph 5.1", "Stage 1.1 empirical sensorimotor contingency cross-correlation matrix", "27"),
        ("Graph 5.2", "Stage 1.1 10,000-tick dynamical stability phase space trajectory", "28"),
        ("Graph 5.3", "Stage 1.1 friction gradient response and kinematic wheel-slip tracking", "28"),
        ("Figure 6.1", "Stage 2.1 2,114-unit continuous attractor neural network architecture", "30"),
        ("Graph 6.1", "Physical reality vs internal CANN self-model homing trajectory", "30"),
        ("Graph 6.2", "CANN 1D ring attractor activity packet and angular bump dynamics", "31"),
        ("Graph 6.3", "2D grid cell torus (1,024 units) spatial activation profile", "31"),
        ("Figure 6.2", "Allocentric raster occupancy memory field generated via inverse sonar model", "32"),
        ("Graph 6.4", "Model-based prospective trajectory evaluation and rotational swept-cone veto", "34"),
        ("Graph 6.5", "Stage 2 canonical maze navigation clearance trajectory across challenge mazes", "34"),
        ("Graph 7.1", "Stage 3.1 CANN causal ablation battery: action divergence distributions", "36"),
        ("Graph 7.2", "Stage 3.1 candidate trajectory rank correlation distributions", "36"),
        ("Graph 7.3", "Stage 3.2 individual counterfactual branch fidelity vs physical MuJoCo steps", "38"),
        ("Graph 7.4", "Stage 3.2 non-LOS spatial memory necessity evaluation across 5 challenge families", "38"),
        ("Figure 7.1", "Stage 3.3 Model Predictive Path Integral (MPPI) control architecture", "40"),
        ("Graph 7.5", "Stage 3.3 continuous MPPI trajectory rollout and sampling distribution", "40"),
        ("Graph 7.6", "Stage 3.3 autonomous corridor escape and target acquisition", "41"),
        ("Graph 8.1", "Stage 3.3 empirical performance benchmarks from master defense trials", "50"),
        ("Graph 8.2", "Real-time cognitive cycle latency distribution across 50 episodes", "52"),
        ("Graph 8.3", "Stage 3.5 empirical performance matrix and endocrine adaptation to friction drops", "53"),
        ("Graph 8.4", "Stage 3.6 Physarum plasmodial streamlines and fluid flux concentration", "54"),
        ("Graph 8.5", "Stage 3.6 2,048-D Hyperdimensional Computing (HDC) motor synergy clustering", "55"),
        ("Graph 8.6", "Stage 3.7 Retinal 64x64 RGB vision, spatial feature maps and attention saliency", "56"),
        ("Graph 8.7", "Stage 3.7 Active head gaze dynamics and efference copy reafference cancellation", "56"),
        ("Figure 10.1", "Stage 4.1 Reward-Modulated STDP (R-STDP) online synaptic weight matrix evolution", "64"),
        ("Figure 11.1", "Stage 5.1 & 5.2 'The Witness' 7-channel introspective telemetry signal traces", "68"),
        ("Figure 11.2", "Stage 5.4 Physical trajectory recovery comparison under motor drag failure", "70"),
        ("Figure 12.1", "Stage 6.2 Foreign Embodiment Transfer — Google DeepMind MuJoCo Franka Panda arm", "71"),
        ("Figure 12.2", "Stage 6.2 Foreign Embodiment Transfer — Skid-Steer Rover and Holonomic Omni-base", "72"),
        ("Figure 12.3", "Stage 6.3 Dense 4-chamber Heavy 3D Clutter Arena environment", "73"),
        ("Figure 12.4", "Stage 6.3 Multi-Chamber Trajectory Clearance Heatmap across 20 trials", "74")
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
    # 8. LIST OF TABLES (Page viii)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_lot_t = doc.add_paragraph()
    p_lot_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lot_t.paragraph_format.space_before = Pt(14)
    p_lot_t.paragraph_format.space_after = Pt(12)
    r_lot_t = p_lot_t.add_run("LIST OF TABLES")
    r_lot_t.font.name = 'Times New Roman'
    r_lot_t.font.size = Pt(13)
    r_lot_t.font.bold = True
    
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
    # 9. NOMENCLATURE & ABBREVIATIONS (Page ix)
    # -------------------------------------------------------------
    add_page_break(doc)
    p_nom_t = doc.add_paragraph()
    p_nom_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_nom_t.paragraph_format.space_before = Pt(14)
    p_nom_t.paragraph_format.space_after = Pt(12)
    r_nom_t = p_nom_t.add_run("NOMENCLATURE AND ABBREVIATIONS")
    r_nom_t.font.name = 'Times New Roman'
    r_nom_t.font.size = Pt(13)
    r_nom_t.font.bold = True
    
    p_nom_sub1 = doc.add_paragraph()
    r_n1 = p_nom_sub1.add_run("Symbols and Variables")
    r_n1.font.name = 'Times New Roman'
    r_n1.font.size = Pt(11.5)
    r_n1.font.bold = True
    
    symbols_data = [
        ("u", "Control action vector [u_L, u_R]^T representing normalized wheel motor commands in [-1.0, 1.0]"),
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
        p.paragraph_format.space_after = Pt(3)
        r_s = p.add_run(f"{sym:15s}: ")
        r_s.font.name = 'Times New Roman'
        r_s.font.size = Pt(10)
        r_s.font.bold = True
        r_d = p.add_run(desc)
        r_d.font.name = 'Times New Roman'
        r_d.font.size = Pt(10)
        
    p_nom_sub2 = doc.add_paragraph()
    p_nom_sub2.paragraph_format.space_before = Pt(8)
    r_n2 = p_nom_sub2.add_run("Abbreviations and Acronyms")
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
        p.paragraph_format.space_after = Pt(3)
        r_a = p.add_run(f"{abb:10s}: ")
        r_a.font.name = 'Times New Roman'
        r_a.font.size = Pt(10)
        r_a.font.bold = True
        r_d = p.add_run(desc)
        r_d.font.name = 'Times New Roman'
        r_d.font.size = Pt(10)

    print("Front matter generated successfully.")
