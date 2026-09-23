import sys
import math
import time
import json
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"

configs = build_50_matched_configurations()
cfg_map = {c["config_id"]: c for c in configs}

print("Running test on Configs 20, 21, 22, 23, 24...")
for cfg_id in [20, 21, 22, 23, 24]:
    cfg = cfg_map[cfg_id]
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    seed = cfg["seed"]

    np.random.seed(seed)
    torch.manual_seed(seed)

    hal = CarlStage1HAL(xml_path=str(ENV2_XML))
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    ctrl = CARLActiveInferenceEngine(
        grid_path=str(ENV2_GRID),
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    ctrl.initialize_pose(sx, sy, syaw)

    had_collision = False
    escaped = False
    v_est = 0.0

    for tick in range(220):
        sensors = hal.read_sensors()
        gyro_w = float(sensors[20])
        dt = ctrl.dt
        ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_w, dt=dt)

        u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=gyro_w)

        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(u_star[0])
        cmd_6d[1] = float(u_star[1])
        hal.step(cmd_6d)

        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        new_x, new_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        c_info = hal.get_carl_contact_info()
        if c_info["carl_contacts"] - c_info["floor_contacts"] > 0:
            had_collision = True
            break
        if new_y <= -1.20:
            escaped = True
            break

    outcome = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")
    print(f"Config {cfg_id}: outcome={outcome} (tick {tick+1}, final_y={new_y:.3f}, final_x={new_x:.3f})")
