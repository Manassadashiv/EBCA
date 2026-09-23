"""
generate_jntuh_lit_review.py — JNTUH Format Literature Review Generator
Loads the JNTUH template and copies the papers, tables, introduction, and objectives
verbatim from CARL (1).pptx to generate the official presentation.
Saves to D:\\ebca\\CARL_Literature_Review_JNTUH_FORMAT.pptx.
"""
import os, sys
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def build_jntuh_presentation():
    template_path = r"C:\Users\MANAS\Downloads\CARL_Literature_Review_JNTUH_FORMAT.pptx"
    out_path = r"d:\ebca\CARL_Literature_Review_JNTUH_FORMAT.pptx"

    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        return

    prs = Presentation(template_path)
    print(f"Loaded JNTUH template slide count: {len(prs.slides)}")

    # 1. Update Title Slide (Slide 1, index 0)
    slide1 = prs.slides[0]
    for shape in slide1.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if "Design and Simulation" in text or "Design and Development" in text:
                shape.text_frame.text = "Design and Development of a Digital Twin Framework for Biologically Inspired Cognitive Robotic Systems"
                for paragraph in shape.text_frame.paragraphs:
                    paragraph.font.name = "Segoe UI"
                    paragraph.font.size = Pt(20)
                    paragraph.font.bold = True
            elif "Department Of" in text:
                tf = shape.text_frame
                tf.clear()
                p0 = tf.paragraphs[0]; p0.text = "Department Of Mechanical Engineering"
                p1 = tf.add_paragraph(); p1.text = "JNTUH University College Of Engineering Science And Technology Hyderabad"
                p2 = tf.add_paragraph(); p2.text = "Kukatpally, Hyderabad - 500085, Telangana, India"
                for p in tf.paragraphs:
                    p.font.name = "Segoe UI"
                    p.font.size = Pt(11)
            elif "Presented By" in text:
                tf = shape.text_frame
                tf.clear()
                p0 = tf.paragraphs[0]; p0.text = "Presented By"
                p1 = tf.add_paragraph(); p1.text = "Manas Sadashiv (22011P0310)"
                for p in tf.paragraphs:
                    p.font.name = "Segoe UI"
                    p.font.size = Pt(11)

    # 2. Update Introduction Slide (Slide 2, index 1)
    slide2 = prs.slides[1]
    intro_bullets = [
        "Autonomous robotics demands real-time adaptive behaviour under noisy, dynamic physical environments — a challenge that rigid hand-coded controllers fail to meet.",
        "Biological organisms solve this through tightly-coupled neural, chemical, and bodily feedback loops operating across multiple temporal and spatial scales.",
        "Cognitive Autonomous Recurrent Lifeform (CARL) is proposed as a biologically-inspired digital organism, to be simulated within the MuJoCo physics engine, designed to replicate these multi-scale biological control principles.",
        "CARL will integrate a Liquid State Machine (LSM) reservoir brain, 4-factor endocrine neuromodulation (Dopamine, Serotonin, Norepinephrine, Acetylcholine), Spike-Timing-Dependent Plasticity (STDP), hippocampal grid/place cell spatial navigation, and a Free-Energy active inference engine.",
        "Traditional autonomous systems treat perception, navigation, memory, and motor control as isolated software modules — leading to brittle integration and failure under environmental perturbation.",
        "Biological brains maintain robustness through continuous prediction-error minimisation (Free-Energy Principle), neuromodulatory gain control, and activity-dependent synaptic reorganisation.",
        "This study proposes to design and simulate a Cognitive Autonomous Recurrent Lifeform (CARL) using Embodied Biological Cognitive Architecture to achieve adaptive, brain-like autonomous robotic behaviour."
    ]
    slide2.placeholders[0].text = "INTRODUCTION"
    tf_intro = slide2.placeholders[1].text_frame
    tf_intro.clear()
    for idx, b in enumerate(intro_bullets):
        p = tf_intro.add_paragraph() if idx > 0 else tf_intro.paragraphs[0]
        p.text = b
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.space_after = Pt(4)

    # 3. Create & Insert Objectives Slide (Slide 3, index 2)
    # Duplicate layout of slide 2
    slide_layout = slide2.slide_layout
    new_slide = prs.slides.add_slide(slide_layout)
    
    # Move the new slide to index 2 (3rd slide)
    sldIdLst = prs.slides._sldIdLst
    slide_id = sldIdLst[-1]
    sldIdLst.remove(slide_id)
    sldIdLst.insert(2, slide_id)
    
    # Populate Objectives Slide
    new_slide.placeholders[0].text = "OBJECTIVES"
    tf_obj = new_slide.placeholders[1].text_frame
    tf_obj.clear()
    obj_bullets = [
        "To design and simulate CARL as an integrated cognitive-robotic architecture within the MuJoCo physics engine, replicating multi-scale biological control principles.",
        "To integrate a Liquid State Machine (LSM) reservoir brain with 4-factor endocrine neuromodulation (Dopamine, Serotonin, Norepinephrine, Acetylcholine) for adaptive gain control.",
        "To implement Spike-Timing-Dependent Plasticity (STDP) for activity-dependent synaptic reorganisation and continual learning.",
        "To develop hippocampal grid/place cell-based spatial navigation for embodied wayfinding.",
        "To incorporate a Free-Energy active inference engine for continuous prediction-error minimisation and action selection.",
        "To validate the architecture through digital twin experiments measuring adaptive behaviour emergence, energy homeostasis, and spatial navigation accuracy within a real-time (30 Hz) control loop."
    ]
    for idx, b in enumerate(obj_bullets):
        p = tf_obj.add_paragraph() if idx > 0 else tf_obj.paragraphs[0]
        p.text = b
        p.font.name = "Segoe UI"
        p.font.size = Pt(11.5)
        p.space_after = Pt(6)

    # 4. Update the 13 Literature Review Slides (now index 3 to 15)
    # The exact 13 papers data from CARL (1).pptx
    carl_1_papers = [
        [
            "1. Zang et al. (2024)",
            "Model Predictive Control and Reinforcement Learning Integration for Unstable Robots",
            "Hybrid architecture combining a learned continuous controller with receding-horizon MPC safety rollouts, tested on unstable robotic platforms.",
            "Coupling reactive neural control with short-horizon MPC rollouts improves recovery and stability where either method alone fails.",
            "Computational cost increases with horizon length, and performance depends on the accuracy of the internal rollout model."
        ],
        [
            "2. D. Hafner, J. Pasukonis, J. Ba, and T. Lillicrap (2023)",
            "Mastering Diverse Domains Through World Models (DreamerV3)",
            "Learning a latent world model from experience and training a policy purely through imagined rollouts within that model.",
            "Latent imagination enables sample-efficient learning across diverse domains without task-specific tuning.",
            "Performance depends on world-model accuracy; errors in the learned model can compound over longer imagined rollouts."
        ],
        [
            "3. Rahimi et al. (2023)",
            "Hyperdimensional Computing for Efficient Embodied Learning and Memory",
            "Algebraic analysis and robotic benchmarking of high-dimensional (40,000-D) bipolar vector representations for state and memory encoding.",
            "Near-orthogonal high-dimensional vectors give constant-time binding, bundling, and associative memory retrieval robust to noise.",
            "Validated mainly in controlled benchmarks; robustness under highly variable real-world sensor noise is less established."
        ],
        [
            "4. P. Mazzaglia, T. Verbelen, O. Çatal, and B. Dhoedt (2022)",
            "Free-Energy Minimization and Active Inference in Embodied Agents",
            "Formal derivation of an expected-free-energy objective for embodied agents, evaluated in simulated robotic control tasks.",
            "Minimizing expected free energy unifies goal-seeking, risk avoidance, and exploration into a single action-selection objective.",
            "Requires several simplifying assumptions to remain computationally tractable in real time."
        ],
        [
            "5. C. D. Schuman, S. R. Kulkarni, M. Parsa, J. P. Mitchell, P. Date, and B. Kay (2022)",
            "Opportunities for Neuromorphic Computing and Spiking Neural Networks",
            "Review and synthesis of spiking neural network architectures and eligibility-trace learning rules for edge robotics.",
            "Event-based spiking execution with eligibility traces enables energy-efficient, online synaptic learning without backpropagation.",
            "Hardware and software tooling for neuromorphic systems remain immature compared to conventional deep learning frameworks."
        ],
        [
            "6. F. Zenke and T. P. Vogels (2021)",
            "Visualizing and Understanding Plasticity Rules in Spiking Neural Networks",
            "Surrogate-gradient training of spiking neural networks combined with analysis of homeostatic synaptic scaling mechanisms.",
            "Homeostatic downscaling of synaptic weights prevents runaway excitation and consolidates memory while restoring signal-to-noise ratio.",
            "Demonstrated mainly on small benchmark networks; general scaling to large, embodied systems is not established."
        ],
        [
            "7. V. Makoviychuk, L. Wawrzyniak, Y. Guo, M. Lu, K. Storey, M. Macklin, D. Hoeller, N. Rudin, A. Allshire, A. Handa, and G. State (2021)",
            "GPU-Accelerated Rigid Body Physics Simulation for Robot Learning",
            "Engineering development and benchmarking of a GPU-parallelized, convex-contact rigid-body physics engine for robot learning.",
            "High-throughput, contact-rich simulation supports fast domain randomization and real-time model-based control.",
            "A simulation-to-reality gap remains, since contact and friction models are still approximations of true physical behaviour."
        ],
        [
            "8. R. Hasani, M. Lechner, A. Amini, D. Rus, and R. Grosu (2021)",
            "Liquid Time-Constant Networks",
            "Continuous-time neural ODE formulation with input-dependent, learnable time constants, benchmarked on time-series and control tasks.",
            "Adaptive per-neuron time constants match processing speed to input dynamics, giving expressive control with far fewer parameters than LSTMs.",
            "Higher computational cost per simulation step than discrete RNNs; behaviour at much larger network scale remains untested."
        ],
        [
            "9. P. Sterling (2020)",
            "Allostasis and Predictive Energy Allocation in Neural Systems",
            "Theoretical synthesis of physiological and neuroscientific evidence into a predictive model of biological drive regulation.",
            "Anticipatory, predictive regulation of internal drives allocates resources more efficiently than reactive homeostasis alone.",
            "Largely conceptual, with limited guidance on how to implement predictive drive allocation computationally."
        ],
        [
            "10. J. C. R. Whittington, T. H. Muller, S. Mark, G. Chen, C. Barry, N. Burgess, and T. E. J. Behrens (2020)",
            "The Tolman-Eichenbaum Machine: Unifying Space and Cognition",
            "Computational modelling of hippocampal place cells and entorhinal grid cells, tested against rodent electrophysiology and generalization tasks.",
            "A shared entorhinal-hippocampal code generalizes spatial and relational structure, unifying navigation and memory.",
            "Validated mainly on small simulated environments; translating it to noisy real-world sensor data is non-trivial."
        ],
        [
            "11. A. Howard, M. Sandler, G. Chu, L.-C. Chen, B. Chen, M. Tan, W. Wang, Y. Zhu, R. Pang, V. Vasudevan, Q. V. Le, and H. Adam (2019)",
            "Searching for MobileNetV3: Lightweight Vision for Edge Devices",
            "Neural architecture search combined with hardware-aware optimization to design lightweight convolutional networks for edge inference.",
            "Depthwise-separable convolutions and efficient activations enable real-time visual feature extraction at low latency and memory cost.",
            "Accuracy is traded off against speed, and performance depends on the target edge hardware's compute constraints."
        ],
        [
            "12. A. A. Rusu, M. Večerík, T. Rothörl, N. Heess, R. Pascanu, and R. Hadsell; J. Tobin, R. Fong, A. Ray, J. Schneider, W. Zaremba, and P. Abbeel (2018)",
            "Sim-to-Real Transfer and Domain Randomization for Robotic Control",
            "Systematic training of control policies across randomized physics parameters (friction, mass, delay, sensor noise), then transfer evaluation.",
            "Domain randomization bridges the sim-to-real gap, producing policies robust to unmodeled friction, mass, and sensor disturbances.",
            "Needs wide, carefully chosen randomization ranges, and transfer quality still depends on simulator fidelity."
        ],
        [
            "13. J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov (2017)",
            "Proximal Policy Optimization Algorithms",
            "Empirical benchmarking of a clipped surrogate policy-gradient objective across continuous-control robotic locomotion tasks.",
            "The clipped objective gives stable, sample-efficient policy learning and a robust baseline for continuous motor control.",
            "Requires large numbers of environment samples to converge and remains sensitive to hyperparameter choices."
        ]
    ]

    for idx, paper in enumerate(carl_1_papers):
        slide_idx = idx + 3
        slide = prs.slides[slide_idx]
        
        # Ensure title is correct
        for shape in slide.shapes:
            if shape.has_text_frame and "LITERATURE" in shape.text_frame.text:
                shape.text_frame.text = "LITERATURE REVIEW" if idx == 0 else "LITERATURE REVIEW (CONTINUED)"
                for p in shape.text_frame.paragraphs:
                    p.font.name = "Segoe UI"
                    p.font.size = Pt(20)
                    p.font.bold = True
            
            # Find and fill the table
            if shape.has_table:
                table = shape.table
                if len(table.rows) >= 2:
                    row2 = table.rows[1]
                    row2.cells[0].text = paper[0]
                    row2.cells[1].text = paper[1]
                    row2.cells[2].text = paper[2]
                    row2.cells[3].text = paper[3]
                    row2.cells[4].text = paper[4]
                    
                    # Apply Segoe UI font and Pt(9) size to avoid any cell overflow
                    for cell in row2.cells:
                        for p in cell.text_frame.paragraphs:
                            p.font.name = "Segoe UI"
                            p.font.size = Pt(9.0)

    # 5. Update Slide 17: LITERATURE SUMMARY (index 16)
    slide17 = prs.slides[16]
    summary_bullets = [
        "The 13 core papers span 2017–2024 across reinforcement learning, sim-to-real transfer, edge vision, spatial cognition, predictive homeostasis, and continuous/spiking neural control — covering every subsystem of CARL.",
        "Schulman's PPO and Rusu & Tobin's domain randomization ground CARL's motor policy training and sim-to-real transfer strategy.",
        "Howard's MobileNetV3 grounds CARL's real-time edge visual perception pipeline.",
        "Whittington's Tolman-Eichenbaum Machine and Sterling's allostasis research ground CARL's spatial mapping and predictive drive regulation.",
        "Hasani's Liquid Time-Constant Networks and Makoviychuk's GPU physics engine ground CARL's continuous motor dynamics and digital twin simulation substrate.",
        "Zenke's synaptic plasticity research and Schuman's neuromorphic computing review ground CARL's spiking plasticity and sleep-consolidation mechanisms.",
        "Mazzaglia's active inference work grounds CARL's free-energy-based drive reduction and action selection.",
        "Rahimi's hyperdimensional computing and Hafner's DreamerV3 ground CARL's holographic memory and latent-imagination planning, with Zang's MPC-RL integration grounding its emergency recovery controller."
    ]
    slide17.placeholders[0].text = "LITERATURE SUMMARY"
    tf_sum = slide17.placeholders[1].text_frame
    tf_sum.clear()
    for idx, b in enumerate(summary_bullets):
        p = tf_sum.add_paragraph() if idx > 0 else tf_sum.paragraphs[0]
        p.text = b
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.space_after = Pt(4)

    # 6. Update Slide 18: RESEARCH GAP (index 17)
    slide18 = prs.slides[17]
    gap_bullets = [
        "Most existing robotic cognitive architectures implement either purely connectionist deep-learning controllers OR simplified spiking neuron simulations — none integrate both within a single real-time control loop.",
        "Limited research exists on coupling multi-factor endocrine neuromodulation (DA/NE/5-HT/ACh) with Liquid State Machine reservoir brains for continuous autonomous control.",
        "No prior work has directly coupled hippocampal continuous attractor grid cells with real-time MuJoCo physics-based motor controllers for embodied spatial navigation.",
        "PROPOSED GAP",
        "Develop CARL as an integrated architecture combining LSM reservoir computing, STDP spiking plasticity, 4-factor endocrine gain control, hippocampal grid cell navigation, and Free-Energy active inference within a single 30 Hz real-time MuJoCo simulation loop.",
        "Validate the architecture through systematic digital twin experiments measuring adaptive behaviour emergence, energy homeostasis, and spatial navigation accuracy."
    ]
    slide18.placeholders[0].text = "RESEARCH GAP"
    tf_gap = slide18.placeholders[1].text_frame
    tf_gap.clear()
    for idx, b in enumerate(gap_bullets):
        p = tf_gap.add_paragraph() if idx > 0 else tf_gap.paragraphs[0]
        p.text = b
        p.font.name = "Segoe UI"
        if b == "PROPOSED GAP":
            p.font.bold = True
            p.font.size = Pt(12)
            p.font.color.rgb = RGBColor(2, 132, 199)
            p.space_before = Pt(8)
        else:
            p.font.size = Pt(11)
        p.space_after = Pt(4)

    # 7. Update Slide 19: REFERENCES (index 18) and duplicate for index 19
    # Duplicate Slide 19 to Slide 20
    slide19 = prs.slides[18]
    ref_layout = slide19.slide_layout
    ref_slide2 = prs.slides.add_slide(ref_layout)
    
    # Move to index 19 (Slide 20)
    sldIdLst = prs.slides._sldIdLst
    slide_id = sldIdLst[-1]
    sldIdLst.remove(slide_id)
    sldIdLst.insert(19, slide_id)

    # Populate Slide 19 (References Part 1, [1] to [8])
    ref1_list = [
        "[1] X. Zang et al., “Model predictive control and reinforcement learning integration for unstable robotic systems,” IEEE Trans. Robotics (T-RO), 2024.",
        "[2] D. Hafner, J. Pasukonis, J. Ba, and T. Lillicrap, “Mastering diverse domains through world models (DreamerV3),” Nature / arXiv:2301.04104, 2023.",
        "[3] A. Rahimi et al., “Hyperdimensional computing for efficient embodied learning and memory,” IEEE Trans. Neural Networks and Learning Systems (TNNLS), 2023.",
        "[4] P. Mazzaglia, T. Verbelen, O. Çatal, and B. Dhoedt, “Free-energy minimization and active inference in embodied agents,” IEEE Trans. Cognitive and Developmental Systems, 2022.",
        "[5] C. Schuman et al., “Opportunities for neuromorphic computing and spiking neural networks,” Nature Computational Science, vol. 2, pp. 10–19, 2022.",
        "[6] F. Zenke and T. P. Vogels, “Visualizing and understanding plasticity rules in spiking neural networks,” Nature Communications, vol. 12, 2021.",
        "[7] V. Makoviychuk et al. / E. Todorov, T. Erez, and Y. Tassa, “GPU-accelerated rigid body physics simulation for robot learning,” NeurIPS / IEEE Trans. Robotics, 2021/2024.",
        "[8] R. Hasani, M. Lechner, A. Amini, D. Rus, and R. Grosu, “Liquid time-constant networks,” Nature Machine Intelligence, vol. 3, no. 2, pp. 148–158, 2021."
    ]
    slide19.placeholders[0].text = "REFERENCES"
    tf_ref1 = slide19.placeholders[1].text_frame
    tf_ref1.clear()
    for idx, ref in enumerate(ref1_list):
        p = tf_ref1.add_paragraph() if idx > 0 else tf_ref1.paragraphs[0]
        p.text = ref
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.space_after = Pt(4)

    # Populate Slide 20 (References Part 2, [9] to [13])
    ref2_list = [
        "[9] P. Sterling, “Allostasis and predictive energy allocation in neural systems,” Trends in Neurosciences, vol. 43, no. 12, 2020.",
        "[10] J. Whittington, T. Muller, S. Mark, et al., “The Tolman-Eichenbaum machine: Unifying space and relational memory through generalization in the hippocampal formation,” Cell, vol. 183, no. 5, pp. 1249–1263, 2020.",
        "[11] A. Howard et al., “Searching for MobileNetV3: Lightweight vision for edge devices,” in Proc. IEEE ICCV, 2019.",
        "[12] A. A. Rusu et al. and J. Tobin et al., “Sim-to-real transfer and domain randomization for robotic control,” IEEE ICRA / CoRL, 2018/2022.",
        "[13] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, “Proximal policy optimization algorithms,” arXiv:1707.06347, 2017."
    ]
    ref_slide2.placeholders[0].text = "REFERENCES (CONTINUED)"
    tf_ref2 = ref_slide2.placeholders[1].text_frame
    tf_ref2.clear()
    for idx, ref in enumerate(ref2_list):
        p = tf_ref2.add_paragraph() if idx > 0 else tf_ref2.paragraphs[0]
        p.text = ref
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.space_after = Pt(4)

    # Slide 21 (index 20) is THANK YOU
    slide21 = prs.slides[20]
    slide21.placeholders[0].text = "THANK YOU"

    prs.save(out_path)
    print(f"SUCCESS: Created exact matching JNTUH presentation at {out_path} with slide count {len(prs.slides)}")

if __name__ == "__main__":
    build_jntuh_presentation()
