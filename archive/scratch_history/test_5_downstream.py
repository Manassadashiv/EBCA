import sys
import math
import time
sys.path.insert(0, ".")
import mujoco
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

configs = generate_matched_configs(5, seed=6001)
hal = CarlStage1HAL(xml_path=str(XML_PATH))

print("=== TESTING 5 CONFIGS WITH PRINCIPLED PHYSARUM DOWNSTREAM STREAMLINES ===")
for cfg in configs:
    cfg_idx = cfg["config_id"]
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
    
    # Configure downstream streamline sampling in agent deliberation
    def patched_streamline_heading(c_x, c_y, f_star_x, f_star_y):
        # Set sink at open reservoir gateway
        snk_x = -2.5
        snk_y = 0.0
        agent.deliberation.physarum.step(src_pos=(c_x, c_y), snk_pos=(snk_x, snk_y), occ_grid_128=agent.deliberation.grid_np[0])
        
        # Sample downstream 0.25m
        dx = snk_x - c_x
        dy = snk_y - c_y
        dist = math.hypot(dx, dy)
        if dist > 0.30:
            ds_x = c_x + 0.25 * (dx / dist)
            ds_y = c_y + 0.25 * (dy / dist)
        else:
            ds_x, ds_y = snk_x, snk_y
            
        vx, vy, th = agent.deliberation.physarum.get_topological_current(ds_x, ds_y)
        if math.hypot(vx, vy) > 0.05:
            return th
        return math.atan2(dy, dx)
        
    # Hook into agent's deliberation
    agent.deliberation._get_physarum_flow_heading = patched_streamline_heading

    escaped = False
    collision = False
    t0 = time.perf_counter()
    for tick in range(450):
        # In deliberate loop:
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
            t_ep = time.perf_counter() - t0
            print(f"Config {cfg_idx}: ESCAPED at tick {tick}! pos=({qx:.2f}, {qy:.2f}) in {t_ep:.2f}s")
            break
    if not escaped and not collision:
        print(f"Config {cfg_idx}: TIMEOUT at tick {tick}: pos=({qx:.2f}, {qy:.2f})")
