"""
dissertation_content_p4.py
Contains Chapters 10, 11, 12, 13, References, and Appendices for CARL-DX Dissertation.
Strictly compliant with JNTUH-UCESTH guidelines and project_report_2.pdf benchmark.
British spelling throughout. Single standalone figures only. ZERO compound dashboards.
Alphabetical Harvard references per Rules 15, 16, 17.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dissertation_helpers import (
    add_page_break, add_chapter_title, add_appendix_title, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_equation_p, add_image_figure,
    add_table_caption, add_clean_table
)

def add_chapter_10(doc):
    # -------------------------------------------------------------
    # CHAPTER 10: AUTOPOIETIC LIFELONG MEMORY (STAGE 4)
    # -------------------------------------------------------------
    add_chapter_title(doc, 10, "AUTOPOIETIC LIFELONG MEMORY AND PERSISTENCE (STAGE 4)")
    
    add_heading_2(doc, "10.1", "Reward-Modulated STDP Synaptic Plasticity")
    add_body_p(doc, "In Stage 4.1, CARL-DX is endowed with lifelong adaptive capability via a 3-factor Reward-Modulated Spike-Timing-Dependent Plasticity (R-STDP) mechanism. Rather than freezing weights after initial training, synapses dynamically update based on pre- and post-synaptic spike coincidence modulated by a global neuromodulatory reward signal R(t) and bounded by Turrigiano homeostatic scaling:")
    add_equation_p(doc, "d/dt W_ij = eta * R(t) * e_ij(t) - gamma_homeo * (sum_k W_ik - W_target)", "10.1")
    add_body_p(doc, "where e_ij(t) is the eligibility trace storing recent coincidence events. This continuous plasticity allows the agent to reinforce successful trajectory choices online while preventing run-away synaptic saturation.")
    
    add_image_figure(doc, "image33.png", "Fig. 10.1: Stage 4.1 Reward-Modulated STDP (R-STDP) online synaptic weight matrix evolution")

    add_heading_2(doc, "10.2", "2,048-D FHRR Holographic Associative Memory")
    add_body_p(doc, "To ensure that lifelong learning does not degrade previously acquired memories, Stage 4.2 incorporates a 2,048-dimensional Fractional Holographic Reduced Representation (FHRR) memory module. Sensory observations, spatial locations, and motor decisions are bound using circular convolution and stored in a holographic associative superposition vector S_mem in C^2048.")
    add_body_p(doc, "Due to the quasi-orthogonality of high-dimensional random hypervectors, thousands of distinct episodic experiences can be stored in the single vector S_mem with near-zero mutual crosstalk, entirely eliminating catastrophic forgetting.")

    add_heading_2(doc, "10.3", "SWR Reverse Replay and Sleep Consolidation")
    add_body_p(doc, "Drawing directly from mammalian hippocampal neurobiology, Stage 4.3 implements an offline consolidation phase inspired by Sharp-Wave Ripple (SWR) dynamics during non-REM sleep. During quiescent periods, the organism enters an offline replay state, executing reverse geodesic replay of recent navigation traces:")
    add_equation_p(doc, "tau_replay: s_T -> s_{T-1} -> ... -> s_0", "10.2")
    add_body_p(doc, "Replay prunes redundant spatial loops according to the Synaptic Homeostasis Hypothesis (SHY), downscaling non-essential synaptic weights by a global decay factor beta_SHY = 0.985, thereby consolidating efficient pathways into long-term memory.")

    add_heading_2(doc, "10.4", "Autopoietic Lifelong Persistence (GIS-901 Atomic WAL)")
    add_body_p(doc, "To guarantee survival across hardware power resets, Stage 4.4 incorporates a cryptographic Write-Ahead Log (WAL) persistence engine designated GIS-901. Synaptic matrices, CANN manifold offsets, and holographic memory traces are serialized atomically using SHA-256 integrity verification, achieving sub-15 ms warm-boot re-instantiation with 100% state compounding.")


def add_chapter_11(doc):
    # -------------------------------------------------------------
    # CHAPTER 11: METACOGNITION AND SELF-MODIFICATION (STAGE 5)
    # -------------------------------------------------------------
    add_chapter_title(doc, 11, "METACOGNITION AND PERMISSION-GATED SELF-MODIFICATION (STAGE 5)")
    
    add_heading_2(doc, "11.1", "Introspective Failure Telemetry Monitoring")
    add_body_p(doc, "Stage 5 introduces high-level metacognitive monitoring through 'The Witness'—a 7-channel continuous introspective telemetry supervisor that tracks internal distress signals without accessing simulator physics:")
    add_bullet_p(doc, "Channel 1 (Prediction Surprise)", "Exponential moving average of 1-step world model sensory prediction errors.")
    add_bullet_p(doc, "Channel 2 (Kinematic Slip Discrepancy)", "Discrepancy between wheel encoder velocity and IMU longitudinal acceleration.")
    add_bullet_p(doc, "Channel 3 (Torque Saturation)", "Normalized actuator command duration at maximum saturation limits.")
    add_bullet_p(doc, "Channel 4 (Attractor Energy Divergence)", "Lyapunov energy function anomaly of CANN bump manifolds.")
    add_bullet_p(doc, "Channel 5 (Spatial Entrapment)", "Geodesic spatial displacement over a sliding temporal window of 100 ticks.")
    add_bullet_p(doc, "Channel 6 (Vision-Gaze Misalignment)", "Discrepancy between commanded gaze angle and observed optical flow.")
    add_bullet_p(doc, "Channel 7 (Jerk / Suspension Chatter)", "High-frequency pitch chatter detected across the caster suspension.")
    
    add_image_figure(doc, "image36.png", "Fig. 11.1: Stage 5.1 & 5.2 'The Witness' 7-channel introspective telemetry signal traces")

    add_heading_2(doc, "11.2", "Abductive Causal Attribution and PFL2 Steering")
    add_body_p(doc, "When aggregate introspective distress exceeds a critical threshold, Stage 5.2 performs abductive causal attribution using Pearl's do-calculus framework over recent episodic memory traces. If entrapment or motor failure is diagnosed, control is temporarily transferred to a biologically inspired Drosophila PFL2 steering circuit, executing an emergency 180-degree ballistic escape maneuver.")

    add_heading_2(doc, "11.3", "Permission-Gated Self-Modification")
    add_body_p(doc, "Uncontrolled self-modification in autonomous systems risks catastrophic divergence. Stage 5.3 institutes a triple-latch permission gating protocol before any internal hyperparameter (e.g. MPPI temperature lambda, exploration noise sigma_u, or motor gains) can be adjusted. Modifications must satisfy strict Lipschitz continuity bounds (|Delta theta| <= 0.05) and demonstrate exponential homeostatic recovery (R^2 = 1.0000).")

    add_heading_2(doc, "11.4", "40-Episode Adversarial Acceptance Battery")
    add_body_p(doc, "The Stage 5 metacognitive organ was evaluated across a rigorous 40-episode adversarial stress suite comprising sudden motor disconnects, unexpected barricades, and grease patches. As shown in Fig. 11.2, the metacognitive organism achieved an 81.5% recovery advantage (p = 9.70e-9) compared to the non-introspective baseline.")
    
    add_image_figure(doc, "image37.png", "Fig. 11.2: Stage 5.4 Physical trajectory recovery comparison under motor drag failure")


def add_chapter_12(doc):
    # -------------------------------------------------------------
    # CHAPTER 12: FOREIGN EMBODIMENT & PROTOTYPING (STAGE 6)
    # -------------------------------------------------------------
    add_chapter_title(doc, 12, "FOREIGN EMBODIMENT AND PHYSICAL PROTOTYPING (STAGE 6)")
    
    add_heading_2(doc, "12.1", "Cross-Embodiment Transfer Across Diverse Morphologies")
    add_body_p(doc, "To prove that CARL's neuromorphic computational principles are genuinely morphology-agnostic, Stage 6.2 transferred the cognitive architecture across four radically distinct mechanical embodiments without modifying core algorithmic code:")
    add_bullet_p(doc, "Tier 1 (Skid-Steer Rover)", "4-wheel differential rover operating on rough terrain.")
    add_bullet_p(doc, "Tier 2 (Holonomic Omni-Base)", "3-wheel omnidirectional base with full 3-DOF planar mobility.")
    add_bullet_p(doc, "Tier 3 (Articulated Manipulator)", "3-DOF planar arm executing dynamic pick-and-place, ballistic throw, and catch tasks.")
    add_bullet_p(doc, "DeepMind Menagerie Panda", "7-DOF Franka Emika Panda robotic manipulator operating under 100% pure contact physics.")
    
    add_image_figure(doc, "image39.png", "Fig. 12.1: Stage 6.2 Foreign Embodiment Transfer — Google DeepMind MuJoCo Franka Panda arm")
    add_image_figure(doc, "image40.png", "Fig. 12.2: Stage 6.2 Foreign Embodiment Transfer — Skid-Steer Rover and Holonomic Omni-base")
    
    add_table_caption(doc, "Table 12.1: Stage 6.2 Cross-Embodiment Transfer Performance Across 4 Morphological Tiers")
    headers_121 = ["Mechanical Embodiment", "Degrees of Freedom", "Control Paradigm", "Success Rate", "Mean Cycle Latency"]
    data_121 = [
        ["Tier 1: Skid-Steer 4WD Rover", "4 Actuators (Diff)", "CANN + MPPI Velocity", "100.0% (20/20)", "14.20 ms"],
        ["Tier 2: Holonomic Omni-Base", "3 Omni-Wheels", "3-DOF Velocity Space", "100.0% (20/20)", "16.10 ms"],
        ["Tier 3: Planar Manipulator Arm", "3 Revolute Joints", "Ballistic Throw / Catch", "95.0% (19/20)", "18.40 ms"],
        ["DeepMind Franka Panda (7-DOF)", "7 Joint Torques", "Torque Space MPPI", "100.0% (10/10)", "24.60 ms"]
    ]
    add_clean_table(doc, headers_121, data_121, col_widths=[1.8, 1.2, 1.4, 1.0, 1.2])

    add_heading_2(doc, "12.2", "Heavy 3D Clutter Arena Stress Benchmark")
    add_body_p(doc, "In Stage 6.3, CARL was subjected to a dense 4-chamber arena containing 52 heavy geometric obstacles. Across 20 consecutive trials, the organism achieved 100.0% escape success with zero collisions and a mean hull clearance of 0.058 m.")
    
    add_image_figure(doc, "image41.png", "Fig. 12.3: Stage 6.3 Dense 4-chamber Heavy 3D Clutter Arena environment")
    add_image_figure(doc, "image43.png", "Fig. 12.4: Stage 6.3 Multi-Chamber Trajectory Clearance Heatmap across 20 trials")

    add_heading_2(doc, "12.3", "Frugal ESP32 Embedded Prototype Design")
    add_body_p(doc, "Stage 6.4 formulated an ultra-low-cost embedded hardware architecture capable of running the 2,114-unit CANN on an ESP32-WROOM-32 microcontroller (dual Xtensa LX6 cores, 240 MHz). By compiling neural weights into Q7 fixed-point arithmetic (int8_t), memory consumption is restricted to 33.6 KB SRAM (less than 11% of available SRAM), with a total component bill of materials (BOM) of exactly ₹2,150 ($25.80 USD).")
    
    add_table_caption(doc, "Table 12.2: Stage 6.4 ₹2,150 ESP32 Embedded Prototype Bill of Materials (BOM)")
    headers_122 = ["Component Description", "Model / Specification", "Quantity", "Unit Cost (INR)", "Total Cost (INR)"]
    data_122 = [
        ["Microcontroller Board", "ESP32-WROOM-32 (30-pin, dual core)", "1", "380", "380"],
        ["Ultrasonic Rangefinders", "HC-SR04 Transducer Modules", "3", "75", "225"],
        ["Inertial Measurement Unit", "MPU-6050 6-DOF Accelerometer / Gyro", "1", "140", "140"],
        ["Optical Wheel Encoders", "Magnetic Hall Sensor Discs (pair)", "1 pair", "180", "180"],
        ["Geared DC Drive Motors", "N20 12V 300 RPM Micro Metal Gear", "2", "220", "440"],
        ["Dual Motor Driver H-Bridge", "DRV8833 Dual DC Motor Driver", "1", "95", "95"],
        ["Active Gaze Servo Motor", "SG90 9g Micro Servo (180 deg)", "1", "110", "110"],
        ["Chassis Structure & Caster", "Laser-cut 3mm Acrylic Base + Ball Caster", "1 set", "280", "280"],
        ["Li-Ion Rechargeable Battery", "18650 3.7V 2500mAh Cells (2S Pack)", "2", "150", "300"],
        ["Total Component Cost", "Complete Frugal Autonomous Mobile Robot", "—", "—", "₹2,150"]
    ]
    add_clean_table(doc, headers_122, data_122, col_widths=[1.6, 2.0, 0.6, 1.2, 1.2])

    add_heading_2(doc, "12.4", "Neuromorphic Authenticity Verification")
    add_body_p(doc, "To verify that the architecture is scientifically authentic, double-blind causal ablations were performed: zeroing CANN recurrent connections caused a catastrophic 93.3% behavioral collapse (p < 0.0001), establishing that locomotion is genuinely steered by the neural attractor manifold.")


def add_chapter_13(doc):
    # -------------------------------------------------------------
    # CHAPTER 13: CONCLUSIONS AND FUTURE SCOPE (STAGE 7)
    # -------------------------------------------------------------
    add_chapter_title(doc, 13, "CONCLUSIONS AND FUTURE SCOPE (STAGE 7 FUTURE WORK)")
    
    add_heading_2(doc, "13.1", "Conclusions")
    add_body_p(doc, "This dissertation has presented the design, implementation, formal verification, and empirical benchmark evaluation of CARL-DX—a 2,114-unit neuromorphic computational architecture for biologically inspired mobile robotics. Key scientific conclusions established by this work include:")
    add_bullet_p(doc, "1. Grounding without Priors", "Sensorimotor babbling autonomously establishes kinematic coordinate frames, motor polarities, and forward momentum models (R^2 = 0.984) without privileged simulator coordinates.")
    add_bullet_p(doc, "2. Causal Attractor Necessity", "Continuous Attractor Neural Networks are causally indispensable for spatial steering; abverting recurrent weights produces an immediate seven-fold increase in collisions (p = 9.00e-17).")
    add_bullet_p(doc, "3. Active Inference Efficiency", "Continuous MPPI trajectory synthesis driven by Expected Free Energy minimization achieves 100% escape rates in complex mazes and online adaptation to 76% friction drops.")
    add_bullet_p(doc, "4. Autopoietic Lifelong Resilience", "Reward-modulated STDP and holographic memory eliminate catastrophic forgetting, while 'The Witness' introspective telemetry enables autonomous recovery from hardware failures.")
    add_bullet_p(doc, "5. Frugal Deployability", "The entire 2,114-unit architecture is capable of executing within 33.6 KB SRAM on a ₹2,150 ESP32 microcontroller, operating under a 30 ms real-time deadline.")

    add_heading_2(doc, "13.2", "Limitations")
    add_body_p(doc, "Despite these advancements, several limitations remain. While the digital twin incorporates contact-rich physics and motor noise, real-world deployment introduces unmodelled sensor anomalies (such as ultrasonic specular reflections from smooth acoustic surfaces). Second, while 64x64 retinal vision was demonstrated, higher resolution visual pipelines require dedicated micro-NPU co-processors.")

    add_heading_2(doc, "13.3", "Future Scope: Stage 7 Physical Deployment and Swarms")
    add_body_p(doc, "The logical culmination of this developmental continuum is designated Stage 7, planned as immediate post-dissertation research:")
    add_bullet_p(doc, "Stage 7.1 (Physical Sim-to-Real Deployment)", "Fabrication of the ₹2,150 ESP32 hardware platform, deploying the Q7 fixed-point CANN on bare-metal FreeRTOS to characterize physical sim-to-real transfer gaps.")
    add_bullet_p(doc, "Stage 7.2 (Multi-Agent Swarm Coordination)", "Extending Physarum flux dynamics to multi-robot stigmergy, allowing swarms of frugal CARL agents to explore interconnected cavern networks collaboratively.")
    add_bullet_p(doc, "Stage 7.3 (Continual Plasticity under Environmental Shift)", "Evaluating lifelong R-STDP adaptation over weeks of continuous physical operation without manual intervention.")


def add_references(doc):
    # -------------------------------------------------------------
    # REFERENCES (Alphabetical Harvard Style per Rules 15, 16, 17)
    # -------------------------------------------------------------
    add_page_break(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(14)
    p.paragraph_format.keep_with_next = True
    r = p.add_run("REFERENCES")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True
    
    # Per Rule 6: References can be single-spaced with half-space between entries
    ref_list = [
        "Amari, S. (1977), 'Dynamics of pattern formation in lateral-inhibition type neural fields', Biological Cybernetics, Vol. 27, No. 2, pp. 77-87.",
        "Barbarino, S., Bilgen, O., Ajaj, R.M., Friswell, M.I. and Inman, D.J. (2011), 'A review of morphing aircraft', Journal of Intelligent Material Systems and Structures, Vol. 22, No. 9, pp. 823-877.",
        "Bashir, M., Rajendran, P. and Sharma, C. (2018), 'Aerodynamic analysis of a smart material actuators morphing wing using CFD', Journal of Aerospace Engineering, Vol. 31, No. 4, pp. 112-124.",
        "Bernstein, N.A. (1967), The Co-ordination and Regulation of Movements, Pergamon Press, Oxford, pp. 1-196.",
        "Bi, G.Q. and Poo, M.M. (1998), 'Synaptic modifications in cultured hippocampal neurons: dependence on spike timing, calcium influx, and postsynaptic transcription', Journal of Neuroscience, Vol. 18, No. 24, pp. 10464-10472.",
        "Braitenberg, V. (1984), Vehicles: Experiments in Synthetic Psychology, MIT Press, Cambridge, MA, pp. 1-152.",
        "Brooks, R.A. (1991), 'Intelligence without representation', Artificial Intelligence, Vol. 47, No. 1-3, pp. 139-159.",
        "Burak, Y. and Fiete, I.R. (2009), 'Accurate path integration in continuous attractor network models of grid cells', PLoS Computational Biology, Vol. 5, No. 2, pp. e1000291.",
        "Buzsáki, G. (2015), 'Hippocampal sharp wave-ripple: a cognitive biomarker for episodic memory and planning', Hippocampus, Vol. 25, No. 10, pp. 1073-1188.",
        "Costanza, G. and Tata, M.E. (2020), 'Shape memory alloys for aerospace, recent developments, and new applications: a short review', Materials, Vol. 13, No. 8, pp. 1856-1870.",
        "Diehl, P.U. and Cook, M. (2015), 'Unsupervised learning of digit recognition using spike-timing-dependent plasticity', Frontiers in Computational Neuroscience, Vol. 9, pp. 99-112.",
        "Fleming, S.M. and Dolan, R.J. (2012), 'The neural basis of metacognitive ability', Philosophical Transactions of the Royal Society B: Biological Sciences, Vol. 367, No. 1594, pp. 1338-1349.",
        "Friston, K. (2010), 'The free-energy principle: a unified brain theory?', Nature Reviews Neuroscience, Vol. 11, No. 2, pp. 127-138.",
        "Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P. and Pezzulo, G. (2016), 'Active inference and learning', Neuroscience & Biobehavioral Reviews, Vol. 68, pp. 862-879.",
        "Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P. and Pezzulo, G. (2017), 'Active inference: a process theory', Neural Computation, Vol. 29, No. 1, pp. 1-49.",
        "Fyhn, M., Molden, S., Witter, M.P., Moser, E.I. and Moser, M.B. (2004), 'Spatial representation in the entorhinal cortex', Science, Vol. 305, No. 5688, pp. 1258-1264.",
        "Green, J., Adachi, A., Shah, K.K., Hirokawa, J., Magani, P.S. and Maimon, G. (2017), 'A neural circuit architecture for angular integration in Drosophila', Nature, Vol. 546, No. 7656, pp. 101-106.",
        "Grieves, M. and Vickers, J. (2017), 'Digital twin: mitigating unpredictable, undesirable emergent behavior in complex systems', Transdisciplinary Perspectives on Complex Systems, Springer, Cham, pp. 85-113.",
        "Hafting, T., Fyhn, M., Molden, S., Moser, M.B. and Moser, E.I. (2005), 'Microstructure of a spatial map in the entorhinal cortex', Nature, Vol. 436, No. 7052, pp. 801-806.",
        "Han, X., Lu, W., Dong, X. and Sun, Z. (2003), 'Optimal design of a shape memory alloy actuator using a genetic algorithm', Smart Materials and Structures, Vol. 12, No. 4, pp. 588-596.",
        "Kanerva, P. (1988), Sparse Distributed Memory, MIT Press, Cambridge, MA, pp. 1-155.",
        "Kanerva, P. (2009), 'Hyperdimensional computing: an introduction to computing in distributed representation with high-dimensional random vectors', Cognitive Computation, Vol. 1, No. 2, pp. 139-159.",
        "Nakagaki, T., Yamada, H. and Tóth, Á. (2000), 'Maze-solving by an amoeboid organism', Nature, Vol. 407, No. 6803, pp. 470-470.",
        "O'Keefe, J. and Nadel, L. (1978), The Hippocampus as a Cognitive Map, Oxford University Press, Oxford, pp. 1-570.",
        "Parr, T., Pezzulo, G. and Friston, K.J. (2022), Active Inference: The Free Energy Principle in Mind, Brain, and Behavior, MIT Press, Cambridge, MA, pp. 1-320.",
        "Pearl, J. (2009), Causality: Models, Reasoning, and Inference, 2nd edn, Cambridge University Press, Cambridge, pp. 1-464.",
        "Stone, T., Webb, B., Adden, A., Weddig, N.B., Honkanen, A., Templin, R., Wcislo, W., Green, K. and Heinze, S. (2017), 'An anatomically constrained model for path integration in the bee brain', Current Biology, Vol. 27, No. 20, pp. 3069-3085.",
        "Taube, J.S., Muller, R.U. and Ranck, J.B. (1990), 'Head-direction cells recorded from the postsubiculum in freely moving rats. I. Description and quantitative analysis', Journal of Neuroscience, Vol. 10, No. 2, pp. 420-435.",
        "Tero, A., Takagi, S., Saigusa, T., Ito, K., Bebber, D.P., Fricker, M.D., Yumiki, K., Kobayashi, R. and Nakagaki, T. (2010), 'Rules for biologically inspired adaptive network design', Science, Vol. 327, No. 5964, pp. 439-442.",
        "Theodorou, E., Buchli, J. and Schaal, S. (2010), 'A generalized path integral control approach to reinforcement learning', Journal of Machine Learning Research, Vol. 11, pp. 3137-3181.",
        "Todorov, E., Echeveste, T. and Tassa, Y. (2012), 'MuJoCo: a physics engine for model-based control', 2012 IEEE/RSJ International Conference on Intelligent Robots and Systems, Algarve, Portugal, pp. 5026-5033.",
        "Tononi, G. and Cirelli, C. (2014), 'Sleep and the price of plasticity: from synaptic and cellular homeostasis to memory consolidation and integration', Neuron, Vol. 81, No. 1, pp. 12-34.",
        "Turrigiano, G.G. (2008), 'The self-tuning neuron: synaptic scaling of excitatory synapses', Cell, Vol. 135, No. 3, pp. 422-435.",
        "Wang, L., Sun, K., Zhang, Y. and Liu, Y. (2023), 'Smart materials and structures for aerospace applications: a review', Progress in Aerospace Sciences, Vol. 138, pp. 100892.",
        "Williams, G., Aldrich, A. and Theodorou, E.A. (2017), 'Model predictive path integral control: from theory to parallel computation', Journal of Guidance, Control, and Dynamics, Vol. 40, No. 2, pp. 344-357.",
        "Zhang, K. (1996), 'Representation of spatial orientation by the intrinsic dynamics of the head-direction cell ensemble: a continuous attractor network model', Journal of Neuroscience, Vol. 16, No. 6, pp. 2112-2126."
    ]
    
    for ref in ref_list:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)


def add_appendices(doc):
    # -------------------------------------------------------------
    # APPENDIX A: COMPLETE MATHEMATICAL FORMULATIONS
    # -------------------------------------------------------------
    add_appendix_title(doc, "A", "COMPLETE MATHEMATICAL FORMULATIONS")
    
    add_heading_2(doc, "A.1", "Continuous Attractor Ring Dynamics")
    add_body_p(doc, "The membrane potential u_i(t) of neuron i on the 1D head-direction ring attractor obeys the continuous neural field equation:")
    add_equation_p(doc, "tau_hd * d/dt u_i(t) = -u_i(t) + sum_{j=1}^{N_hd} W_ij^hd * r_j(t) + I_ext,i(t)", "A.1")
    add_body_p(doc, "where the firing rate r_j(t) is governed by a rectified linear or sigmoid transfer function r_j = max(0, u_j)^2 / (1 + beta_inhibit * sum_k max(0, u_k)^2).")

    add_heading_2(doc, "A.2", "Expected Free Energy Functional Derivation")
    add_body_p(doc, "The Expected Free Energy G(pi) for policy pi is derived from the Kullback-Leibler (KL) divergence between predicted future sensory outcomes and prior preferred outcomes:")
    add_equation_p(doc, "G(pi) = sum_tau D_{KL}[ q(s_tau | pi) || p(s_tau) ] + E_{q(s_tau | pi)}[ H[ p(o_tau | s_tau) ] ]", "A.2")
    add_body_p(doc, "The first term represents risk-sensitive pragmatic pursuit of preferred goal states, while the second term represents epistemic ambiguity reduction.")

    # -------------------------------------------------------------
    # APPENDIX B: HYPERPARAMETER AND CONFIGURATION TABLES
    # -------------------------------------------------------------
    add_appendix_title(doc, "B", "HYPERPARAMETER AND CONFIGURATION TABLES")
    
    add_table_caption(doc, "Table B.1: Complete Hyperparameter and Configuration Index")
    headers_b1 = ["Hyperparameter Category", "Parameter Name", "Configured Value", "Algorithmic Role"]
    data_b1 = [
        ["MuJoCo Physics Engine", "Physics Timestep dt_sim", "0.005 s (200 Hz)", "Base numerical integration rate"],
        ["MuJoCo Physics Engine", "Substeps n_substeps", "6 steps", "Decimation factor for control cycle"],
        ["Cognitive Control Cycle", "Control Timestep dt_ctrl", "0.030 s (33.3 Hz)", "Discrete cognitive decision loop"],
        ["CANN Ring Attractor", "Excitatory Kernel J_1", "2.400", "Recurrent bump maintenance strength"],
        ["CANN Ring Attractor", "Inhibitory Kernel J_0", "-1.200", "Global lateral inhibition baseline"],
        ["CANN Ring Attractor", "Velocity Coupling J_v", "0.180", "Phase shift rate per unit yaw angular velocity"],
        ["MPPI Action Optimizer", "Candidate Trajectories M", "128 rollouts", "Monte Carlo sample density"],
        ["MPPI Action Optimizer", "Planning Horizon H", "15 steps (0.45 s)", "Lookahead prediction depth"],
        ["MPPI Action Optimizer", "Temperature lambda", "0.250", "Softmax importance distribution entropy"],
        ["MPPI Action Optimizer", "Exploration Covariance sigma_u", "0.250", "Injected noise per wheel channel"],
        ["Physarum Hydrodynamics", "Decay Constant r", "0.050 / s", "Rate of unused tubule atrophy"],
        ["Physarum Hydrodynamics", "Flux Exponent alpha", "1.200", "Non-linear feedback on tube conductivity"],
        ["R-STDP Synaptic Scaling", "Learning Rate eta", "0.005", "Plasticity adaptation magnitude"],
        ["R-STDP Synaptic Scaling", "Homeostatic Bound W_max", "15.000", "Frobenius norm ceiling on synaptic matrix"]
    ]
    add_clean_table(doc, headers_b1, data_b1, col_widths=[1.8, 1.8, 1.2, 1.8])

    print("Chapters 10-13, References, and Appendices ready.")
