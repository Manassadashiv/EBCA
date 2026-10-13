import sys
sys.path.insert(0, ".")
import math
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco

configs = generate_matched_configs(5, seed=6001)
hal = CarlStage1HAL(xml_path=str(XML_PATH))

# Patch _compute_macro_frontier to prioritize corridor centerline
original_compute = CarlAutonomousOrganismAgent

print("=== TESTING CONFIGS 0 TO 4 WITH CENTERLINE FRONTIER TARGET ===")
for cfg_idx in range(5):
    cfg = configs[cfg_idx]
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]

    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa + 2] = [sx, sy]
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    agent = CarlAutonomousOrganismAgent(
        dt=hal.dt,
        deliberation_mode="active_inference",
        grid_path=str(GRID_PATH)
    )
    agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))
    
    # Wrap agent's _compute_macro_frontier to center fy near 0.0 when in corridor
    old_macro_fn = agent.deliberation._compute_macro_frontier
    def centered_macro_fn(c_x, c_y):
        res = old_macro_fn(c_x, c_y)
        if res is not None:
            fx, fy, dist, dfield = res
            if c_x > -0.60:
                # Clamp frontier sink lateral offset to stay inside corridor width
                fy = float(np.clip(fy, -0.15, 0.15))
            return fx, fy, dist, dfield
        return res
    agent.deliberation._compute_macro_frontier = centered_macro_fn

    escaped = False
    collision = False
    for tick in range(400):
        res = agent.step_cognitive_cycle(hal)
        u_cmd = res["action_cmd"]
        s_next, diag = hal.step(u_cmd)
        
        qx = float(hal.data.qpos[qa])
        qy = float(hal.data.qpos[qa + 1])
        impact = hal.get_carl_impact_info()
        
        if impact["damaging_impacts"] > 0:
            collision = True
            print(f"Config {cfg_idx}: COLLISION at tick {tick}: pos=({qx:.2f}, {qy:.2f}) | max_fn={impact['max_normal_force']:.2f} N")
            break
        if qx <= -0.55:
            escaped = True
            print(f"Config {cfg_idx}: ESCAPED at tick {tick}! pos=({qx:.2f}, {qy:.2f})")
            break
    if not escaped and not collision:
        print(f"Config {cfg_idx}: TIMEOUT at tick {tick}: pos=({qx:.2f}, {qy:.2f})")
