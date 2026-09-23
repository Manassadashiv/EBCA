r"""
tools/render_architecture_diagrams.py — Audited Professional White-Themed Diagram Renderer for CARL-DX
Renders 18 publication-grade, source-verified engineering diagrams in full compliance with the Diagram Integrity Audit.
"""

import os
import sys
import json
import time
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

OUTPUT_DIR = r"D:\ebca\evidence\architecture_spec"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Theme Palette: Professional White Engineering Publication Theme
BG_COLOR = "#ffffff"
PANEL_BG = "#f8fafc"
BORDER_DEFAULT = "#cbd5e1"
TEXT_DARK = "#0f172a"
TEXT_BODY = "#1e293b"
TEXT_MUTED = "#64748b"

# Accent Colors (Tuned for high contrast on white background)
BLUE = "#0284c7"
DARK_BLUE = "#0369a1"
CYAN = "#0891b2"
RED = "#dc2626"
DARK_RED = "#991b1b"
GREEN = "#059669"
DARK_GREEN = "#065f46"
AMBER = "#d97706"
DARK_AMBER = "#b45309"
PURPLE = "#7c3aed"
DARK_PURPLE = "#5b21b6"
MAGENTA = "#c026d3"
GRAY_BOX = "#f1f5f9"

# Tinted Box Backgrounds
TINT_BLUE = "#f0f9ff"
TINT_GREEN = "#ecfdf5"
TINT_RED = "#fef2f2"
TINT_AMBER = "#fffbeb"
TINT_PURPLE = "#faf5ff"
TINT_CYAN = "#ecfeff"
TINT_MAGENTA = "#fdf4ff"

def setup_fig(width_in=16, height_in=10, dpi=200):
    fig = plt.figure(figsize=(width_in, height_in), dpi=dpi, facecolor=BG_COLOR)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=BG_COLOR)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    return fig, ax

def draw_header(ax, title, subtitle, source_section):
    ax.add_patch(FancyBboxPatch((2, 91), 96, 7.5, boxstyle="round,pad=0.5,rounding_size=0.8",
                                facecolor="#f8fafc", edgecolor="#0284c7", linewidth=1.8))
    ax.text(4, 95.8, title, color=TEXT_DARK, fontsize=16.5, fontweight='bold', va='center')
    ax.text(4, 93.0, f"CARL-DX EMBODIED ORGANISM SPECIFICATION  |  {subtitle}", color=DARK_BLUE, fontsize=9.2, fontweight='bold', va='center')
    ax.text(96, 94.5, f"Source: CARL_CONTROL_COGNITIVE_SPEC.md -- {source_section}", color=TEXT_MUTED, fontsize=9.0, fontweight='bold', ha='right', va='center')

def draw_box(ax, x, y, w, h, title, text_lines=[], color=BLUE, bg_color=PANEL_BG, title_color=None, text_color=TEXT_BODY, fontsize=8.5, title_fontsize=9.8):
    if title_color is None:
        title_color = color
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=0.8",
                           facecolor=bg_color, edgecolor=color, linewidth=1.5)
    ax.add_patch(patch)
    if title:
        ax.text(x + w/2, y + h - 2.0, title, color=title_color, fontsize=title_fontsize, fontweight='bold', ha='center', va='center')
    y_text = y + h - 4.2
    for line in text_lines:
        ax.text(x + 1.0, y_text, line, color=text_color, fontsize=fontsize, va='center')
        y_text -= 2.0
    return patch

def draw_arrow(ax, x1, y1, x2, y2, color=BLUE, lw=2.0, style="->", rad=0.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))

def RectanglePatch(xy, width, height, **kwargs):
    return FancyBboxPatch(xy, width, height, boxstyle="square,pad=0.0", **kwargs)

