import sys, math, numpy as np, torch, mujoco
from pathlib import Path
repo_root = Path('d:/ebca')
sys.path.insert(0, str(repo_root))
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg_map = {c['config_id']: c for c in configs}

def diagnose(cid):
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
    print(f"\n--- DIAGNOSTIC FOR CONFIG {cid} (Env {cfg['env_id']}) ---", flush=True)
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
        wall_contacts = c_info['carl_contacts'] - c_info['floor_contacts']
        
        # Print periodic or key event telemetry
        if tick % 25 == 0 or wall_contacts > 0:
            print(f"t={tick:3d}: x={nx:.3f}, y={ny:.3f}, th={ctrl.pose[2]:.2f}, u=[{u[0]:.2f},{u[1]:.2f}], u_fwd={u_fwd:.2f}, v_est={v_est:.3f}, acc={telem['accepted_candidates']}/128, rej={telem['rejected_candidates']}/128, min_d={telem['min_predicted_hull_clearance']:.3f}", flush=True)
        if wall_contacts > 0:
            print(f"--> COLLISION at t={tick} with contacts={wall_contacts} at x={nx:.3f}, y={ny:.3f}!", flush=True)
            break
        if cfg['env_id'] == 1 and nx <= -0.55:
            print(f"--> ESCAPED at t={tick}!", flush=True)
            break
        elif cfg['env_id'] == 2 and ny <= -1.20:
            print(f"--> ESCAPED at t={tick}!", flush=True)
            break

for c in [1, 20, 23, 24]:
    diagnose(c)
