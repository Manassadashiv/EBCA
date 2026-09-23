import sys
sys.path.insert(0, '.')
import mujoco, numpy as np, math
from brain.carl_stage1_hal import CarlStage1HAL

from brain.carl_active_inference import CARLActiveInferenceEngine

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
ctrl = CARLActiveInferenceEngine(grid_path='world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt', w_info=1.0, frontier_mode='macro', norm_mode='dimensionless')

# Spawn pose for Config 8: x=0.491, y=-0.009, yaw=0.0
sx, sy, syaw = 0.491, -0.009, 0.0
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
    
    w_l_id = hal.model.sensor('sens_vel_w_left').id
    w_r_id = hal.model.sensor('sens_vel_w_right').id
    wl = float(hal.data.sensordata[hal.model.sensor_adr[w_l_id]])
    wr = float(hal.data.sensordata[hal.model.sensor_adr[w_r_id]])
    wheel_spd = 0.5 * (wl + wr) * 0.048
    v_est = 0.70 * v_est + 0.30 * (0.5 * (cmd_6d[0] + cmd_6d[1]) * 0.30)
    
    if tick % 10 == 0:
        macro_res = ctrl._cached_macro_frontier
        dist_curr = ctrl._cached_current_dist
        best_c = telem['best_cost']
        act_str = f"[{action[0]:+.2f}, {action[1]:+.2f}]"
        print(f"tick {tick:3d}: pos=({px:+.2f},{py:+.2f}), yaw={math.degrees(pyaw):+5.1f}deg, spd={wheel_spd:+.2f}, act={act_str}, best_c={best_c:+.2f}, target={macro_res}, d_curr={dist_curr:.2f}")
    if px <= -0.55:
        print("ESCAPED at tick", tick)
        break
