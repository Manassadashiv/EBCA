import sys
sys.path.insert(0, 'd:/ebca')
import numpy as np
from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.p1_integrate.carl_p1_integrate_agent import CarlP1IntegrateAgent

hal = MuJoCoHardwareAbstractionLayer('d:/ebca/world/vessel_kinetic.xml')
agent = CarlP1IntegrateAgent(mode='THREE_FACTOR_STDP', seed=101)

# Run 1: Crash
hal.reset()
hal.model.body_pos[hal.model.body('hazard_cube').id] = np.array([1.0, 0.0, 0.15])
for t in range(80):
    res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
    for _ in range(3): hal.step()
    if res['collision']: break

print(f"Post-crash Synaptic Matrix shape: {agent.W_hazard.shape}")
print(f"Straight hazard weights: sum={agent.W_hazard[:, 0].sum():.3f}, max={agent.W_hazard[:, 0].max():.3f}")
print(f"Curve-L hazard weights: sum={agent.W_hazard[:, 1].sum():.3f}, max={agent.W_hazard[:, 1].max():.3f}")

# Run 2: Inspect EFE scores
print("\n--- RUN 2 STEP-BY-STEP EFE INSPECTION ---")
hal.reset()
hal.model.body_pos[hal.model.body('hazard_cube').id] = np.array([1.0, 0.0, 0.15])
for t in range(60):
    sensory = agent.base_agent.embodiment.read_proprioception(hal)
    u = agent.encode_sensors(sensory, (2.2, 0.0))
    x_t = agent.step_reservoir(u)
    q_haz = agent.predict_hazard_qualities(x_t)
    
    if t % 10 == 0 or q_haz[0] > 0.01:
        print(f"\n[Tick {t:02d}] Robot Pos: ({sensory.pos_x:.3f}, {sensory.pos_y:.3f}) | Sonar min: {min(sensory.sonar_distances):.3f}m")
        print(f"  Q_hazard: Straight={q_haz[0]:.4f} | Curve-L={q_haz[1]:.4f} | Swerve-L={q_haz[3]:.4f}")
        for act_name, act_info in agent.candidate_actions.items():
            idx = agent.action_to_idx[act_name]
            # Print EFE components
            w_L, w_R = act_info["cmd"][0], act_info["cmd"][1]
            v_k = (w_L + w_R) * 0.5 * 0.048
            omega_k = (w_R - w_L) * (0.048 / 0.230)
            yaw_sim = sensory.yaw + omega_k * (0.033 * 15)
            pos_x_sim = sensory.pos_x + v_k * np.cos(yaw_sim) * (0.033 * 15)
            pos_y_sim = sensory.pos_y + v_k * np.sin(yaw_sim) * (0.033 * 15)
            init_dist = np.sqrt((2.2 - sensory.pos_x)**2 + (0.0 - sensory.pos_y)**2)
            final_dist = np.sqrt((2.2 - pos_x_sim)**2 + (0.0 - pos_y_sim)**2)
            goal_cost = (final_dist - init_dist) * 20.0
            effort_cost = 2.0 * (act_info["curv"] ** 2)
            haz_cost = agent.hazard_weight * q_haz[idx]
            bias = -1.5 if act_name == "STRAIGHT_FORWARD" else 0.0
            total_efe = goal_cost + effort_cost + bias + haz_cost
            if "GENTLE" in act_name or act_name == "STRAIGHT_FORWARD":
                print(f"    {act_name:20s}: EFE={total_efe:6.2f} (Goal={goal_cost:5.2f}, Effort={effort_cost:4.2f}, HazCost={haz_cost:5.2f})")
    
    res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
    for _ in range(3): hal.step()
