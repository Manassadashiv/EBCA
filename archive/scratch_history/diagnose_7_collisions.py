import sys
import math
from pathlib import Path
import numpy as np
import torch
import mujoco

repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

configs = build_50_matched_configurations()
collide_cfgs = [3, 6, 10, 15, 17, 41, 47]

for cid in collide_cfgs:
    cfg = configs[cid]
    hal = CarlStage1HAL(xml_path=cfg["xml_path"])
    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]

    np.random.seed(cfg["seed"])
    torch.manual_seed(cfg["seed"])
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    controller = CARLActiveInferenceEngine(
        grid_path=cfg["grid_path"],
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    controller.initialize_pose(sx, sy, syaw)

    v_est = 0.0
    for tick in range(220):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])

        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, _ = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)

        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(action[0])
        cmd_6d[1] = float(action[1])

        hal.step(cmd_6d)

        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            # find which geoms collided
            q_curr = hal.data.qpos[qa:qa+7]
            curr_pos = [float(q_curr[0]), float(q_curr[1])]
            curr_yaw = math.degrees(2.0 * math.atan2(float(q_curr[6]), float(q_curr[3])))
            # Inspect contacts
            contact_geoms = []
            for i in range(hal.data.ncon):
                con = hal.data.contact[i]
                g1 = hal.model.geom(con.geom1).name
                g2 = hal.model.geom(con.geom2).name
                if "floor" not in g1 and "floor" not in g2:
                    contact_geoms.append(f"{g1} <-> {g2} (dist={con.dist:.4f})")
            print(f"Cfg {cid:2d} (Env{cfg['env_id']}) collided at tick {tick:3d}: pos=({curr_pos[0]:.3f}, {curr_pos[1]:.3f}), yaw={curr_yaw:.1f}deg, u=[{cmd_6d[0]:.2f}, {cmd_6d[1]:.2f}], contacts: {contact_geoms[:3]}")
            break

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.65 * v_est + 0.35 * (u_fwd * 0.35)
