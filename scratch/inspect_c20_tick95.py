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

for tick in range(110):
    sens = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
    u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
    cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
    hal.step(cmd)
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
    u_fwd = 0.5*(u[0]+u[1])
    v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
    if tick >= 95:
        macro_res = ctrl._compute_macro_frontier(ctrl.pose[0], ctrl.pose[1])
        fx, fy = (macro_res[0], macro_res[1]) if macro_res else (0,0)
        acc = telem['accepted_candidates']
        rej = telem['rejected_candidates']
        min_sd = telem['min_predicted_hull_clearance']
        rej_r = telem['rejection_reason']
        print(f"t={tick:3d}: pos=({nx:.3f},{ny:.3f}), th={ctrl.pose[2]:.2f}, min_d={min_sd:.3f}, acc={acc}, rej={rej}, reason={rej_r}", flush=True)