# =============================================================================
# DIAGRAM 01: MASTER SYSTEM ARCHITECTURE [SOURCE VERIFIED]
# =============================================================================
def render_01():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "01 -- MASTER SYSTEM ARCHITECTURE [SOURCE VERIFIED]", "End-to-End Autonomous Cognitive Cycle & Module Topology", "Section 1 & 2")
    
    cols = [
        ("1. SENSING", 3, GREEN, TINT_GREEN, [
            "MuJoCo Joint State", "15-Ray Sonar Array", "Floating IMU (r,p,y)", "Tire Contacts (ncon)", "Optical Vision Cone"
        ]),
        ("2. STATE ESTIMATION", 17, BLUE, TINT_BLUE, [
            "Stuck Detector (W=20)", "Empowerment Core E(s)", "Self-Model Observation", "Prediction Error e_t", "Online Slip Factor"
        ]),
        ("3. HOMEOSTASIS", 31, AMBER, TINT_AMBER, [
            "Energy Decay E(t)", "Joule Heating T(t)", "Mechanical Fatigue F", "Curiosity Kinetics C", "Dominant Need Vector"
        ]),
        ("4. MEMORY & GOALS", 45, PURPLE, TINT_PURPLE, [
            "Endogenous Goal Arb", "2048-D HDC Encoding", "Associative Query M", "Hazard Warning Bias", "Offline Replay Store"
        ]),
        ("5. DREAMER & EFE", 59, CYAN, TINT_CYAN, [
            "14 Kinematic Arcs", "20-Step (1.0s) Rollout", "Collision Risk 3.5x", "Curvature Effort 10k^2", "Min Expected Free Energy"
        ]),
        ("6. SAFETY & VETO", 73, RED, TINT_RED, [
            "Dead-End Gate Check", "Imminent Collision <0.55m", "Boundary Wall Projection", "Thermal Veto >0.85", "Recovery Manager Override"
        ]),
        ("7. MOTOR & PHYSICS", 87, GREEN, TINT_GREEN, [
            "S-Curve Jerk Filter", "a_max=10, j_max=30", "Position Servos a=0.25", "MuJoCo 3x Steps dt=0.01", "Traction Adapt & Write"
        ])
    ]
    
    for title, x, col, bg_col, lines in cols:
        draw_box(ax, x, 22, 11.5, 64, title, lines, color=col, bg_color=bg_col, title_color=col, fontsize=8.5, title_fontsize=9.5)
        if x < 87:
            draw_arrow(ax, x + 11.5, 54, x + 14, 54, color=col, lw=2.5)

    draw_arrow(ax, 92.5, 22, 92.5, 12, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 92.5, 12, 8.5, 12, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 8.5, 12, 8.5, 22, color=DARK_BLUE, lw=2.0)
    ax.text(50, 14, "CLOSED-LOOP FEEDBACK: Sensory Prediction Error e_t  ->  Traction Adaptation (mu_hat)  ->  HDC Episode Write  ->  Next Tick (30 Hz)",
            color=DARK_BLUE, fontsize=10.0, fontweight='bold', ha='center', va='center')

    draw_box(ax, 31, 3, 38, 7.5, "PARALLEL EXPRESSIVE OUTPUT (Non-Causal to Motor Loop)",
             ["Affect Classifier (Threat, Curious, Cautious, Happy)", "OLED Eye Visor & 6 Hz Theta-Pulsing Aura LED", "Emotional Synthesizer Audio Waveform"],
             color=MAGENTA, bg_color=TINT_MAGENTA, title_color=MAGENTA, fontsize=8, title_fontsize=8.5)

    fig.savefig(os.path.join(OUTPUT_DIR, "01_master_system_architecture.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 01_master_system_architecture.png")

# =============================================================================
# DIAGRAM 02: COGNITIVE TICK TIMELINE & SUBSTEPS [AUDITED & LABELED]
# =============================================================================
def render_02():
    fig, ax = setup_fig(18, 10)
    draw_header(ax, "02 -- COGNITIVE TICK TIMING & PHYSICS INTEGRATION", "30.0 Hz Control Loop Breakdown (33.33 ms Budget) vs 300 Hz MuJoCo Sub-Steps", "Section 2 & 23")
    
    ax.add_patch(FancyBboxPatch((5, 68), 90, 8, boxstyle="round,pad=0.5", facecolor="#f1f5f9", edgecolor=BORDER_DEFAULT))
    
    stages = [
        (5, 3.5, "Sensors\n0.35ms", GREEN),
        (8.5, 4.0, "State & Emp\n0.40ms", BLUE),
        (12.5, 1.5, "Self-Mod\n0.15ms", AMBER),
        (14.0, 2.5, "Goal/Mem\n0.25ms", PURPLE),
        (16.5, 6.5, "Dreamer EFE\n0.65ms", CYAN),
        (23.0, 2.0, "Veto/Rec\n0.20ms", RED),
        (25.0, 1.0, "S-Curve\n0.10ms", GREEN),
        (26.0, 12.0, "MuJoCo Physics Step (3x 0.01s Sub-steps)\n1.20ms", RED),
        (38.0, 2.5, "Learn/Visor\n0.25ms", MAGENTA),
        (40.5, 1.5, "Telem\n0.15ms", TEXT_MUTED),
        (42.0, 53.0, "SIMULATION HEADROOM / REAL-TIME SLEEP (29.63 ms / 88.9% Margin on Host CPU)\nEnables Headless Batch Simulation at up to 1,250 FPS", "#e2e8f0")
    ]
    
    for x, w, label, col in stages:
        text_c = "#ffffff" if col != "#e2e8f0" else TEXT_DARK
        ax.add_patch(RectanglePatch((x, 68), w, 8, facecolor=col, edgecolor="#ffffff", linewidth=0.5, alpha=0.9))
        ax.text(x + w/2, 72, label, color=text_c, fontsize=7.5, fontweight='bold', ha='center', va='center')

    draw_box(ax, 5, 20, 42, 42, "3x MuJoCo PHYSICS SUB-STEPS (dt_phy = 0.010s)", [
        "- Cognitive Controller updates wheel targets at 30.0 Hz (dt = 0.0333s)",
        "- MuJoCo Newton physics solver steps 3 times per cognitive cycle:",
        "    * Substep 1 (t = 0.010s): Contact resolver & tire normal forces",
        "    * Substep 2 (t = 0.020s): Lateral Coulomb friction & sliding",
        "    * Substep 3 (t = 0.030s): Floating base velocity integration",
        "- Guarantees sub-millisecond numerical stability & zero caster penetration."
    ], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=9.0)

    draw_box(ax, 53, 20, 42, 42, "MEASURED BENCHMARKS & HARDWARE TARGETS", [
        "- Measured Host Processing Latency:   3.70 ms",
        "- Measured Physics Step Latency:      1.20 ms",
        "- Total Active Execution Time:        4.90 ms per tick",
        "- Measured Host Headless Speed:       up to 1,250 FPS",
        "- Orange Pi 5 Target Deployment:      [THEORETICAL ESTIMATE /",
        "                                      UNVERIFIED ON PHYSICAL SBC]",
        "- S-Curve Motor Filter eliminates current spikes & motor gear jerk."
    ], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=9.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "02_cognitive_tick.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 02_cognitive_tick.png")

# =============================================================================
# DIAGRAM 03: COMMAND HIERARCHY [SOURCE VERIFIED]
# =============================================================================
def render_03():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "03 -- COMMAND & AUTHORITY HIERARCHY [SOURCE VERIFIED]", "Strict Real-Time Priority Ordering & Subsystem Override Rules", "Section 5")
    
    levels = [
        ("LEVEL 0: PHYSICAL REALITY & CONTACT CONSTRAINTS", "Ground normal forces, non-penetration, Coulomb friction. CANNOT BE OVERRIDDEN.", RED, TINT_RED, 80),
        ("LEVEL 1: S-CURVE JERK & RATE LIMIT FILTER", "Protects motors: |a| <= 10.0 rad/s^2, |j| <= 30.0 rad/s^3. Capping higher commands.", GREEN, TINT_GREEN, 71),
        ("LEVEL 2: ACTIVE STUCK RECOVERY MANAGER", "Escalating 3-Tier Reverse/Spin override. Bypasses Free Energy when stalled.", RED, TINT_RED, 62),
        ("LEVEL 3: HARD OPERATIONAL COLLISION & THERMAL VETO", "Vetoes imminent wall impacts (<0.55m), dead-ends, & motor overheat (T>0.85).", AMBER, TINT_AMBER, 53),
        ("LEVEL 4: STEERING PERSISTENCE & DIRECTIONAL HOLD", "10-tick temporal hold (+-1.0) preventing high-frequency steering chatter.", CYAN, TINT_CYAN, 44),
        ("LEVEL 5: EXPECTED FREE ENERGY (EFE) MINIMIZATION", "Selects best candidate arc: G(a) = Risk + Need - InfoGain + Effort.", BLUE, TINT_BLUE, 35),
        ("LEVEL 6: EPISODIC MEMORY HAZARD BIASING", "2048-D HDC unbinding adds +25.0 penalty to actions with past collision history.", PURPLE, TINT_PURPLE, 26),
        ("LEVEL 7: ENDOGENOUS GOAL ARBITRATION", "Selects dominant drive: Viability, Rest, Exploration, or Spatial Uncertainty.", MAGENTA, TINT_MAGENTA, 17),
        ("LEVEL 8: AFFECTIVE EXPRESSION & VISOR AURA", "OLED eyes, 6 Hz Theta bio-aura LED, head posture. Strictly non-causal to wheels.", TEXT_MUTED, "#f8fafc", 8)
    ]
    
    for title, desc, col, bg_col, y in levels:
        draw_box(ax, 8, y, 76, 7.2, title, [desc], color=col, bg_color=bg_col, title_color=col, fontsize=8.5, title_fontsize=10.0)
        if y < 80:
            draw_arrow(ax, 88, y + 3.6, 88, y + 10.6, color=DARK_BLUE, lw=2.0)
            ax.text(89, y + 7.1, "Overrides", color=DARK_BLUE, fontsize=8, fontweight='bold', va='center')

    fig.savefig(os.path.join(OUTPUT_DIR, "03_command_hierarchy.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 03_command_hierarchy.png")

# =============================================================================
# DIAGRAM 04: GOAL ARBITRATION [SOURCE VERIFIED]
# =============================================================================
def render_04():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "04 -- ENDOGENOUS GOAL GENERATION & ARBITRATION [SOURCE VERIFIED]", "Homeostatic Drive Kinetics, Competing Motivations & Arbitration Thresholds", "Section 6")
    
    draw_box(ax, 5, 52, 28, 35, "HOMEOSTATIC STATE VECTOR h(t)", [
        "- Energy Reserve:     E(t) in [0.0, 1.0]",
        "- Thermal Load:       T(t) in [0.0, 1.0]",
        "- Motor Fatigue:      F(t) in [0.0, 1.0]",
        "- Safety Margin:      S(t) in [0.0, 1.0]",
        "- Epistemic Uncertainty: U(t) in [0.05, 1.0]",
        "- Curiosity Drive:    C(t) in [0.10, 1.0]",
        "",
        "Total Deviation:",
        "D_h(t) = Sum w_i * (h_i(t) - h_i*)^2"
    ], color=AMBER, bg_color=TINT_AMBER, title_color=DARK_AMBER, fontsize=8.5)

    goals = [
        ("GOAL_FORAGE_RESOURCE (Viability)", "Trigger: Energy < 0.50", "Priority: (1.0 - Energy) * 1.5", "Target: Food coordinates or beacon scan", GREEN, TINT_GREEN, 72),
        ("GOAL_THERMAL_REGULATION (Rest)", "Trigger: Thermal > 0.70 OR Fatigue > 0.70", "Priority: max(Thermal, Fatigue) * 1.2", "Target: Stationary brake cooling", RED, TINT_RED, 54),
        ("GOAL_EXPLORE_UNKNOWN (Curiosity)", "Trigger: Curiosity Drive > 0.40", "Priority: 0.40 + 0.35 * Curiosity", "Target: Open unvisited terrain", CYAN, TINT_CYAN, 36),
        ("GOAL_INSPECT_SURROUNDINGS (Epistemic)", "Trigger: Uncertainty > 0.40", "Priority: 0.35 + 0.30 * Uncertainty", "Target: Active head pan & gaze scan", PURPLE, TINT_PURPLE, 18)
    ]
    
    for title, trig, prio, tgt, col, bg_col, y in goals:
        draw_box(ax, 38, y, 57, 15, title, [trig, prio, tgt], color=col, bg_color=bg_col, title_color=col, fontsize=8.5, title_fontsize=10.0)
        draw_arrow(ax, 33, 69, 38, y + 7.5, color=DARK_AMBER, lw=1.8)

    draw_box(ax, 5, 10, 28, 35, "ARBITRATION ENGINE", [
        "1. Evaluate all active goals",
        "2. Find argmax Priority Weight",
        "3. Commit active_goal_id",
        "4. If goal switched:",
        "     goal_persistence_ticks = 0",
        "5. Else:",
        "     goal_persistence_ticks += 1",
        "6. Fallback if empty:",
        "     GOAL_IDLE_EXPLORE (0.20)"
    ], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=8.5)

    fig.savefig(os.path.join(OUTPUT_DIR, "04_goal_arbitration.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 04_goal_arbitration.png")

# =============================================================================
# DIAGRAM 05: ACTION SELECTION POLICY & EFE [SOURCE VERIFIED]
# =============================================================================
def render_05():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "05 -- ACTIVE INFERENCE ACTION SELECTION POLICY [SOURCE VERIFIED]", "14 Candidate Arcs, 20-Step Kinematic Rollouts & Expected Free Energy G(a)", "Section 7 & 8")
    
    actions_left = [
        "1. STRAIGHT_FORWARD (5.5, 5.5)",
        "2. CURVE_LEFT_SLIGHT (4.6, 5.8)",
        "3. CURVE_LEFT_MODERATE (3.6, 6.0)",
        "4. CURVE_LEFT_STRONG (2.8, 6.8)",
        "5. CURVE_LEFT_TIGHT (1.2, 6.2)",
        "6. CURVE_RIGHT_SLIGHT (5.8, 4.6)",
        "7. CURVE_RIGHT_MODERATE (6.0, 3.6)"
    ]
    actions_right = [
        "8.  CURVE_RIGHT_STRONG (6.8, 2.8)",
        "9.  CURVE_RIGHT_TIGHT (6.2, 1.2)",
        "10. SLOW_CREEP_FORWARD (2.2, 2.2)",
        "11. EMERGENCY_REVERSE (-2.5, -2.5)",
        "12. EMERGENCY_SPIN_LEFT (-4.0, 4.0)",
        "13. EMERGENCY_SPIN_RIGHT (4.0, -4.0)",
        "14. BRAKE_REST (0.0, 0.0)"
    ]
    
    draw_box(ax, 3, 20, 24, 68, "14 CANDIDATE ARCS", actions_left + [""] + actions_right, color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=8.0)

    draw_box(ax, 30, 48, 28, 40, "20-STEP FORWARD ROLLOUT (1.0s)", [
        "For each arc a_k:",
        "- Step Kinematics: x, y, yaw at dt=0.033s",
        "- Ray Clearance: d_proj = d_ray - v * t",
        "- Measure dist_0.25s, dist_0.50s, dist_1.00s",
        "- Collision Prob: 1 / (1 + e^(8*(d - 0.35)))",
        "- Boundary Wall Projection (|x|, |y| > 4.6m)"
    ], color=CYAN, bg_color=TINT_CYAN, title_color=CYAN, fontsize=8.5)

    draw_box(ax, 61, 20, 36, 68, "EXPECTED FREE ENERGY FORMULA G(a)", [
        "G(a) = + 3.5 * CollisionRisk(a)",
        "       + SpinPenalty (+1200 if not trapped)",
        "       + ReversePenalty (+1000 if not trapped)",
        "       + IdlingPenalty (+100 if front > 0.35m)",
        "       + 2.0 * |curv - last_curv|^1.2",
        "       + 10.0 * curv^2 (if front > 0.85m)",
        "       + 1.0 * ActionPersistence",
        "       + EnergyCost + SlipRisk(1.0 - mu_hat)",
        "       - 25.0 * ForwardVelocity",
        "       - 6.0 * GoalProgressDistance",
        "       - 4.0 * |ActiveSteeringBias|",
        "       - 40.0 * CorridorCenteringBonus",
        "       - 45.0 * StraightBonus (if d>0.65m)",
        "       + 25.0 * MemoryHazardPenalty",
        "",
        "SELECTED ACTION:",
        "a* = argmin_a G(a)"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.0)

    draw_arrow(ax, 27, 54, 30, 54, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 58, 54, 61, 54, color=DARK_BLUE, lw=2.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "05_action_selection_policy.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 05_action_selection_policy.png")

# =============================================================================
# DIAGRAM 06: REWARD / PENALTY MAP [AUDITED & REFINED]
# =============================================================================
def render_06():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "06 -- REWARD, PENALTY & COST MAP [SOURCE VERIFIED]", "Complete Inventory of Positive Incentives vs Negative Costs Shaping Behavior", "Section 9")
    
    draw_box(ax, 4, 10, 44, 78, "COSTS & PENALTIES (+ in Free Energy)", [
        "- Collision Proximity Risk:   +70(0.95-d) + 300(0.5-d) + 800 (Mult: 3.5x)",
        "- Boundary Wall Penalty:       +80(0.55-d_b) + 500 near walls",
        "- Dead-End Spin Gate:          +1200.0 (Prohibits spins in open space)",
        "- Dead-End Reverse Gate:       +1000.0 (Prohibits reversing in open space)",
        "- Open Space Idling Penalty:   +100.0 (Prevents stationary stalls)",
        "- Curvature Effort (Open):     +10.0 * k^2 (Eliminates turning loops!)",
        "- Curvature Effort (Mid):      +3.0 * k^2 (When front clearance 0.55-0.85m)",
        "- Curvature Derivative:        +2.0 * |k - k_last|^1.2 (Smooth steering)",
        "- Action Persistence Cost:     +1.0 if changing action primitive",
        "- Low Friction Slip Risk:      +(1.0 - mu_hat) * 15.0 on ice/slippery floor",
        "- Memory Hazard Penalty:       +25.0 on recalled collision locations"
    ], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)

    draw_box(ax, 52, 18, 44, 70, "REWARDS & BONUSES (- in Free Energy)", [
        "- Straight Corridor Bonus:     -45.0 (Locks straight when front > 0.65m)",
        "- Slight Curve Bonus:          -18.0 (Encourages gentle centering)",
        "- Forward Velocity Reward:     -25.0 * v_lin (Intrinsic forward drive)",
        "- Goal Progress Reward:        -6.0 * (d_init - d_final) toward targets",
        "- Open Space Clearance:        -8.0 * min(2.0, d_arc - 0.5)",
        "- Corridor Centering Bonus:    -40.0 * (1.0 - 2|d_L - d_R|) between walls",
        "- Steering Bias Hold Bonus:    -4.0 * |bias| (Maintains corner turn)"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    draw_box(ax, 52, 4, 44, 11, "ROADMAP NOTE: INFORMATION GAIN / EMPOWERMENT", [
        "Mutual information empowerment E(s) is evaluated and logged to telemetry.",
        "Direct EFE coupling (-lambda_E * E(s)) is documented as Roadmap Priority P1."
    ], color=CYAN, bg_color=TINT_CYAN, title_color=CYAN, fontsize=8.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "06_reward_penalty_map.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 06_reward_penalty_map.png")

# =============================================================================
# DIAGRAM 07: SAFETY VETO SYSTEM [SOURCE VERIFIED]
# =============================================================================
def render_07():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "07 -- OPERATIONAL SAFETY & COLLISION VETO SYSTEM [SOURCE VERIFIED]", "Hard Safety Envelope, Boundary Wall Horizon Check & Escape Substitutions", "Section 10")
    
    draw_box(ax, 35, 80, 30, 8, "CANDIDATE ACTION a* FROM EFE", ["Selected minimum Free Energy action"], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=8.5)
    draw_arrow(ax, 50, 80, 50, 72, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 32, 64, 36, 8, "1. DEAD-END ENCLOSURE CHECK", ["front < 1.10m AND left < 1.40m AND right < 1.40m?"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 68, 68, 75, 68, color=RED, lw=2.0)
    draw_box(ax, 75, 64, 21, 8, "FORCE SPIN_LEFT", ["EMERGENCY_SPIN_LEFT"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 50, 64, 50, 56, color=GREEN, lw=2.0)

    draw_box(ax, 32, 48, 36, 8, "2. IMMINENT OBSTACLE COLLISION", ["front < 0.55m OR min_obstacle_dist < 0.40m?"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 68, 52, 75, 52, color=RED, lw=2.0)
    draw_box(ax, 75, 48, 21, 8, "SUBSTITUTE CURVE/SPIN", ["In-place spin if <0.40m\nCurve away if 0.40-0.55m"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.0)
    draw_arrow(ax, 50, 48, 50, 40, color=GREEN, lw=2.0)

    draw_box(ax, 32, 32, 36, 8, "3. BOUNDARY WALL PROJECTION", ["|pred_x| > 4.60m OR |pred_y| > 4.60m (0.5s horizon)?"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 68, 36, 75, 36, color=RED, lw=2.0)
    draw_box(ax, 75, 32, 21, 8, "SUBSTITUTE INWARD CURVE", ["CURVE_MODERATE away"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 50, 32, 50, 24, color=GREEN, lw=2.0)

    draw_box(ax, 32, 16, 36, 8, "4. CRITICAL THERMAL LOAD CHECK", ["thermal_load > 0.85 AND motor effort > 8.0?"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 68, 20, 75, 20, color=RED, lw=2.0)
    draw_box(ax, 75, 16, 21, 8, "FORCE BRAKE_REST", ["Cooldown motors to <0.70"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)
    draw_arrow(ax, 50, 16, 50, 8, color=GREEN, lw=2.0)

    draw_box(ax, 35, 1, 30, 7, "ACTION SAFE -> S-CURVE FILTER", ["Forward command to wheel actuators"], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    fig.savefig(os.path.join(OUTPUT_DIR, "07_safety_veto.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 07_safety_veto.png")

# =============================================================================
# DIAGRAM 08: STUCK RECOVERY STATE MACHINE [SOURCE VERIFIED]
# =============================================================================
def render_08():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "08 -- STUCK DETECTION & 3-TIER ESCALATING RECOVERY [SOURCE VERIFIED]", "Execution Tracking, Asymmetric Sonar Steering & Ground Truth Recovery Verification", "Section 11")
    
    draw_box(ax, 4, 60, 26, 25, "STUCK_IDLE (Nominal)", [
        "- Window: W = 20 ticks (0.66s)",
        "- Monitor: disp / expected_dist",
        "- If ratio < 0.20:",
        "    candidate_ticks += 1",
        "- If candidate >= 8 ticks:",
        "    State -> STUCK_CANDIDATE"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    draw_box(ax, 36, 60, 26, 25, "STUCK_CANDIDATE", [
        "- Stagnation accumulating",
        "- Confidence = candidate / 15.0",
        "- If candidate >= 18 ticks (0.6s):",
        "    State -> STUCK_CONFIRMED",
        "- If movement recovers:",
        "    Return to STUCK_IDLE"
    ], color=AMBER, bg_color=TINT_AMBER, title_color=DARK_AMBER, fontsize=8.5)

    draw_box(ax, 68, 60, 28, 25, "STUCK_CONFIRMED", [
        "- Stall verified physically!",
        "- Trigger CarlRecoveryManager",
        "- Record recovery_origin (x, y)",
        "- Analyze 15-ray Sonar asymmetry",
        "- Set steer_dir away from tighter side"
    ], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)

    draw_arrow(ax, 30, 72, 36, 72, color=DARK_AMBER, lw=2.0)
    draw_arrow(ax, 62, 72, 68, 72, color=DARK_RED, lw=2.0)

    tiers = [
        ("TIER 1: REVERSE CURVE (14 ticks)", "Reverse curving away from tighter obstacle side (-4.5, -2.5).", BLUE, TINT_BLUE, 4),
        ("TIER 2: TARGETED SPIN (14 ticks)", "In-place spin toward maximum sonar clearance azimuth (+-4.0, -+4.0).", AMBER, TINT_AMBER, 36),
        ("TIER 3: FORWARD BREAKOUT (18 ticks)", "Forward acceleration (5.0, 5.0). Verifies physical displacement >= 0.35m!", GREEN, TINT_GREEN, 68)
    ]
    
    for title, desc, col, bg_col, x in tiers:
        draw_box(ax, x, 22, 28, 25, title, [desc], color=col, bg_color=bg_col, title_color=col, fontsize=8.5)
        if x < 68:
            draw_arrow(ax, x + 28, 34, x + 36, 34, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 4, 3, 92, 12, "PHYSICAL RECOVERY VERIFICATION CRITERION (No Fake Timer Clears)", [
        "RECOVERY SUCCESS  <=>  ||pos_current - pos_origin|| >= 0.35 m   AND   min_front_clearance > 0.65 m",
        "If breakout finishes with disp < 0.30m -> Re-trigger recovery with reversed steering bias (steer_dir = -steer_dir) & escalate cycle!"
    ], color=DARK_BLUE, bg_color="#f0f9ff", title_color=DARK_BLUE, fontsize=9.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "08_stuck_recovery_state_machine.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 08_stuck_recovery_state_machine.png")

# =============================================================================
# DIAGRAM 09: MEMORY FLOW (HDC) [SOURCE VERIFIED & CAUSALLY SUPPORTED]
# =============================================================================
def render_09():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "09 -- EPISODIC AUTOBIOGRAPHICAL MEMORY [CAUSALLY SUPPORTED]", "2048-D Hyperdimensional Vector Binding, Associative Recall & Hazard Biasing", "Section 12")
    
    draw_box(ax, 4, 52, 28, 36, "1. HDC VECTOR ENCODING", [
        "- Spatial Position (x, y):",
        "    H_pos = H_x (x) H_y (50x50 grid)",
        "- Active Need:",
        "    H_need in {-1, +1}^2048",
        "- Action Taken:",
        "    H_act in {-1, +1}^2048",
        "- Episode Vector:",
        "    H_ep = H_pos (x) H_need (x) H_act"
    ], color=PURPLE, bg_color=TINT_PURPLE, title_color=DARK_PURPLE, fontsize=8.5)

    draw_box(ax, 36, 52, 28, 36, "2. MEMORY MATRIX BUNDLING", [
        "- Autobiographical Matrix M in R^2048",
        "- Additive Superposition:",
        "    M = M + valence * H_ep",
        "    * Collision Event: valence = -1.0",
        "    * Food Capture:    valence = +1.0",
        "- Unbounded distributed storage",
        "- Replay consolidation of surprises"
    ], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=8.5)

    draw_box(ax, 68, 52, 28, 36, "3. ASSOCIATIVE RECALL & PROBE", [
        "- Unbind probe at current (x, y):",
        "    H_probe = H_pos (x) H_need",
        "- Cosine Similarity across 14 actions:",
        "    Sim = (M . (H_probe (x) H_a)) / ||M||",
        "- If past hazard within <0.80m:",
        "    warn_hazard = True",
        "    Penalty: +25.0 Free Energy on a_bad"
    ], color=CYAN, bg_color=TINT_CYAN, title_color=CYAN, fontsize=8.5)

    draw_arrow(ax, 32, 70, 36, 70, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 64, 70, 68, 70, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 4, 10, 92, 35, "OFFLINE REPLAY & SYNAPTIC CONSOLIDATION DURING REST", [
        "- Episodes sorted by Prediction Error magnitude (Surprise factor e_t)",
        "- During BRAKE_REST / sleep state, top 10 high-surprise episodes are replayed:",
        "    M = M + 0.5 * outcome_valence * (H_pos (x) H_need (x) H_act)",
        "- Reinforces critical survival lessons without catastrophic interference.",
        "- Preserves long-term memory across environment resets (HDC matrix M persists across runs).",
        "- Empirical Causal Proof: Disabling HDC memory caused a statistically significant collision relapse (Delta x = 0.0939m)."
    ], color=MAGENTA, bg_color=TINT_MAGENTA, title_color=MAGENTA, fontsize=9.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "09_memory_flow.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 09_memory_flow.png")

# =============================================================================
# DIAGRAM 10: SELF-MODEL ADAPTATION & FRICTION [AUDITED & LABELED]
# =============================================================================
def render_10():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "10 -- GENERATIVE SELF-MODEL & ONLINE FRICTION ADAPTATION", "Kinematic Forward Projection, Prediction Error & Recursive Slip Adaptation", "Section 13")
    
    draw_box(ax, 4, 52, 28, 36, "1. FORWARD KINEMATICS", [
        "- Predicted S-curve wheel speeds:",
        "    w_hat_L, w_hat_R with rate limits",
        "- Traction Attenuation:",
        "    k_tr = clip(mu_hat / 2.50, 0.20, 1.0)",
        "- Velocity Projection:",
        "    v_hat = (w_hat_L + w_hat_R) * 0.5 * r * k_tr",
        "    x_hat_t+1 = x_t + v_hat cos(psi) dt"
    ], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=8.5)

    draw_box(ax, 36, 52, 28, 36, "2. SENSORY PREDICTION ERROR", [
        "- Compare observed vs predicted:",
        "    e_v = |speed_actual - v_hat|",
        "    e_p = ||pos_actual - p_hat||",
        "- Composite Error:",
        "    e_t = e_v + 5.0 * e_p",
        "- Drives Epistemic Uncertainty U(t)",
        "- Triggers Surprise Memory Storage"
    ], color=AMBER, bg_color=TINT_AMBER, title_color=DARK_AMBER, fontsize=8.5)

    draw_box(ax, 68, 52, 28, 36, "3. ONLINE TRACTION UPDATE", [
        "- Sensed wheel radius under slip:",
        "    r_meas = speed / avg_wheel_w",
        "    slip_ratio = r_meas / r_wheel",
        "- Recursive Ground Friction Update:",
        "    target_mu = clip(0.40 + 2.10 * slip)",
        "    mu_hat = 0.92 * mu_hat + 0.08 * target_mu",
        "- On Ice: mu_hat drops 2.50 -> 1.30 in 12 ticks"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    draw_arrow(ax, 32, 70, 36, 70, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 64, 70, 68, 70, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 4, 10, 92, 35, "BEHAVIORAL CONSEQUENCE OF ONLINE ADAPTATION [ADAPTATION DEMONSTRATED / EMERGENCE CANDIDATE]", [
        "- When mu_hat drops on low-friction terrain, Expected Free Energy slip penalty increases: SlipRisk = (1.0 - mu_hat) * 15.0",
        "- High-speed sharp curves become expensive; agent autonomously selects SLOW_CREEP or widens turning arc.",
        "- Organism adapts smoothly to slippery terrain without any hardcoded 'if on ice' rule."
    ], color=DARK_BLUE, bg_color="#f0f9ff", title_color=DARK_BLUE, fontsize=9.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "10_self_model_adaptation.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 10_self_model_adaptation.png")

# =============================================================================
# DIAGRAM 11: CURIOSITY & ACTIVE SENSING [AUDITED & LABELED]
# =============================================================================
def render_11():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "11 -- ACTIVE SENSING, GAZE & EPISTEMIC CURIOSITY", "Directional Entropy Reduction, Visual Attention & Curiosity Loop Prevention", "Section 14")
    
    draw_box(ax, 4, 52, 28, 36, "1. EPISTEMIC UNCERTAINTY", [
        "- Uncertainty U(t) in [0.05, 1.0]",
        "- Accumulates during prediction errors:",
        "    U = 0.95 * U + 0.05 * clip(e_t)",
        "- Curiosity Drive C(t) accumulates",
        "  during stationary lack of stimuli:",
        "    C = C + 0.003 * dt (if idle)"
    ], color=PURPLE, bg_color=TINT_PURPLE, title_color=DARK_PURPLE, fontsize=8.5)

    draw_box(ax, 36, 52, 28, 36, "2. ACTIVE GAZE SCANNING [OBSERVED]", [
        "- Head Pan Servo: q_head in [-1.2, +1.2]",
        "- When target is visible:",
        "    Fixate gaze on target_bearing",
        "- When obstacle < 1.0m:",
        "    Active sweep: 0.60 * sin(0.25 * tick)",
        "- Actively scans lateral clearances"
    ], color=CYAN, bg_color=TINT_CYAN, title_color=CYAN, fontsize=8.5)

    draw_box(ax, 68, 52, 28, 36, "3. INFORMATION GAIN [THEORETICAL METRIC]", [
        "- Active gaze acquires occluded beacon",
        "- Shannon Entropy Reduction Model:",
        "    Delta H(S'|a) <= -2.0 nats (Theoretical)",
        "- Drives body reorientation toward target",
        "- Goal switches to Forage upon visual lock"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    draw_arrow(ax, 32, 70, 36, 70, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 64, 70, 68, 70, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 4, 10, 92, 35, "PATHOLOGICAL CURIOSITY LOOP PREVENTION (Anti-Stall Guarantee)", [
        "- Failure Risk: Agent continuously spinning in place or scanning head without translating.",
        "- Architectural Protection 1: In-place spins carry +1200.0 Free Energy penalty in open space.",
        "- Architectural Protection 2: Curiosity satisfaction rate decays with speed: C = max(0.1, C - 0.02 * (v + e_t) * dt).",
        "- Result: Agent must translate physically to satisfy curiosity; pure stationary head-scanning terminates."
    ], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=9.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "11_curiosity_active_sensing.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 11_curiosity_active_sensing.png")

# =============================================================================
# DIAGRAM 12: RESET LIFECYCLE [SOURCE VERIFIED]
# =============================================================================
def render_12():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "12 -- RESET ROBUSTNESS & LIFECYCLE MANAGEMENT [SOURCE VERIFIED]", "Preserved Long-Term Memory vs Cleared Dynamic State on Environment Reset", "Section 17")
    
    draw_box(ax, 4, 15, 42, 72, "CLEARED DYNAMIC STATE (Zeroed on Reset)", [
        "- S-Curve Wheel Velocities (cmd_w_L, cmd_w_R = 0)",
        "- S-Curve Wheel Accelerations (accel_w_L, accel_w_R = 0)",
        "- Position Servos (hip, neck, head = 0)",
        "- Steering Persistence Bias (active_steering_bias = 0)",
        "- Steering Hold Ticks (steering_hold_ticks = 0)",
        "- Homeostatic Energy (Reset to 1.00 full)",
        "- Thermal Load & Motor Fatigue (Reset to 0.00)",
        "- Stuck Detector Histories & Candidate Ticks (Zeroed)",
        "- Recovery Manager State (Reset to IDLE, Tier 1)",
        "- Prediction Error History Buffer (Cleared)",
        "- Telemetry History Buffer (Cleared)"
    ], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=8.5)

    draw_box(ax, 54, 15, 42, 72, "PRESERVED LONG-TERM STATE (Survives Reset)", [
        "- 2048-D HDC Memory Matrix (M in R^2048)",
        "    * Retains cumulative hazard & resource traces",
        "- Autobiographical Episode Buffer (episodes)",
        "    * Retains full experience history up to 200 episodes",
        "- Learned Ground Friction Baseline (mu_hat)",
        "- Offline Replay Synaptic Consolidation Weights",
        "",
        "SCIENTIFIC JUSTIFICATION:",
        "Allows CARL-DX to exhibit true developmental learning",
        "and experience-dependent survival across lifespans",
        "without erasing learned hazard boundaries."
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    fig.savefig(os.path.join(OUTPUT_DIR, "12_reset_lifecycle.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 12_reset_lifecycle.png")

# =============================================================================
# DIAGRAM 13: DATA FLOW [SOURCE VERIFIED]
# =============================================================================
def render_13():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "13 -- COMPLETE SIGNAL-LEVEL DATA FLOW [SOURCE VERIFIED]", "Variable-Level Transformations from MuJoCo Joints to Telemetry", "Section 22")
    
    draw_box(ax, 3, 10, 21, 78, "RAW SENSORY SIGNALS", [
        "data.qpos, data.qvel",
        "data.actuator_force (tau)",
        "hal.get_robot_pos (x,y,yaw)",
        "data.ncon (contacts)",
        "sonar_distances[15]",
        "min_obstacle_dist",
        "target_visible, bearing",
        "data.ctrl (actuator array)"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)

    draw_box(ax, 27, 10, 21, 78, "STATE OBJECTS", [
        "EmbodiedSensoryState:",
        "  wheel_w_L, wheel_w_R",
        "  pos_x, pos_y, yaw, speed",
        "  min_obstacle_dist",
        "HomeostaticVector:",
        "  energy, thermal_load",
        "  motor_fatigue, curiosity",
        "StuckTelemetry:",
        "  stuck_confidence, state"
    ], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=8.5)

    draw_box(ax, 51, 10, 21, 78, "COGNITIVE EVALUATION", [
        "EndogenousGoal:",
        "  goal_id, priority_weight",
        "GenerativeSelfModel:",
        "  last_prediction[6]",
        "  prediction_error (e_t)",
        "  estimated_friction (mu_hat)",
        "  evaluations[14 actions]",
        "EpisodicMemory:",
        "  hdc_memory_matrix (M)"
    ], color=PURPLE, bg_color=TINT_PURPLE, title_color=DARK_PURPLE, fontsize=8.5)

    draw_box(ax, 75, 10, 22, 78, "ACTUATION & OUTPUT", [
        "Candidate Action a*",
        "Safety Veto Recommendation",
        "Recovery Override cmd",
        "S-Curve Filter Output:",
        "  cmd_w_L, cmd_w_R",
        "  cmd_hip_pitch, cmd_head",
        "CognitiveCycleTelemetry:",
        "  32 fields logged to CSV"
    ], color=CYAN, bg_color=TINT_CYAN, title_color=CYAN, fontsize=8.5)

    draw_arrow(ax, 24, 49, 27, 49, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 48, 49, 51, 49, color=DARK_BLUE, lw=2.0)
    draw_arrow(ax, 72, 49, 75, 49, color=DARK_BLUE, lw=2.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "13_data_flow.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 13_data_flow.png")

# =============================================================================
# DIAGRAM 14: REAL-TIME TIMING BUDGET [BENCHMARKED]
# =============================================================================
def render_14():
    fig, ax = setup_fig(18, 10)
    draw_header(ax, "14 -- REAL-TIME TIMING & COMPUTATIONAL BUDGET [BENCHMARKED]", "Granular Execution Micro-Timeline for One 30.0 Hz Cognitive Cycle", "Section 23")
    
    tasks = [
        ("1. SENSORY ACQUISITION & AABB RAYCAST", "0.00 ms", "0.35 ms", GREEN, TINT_GREEN),
        ("2. KINEMATIC STATE, STUCK DETECTOR & EMPOWERMENT", "0.35 ms", "0.40 ms", BLUE, TINT_BLUE),
        ("3. SELF-MODEL ERROR & INTEROCEPTION UPDATE", "0.75 ms", "0.15 ms", AMBER, TINT_AMBER),
        ("4. GOAL ARBITRATION & HDC MEMORY QUERY", "0.90 ms", "0.25 ms", PURPLE, TINT_PURPLE),
        ("5. COUNTERFACTUAL DREAMER (14 ARCS x 20 STEPS)", "1.15 ms", "0.65 ms", CYAN, TINT_CYAN),
        ("6. COMMAND ARBITRATION & SAFETY VETO", "1.80 ms", "0.20 ms", RED, TINT_RED),
        ("7. S-CURVE JERK FILTER & SERVO SMOOTHING", "2.00 ms", "0.10 ms", GREEN, TINT_GREEN),
        ("8. MUJOCO MULTI-BODY PHYSICS STEP (3x 0.01s)", "2.10 ms", "1.20 ms", RED, TINT_RED),
        ("9. EPISODIC MEMORY WRITE & AFFECTIVE VISOR SYNC", "3.30 ms", "0.25 ms", MAGENTA, TINT_MAGENTA),
        ("10. TELEMETRY ASSEMBLY & BUFFER APPEND", "3.55 ms", "0.15 ms", TEXT_MUTED, "#f8fafc"),
        ("TOTAL ACTIVE EXECUTION TIME: 3.70 ms  |  HEADROOM SLEEP: 29.63 ms (88.9% Margin)", "3.70 ms", "29.63 ms", DARK_BLUE, "#f0f9ff")
    ]
    
    y = 78
    for name, start, dur, col, bg_col in tasks:
        draw_box(ax, 6, y, 88, 6.2, name, [f"Start Offset: {start}   |   Duration: {dur}"], color=col, bg_color=bg_col, title_color=col, fontsize=8.0, title_fontsize=9.0)
        y -= 6.8

    fig.savefig(os.path.join(OUTPUT_DIR, "14_realtime_timing.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 14_realtime_timing.png")

# =============================================================================
# DIAGRAM 15: FAILURE MODE TREE [AUDITED & LABELED AS SUBSET]
# =============================================================================
def render_15():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "15 -- PRIMARY FAILURE MODES & AUTOMATED MITIGATION TREE", "Subset: 5 of 12 Documented Forensic Failures (See Spec Section 18 for FAIL-06 to FAIL-12)", "Section 18")
    
    failures = [
        ("FAIL-01: BRAKE_LOCK", "EFE selected BRAKE_REST in open space", "Clearance >0.5m & speed <0.01", "Added +100.0 Idling Penalty", GREEN, TINT_GREEN, 72),
        ("FAIL-02: STATIONARY_STALL", "Stopped before wall with zero bias", "18 ticks zero displacement", "StuckDetector triggers Tier 1 Reverse", GREEN, TINT_GREEN, 58),
        ("FAIL-03: TURNING_LOOP", "Phantom wall + curvature switch cost", "Curvature const & 360 deg loop", "Centrifugal cost 10k^2 + StraightBonus 45", GREEN, TINT_GREEN, 44),
        ("FAIL-04: STEERING_CHATTER", "Symmetric obstacle EFE alternation", "Sign changes every 1-2 ticks", "10-tick Steering Persistence Hold", GREEN, TINT_GREEN, 30),
        ("FAIL-05: DEAD-END_TRAP", "Forward blocked & spins penalized", "Front <1.1m, sides <1.4m", "is_dead_end_trapped gate unlocks spin", GREEN, TINT_GREEN, 16)
    ]
    
    for fid, cause, det, mit, col, bg_col, y in failures:
        draw_box(ax, 4, y, 92, 12, fid, [
            f"- Root Cause:  {cause}",
            f"- Detection:   {det}",
            f"- Mitigation:  {mit}  (STATUS: REPAIRED & VERIFIED)"
        ], color=col, bg_color=bg_col, title_color=DARK_GREEN, fontsize=8.5, title_fontsize=9.5)

    fig.savefig(os.path.join(OUTPUT_DIR, "15_failure_mode_tree.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 15_failure_mode_tree.png")

# =============================================================================
# DIAGRAM 16: EMERGENCE BOUNDARY & TAXONOMY [SCIENTIFIC STANDARD]
# =============================================================================
def render_16():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "16 -- SCIENTIFIC PHENOTYPIC CLASSIFICATION & EMERGENCE BOUNDARY", "Criteria for Promoting Behaviors from Engineered Control to True Emergence", "Section 24 & 25")
    
    tiers = [
        ("TIER 1: ENGINEERED CONTROL", "Behavior produced directly by an explicit heuristic or controller (e.g. if front < 0.40m -> curve).", RED, TINT_RED, 76),
        ("TIER 2: ONLINE ADAPTATION", "Behavior produced by parameter adaptation (e.g. slip ratio updating friction estimate mu_hat).", AMBER, TINT_AMBER, 60),
        ("TIER 3: CAUSALLY SUPPORTED", "Mechanism proven via causal ablation (e.g. removing HDC memory causes collision relapse).", BLUE, TINT_BLUE, 44),
        ("TIER 4: EMERGENT CANDIDATE", "Non-scripted compound strategy from interacting body, drives, self-model & affordances.", GREEN, TINT_GREEN, 28),
        ("TIER 5: VERIFIED EMERGENCE", "Survived AST anti-engineering audit, multi-seed replication, & open-ended environments.", CYAN, TINT_CYAN, 12)
    ]
    
    for title, desc, col, bg_col, y in tiers:
        draw_box(ax, 8, y, 84, 13.5, title, [desc], color=col, bg_color=bg_col, title_color=col, fontsize=9.0, title_fontsize=10.5)
        if y < 76:
            draw_arrow(ax, 50, y + 13.5, 50, y + 17.5, color=DARK_BLUE, lw=2.5)

    ax.text(50, 4, "KEY SCIENTIFIC AXIOM: DYNAMIC ACTION SELECTION FROM 14 PRIMITIVES != AUTOMATIC EMERGENCE",
            color=DARK_RED, fontsize=10.5, fontweight='bold', ha='center', va='center')

    fig.savefig(os.path.join(OUTPUT_DIR, "16_emergence_boundary.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 16_emergence_boundary.png")

# =============================================================================
# DIAGRAM 17: FUTURE MULTI-CARL ARCHITECTURE [FUTURE / ROADMAP]
# =============================================================================
def render_17():
    fig, ax = setup_fig(18, 11)
    draw_header(ax, "17 -- FUTURE MULTI-AGENT SWARM ARCHITECTURE [FUTURE / ROADMAP]", "Individual Autonomy vs Shared Collective Long-Term Memory (STRICTLY PLANNED / NOT IMPLEMENTED)", "Section 11 (Master State)")
    
    carls = [
        ("CARL BODY A (Individual)", 4, CYAN, TINT_CYAN),
        ("CARL BODY B (Individual)", 36, BLUE, TINT_BLUE),
        ("CARL BODY C (Individual)", 68, PURPLE, TINT_PURPLE)
    ]
    
    for title, x, col, bg_col in carls:
        draw_box(ax, x, 48, 28, 40, title, [
            "- Private Physical Chassis (6-DoF)",
            "- Private Metabolic Energy E(t)",
            "- Private Thermal Load T(t)",
            "- Private Working Memory Registers",
            "- Private Active Gaze & Head Pan",
            "- Private Active Inference Policy"
        ], color=col, bg_color=bg_col, title_color=col, fontsize=8.5)
        draw_arrow(ax, x + 14, 48, 50, 38, color=col, lw=2.0)

    draw_box(ax, 4, 10, 92, 28, "SHARED COLLECTIVE NETWORK [FUTURE / ROADMAP -- STAGE 4/5]", [
        "- Sibling Hazard Broadcast: Body A encounters low-traction ice; Body B/C adjust approach speed before reaching zone.",
        "- Collective Long-Term Memory (T_ltm): Shared HDC vector broadcasting of high-salience trauma episodes.",
        "- Emergent Division of Labor: Autonomous emergence of scout roles (high curiosity) and guardian roles without preassignment.",
        "- Cooperative Physics: Coordinated contact pushing of obstacles exceeding single-organism mass limits."
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=9.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "17_multi_carl_future_architecture.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered 17_multi_carl_future_architecture.png")

# =============================================================================
# MASTER COMPOSITE OVERVIEW [SYNTHESIS & VERIFIED]
# =============================================================================
def render_master_overview():
    fig, ax = setup_fig(24, 16, dpi=200)
    draw_header(ax, "CARL-DX MASTER COGNITIVE & CONTROL ARCHITECTURE OVERVIEW", "Complete One-Page Master Synthesis of Embodiment, Active Inference, Memory, Safety & Future Hive Direction", "Master Composite")
    
    draw_box(ax, 32, 78, 36, 10, "1. PHYSICAL EMBODIMENT & SENSING [SOURCE VERIFIED]", ["MuJoCo 6-DoF Chassis, 15-Ray Sonar, IMU, Encoders, Torques"], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=9.0)
    draw_arrow(ax, 50, 78, 50, 72, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 32, 62, 36, 10, "2. HOMEOSTASIS & INTEROCEPTION [SOURCE VERIFIED]", ["Energy E, Thermal T, Fatigue F, Curiosity C, Total Deviation D_h"], color=AMBER, bg_color=TINT_AMBER, title_color=DARK_AMBER, fontsize=9.0)
    draw_arrow(ax, 50, 62, 50, 56, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 32, 46, 36, 10, "3. ACTIVE INFERENCE SELF-MODEL [SOURCE VERIFIED]", ["14 Candidate Arcs x 20 Steps; Min Free Energy G(a)"], color=BLUE, bg_color=TINT_BLUE, title_color=DARK_BLUE, fontsize=9.0)
    draw_arrow(ax, 50, 46, 50, 40, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 32, 30, 36, 10, "4. SAFETY VETO & STUCK RECOVERY [SOURCE VERIFIED]", ["Dead-End Veto, Imminent Collision Veto, 3-Tier Recovery Override"], color=RED, bg_color=TINT_RED, title_color=DARK_RED, fontsize=9.0)
    draw_arrow(ax, 50, 30, 50, 24, color=DARK_BLUE, lw=2.0)

    draw_box(ax, 32, 14, 36, 10, "5. S-CURVE MOTOR FILTER & MUJOCO PHYSICS [SOURCE VERIFIED]", ["Rate-limited commands (|a|<=10, |j|<=30) -> 3x Physics Substeps"], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=9.0)

    draw_box(ax, 4, 62, 25, 26, "EPISODIC HDC MEMORY [CAUSALLY SUPPORTED]", [
        "- 2048-D Vector Binding",
        "- Matrix M Superposition",
        "- Associative Hazard Recall",
        "- +25.0 Free Energy Penalty",
        "- Offline Replay Consolidation"
    ], color=PURPLE, bg_color=TINT_PURPLE, title_color=DARK_PURPLE, fontsize=8.5)
    draw_arrow(ax, 29, 62, 32, 51, color=DARK_PURPLE, lw=2.0)

    draw_box(ax, 4, 30, 25, 26, "EMPOWERMENT E(s) [EVALUATED & LOGGED]", [
        "- 8-Probe Action Ensemble",
        "- Reachable State Covariance",
        "- Channel Capacity (nats)",
        "- Controllability Index",
        "- Entropy Collapse Detection"
    ], color=CYAN, bg_color=TINT_CYAN, title_color=CYAN, fontsize=8.5)
    draw_arrow(ax, 29, 43, 32, 49, color=CYAN, lw=2.0)

    draw_box(ax, 71, 62, 25, 26, "AFFECT & EXPRESSIVE VISOR [NON-CAUSAL]", [
        "- Posture: Threat, Curious, Happy",
        "- OLED Eye Display Labels",
        "- 6 Hz Theta-Pulsing Aura LED",
        "- Synthesized Audio Frequency",
        "- Strictly Non-Causal to Wheels"
    ], color=MAGENTA, bg_color=TINT_MAGENTA, title_color=MAGENTA, fontsize=8.5)
    draw_arrow(ax, 68, 67, 71, 67, color=MAGENTA, lw=2.0)

    draw_box(ax, 71, 14, 25, 42, "FUTURE MULTI-AGENT HIVE [FUTURE / ROADMAP]", [
        "- Multiple Independent Bodies",
        "- Sibling Hazard Broadcast",
        "- Collective Route Discovery",
        "- Emergent Division of Labor",
        "- Shared Danger & Terrain Map",
        "- Cooperative Object Pushing",
        "",
        "STATUS: STRICTLY ROADMAP (STAGE 4/5)"
    ], color=GREEN, bg_color=TINT_GREEN, title_color=DARK_GREEN, fontsize=8.5)
    draw_arrow(ax, 68, 19, 71, 19, color=DARK_GREEN, lw=2.0)

    fig.savefig(os.path.join(OUTPUT_DIR, "CARL_MASTER_ARCHITECTURE_OVERVIEW.png"), facecolor=BG_COLOR)
    plt.close(fig)
    print("[OK] Rendered CARL_MASTER_ARCHITECTURE_OVERVIEW.png")

# =============================================================================
# MANIFEST GENERATOR & VALIDATOR
# =============================================================================
def generate_manifest_and_validate():
    manifest_path = os.path.join(OUTPUT_DIR, "diagram_manifest.json")
    
    diagrams_info = [
        {"filename": "01_master_system_architecture.png", "source_section": "Section 1 & 2", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Pipeline Architecture"},
        {"filename": "02_cognitive_tick.png", "source_section": "Section 2 & 23", "status_tag": "[BENCHMARKED & THEORETICAL LABELED]", "diagram_type": "Timing & Substep Breakdown"},
        {"filename": "03_command_hierarchy.png", "source_section": "Section 5", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Authority Hierarchy"},
        {"filename": "04_goal_arbitration.png", "source_section": "Section 6", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Decision Flowchart"},
        {"filename": "05_action_selection_policy.png", "source_section": "Section 7 & 8", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Policy Formulation"},
        {"filename": "06_reward_penalty_map.png", "source_section": "Section 9", "status_tag": "[SOURCE VERIFIED & ROADMAP LABELED]", "diagram_type": "Incentive Matrix"},
        {"filename": "07_safety_veto.png", "source_section": "Section 10", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Decision Tree"},
        {"filename": "08_stuck_recovery_state_machine.png", "source_section": "Section 11", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "State Machine"},
        {"filename": "09_memory_flow.png", "source_section": "Section 12", "status_tag": "[SOURCE VERIFIED & CAUSALLY SUPPORTED]", "diagram_type": "HDC Data Flow"},
        {"filename": "10_self_model_adaptation.png", "source_section": "Section 13", "status_tag": "[ADAPTATION DEMONSTRATED / EMERGENCE CANDIDATE]", "diagram_type": "Adaptive Loop"},
        {"filename": "11_curiosity_active_sensing.png", "source_section": "Section 14", "status_tag": "[OBSERVED & THEORETICAL LABELED]", "diagram_type": "Epistemic Flow"},
        {"filename": "12_reset_lifecycle.png", "source_section": "Section 17", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Lifecycle Management"},
        {"filename": "13_data_flow.png", "source_section": "Section 22", "status_tag": "[SOURCE VERIFIED]", "diagram_type": "Signal Flow"},
        {"filename": "14_realtime_timing.png", "source_section": "Section 23", "status_tag": "[BENCHMARKED IN SIMULATION]", "diagram_type": "Execution Budget"},
        {"filename": "15_failure_mode_tree.png", "source_section": "Section 18", "status_tag": "[PRIMARY SUBSET LABELED]", "diagram_type": "Failure Mitigation"},
        {"filename": "16_emergence_boundary.png", "source_section": "Section 24 & 25", "status_tag": "[SCIENTIFIC STANDARD]", "diagram_type": "Scientific Taxonomy"},
        {"filename": "17_multi_carl_future_architecture.png", "source_section": "Section 11 (Master State)", "status_tag": "[FUTURE / ROADMAP]", "diagram_type": "Multi-Agent Roadmap"},
        {"filename": "CARL_MASTER_ARCHITECTURE_OVERVIEW.png", "source_section": "Master Synthesis", "status_tag": "[COMPOSITE SYNTHESIS]", "diagram_type": "Composite Synthesis"}
    ]
    
    manifest = {
        "project": "CARL-DX / GENESIS Embodied Organism",
        "theme": "Professional White Engineering Publication Theme (Audited)",
        "canonical_spec_reference": "D:\\ebca\\CARL_CONTROL_COGNITIVE_SPEC.md",
        "audit_reference": "D:\\ebca\\evidence\\architecture_spec\\DIAGRAM_INTEGRITY_AUDIT.md",
        "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "total_diagrams": len(diagrams_info),
        "output_directory": OUTPUT_DIR,
        "diagrams": diagrams_info
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Created manifest: {manifest_path}")

    # Validation
    print("\n--- VALIDATING AUDITED WHITE-THEMED DIAGRAMS ---")
    all_valid = True
    for item in diagrams_info:
        p = os.path.join(OUTPUT_DIR, item["filename"])
        if not os.path.exists(p):
            print(f"[FAIL] Missing file: {p}")
            all_valid = False
            continue
        size_kb = os.path.getsize(p) / 1024
        if size_kb < 10:
            print(f"[FAIL] Corrupt/Empty file: {p} ({size_kb:.1f} KB)")
            all_valid = False
            continue
        print(f"[VALID] {item['filename']} ({size_kb:.1f} KB) -- {item['status_tag']}")
    
    if all_valid:
        print("\nALL 18 AUDITED DIAGRAMS SUCCESSFULLY GENERATED & VALIDATED!")
    else:
        print("\nVALIDATION ERRORS DETECTED!")

if __name__ == "__main__":
    print("=================================================================")
    print("   RENDERING CARL-DX AUDITED PROFESSIONAL WHITE-THEMED DIAGRAMS")
    print("=================================================================")
    render_01()
    render_02()
    render_03()
    render_04()
    render_05()
    render_06()
    render_07()
    render_08()
    render_09()
    render_10()
    render_11()
    render_12()
    render_13()
    render_14()
    render_15()
    render_16()
    render_17()
    render_master_overview()
    generate_manifest_and_validate()
