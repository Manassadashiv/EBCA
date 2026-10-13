import sys, math, numpy as np, mujoco
from brain.carl_active_inference import CARLActiveInferenceEngine
from brain.carl_stage1_hal import CarlStage1HAL
from tests.diagnose_env2_failures import build_50_matched_configurations

configs = build_50_matched_configurations()
for cfg in [c for c in configs if c['config_id'] in [20, 21, 22, 23, 24]]:
    cfg_id = cfg['config_id']
    hal = CarlStage1HAL(xml_path='world/stage3_4_environments/asymmetric_t_junction.xml')
    ctrl = CARLActiveInferenceEngine(
        grid_path='world/stage3_4_environments/asymmetric_t_junction_grid.pt',
        w_info=1.0,
        frontier_mode='macro',
        norm_mode='dimensionless',
    )
    sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
    ctrl.initialize_pose(sx, sy, syaw)
    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2.0), 0.0, 0.0, math.sin(syaw/2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    v_est = 0.0
    collided = False
    escaped = False
    for tick in range(220):
        sensors = hal.read_sensors()
        gyro_yaw = float(sensors[20])
        ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=gyro_yaw)
        cmd_6d = np.zeros(6); cmd_6d[:2] = u_star[:2]
        hal.step(cmd_6d)
        v_est = 0.70 * v_est + 0.30 * (0.5 * (u_star[0] + u_star[1]) * 0.30)
        
        qa = int(hal.model.joint('spatial_identity').qposadr[0])
        curr_y = hal.data.qpos[qa+1]
        if curr_y <= -1.20:
            escaped = True
            print(f"Config {cfg_id}: ESCAPED at tick {tick}! Final pos: [{hal.data.qpos[qa]:.4f}, {curr_y:.4f}]")
            break

        ci = hal.get_carl_contact_info()
        if (ci['carl_contacts'] - ci['floor_contacts']) > 0:
            print(f"Config {cfg_id}: COLLISION at tick {tick}: pos=[{hal.data.qpos[qa]:.4f}, {curr_y:.4f}]")
            collided = True
            break

    if not collided and not escaped:
        print(f"Config {cfg_id}: TIMEOUT! Final pos: [{hal.data.qpos[qa]:.4f}, {hal.data.qpos[qa+1]:.4f}]")
