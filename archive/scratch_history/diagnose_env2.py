import sys
import math
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations, ENV2_XML, ENV2_GRID

configs = build_50_matched_configurations()
cfg = configs[20] # First Env 2 config
sx, sy = cfg["spawn_pos"]
syaw = cfg["spawn_yaw"]
print(f"Config 20: spawn=({sx}, {sy}), yaw={syaw}")

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

v_est = 0.0
for tick in range(120):
    sensors = hal.read_sensors()
    sonars = sensors[:15]
    gyro_yaw = float(sensors[20])
    ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
    u_star, telem = ctrl.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
    cmd_6d = telem.get("action_6d", np.zeros(6, dtype=np.float64))
    hal.step(cmd_6d)
    
    q_curr = hal.data.qpos[qa:qa+7]
    cx, cy = float(q_curr[0]), float(q_curr[1])
    cyaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
    u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
    v_est = 0.65 * v_est + 0.35 * (u_fwd * 0.35)
    
    if tick % 10 == 0 or cy <= -1.20:
        d_fwd = sonars[7]
        d_flank_r = max(sonars[3], sonars[4])
        d_flank_l = max(sonars[10], sonars[11])
        print(f"Tick {tick:03d}: pos=({cx:.2f}, {cy:.2f}, yaw={math.degrees(cyaw):.1f}deg) u=({u_star[0]:.2f}, {u_star[1]:.2f}) fwd={d_fwd:.2f} fl_r={d_flank_r:.2f} fl_l={d_flank_l:.2f}")
    if cy <= -1.20:
        print(f"ESCAPED at tick {tick}!")
        break
