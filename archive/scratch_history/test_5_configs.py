import sys
sys.path.insert(0, ".")
import math
import time
import mujoco
from pathlib import Path
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH

configs = generate_matched_configs(5, seed=6001)
hal = CarlStage1HAL(xml_path=str(XML_PATH))

def fixed_update_occupancy(self, occ_grid_128, thresh=0.35):
    if occ_grid_128.ndim == 3:
        occ = occ_grid_128[0]
    else:
        occ = occ_grid_128
    factor = occ.shape[0] // self.grid_dim
    down = occ.reshape(self.grid_dim, factor, self.grid_dim, factor).mean(axis=(1, 3))
    self.obstacle_mask = down > thresh

# Patch the class directly
from brain.carl_physarum import CarlPhysarumRoutingEngine
CarlPhysarumRoutingEngine.update_occupancy = fixed_update_occupancy

print("=== TESTING 5 CONFIGS WITH FIXED PHYSARUM ===")
for cfg in configs:
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

    escaped = False
    collision = False
    for tick in range(500):
        res = agent.step_cognitive_cycle(hal)
        hal.step(res["action_cmd"])
        qx = float(hal.data.qpos[qa])
        qy = float(hal.data.qpos[qa + 1])
        for c_i in range(hal.data.ncon):
            con = hal.data.contact[c_i]
            g1 = hal.model.geom(con.geom1).name
            g2 = hal.model.geom(con.geom2).name
            if "chassis" in g1 or "chassis" in g2:
                if any(w in g1 or w in g2 for w in ["wall", "tb_"]):
                    collision = True
                    break
        if collision:
            break
        if qx <= -0.55:
            escaped = True
            break
    print(f"Config {cfg['config_id']}: spawn=({sx:.2f},{sy:.2f}, yaw={syaw:.2f}) -> Escaped={escaped}, Collision={collision}, Ticks={tick}")
