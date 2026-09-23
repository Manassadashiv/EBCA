import sys
sys.path.insert(0, '.')
import mujoco, numpy as np, math
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

for cfg_id, sx, sy, syaw in [
    (0, 0.50, 0.00, 0.00),
    (5, 0.575, 0.057, 0.08),
    (8, 0.491, -0.009, 0.00),
]:
    hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
    ctrl = CARLActiveInferenceEngine(
        grid_path='world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt',
        w_info=1.0,
        frontier_mode='macro',
        norm_mode='dimensionless'
    )
    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
    mujoco.mj_forward(hal.model, hal.data)
    ctrl.initialize_pose(sx, sy, syaw)

    v_est = 0.0
    print(f"\n--- Checking Config {cfg_id} ---")
    stall_step = None
    for tick in range(220):
        sensors = hal.read_sensors()
        ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=0.030)
        action, telem = ctrl.select_action(sensors[:15], curr_v=v_est, curr_w=float(sensors[20]))
        cmd_6d = np.zeros(6, dtype=np.float64); cmd_6d[0]=float(action[0]); cmd_6d[1]=float(action[1])
        hal.step(cmd_6d)
        v_est = 0.70 * v_est + 0.30 * (0.5 * (cmd_6d[0] + cmd_6d[1]) * 0.30)
        
        q_curr = hal.data.qpos[qa:qa+7]
        px, py = float(q_curr[0]), float(q_curr[1])
        yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        cos_yaw = math.cos(yaw)
        
        # Check condition: inside turning bay (px in [0.35, 0.85]), facing exit (cos_yaw < -0.5, i.e. yaw > 120 deg)
        if 0.35 <= px <= 0.85 and cos_yaw < -0.70:
            if stall_step is None:
                stall_step = tick
                print(f"First oriented toward exit at tick {tick}: pos=({px:.3f}, {py:.3f}), yaw={math.degrees(yaw):.1f}deg, cos_yaw={cos_yaw:.2f}, action=[{action[0]:.2f}, {action[1]:.2f}]")
        
        # Check collision
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            print(f"Collided at tick {tick}: pos=({px:.3f}, {py:.3f}), yaw={math.degrees(yaw):.1f}deg")
            break
        if px <= -0.55:
            print(f"Escaped at tick {tick}")
            break
    print(f"Final tick: {tick}, pos=({px:.3f}, {py:.3f}), yaw={math.degrees(yaw):.1f}deg")
