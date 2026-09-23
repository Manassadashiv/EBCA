import sys, math, numpy as np, torch, mujoco
from pathlib import Path
repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg_map = {c['config_id']: c for c in configs}

for cid in [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]:
    cfg = cfg_map[cid]
    hal = CarlStage1HAL(xml_path=cfg['xml_path'])
    hal.reset()
    qa = int(hal.model.joint('spatial_identity').qposadr[0])
    sx, sy = cfg['spawn_pos']
    syaw = cfg['spawn_yaw']
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
    mujoco.mj_forward(hal.model, hal.data)
    ctrl = CARLActiveInferenceEngine(grid_path=cfg['grid_path'], w_info=1.0)
    ctrl.initialize_pose(sx, sy, syaw)
    v_est = 0.0
    coll, esc = False, False
    for tick in range(220):
        sens = hal.read_sensors()
        ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sens[20]), dt=ctrl.dt)
        u, telem = ctrl.select_action(sens, curr_v=v_est, curr_w=float(sens[20]))
        cmd = np.zeros(6); cmd[0], cmd[1] = u[0], u[1]
        hal.step(cmd)
        qa = int(hal.model.joint('spatial_identity').qposadr[0])
        nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = 0.5*(u[0]+u[1])
        v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
        c_info = hal.get_carl_contact_info()
        if c_info['carl_contacts'] - c_info['floor_contacts'] > 0:
            coll = True; break
        if cfg['env_id'] == 1 and nx <= -0.55: esc = True; break
        elif cfg['env_id'] == 2 and ny <= -1.20: esc = True; break
    out = 'ESCAPE' if esc else ('COLLISION' if coll else 'TIMEOUT')
    print(f"Config {cid:2d} (Env {cfg['env_id']}): {out:<10} at tick {tick+1:3d}, x={nx:.3f}, y={ny:.3f}", flush=True)
