import sys
import math
from pathlib import Path
import numpy as np

repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
import mujoco

from tests.test_stage3_1_cann_causal_battery import TASK_SPECS, generate_spawn_configs

hal = CarlStage1HAL()
delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
cann = CarlStage2BIntegratedBrain(dt=0.030)
cann.w_rot[20] = 1.0
cann.w_fwd[15] = 1.0
cann.is_developmentally_trained = True

configs = generate_spawn_configs(2001)

# Find first episode in layout_1_left_trap that collided in ARM-A
cfg = configs[0]
print("Running trace on layout:", cfg["layout_id"], "pos:", cfg["pos"], "yaw:", cfg["yaw"])

spec = TASK_SPECS[cfg["layout_id"]]
max_ticks = spec["max_ticks"]
blackout_start, blackout_end = spec["blackout_range"]

for arm in ["ARM-A_Intact", "ARM-B_Frozen", "ARM-C_Zeroed"]:
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.reset()
    hal.data.qpos[qa:qa + 2] = cfg["pos"]
    hal.data.qpos[qa + 3:qa + 7] = [math.cos(cfg["yaw"] / 2.0), 0.0, 0.0, math.sin(cfg["yaw"] / 2.0)]
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)

    delib.initialize_pose(cfg["pos"][0], cfg["pos"][1], cfg["yaw"])
    cann.reset_at_birthplace()

    spawn_sensors = hal.read_sensors()
    initial_res = cann.update_brain(u_executed=np.zeros(6), s_current=spawn_sensors)
    initial_heading = float(initial_res["hd_decoded_heading"])
    k_shift = int(round(cfg["yaw"] / (2.0 * math.pi / 64.0)))

    v_est = 0.0
    last_action = np.zeros(6, dtype=np.float64)
    print(f"\n--- {arm} ---")
    for t in range(max_ticks):
        sensors = hal.read_sensors()
        sonars = sensors[:15].copy()
        is_blackout = (blackout_start <= t <= blackout_end)
        if is_blackout:
            sonars[:] = 5.0

        gyro_yaw = float(sensors[20]) if len(sensors) > 20 else 0.0
        u_fwd = float(0.5 * (last_action[0] + last_action[1]))
        v_target = u_fwd * (delib.k_fwd / 0.030)
        v_est = 0.70 * v_est + 0.30 * v_target
        delib.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

        if arm == "ARM-A_Intact":
            res = cann.update_brain(u_executed=last_action, s_current=sensors)
            hd_rel = float(res["hd_decoded_heading"]) - initial_heading
            hd_arena = math.atan2(math.sin(cfg["yaw"] + hd_rel), math.cos(cfg["yaw"] + hd_rel))
            dx_rel = float(res["grid_unwrapped_x"])
            dy_rel = float(res["grid_unwrapped_y"])
            dx_arena = dx_rel * math.cos(cfg["yaw"]) - dy_rel * math.sin(cfg["yaw"])
            dy_arena = dx_rel * math.sin(cfg["yaw"]) + dy_rel * math.cos(cfg["yaw"])
            r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
            cann_state = {
                "hd_decoded_heading": hd_arena,
                "grid_unwrapped_x": float(cfg["pos"][0] + dx_arena),
                "grid_unwrapped_y": float(cfg["pos"][1] + dy_arena),
                "hd_rates": r_hd_shifted,
                "bump_amplitude": float(res["hd_bump_amplitude"]),
            }
        elif arm == "ARM-B_Frozen":
            r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
            cann_state = {
                "hd_decoded_heading": cfg["yaw"],
                "grid_unwrapped_x": float(cfg["pos"][0]),
                "grid_unwrapped_y": float(cfg["pos"][1]),
                "hd_rates": r_hd_shifted,
                "bump_amplitude": 1.0,
            }
        elif arm == "ARM-C_Zeroed":
            cann_state = {
                "hd_decoded_heading": 0.0,
                "grid_unwrapped_x": 0.0,
                "grid_unwrapped_y": 0.0,
                "hd_rates": np.zeros(64, dtype=np.float64),
                "bump_amplitude": 0.0,
            }

        action, tel = delib.select_action(
            curr_sensors=sonars,
            curr_v=v_est,
            curr_w=gyro_yaw,
            forced_pose=None,
            cann_state=cann_state
        )
        last_action = action
        hal.step(action)

        con = hal.get_carl_contact_info()
        ext_contacts = con["carl_contacts"] - con["floor_contacts"]
        
        true_pos = hal.data.qpos[qa:qa + 2]
        true_qw = hal.data.qpos[qa + 3]
        true_qz = hal.data.qpos[qa + 6]
        true_yaw = 2.0 * math.atan2(true_qz, true_qw)

        if t in [0, 5, 10, 14, 15, 20, 25, 30, 39, 40, 45, 50] or ext_contacts > 0:
            print(f"t={t:02d} | true=({true_pos[0]:.2f}, {true_pos[1]:.2f}, yaw={math.degrees(true_yaw):.1f}) | delib_pose=({delib.pose[0]:.2f}, {delib.pose[1]:.2f}, yaw={math.degrees(delib.pose[2]):.1f}) | cann_pos=({cann_state['grid_unwrapped_x']:.2f}, {cann_state['grid_unwrapped_y']:.2f}, yaw={math.degrees(cann_state['hd_decoded_heading']):.1f}) | branch={tel['selected_branch']} | u=({action[0]:.2f}, {action[1]:.2f}) | ext_con={ext_contacts}")

        if ext_contacts > 0:
            print(f"*** COLLISION AT TICK {t} for {arm} ***")
            break
