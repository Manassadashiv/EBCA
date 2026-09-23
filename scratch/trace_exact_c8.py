import sys
sys.path.insert(0, '.')
import mujoco, numpy as np, math
from tests.test_stage3_4R2_remediation import build_50_matched_configurations
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

configs = build_50_matched_configurations()
cfg = configs[8]
hal = CarlStage1HAL(xml_path=cfg['xml_path'])
ctrl = CARLActiveInferenceEngine(
    grid_path=cfg['grid_path'],
    w_info=1.0,
    frontier_mode='macro',
    norm_mode='dimensionless'
)

sx, sy = cfg['spawn_pos']
syaw = cfg['spawn_yaw']

hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
mujoco.mj_forward(hal.model, hal.data)
ctrl.initialize_pose(sx, sy, syaw)

v_est = 0.0
for tick in range(220):
    sensors = hal.read_sensors()
    sonars = sensors[:15]
    gyro_yaw = float(sensors[20])
    
    ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
    action, telem = ctrl.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
    
    cmd_6d = np.zeros(6, dtype=np.float64)
    cmd_6d[0], cmd_6d[1] = float(action[0]), float(action[1])
    hal.step(cmd_6d)
    
    q_curr = hal.data.qpos[qa:qa+7]
    px, py = float(q_curr[0]), float(q_curr[1])
    pyaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
    deg_yaw = math.degrees(pyaw)
    
    u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
    v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)
    
    # Check orientation towards corridor (-x axis): deg_yaw in [135, 180] or [-180, -135]
    facing_exit = abs(deg_yaw) >= 135.0
    in_bay = (0.35 <= px <= 0.85)
    
    if facing_exit and in_bay:
        print(f"STALL CANDIDATE tick {tick:3d}: pos=({px:.3f}, {py:.3f}), yaw={deg_yaw:+6.1f}deg, act=[{action[0]:+.2f}, {action[1]:+.2f}], best_c={telem['best_cost']:+.3f}, target={ctrl._cached_macro_frontier}")
