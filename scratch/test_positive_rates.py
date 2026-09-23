import sys
sys.path.insert(0, 'd:/ebca')
import numpy as np
from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.p1_integrate.carl_p1_integrate_agent import CarlP1IntegrateAgent

# Subclass to test non-negative firing rates r(t) = 0.5 * (1 + tanh(x))
class FiringRateAgent(CarlP1IntegrateAgent):
    def get_firing_rates(self, x: np.ndarray) -> np.ndarray:
        return 0.5 * (1.0 + np.tanh(x))

    def predict_hazard_qualities(self, state_x: np.ndarray) -> np.ndarray:
        r = self.get_firing_rates(state_x)
        raw_act = self.W_hazard.T @ r
        # Scale to [0, 1]
        return np.tanh(np.maximum(0.0, raw_act * 0.05))

    def step_stdp_learning(self, state_x, chosen_action_idx, collision_occurred, is_stall=False, prediction_error=0.0):
        r = self.get_firing_rates(state_x)
        return super().step_stdp_learning(r, chosen_action_idx, collision_occurred, is_stall, prediction_error)

hal = MuJoCoHardwareAbstractionLayer('d:/ebca/world/vessel_kinetic.xml')
agent = FiringRateAgent(mode='THREE_FACTOR_STDP', seed=101, hazard_weight=200.0)

# Run 1: Crash
print("=== RUN 1: CRASHING ===")
hal.reset()
hal.model.body_pos[hal.model.body('hazard_cube').id] = np.array([1.0, 0.0, 0.15])
for t in range(80):
    res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
    for _ in range(3): hal.step()
    if res['collision']:
        print(f"  Collision at tick {t}, dW_mag={res['dw_magnitude']:.3f}")
        break

# Run 2: Test Avoidance
print("\n=== RUN 2: POST-LEARNING AVOIDANCE ===")
hal.reset()
hal.model.body_pos[hal.model.body('hazard_cube').id] = np.array([1.0, 0.0, 0.15])
traj = []
actions = []
cols = 0
for t in range(120):
    res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
    for _ in range(3): hal.step()
    sens = agent.base_agent.embodiment.read_proprioception(hal)
    traj.append((sens.pos_x, sens.pos_y))
    actions.append(res['chosen_action'])
    if res['collision']: cols += 1
    if t % 15 == 0:
        print(f"  [Tick {t:02d}] Pos: ({sens.pos_x:.3f}, {sens.pos_y:.3f}) | Action: {res['chosen_action']:20s} | Q_hazard(Straight): {res['q_hazard_chosen']:.3f}")

print(f"\nRun 2 Result: Collisions={cols}, Final Pos=({traj[-1][0]:.3f}, {traj[-1][1]:.3f})")
from collections import Counter
print("Action counts in Run 2:", Counter(actions))
