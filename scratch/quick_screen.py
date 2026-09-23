import sys
import math
import numpy as np
import torch
import mujoco
from pathlib import Path

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg_map = {c["config_id"]: c for c in configs}

ENV1_XML = repo_root / "world/stage3_4_environments/cul_de_sac_turning_bay.xml"
ENV1_GRID = repo_root / "world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt"
ENV2_XML = repo_root / "world/stage3_4_environments/asymmetric_t_junction.xml"
ENV2_GRID = repo_root / "world/stage3_4_environments/asymmetric_t_junction_grid.pt"

print("=== SCREENING CURRENT carl_active_inference.py ===", flush=True)
results = []
for cfg_id in [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]:
    cfg = cfg_map[cfg_id]
    env_id = cfg["env_id"]
    xml_path = str(ENV1_XML if env_id == 1 else ENV2_XML)
    grid_path = str(ENV1_GRID if env_id == 1 else ENV2_GRID)
    sx, sy, syaw = cfg["spawn_pos"][0], cfg["spawn_pos"][1], cfg["spawn_yaw"]
    seed = cfg["seed"]

    np.random.seed(seed); torch.manual_seed(seed)
    hal = CarlStage1HAL(xml_path=xml_path)
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    ctrl = CARLActiveInferenceEngine(grid_path=grid_path, w_info=1.0)
    ctrl.initialize_pose(sx, sy, syaw)

    had_collision, escaped = False, False
    v_est = 0.0
    for tick in range(220):
        sensors = hal.read_sensors()
        ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=ctrl.dt)
        u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=float(sensors[20]))
        cmd_6d = np.zeros(6)
        cmd_6d[0], cmd_6d[1] = float(u_star[0]), float(u_star[1])
        hal.step(cmd_6d)
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        new_x, new_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = float(0.5*(cmd_6d[0]+cmd_6d[1]))
        v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
        c_info = hal.get_carl_contact_info()
        if c_info["carl_contacts"] - c_info["floor_contacts"] > 0:
            had_collision = True; break
        
        if env_id == 1 and new_x <= -0.55:
            escaped = True; break
        elif env_id == 2 and new_y <= -1.20:
            escaped = True; break

    outcome = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")
    print(f"Config {cfg_id:2d} (Env{env_id}): {outcome:<10} ticks={tick+1:3d} final_y={new_y:.3f} final_x={new_x:.3f}", flush=True)
    results.append({"cfg_id": cfg_id, "env_id": env_id, "outcome": outcome})

print("\n=== SUMMARY ===", flush=True)
e1 = [r for r in results if r["env_id"] == 1]
e2 = [r for r in results if r["env_id"] == 2]
esc1 = sum(1 for r in e1 if r["outcome"] == "ESCAPE")
col1 = sum(1 for r in e1 if r["outcome"] == "COLLISION")
esc2 = sum(1 for r in e2 if r["outcome"] == "ESCAPE")
col2 = sum(1 for r in e2 if r["outcome"] == "COLLISION")
print(f"Env1 Escapes: {esc1}/5, Collisions: {col1}/5", flush=True)
print(f"Env2 Escapes: {esc2}/5, Collisions: {col2}/5", flush=True)
