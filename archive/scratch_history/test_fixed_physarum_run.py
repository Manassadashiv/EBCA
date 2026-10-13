import sys
sys.path.insert(0, ".")
import math
import time
import mujoco
from pathlib import Path
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

ENV_DIR = Path("world/stage3_4_environments")
XML_PATH = ENV_DIR / "cul_de_sac_turning_bay.xml"
GRID_PATH = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"

hal = CarlStage1HAL(xml_path=str(XML_PATH))
hal.reset()
spawn_x, spawn_y, spawn_yaw = 0.58, 0.0, 0.0
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(
    dt=hal.dt,
    deliberation_mode="active_inference",
    grid_path=str(GRID_PATH)
)
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(GRID_PATH))

# Apply the downsampling fix to agent's Physarum organ
def fixed_update_occupancy(occ_grid_128, thresh=0.35):
    if occ_grid_128.ndim == 3:
        occ = occ_grid_128[0]
    else:
        occ = occ_grid_128
    factor = occ.shape[0] // agent.deliberation.physarum.grid_dim
    down = occ.reshape(agent.deliberation.physarum.grid_dim, factor, agent.deliberation.physarum.grid_dim, factor).mean(axis=(1, 3))
    agent.deliberation.physarum.obstacle_mask = down > thresh

agent.deliberation.physarum.update_occupancy = fixed_update_occupancy

print("Starting simulation with fixed Physarum corridor downsampling...")
escaped = False
collision = False
trajectory = []

t_start = time.perf_counter()
for tick in range(500):
    res = agent.step_cognitive_cycle(hal)
    u_cmd = res["action_cmd"]
    hal.step(u_cmd)
    
    qx = float(hal.data.qpos[qa])
    qy = float(hal.data.qpos[qa + 1])
    trajectory.append((qx, qy))
    
    # Check physical contacts
    for c_i in range(hal.data.ncon):
        con = hal.data.contact[c_i]
        g1 = hal.model.geom(con.geom1).name
        g2 = hal.model.geom(con.geom2).name
        if "chassis" in g1 or "chassis" in g2:
            if any(w in g1 or w in g2 for w in ["wall", "tb_"]):
                collision = True
                print(f"Collision at tick {tick}: {g1} <-> {g2}")
                break
    if collision:
        break
        
    if qx <= -0.55:
        escaped = True
        print(f"ESCAPED CUL-DE-SAC AT TICK {tick}! (x={qx:.2f}, y={qy:.2f})")
        break

t_total = time.perf_counter() - t_start
print(f"Result: Escaped={escaped}, Collision={collision}, Ticks={len(trajectory)}, Time={t_total:.2f}s")
print(f"Trajectory start: {trajectory[0]} -> end: {trajectory[-1]}")
