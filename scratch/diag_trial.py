import sys
sys.path.insert(0, '.')
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_trap.xml')
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
hal.data.qpos[qa:qa+2] = [0.60, 0.0]
hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
mujoco.mj_forward(hal.model, hal.data)

engine = CARLActiveInferenceEngine(grid_path='world/stage3_4_environments/cul_de_sac_trap_grid.pt', w_info=1.0)
engine.initialize_pose(0.60, 0.0, 0.0)

v_est = 0.0
for tick in range(180):
    s = hal.read_sensors()
    sonars = s[:15]
    gyro_yaw = float(s[20])
    engine.update_odometry(v_est, gyro_yaw, dt=0.03)
    act, tel = engine.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
    cmd = np.zeros(6)
    cmd[0], cmd[1] = act[0], act[1]
    hal.step(cmd)

    ci = hal.get_carl_contact_info()
    non_floor = ci['carl_contacts'] - ci['floor_contacts']
    pos = hal.data.qpos[qa:qa+2]
    if non_floor > 0:
        print(f"Tick {tick}: non_floor={non_floor} at pos=({pos[0]:.3f}, {pos[1]:.3f})")
        for i in range(hal.data.ncon):
            c = hal.data.contact[i]
            in1 = c.geom1 in hal.carl_geom_ids
            in2 = c.geom2 in hal.carl_geom_ids
            if (in1 and not in2) or (in2 and not in1):
                other = c.geom2 if in1 else c.geom1
                if other != hal.floor_geom_id:
                    print(f"  WALL HIT: {hal.model.geom(c.geom1).name} <-> {hal.model.geom(c.geom2).name}, dist={c.dist:.4f}")
        break

    if tick % 10 == 0:
        print(f"Tick {tick}: pos=({pos[0]:.2f}, {pos[1]:.2f}), act=({act[0]:.2f}, {act[1]:.2f}), son_front={np.min(sonars[6:9]):.2f}m, prag={tel['efe_pragmatic_mean']:.1f}, epist={tel['efe_epistemic_mean']:.1f}")
    if pos[0] < -0.70:
        print(f"ESCAPED at tick {tick}! Final pos: {pos}")
        break
    u_fwd = float(0.5 * (cmd[0] + cmd[1]))
    v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

print(f"Trial ended at tick 120. Final pos: {pos}")
