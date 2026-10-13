import sys
import math
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg0 = configs[0]

hal = CarlStage1HAL(xml_path=cfg0["xml_path"])
sx, sy = cfg0["spawn_pos"]
syaw = cfg0["spawn_yaw"]

hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

controller = CARLActiveInferenceEngine(
    grid_path=cfg0["grid_path"],
    w_info=1.0,
    frontier_mode="macro",
    norm_mode="dimensionless"
)
controller.initialize_pose(sx, sy, syaw)

v_est = 0.0
for tick in range(50):
    sensors = hal.read_sensors()
    sonars = sensors[:15]
    gyro_yaw = float(sensors[20])

    controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
    action, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)

    cmd_6d = np.zeros(6, dtype=np.float64)
    cmd_6d[0] = float(action[0])
    cmd_6d[1] = float(action[1])

    hal.step(cmd_6d)
    q_curr = hal.data.qpos[qa:qa+7]
    curr_pos = [float(q_curr[0]), float(q_curr[1])]
    curr_yaw = math.degrees(2.0 * math.atan2(float(q_curr[6]), float(q_curr[3])))

    if tick % 5 == 0 or tick > 10 and tick < 20 or tick >= 25:
        d_fwd = float(np.min(sonars[6:9]))
        cached_f = controller._cached_macro_frontier
        print(f"Tick {tick:2d}: pos=({curr_pos[0]:.3f}, {curr_pos[1]:.3f}), yaw={curr_yaw:6.1f}deg, u=[{action[0]:.2f}, {action[1]:.2f}], d_fwd={d_fwd:.3f}, f_star={cached_f}")

    u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
    v_est = 0.65 * v_est + 0.35 * (u_fwd * 0.35)
