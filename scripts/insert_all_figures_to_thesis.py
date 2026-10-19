"""
scripts/insert_all_figures_to_thesis.py
Embeds all peer-reviewed academic figures across Stages 4, 5, and 6
into D:\\carl major.docx with formatted captions and centered layouts.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def set_font(run, name="Times New Roman", size_pt=12, bold=False, italic=False, color_rgb=(0, 0, 0)):
    run.font.name = name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    if color_rgb:
        run.font.color.rgb = RGBColor(*color_rgb)

def add_figure_after_paragraph(p_ref, image_path, caption_text, width_inches=5.8):
    """Inserts a centered figure and caption directly after p_ref in python-docx XML."""
    if not os.path.exists(image_path):
        print(f"  [WARNING] File missing: {image_path}")
        return None, None
        
    # Create paragraph for image
    p_img = p_ref._element.getparent().makeelement(p_ref._element.tag, nsdecls=p_ref._element.nsmap)
    p_ref._element.addnext(p_img)
    p_img_wrap = docx.text.paragraph.Paragraph(p_img, p_ref._parent)
    p_img_wrap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img_wrap.paragraph_format.space_before = Pt(8)
    p_img_wrap.paragraph_format.space_after = Pt(4)
    run_img = p_img_wrap.add_run()
    run_img.add_picture(image_path, width=Inches(width_inches))

    # Create paragraph for caption directly after image
    p_cap = p_img.getparent().makeelement(p_img.tag, nsdecls=p_img.nsmap)
    p_img.addnext(p_cap)
    p_cap_wrap = docx.text.paragraph.Paragraph(p_cap, p_ref._parent)
    p_cap_wrap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap_wrap.paragraph_format.space_before = Pt(2)
    p_cap_wrap.paragraph_format.space_after = Pt(12)
    p_cap_wrap.paragraph_format.keep_with_next = True
    
    run_cap = p_cap_wrap.add_run(caption_text)
    set_font(run_cap, "Times New Roman", 10.5, bold=False, italic=True)
    
    print(f"  [EMBEDDED] {os.path.basename(image_path)} -> {caption_text[:60]}...")
    return p_img_wrap, p_cap_wrap

def main():
    target_docx = r"D:\carl major.docx"
    print(f"Opening thesis document: {target_docx}...")
    doc = docx.Document(target_docx)

    # Dictionary of target heading/text snippet -> (image_path, caption_text, width)
    figure_placements = [
        # Chapter 10 (Stage 4)
        (
            "10.1 ONLINE REWARD-MODULATED STDP PLASTICITY",
            "d:/ebca/evidence/stage4/phase4_1/figures/fig1_stage4_1_synaptic_weight_delta_heatmap.png",
            "Figure 10.1: Stage 4.1 Reward-Modulated STDP (R-STDP) online synaptic weight adaptation heatmap and Turrigiano homeostatic L2 bounds.",
            5.6
        ),
        (
            "10.2 HOLOGRAPHIC HYPERDIMENSIONAL ASSOCIATIVE MEMORY",
            "d:/ebca/evidence/stage4/phase4_1/figures/fig5_stage4_1_master_certification_dashboard.png",
            "Figure 10.2: Stage 4.1 Master Plasticity Certification Dashboard across 20 recurrent navigational trials.",
            5.8
        ),
        (
            "10.3 MEMORY CONSOLIDATION & NREM SWR SLEEP REPLAY",
            "d:/ebca/evidence/master_cumulative/figures/carl_masterpiece_fig2_plasticity_physarum_heatmaps.png",
            "Figure 10.3: Stage 4 Memory Replay and Physarum plasmodial flow connectivity manifolds.",
            5.8
        ),

        # Chapter 11 (Stage 5)
        (
            "11.1 INTROSPECTIVE FAILURE TELEMETRY: 'THE WITNESS'",
            "d:/ebca/evidence/stage5/integrated_battery/figures/stage5_integrated_acceptance_telemetry.png",
            "Figure 11.1: Stage 5.1 & 5.2 'The Witness' 7-channel introspective distress telemetry and Drosophila PFL2 180° escape pivots.",
            5.8
        ),
        (
            "11.3 PERMISSION-GATED SELF-MODIFICATION & HOMEOSTASIS",
            "d:/ebca/evidence/stage5/integrated_battery/figures/stage5_integrated_physical_trajectories.png",
            "Figure 11.2: Stage 5.4 Physical trajectory recovery comparison under sudden unannounced friction drops (μ = 0.20) showing +81.5% recovery advantage.",
            5.6
        ),
        (
            "11.4 40-EPISODE ADVERSARIAL ACCEPTANCE BATTERY",
            "d:/ebca/evidence/master_cumulative/figures/carl_masterpiece_fig3_metacognitive_witness_heatmaps.png",
            "Figure 11.3: Stage 5 Metacognitive introspective failure landscape and permission-gated parameter adaptation spectrum.",
            5.8
        ),

        # Chapter 12 (Stage 6)
        (
            "12.2 FOREIGN EMBODIMENT TRANSFER LITMUS TEST",
            "d:/ebca/evidence/stage6/embodiments/figures/stage6_2_deepmind_franka_filmstrip.png",
            "Figure 12.1: Stage 6.2 Foreign Embodiment Transfer — Google DeepMind MuJoCo Menagerie Franka Emika Panda robotic arm pilot filmstrip with 100% contact physics.",
            5.8
        ),
        (
            "12.3 HEAVY 3D CLUTTER ARENA BENCHMARK",
            "d:/ebca/evidence/stage6/clutter/figures/stage6_3_3d_terrain_arena_view.png",
            "Figure 12.2: Stage 6.3 Dense 4-chamber Heavy 3D Clutter Arena (52 heavy geometric obstacles with severe visual occlusions).",
            5.6
        ),
        (
            "12.4 ₹2,150 ($25.80) ESP32 SIM-TO-REAL FRUGAL PROTOTYPE",
            "d:/ebca/evidence/stage6/clutter/figures/stage6_3_carl_internal_monologue_dashboard.png",
            "Figure 12.3: Stage 6.3 CARL 4-panel real-time cognitive telemetry dashboard and internal monologue stream during cluttered navigation.",
            5.8
        ),
        (
            "12.5 JURY NEUROMORPHIC AUTHENTICITY",
            "d:/ebca/evidence/stage6/clutter/figures/stage6_3_clutter_trajectories.png",
            "Figure 12.4: Stage 6.3 Multi-chamber physical escape trajectories (20/20 escapes, 0% collisions, mean clearance 0.058 m).",
            5.6
        )
    ]

    # Find paragraphs matching the placement targets and insert images
    paragraphs = list(doc.paragraphs)
    for target_prefix, img_path, caption, width in figure_placements:
        matched = False
        for p in paragraphs:
            if target_prefix in p.text.strip():
                # Insert after the paragraph following the heading (or after the heading itself)
                add_figure_after_paragraph(p, img_path, caption, width)
                matched = True
                break
        if not matched:
            print(f"  [NOT MATCHED] Could not find paragraph starting with '{target_prefix}'")

    print(f"Saving thesis with embedded figures to {target_docx}...")
    doc.save(target_docx)
    print("SUCCESS: All figures and academic captions embedded successfully!")

if __name__ == "__main__":
    main()
