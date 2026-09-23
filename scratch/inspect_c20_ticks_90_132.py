import sys, math, numpy as np, torch, mujoco
from pathlib import Path
repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.test_stage3_4R3_certification import build_50_matched_configurations
from scratch.test_harmonized_engine import HarmonizedEngine

configs = build_50_matched_configurations()
cfg = configs[20]
hal = CarlStage1HAL(xml_path=cfg['xml_path'])
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)
ctrl = HarmonizedEngine(grid_path=cfg['grid_path'], w_info=1.0)
ctrl.initialize_pose(sx, sy, syaw)
v_est = 0.0

for tick in range(135):
    sens = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
    
    # Peek macro_frontier
    macro_res = ctrl._compute_macro_frontier(ctrl.pose[0], ctrl.pose[1])
    th_geo = None
    if macro_res is not None:
        f_star_x, f_star_y, current_geo_dist, dist_field = macro_res
        rc_ix = int(np.clip((ctrl.pose[0] + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
        rc_iy = int(np.clip((ctrl.pose[1] + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
        d_e = dist_field[rc_iy, rc_ix + 1]; d_w = dist_field[rc_iy, rc_ix - 1]
        d_n = dist_field[rc_iy + 1, rc_ix]; d_s = dist_field[rc_iy - 1, rc_ix]
        grad_x = (d_e - d_w) / (2.0 * ctrl.resolution)
        grad_y = (d_n - d_s) / (2.0 * ctrl.resolution)
        th_geo = math.atan2(-grad_y, -grad_x)
    
    u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
    cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
    hal.step(cmd)
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
    u_fwd = 0.5*(u[0]+u[1])
    v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
    c_info = hal.get_carl_contact_info()
    coll = (c_info['carl_contacts'] - c_info['floor_contacts'] > 0)
    
    if tick >= 95:
        d_l = float(sens[12]); d_r = float(sens[2])
        print(f"t={tick:3d}: pos=({nx:.3f},{ny:.3f}), th={ctrl.pose[2]:.2f} ({math.degrees(ctrl.pose[2]):.1f}d), th_geo={th_geo:.2f} ({math.degrees(th_geo) if th_geo else 0:.1f}d), dl={d_l:.2f}, dr={d_r:.2f}, u=[{u[0]:.2f},{u[1]:.2f}], coll={coll}", flush=True)
    if coll:
        break
