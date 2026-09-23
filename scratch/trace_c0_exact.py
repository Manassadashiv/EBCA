import sys, math, numpy as np, torch, mujoco
from pathlib import Path
repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
cfg_map = {c["config_id"]: c for c in configs}

cfg = cfg_map[0]
xml_path = cfg["xml_path"]
grid_path = cfg["grid_path"]

hal = CarlStage1HAL(xml_path=str(xml_path))
hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
sx, sy, syaw = cfg["spawn_pos"][0], cfg["spawn_pos"][1], cfg["spawn_yaw"]
hal.data.qpos[qa:qa+2] = [sx, sy]
hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
mujoco.mj_forward(hal.model, hal.data)

ctrl = CARLActiveInferenceEngine(grid_path=str(grid_path), w_info=1.0)
ctrl.initialize_pose(sx, sy, syaw)

v_est = 0.0
for tick in range(200):
    sensors = hal.read_sensors()
    ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=ctrl.dt)
    u_star, telem = ctrl.select_action(sensors, curr_v=v_est, curr_w=float(sensors[20]))
    cmd_6d = np.zeros(6)
    cmd_6d[0], cmd_6d[1] = float(u_star[0]), float(u_star[1])
    hal.step(cmd_6d)
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    nx, ny = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
    q_rot = hal.data.qpos[qa+3:qa+7]
    yaw = math.atan2(2*(q_rot[0]*q_rot[3] + q_rot[1]*q_rot[2]), 1 - 2*(q_rot[2]**2 + q_rot[3]**2))
    u_fwd = float(0.5*(cmd_6d[0]+cmd_6d[1]))
    v_est = 0.70*v_est + 0.30*(u_fwd*0.30)
    
    c_info = hal.get_carl_contact_info()
    wall_col = (c_info["carl_contacts"] - c_info["floor_contacts"] > 0)
    if tick % 15 == 0 or tick >= 170 or wall_col:
        print(f"tk={tick:3d} x={nx:+.3f} y={ny:+.3f} yaw={yaw:+.2f} u=[{cmd_6d[0]:+.2f},{cmd_6d[1]:+.2f}] col={wall_col}", flush=True)
    if wall_col:
        for i in range(hal.data.ncon):
            con = hal.data.contact[i]
            g1 = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, con.geom1)
            g2 = mujoco.mj_id2name(hal.model, mujoco.mjtObj.mjOBJ_GEOM, con.geom2)
            if g1 != "floor" and g2 != "floor":
                print(f"   Contact: {g1} <-> {g2}", flush=True)
        break
