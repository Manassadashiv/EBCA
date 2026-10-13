import sys
sys.path.insert(0, ".")
import math
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco

cfg = generate_matched_configs(5, seed=6001)[0]
sx, sy = cfg["spawn_pos"]
syaw = cfg["spawn_yaw"]

hal = CarlStage1HAL(xml_path=str(XML_PATH))
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

# Patch _sample_trajectories to ensure straight tracking when aligned
old_sample = agent.deliberation._sample_trajectories
def patched_sample(sigma_scale=1.0):
    u_cands = old_sample(sigma_scale)
    c_th = agent.deliberation.pose[2]
    macro = agent.deliberation._compute_macro_frontier(agent.deliberation.pose[0], agent.deliberation.pose[1])
    if macro:
        th_des = math.atan2(macro[1] - agent.deliberation.pose[1], macro[0] - agent.deliberation.pose[0])
        dth = math.atan2(math.sin(th_des - c_th), math.cos(th_des - c_th))
        if abs(dth) < 0.40:
            # Inject straight cruise candidates into first 16 slots
            for spd_idx, spd in enumerate([0.70, 0.80, 0.85, 0.90]):
                u_cands[spd_idx * 4:(spd_idx + 1) * 4, :, 0] = spd
                u_cands[spd_idx * 4:(spd_idx + 1) * 4, :, 1] = spd
    return u_cands

agent.deliberation._sample_trajectories = patched_sample

print(f"Testing Config 0 with straight candidate injection when aligned:")
escaped = False
collision = False
for tick in range(400):
    res = agent.step_cognitive_cycle(hal)
    u_cmd = res["action_cmd"]
    s_next, diag = hal.step(u_cmd)
    
    qx = float(hal.data.qpos[qa])
    qy = float(hal.data.qpos[qa + 1])
    impact = hal.get_carl_impact_info()
    
    if qx <= -0.55:
        escaped = True
        print(f"Config 0: ESCAPED AT TICK {tick}! pos=({qx:.2f}, {qy:.2f})")
        break
    if impact["damaging_impacts"] > 0:
        collision = True
        print(f"Config 0: COLLISION at tick {tick}: pos=({qx:.2f}, {qy:.2f})")
        break
    if tick % 50 == 0:
        print(f"t={tick:03d} | pos=({qx:.2f}, {qy:.2f}) | cmd=({u_cmd[0]:.2f}, {u_cmd[1]:.2f})")
if not escaped and not collision:
    print(f"Config 0: TIMEOUT at tick {tick}: pos=({qx:.2f}, {qy:.2f})")
