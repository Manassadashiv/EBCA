import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations
import numpy as np, math

cfgs = build_50_matched_configurations()
cfg = cfgs[0]
hal = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"))
ctrl = CARLActiveInferenceEngine(grid_path=cfg["grid_path"], w_info=1.0)
ctrl.initialize_pose(*cfg["spawn_pos"], cfg["spawn_yaw"])
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa+2] = cfg["spawn_pos"]
hal.data.qpos[qa+3:qa+7] = [math.cos(cfg["spawn_yaw"]/2.0), 0.0, 0.0, math.sin(cfg["spawn_yaw"]/2.0)]

v_est = 0.0
for tick in range(180):
    sensors = hal.read_sensors()
    sonars = sensors[:15]
    gyro_yaw = float(sensors[20])
    ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
    action, telem = ctrl.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
    cmd_6d = np.zeros(6, dtype=np.float64)
    cmd_6d[0], cmd_6d[1] = action[0], action[1]
    hal.step(cmd_6d)
    u_fwd = 0.5 * (cmd_6d[0] + cmd_6d[1])
    v_est = 0.65 * v_est + 0.35 * (u_fwd * 0.35)

actual_yaw = 2.0 * math.atan2(hal.data.qpos[qa+6], hal.data.qpos[qa+3])
print(f"actual_yaw: {math.degrees(actual_yaw):.1f} deg ({actual_yaw:.3f} rad)")
print(f"ctrl.pose yaw: {math.degrees(ctrl.pose[2]):.1f} deg ({ctrl.pose[2]:.3f} rad)")
print(f"v_est: {v_est:.4f}")
