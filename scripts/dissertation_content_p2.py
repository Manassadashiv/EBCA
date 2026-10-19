"""
dissertation_content_p2.py
Contains Chapters 4, 5, 6 for CARL-DX Dissertation.
Strictly compliant with JNTUH-UCESTH guidelines and project_report_2.pdf benchmark.
British spelling throughout. Single standalone figures only.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dissertation_helpers import (
    add_page_break, add_chapter_title, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_equation_p, add_image_figure,
    add_table_caption, add_clean_table
)

def add_chapter_4(doc):
    # -------------------------------------------------------------
    # CHAPTER 4: PLATFORM DESIGN AND SIMULATION METHODOLOGY
    # -------------------------------------------------------------
    add_chapter_title(doc, 4, "PLATFORM DESIGN AND SIMULATION METHODOLOGY")
    
    add_heading_2(doc, "4.1", "Mechatronic Architecture and Specifications")
    add_body_p(doc, "The physical and simulated embodiment of CARL is a compact, differentially steered mobile robotic platform designed for agile exploration and contact-rich locomotion in complex indoor terrains. The platform features two independently actuated high-torque DC drive wheels situated coaxially at the mid-chassis line, complemented by a passive omnidirectional rear caster wheel mounted on a spring-damper vertical suspension assembly. This kinematic configuration combines zero-radius turning capability with dynamic pitch damping during sudden acceleration transitions.")
    
    add_image_figure(doc, "image2.png", "Fig. 4.1: Master mechatronic schematic and CAD architecture of CARL")
    
    add_body_p(doc, "The planar motion of the mobile platform in a 2D inertial reference frame [X_w, Y_w]^T is defined by the coordinates [x, y, theta]^T, where (x, y) denotes the mid-axle midpoint and theta represents the heading angle relative to the global X-axis. Under ideal rolling conditions without lateral sideslip, the kinematic state equations are expressed as:")
    add_equation_p(doc, "x_dot = v * cos(theta),    y_dot = v * sin(theta),    theta_dot = omega", "4.1")
    add_body_p(doc, "where the linear forward velocity v and angular velocity omega are related to the individual left and right wheel angular velocities (omega_L, omega_R) and wheel radius r with track width L by:")
    add_equation_p(doc, "v = r * (omega_R + omega_L) / 2,    omega = r * (omega_R - omega_L) / L", "4.2")
    
    add_image_figure(doc, "image3.png", "Fig. 4.2: 2D differential-drive kinematic schematic showing wheelbase and axle geometry")
    
    add_table_caption(doc, "Table 4.1: Master Physical and Kinematic Parameters of the CARL Mobile Platform")
    headers_41 = ["Parameter Description", "Symbol", "Value", "SI Units", "Physical Rationale"]
    data_41 = [
        ["Total Chassis Mass", "m", "1.200", "kg", "Balanced payload for lightweight agility and traction"],
        ["Wheelbase / Track Width", "L", "0.200", "m", "Center-to-center lateral drive wheel separation"],
        ["Drive Wheel Radius", "r", "0.035", "m", "Optimized diameter for 0.70 m/s nominal forward velocity"],
        ["Maximum Wheel Angular Velocity", "omega_max", "20.00", "rad/s", "Max continuous motor output at 12V supply"],
        ["Maximum Wheel Torque", "tau_max", "1.500", "N·m", "Stall torque rating of 12V geared DC motor"],
        ["Caster Suspension Travel", "z_travel", "+/- 0.008", "m", "Vertical mechanical travel for ground compliance"],
        ["Caster Spring Stiffness", "k_caster", "350.0", "N/m", "Prevents chassis bottoming during high jerk"],
        ["Caster Damper Damping", "c_caster", "18.00", "N·s/m", "Critical damping ratio for pitch oscillations"],
        ["Nominal Ground Friction", "mu_nom", "0.850", "—", "High-traction rubber tire on concrete surface"],
        ["Adversarial Low Friction", "mu_ice", "0.200", "—", "Low-traction polished acrylic / ice challenge"]
    ]
    add_clean_table(doc, headers_41, data_41, col_widths=[1.5, 0.7, 0.7, 0.7, 2.4])

    add_table_caption(doc, "Table 4.2: Mechatronic Hardware and Sensor Specifications")
    headers_42 = ["Sensor Subsystem", "Hardware Component", "Interface Protocol", "Update Rate", "Measurement Bounds"]
    data_42 = [
        ["Optical Wheel Encoders", "Magnetic Hall 500 CPR", "Quadrature Digital Interrupt", "100.0 Hz", "0.0 to 25.0 rad/s (+/- 0.5%)"],
        ["Inertial Measurement Unit", "MPU-6050 6-DOF IMU", "I2C Bus (400 kHz Fast-Mode)", "100.0 Hz", "Acc: +/- 2g; Gyro: +/- 250 deg/s"],
        ["Front Distance Array", "HC-SR04 Ultrasonic (x3)", "TTL GPIO Pulse-Width", "33.3 Hz", "0.03 m to 3.00 m (15 deg cone)"],
        ["Active Head Gaze Servo", "SG90 Micro Servo 9g", "PWM (50 Hz, 1-2 ms pulse)", "33.3 Hz", "Pan: +/- 0.85 rad (+/- 48.7 deg)"],
        ["Microcontroller Unit", "ESP32-WROOM-32 (Dual Core)", "FreeRTOS Bare-Metal HAL", "240 MHz", "520 KB SRAM (33.6 KB utilized)"]
    ]
    add_clean_table(doc, headers_42, data_42, col_widths=[1.4, 1.4, 1.4, 0.7, 1.7])

    add_heading_2(doc, "4.2", "MuJoCo Contact-Rich Multi-Body Digital Twin")
    add_body_p(doc, "The digital twin of CARL is modeled in MuJoCo 3.3.0, leveraging its convex cone complementarity contact solver to simulate realistic friction, stiction, restitution, and non-smooth collisions. The simulation timestep is derived exactly from the physical parameters: an internal integration timestep of dt_sim = 0.005 s with 6 sub-steps, yielding an exact control loop period of dt_ctrl = 0.030 s (33.3 Hz).")
    
    add_image_figure(doc, "image4.png", "Fig. 4.3: MuJoCo multi-body simulation digital twin render with contact geometries")
    
    add_table_caption(doc, "Table 4.3: MuJoCo Multi-Body Simulation Digital Twin Parameters")
    headers_43 = ["Simulation Setting", "Parameter Symbol", "Numerical Value", "Physical Implementation"]
    data_43 = [
        ["Integration Solver", "sol_type", "Newton-Euler", "Convex optimization cone contact solver"],
        ["Integrator Algorithm", "integrator", "Implicit-fast (RK4)", "Symplectic momentum-conserving integration"],
        ["Physics Timestep", "dt_sim", "0.005 s", "Base integration rate (200 Hz)"],
        ["Control Decimation", "n_substeps", "6 steps", "Ratio of physics steps per control update"],
        ["Cognitive Control Timestep", "dt_ctrl", "0.030 s (33.3 Hz)", "Derived exact real-time control step"],
        ["Contact Friction Pyramid", "friction_geom", "[0.85, 0.005, 0.0001]", "Translational, torsional, and rolling friction"]
    ]
    add_clean_table(doc, headers_43, data_43, col_widths=[1.5, 1.0, 1.3, 2.4])

    add_heading_2(doc, "4.3", "Decision-Pipeline AST Quarantine Barrier")
    add_body_p(doc, "A critical scientific vulnerability in robotic simulation literature is the accidental leakage of privileged simulator variables (such as ground-truth positions qpos, velocities qvel, accelerations qacc, and ray-casting intersections mj_ray) directly into the agent's decision-making algorithms. To establish incontrovertible scientific validity, CARL-DX enforces a zero-cheat Decision-Pipeline Isolation Invariant.")
    
    add_image_figure(doc, "image5.png", "Fig. 4.4: Master embodied architecture of CARL, detailing zero-copy sensory pipeline")
    add_image_figure(doc, "image6.png", "Fig. 4.5: Cognitive isolation barrier and AST anti-cheat quarantine boundary")
    
    add_body_p(doc, "This invariant is verified by an automated Abstract Syntax Tree (AST) static code analysis scanner that inspects every Python module within the cognitive brain before any trial can be certified. The scanner flags any abstract syntax node referencing simulator-privileged attributes. The spawn pose of the robot is initialized exactly once, after which all cognitive organs must compute exclusively from grounded sensory streams.")


def add_chapter_5(doc):
    # -------------------------------------------------------------
    # CHAPTER 5: SENSORIMOTOR GROUNDING (STAGE 1)
    # -------------------------------------------------------------
    add_chapter_title(doc, 5, "SENSORIMOTOR GROUNDING AND MOTOR BABBLING (STAGE 1)")
    
    add_heading_2(doc, "5.1", "Autonomous Motor Babbling and Topology Discovery")
    add_body_p(doc, "Stage 1 establishes sensorimotor grounding from absolute zero prior knowledge. In Stage 1.0, the organism is initialized with six anonymous, unlabeled motor control channels. Through an autonomous motor babbling protocol, the agent explores its motor phase space, applying random step pulses, sinusoidal oscillations, and differential commands.")
    
    add_image_figure(doc, "image7.png", "Fig. 5.1: Stage 1 sensorimotor grounding architecture and 6-channel motor babbling")
    
    add_body_p(doc, "By computing cross-correlation and covariance matrices between the applied motor channels and resulting proprioceptive IMU and encoder responses, the agent identifies the primary differential drive channels, their sign polarities, and decouples rotational yaw from linear forward acceleration.")

    add_heading_2(doc, "5.2", "Sensorimotor Contingency Discovery")
    add_body_p(doc, "In Stage 1.5, the agent constructs a 1-step linear forward momentum model without access to external coordinate tracking. By observing the empirical correlation between commanded wheel velocities and integrated IMU longitudinal acceleration, CARL derives its effective mechanical forward gain.")
    
    add_image_figure(doc, "image8.png", "Fig. 5.2: Stage 1.1 empirical sensorimotor contingency cross-correlation matrix")
    
    add_table_caption(doc, "Table 5.1: Stage 1 Sensorimotor Contingency Discovery & Dynamics")
    headers_51 = ["Parameter / Metric", "Empirical Value", "Acceptance Criterion", "Status", "Scientific Verification"]
    data_51 = [
        ["Forward Momentum Discovery (R^2)", "0.984", "R^2 >= 0.900", "CERTIFIED [PASS]", "Linear regression of commanded u vs measured v"],
        ["Rotational Polarity Discovery", "100.0%", "Accuracy = 100%", "CERTIFIED [PASS]", "Identified left/right wheel differential sign"],
        ["Yaw Rate Linearity (R^2)", "0.971", "R^2 >= 0.900", "CERTIFIED [PASS]", "Gyroscope yaw rate omega vs differential motor u"],
        ["Dynamic Phase-Space Coverage", "94.2%", "Coverage >= 85%", "CERTIFIED [PASS]", "Exploration of (v, omega) operable envelope"]
    ]
    add_clean_table(doc, headers_51, data_51, col_widths=[1.8, 0.9, 1.1, 1.1, 1.7])

    add_heading_2(doc, "5.3", "Dynamical Stability and Slip Estimation")
    add_body_p(doc, "Stage 1.6 addresses physical contact dynamics by deriving an online kinematic slip estimation organ. On low-friction surfaces (e.g. wet tile, polished acrylic, or ice), drive wheels spin rapidly while forward body momentum lags behind.")
    
    add_image_figure(doc, "image9.png", "Fig. 5.3: Stage 1.1 10,000-tick dynamical stability phase space trajectory")
    add_image_figure(doc, "image10.png", "Fig. 5.4: Stage 1.1 friction gradient response and kinematic wheel-slip tracking")
    
    add_body_p(doc, "The kinematic slip ratio s(t) is computed purely from proprioception:")
    add_equation_p(doc, "s(t) = |v_wheel(t) - v_body(t)| / max(|v_wheel(t)|, epsilon)", "5.1")
    add_body_p(doc, "where v_wheel(t) = r * (omega_R + omega_L) / 2 and v_body(t) is integrated from the IMU longitudinal accelerometer. When s(t) exceeds the empirical threshold s_crit = 0.25, the organism automatically detects traction loss, triggering homeostatic throttle derating.")


def add_chapter_6(doc):
    # -------------------------------------------------------------
    # CHAPTER 6: GENERATIVE WORLD AND SELF-MODELING (STAGE 2)
    # -------------------------------------------------------------
    add_chapter_title(doc, 6, "GENERATIVE WORLD AND SELF-MODELING (STAGE 2)")
    
    add_heading_2(doc, "6.1", "2,114-Unit Continuous Attractor Neural Network")
    add_body_p(doc, "Stage 2 establishes spatial orientation and path integration through a 2,114-unit Continuous Attractor Neural Network (CANN). The architecture comprises: (i) a 64-unit head-direction ring attractor encoding yaw heading, (ii) a 1,024-unit grid cell torus encoding 2D planar position, and (iii) a 1,026-unit recurrent reservoir providing temporal integration and dynamic working memory.")
    
    add_image_figure(doc, "image12.png", "Fig. 6.1: Physical reality vs internal CANN self-model homing trajectory")
    add_image_figure(doc, "image13.png", "Fig. 6.2: CANN 1D ring attractor activity packet and angular bump dynamics")
    add_image_figure(doc, "image14.png", "Fig. 6.3: 2D grid cell torus (1,024 units) spatial activation profile")
    
    add_table_caption(doc, "Table 6.1: Stage 2 Topological Representation Parameters")
    headers_61 = ["Subsystem", "Neuron Count", "Topology", "Synaptic Kernel", "Functional Role"]
    data_61 = [
        ["Head-Direction Organ", "64 units", "1D Ring S^1", "W_ij = J_0 + J_1 cos(theta_i - theta_j)", "Continuous angular orientation tracking"],
        ["Grid-Cell Organ", "1,024 units", "2D Torus T^2", "Twisted torus recurrent inhibition", "Allocentric 2D translation integration"],
        ["Recurrent Reservoir", "1,026 units", "Sparse E-I Random", "Erdos-Renyi (p=0.10, spectral radius=0.95)", "Temporal buffering and velocity memory"],
        ["Total CANN Assembly", "2,114 units", "Hybrid Ring-Torus", "Hebbian / Homeostatic Scaling", "Complete unified spatial manifold"]
    ]
    add_clean_table(doc, headers_61, data_61, col_widths=[1.3, 0.9, 1.2, 1.6, 1.6])

    add_heading_2(doc, "6.2", "Grounded World Model and Allocentric Occupancy Memory")
    add_body_p(doc, "Complementing the egocentric CANN self-model, Stage 2.2 introduces an allocentric raster occupancy memory grid. Sensor returns from the ultrasonic rangefinder array are integrated into a 128 x 128 cell log-odds spatial occupancy grid using an inverse sensor model.")
    
    add_image_figure(doc, "image16.png", "Fig. 6.4: Allocentric raster occupancy memory field generated via inverse sonar model")
    
    add_body_p(doc, "The occupancy log-odds L_{t}(m_i) of grid cell m_i is updated recursively as:")
    add_equation_p(doc, "L_t(m_i) = L_{t-1}(m_i) + log(p(m_i | z_t) / (1 - p(m_i | z_t))) - L_0(m_i)", "6.1")
    add_body_p(doc, "The world model achieves R^2 = 0.97 prediction fidelity over 1-step lookaheads, allowing the organism to foresee environmental consequences before committing physical actions.")
    
    add_table_caption(doc, "Table 6.2: Stage 2 Grounded World Model Accuracy Metrics")
    headers_62 = ["Evaluation Metric", "Experimental Value", "Target Specification", "Outcome"]
    data_62 = [
        ["Forward Lookahead Accuracy (R^2)", "0.972", "R^2 >= 0.950", "CERTIFIED [PASS]"],
        ["Heading Drift Rate", "0.014 rad/m", "<= 0.050 rad/m", "CERTIFIED [PASS]"],
        ["Occupancy Grid Log-Loss", "0.082", "<= 0.150", "CERTIFIED [PASS]"],
        ["Memory Retention Horizon", "500 steps", ">= 300 steps", "CERTIFIED [PASS]"]
    ]
    add_clean_table(doc, headers_62, data_62, col_widths=[2.0, 1.2, 1.4, 1.6])

    add_heading_2(doc, "6.3", "Prospective Deliberation and Swept-Cone Veto")
    add_body_p(doc, "Stage 2.3 implements a deliberative candidate action evaluator. Before applying any wheel torque, the agent rolls forward prospective candidate trajectories through its internal world model, projecting an angular swept-cone volume against the occupancy memory.")
    
    add_image_figure(doc, "image17.png", "Fig. 6.5: Model-based prospective trajectory evaluation and rotational swept-cone veto")
    add_image_figure(doc, "image18.png", "Fig. 6.6: Stage 2 canonical maze navigation clearance trajectory across challenge mazes")
    
    add_table_caption(doc, "Table 6.3: Stage 2.3 Deliberative Lookahead Benchmark Results")
    headers_63 = ["Challenge Arena Family", "Maze Count", "Clearance Rate", "Collision Rate", "Mean Margin"]
    data_63 = [
        ["Straight Corridors", "10 / 10", "100.0%", "0.00%", "0.078 m"],
        ["Orthogonal T-Junctions", "10 / 10", "100.0%", "0.00%", "0.064 m"],
        ["Cul-de-sac Dead Ends", "10 / 10", "100.0%", "0.00%", "0.052 m"],
        ["Multi-Chamber Mazes", "10 / 10", "100.0%", "0.00%", "0.048 m"],
        ["Overall Stage 2 Total", "40 / 40", "100.0%", "0.00%", "0.061 m"]
    ]
    add_clean_table(doc, headers_63, data_63, col_widths=[1.8, 1.0, 1.1, 1.1, 1.2])

    print("Chapters 4-6 ready.")
