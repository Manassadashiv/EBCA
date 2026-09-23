import sys
sys.path.insert(0, 'd:/ebca')
import numpy as np
import math
from collections import Counter
from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.p1_integrate.carl_p1_integrate_agent import CarlP1IntegrateAgent

hal = MuJoCoHardwareAbstractionLayer('d:/ebca/world/vessel_kinetic.xml')
agent = CarlP1IntegrateAgent(mode='THREE_FACTOR_STDP', seed=101)

# Run 1: Training (Naive agent crashes)
print('=== RUN 1: TRAINING (NAIVE AGENT) ===')
hal.reset()
hal.model.body_pos[hal.model.body('hazard_cube').id] = np.array([1.0, 0.0, 0.15])
traj1 = []
actions1 = []
for t in range(120):
    res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
    for _ in range(3): hal.step()
    sens = agent.base_agent.embodiment.read_proprioception(hal)
    traj1.append((sens.pos_x, sens.pos_y))
    actions1.append(res['chosen_action'])
    if res['collision']:
        print(f"  [COLLISION at tick {t}] pos=({sens.pos_x:.3f}, {sens.pos_y:.3f}) | dW_mag={res['dw_magnitude']:.3f}")
        break

print(f"Run 1 final pos: ({traj1[-1][0]:.3f}, {traj1[-1][1]:.3f}) | Synaptic Weight Norm: {np.linalg.norm(agent.W_hazard):.3f}")

# Run 2: Test A (Post-Learning avoidance)
print('\n=== RUN 2: TEST A (AFTER SYNAPTIC REWIRING) ===')
hal.reset()
hal.model.body_pos[hal.model.body('hazard_cube').id] = np.array([1.0, 0.0, 0.15])
traj2 = []
actions2 = []
col2 = 0
for t in range(150):
    res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
    for _ in range(3): hal.step()
    sens = agent.base_agent.embodiment.read_proprioception(hal)
    traj2.append((sens.pos_x, sens.pos_y))
    actions2.append(res['chosen_action'])
    if res['collision']: col2 += 1

print(f"Run 2 final pos: ({traj2[-1][0]:.3f}, {traj2[-1][1]:.3f}) | Collisions: {col2}")
print("Run 2 actions distribution:", Counter(actions2))
print("First 15 actions in Run 2:", actions2[:15])
