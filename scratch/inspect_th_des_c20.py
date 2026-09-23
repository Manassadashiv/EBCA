import sys, math, numpy as np, torch, mujoco
from pathlib import Path
repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg = configs[20]
hal = CarlStage1HAL(xml_path=cfg['xml_path'])
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)
ctrl = CARLActiveInferenceEngine(grid_path=cfg['grid_path'], w_info=1.0)
ctrl.initialize_pose(sx, sy, syaw)
v_est = 0.0

for tick in range(120):
    sens = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
    
    # Peek inside select_action to get th_des
    macro_res = ctrl._compute_macro_frontier(ctrl.pose[0], ctrl.pose[1])
    th_des = float(ctrl.pose[2])
    if macro_res is not None:
        f_star_x, f_star_y, current_geo_dist, dist_field = macro_res
        rc_ix = int(np.clip((ctrl.pose[0] + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
        rc_iy = int(np.clip((ctrl.pose[1] + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
        d_e = dist_field[rc_iy, rc_ix + 1]; d_w = dist_field[rc_iy, rc_ix - 1]
        d_n = dist_field[rc_iy + 1, rc_ix]; d_s = dist_field[rc_iy - 1, rc_ix]
        grad_x = (d_e - d_w) / (2.0 * ctrl.resolution)
        grad_y = (d_n - d_s) / (2.0 * ctrl.resolution)
        grad_mag = math.sqrt(grad_x**2 + grad_y**2)
        if grad_mag > 0.3:
            th_des = math.atan2(-grad_y, -grad_x)
        else:
            th_des = math.atan2(f_star_y - ctrl.pose[1], f_star_x - ctrl.pose[0])
    
    d_l_side = float(sens[12]); d_r_side = float(sens[2])
    tilt = 0.0
    if (d_l_side < 0.65 and d_r_side < 0.65 and (0.35 <= d_l_side + d_r_side <= 0.90)):
        tilt = float(np.clip(1.2 * (d_l_side - d_r_side), -0.22, 0.22))
        th_des += tilt
    
    u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
    cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
    hal.step(cmd)
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
    u_fwd = 0.5*(u[0]+u[1])
    v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
    if tick >= 90:
        print(f"t={tick:2d}: pos=({nx:.3f},{ny:.3f}), th={ctrl.pose[2]:.2f}, th_des={th_des:.2f}, tilt={tilt:.2f}, grad=({grad_x:.2f},{grad_y:.2f}), u=[{u[0]:.2f},{u[1]:.2f}]", flush=True)
