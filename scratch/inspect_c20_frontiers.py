import sys, math, numpy as np, torch, mujoco
from pathlib import Path
repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
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

for tick in range(98):
    sens = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
    if tick >= 94:
        # Force recompute macro frontier without cache
        ctrl._cache_counter = 999
        res = ctrl._compute_macro_frontier(ctrl.pose[0], ctrl.pose[1])
        if res is not None:
            fx, fy, cur_d, dfield = res
            rc_ix = int(np.clip((ctrl.pose[0] + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
            rc_iy = int(np.clip((ctrl.pose[1] + ctrl.half_size) / ctrl.resolution, 0, ctrl.grid_size - 1))
            de, dw = dfield[rc_iy, rc_ix+1], dfield[rc_iy, rc_ix-1]
            dn, ds = dfield[rc_iy+1, rc_ix], dfield[rc_iy-1, rc_ix]
            gx = (de - dw) / (2.0 * ctrl.resolution)
            gy = (dn - ds) / (2.0 * ctrl.resolution)
            print(f"t={tick}: pos=({ctrl.pose[0]:.3f},{ctrl.pose[1]:.3f}), frontier=({fx:.3f},{fy:.3f}), cur_d={cur_d:.3f}, d_center={dfield[rc_iy, rc_ix]:.3f}, de={de:.3f}, dw={dw:.3f}, dn={dn:.3f}, ds={ds:.3f}, gx={gx:.3f}, gy={gy:.3f}, th_geo={math.degrees(math.atan2(-gy, -gx)):.1f} deg", flush=True)
    u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
    cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
    hal.step(cmd)
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
    u_fwd = 0.5*(u[0]+u[1])
    v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
