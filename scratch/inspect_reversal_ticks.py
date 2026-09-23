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

for tick in range(80):
    sens = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
    u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
    cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
    hal.step(cmd)
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
    u_fwd = 0.5*(u[0]+u[1])
    v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
    print(f"t={tick:2d}: u_fwd={u_fwd:.2f}, rev_ticks={ctrl._reverse_ticks}, rev_done={ctrl._reverse_done}, rev_latch={ctrl._reverse_latched}, pos=({nx:.3f},{ny:.3f})", flush=True)
