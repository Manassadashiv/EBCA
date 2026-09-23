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

SEEDS = [1001, 1002, 1003, 1004, 1005]
LAYOUTS = [
    "layout_1_left_trap",
    "layout_2_right_trap",
    "layout_3_t_junction",
    "layout_4_corridor_slit",
]

hal = CarlStage1HAL()
delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
cann = CarlStage2BIntegratedBrain(dt=0.030)
cann.w_rot[20] = 1.0
cann.w_fwd[15] = 1.0
cann.is_developmentally_trained = True

qa = int(hal.model.joint("spatial_identity").qposadr[0])

# Generate configs exactly as in test_stage3_1_cann_causal_battery.py
def generate_configs():
    cfgs = []
    for seed in SEEDS:
        rng = np.random.RandomState(seed)
        for layout_id in LAYOUTS:
            layout_cfgs = []
            attempts = 0
            while len(layout_cfgs) < 5 and attempts < 200:
                attempts += 1
                if layout_id == "layout_1_left_trap":
                    x = float(rng.uniform(-3.05, -2.95))
                    y = float(rng.uniform(-0.25, -0.15))
                    yaw = float(-math.pi / 2.0 + rng.uniform(-0.04, 0.04))
                elif layout_id == "layout_2_right_trap":
                    x = float(rng.uniform(-3.45, -3.35))
                    y = float(rng.uniform(-0.68, -0.62))
                    yaw = float(0.0 + rng.uniform(-0.03, 0.03))
                elif layout_id == "layout_3_t_junction":
                    x = float(rng.uniform(-0.25, -0.15))
                    y = float(rng.uniform(-2.55, -2.45))
                    yaw = float(math.pi + rng.uniform(-0.04, 0.04))
                elif layout_id == "layout_4_corridor_slit":
                    x = float(rng.uniform(-2.55, -2.45))
                    y = float(rng.uniform(2.20, 2.30))
                    yaw = float(0.0 + rng.uniform(-0.03, 0.03))
                
                hal.reset()
                hal.data.qpos[qa:qa + 2] = [x, y]
                hal.data.qpos[qa + 3:qa + 7] = [math.cos(yaw / 2.0), 0.0, 0.0, math.sin(yaw / 2.0)]
                hal.data.qvel[:] = 0.0
                mujoco.mj_forward(hal.model, hal.data)

                con = hal.get_carl_contact_info()
                if (con["carl_contacts"] - con["floor_contacts"]) > 0:
                    continue
                layout_cfgs.append({"layout_id": layout_id, "pos": [x, y], "yaw": yaw, "seed": seed})
            cfgs.extend(layout_cfgs)
    return cfgs

configs = generate_configs()
print(f"Total configs: {len(configs)}")

# Test on 20 configs (1 seed = 5 trials x 4 layouts) for quick diagnosis
sub_configs = configs[:20]

for mode_name, use_coordinate_fix, use_coherence in [
    ("Original_Bugged (c_x=unwrapped_x, coherence=0.25)", False, True),
    ("Coord_Fixed_Only (c_x=arena, coherence=0.25)", True, True),
    ("Coord_Fixed_NoCoherence (c_x=arena, coherence=0.0)", True, False),
    ("Zeroed_CANN (c_x=0, coherence=0.0)", "zeroed", False),
]:
    colls = 0
    clrs = []
    
    for cfg in sub_configs:
        sp_pos = cfg["pos"]
        sp_yaw = cfg["yaw"]
        
        hal.reset()
        hal.data.qpos[qa:qa + 2] = sp_pos
        hal.data.qpos[qa + 3:qa + 7] = [math.cos(sp_yaw / 2.0), 0.0, 0.0, math.sin(sp_yaw / 2.0)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)

        delib.initialize_pose(sp_pos[0], sp_pos[1], sp_yaw)
        cann.reset_at_birthplace()

        spawn_sensors = hal.read_sensors()
        initial_res = cann.update_brain(u_executed=np.zeros(6), s_current=spawn_sensors)
        initial_heading = float(initial_res["hd_decoded_heading"])
        k_shift = int(round(sp_yaw / (2.0 * math.pi / 64.0)))

        v_est = 0.0
        last_action = np.zeros(6, dtype=np.float64)
        min_c = 10.0
        collision = False

        for t in range(60):
            sensors = hal.read_sensors()
            sonars = sensors[:15]
            min_c = min(min_c, float(np.min(sonars)))

            gyro_yaw = float(sensors[20]) if len(sensors) > 20 else 0.0
            u_fwd = float(0.5 * (last_action[0] + last_action[1]))
            v_target = u_fwd * (delib.k_fwd / 0.030)
            v_est = 0.70 * v_est + 0.30 * v_target
            delib.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

            if mode_name == "Zeroed_CANN (c_x=0, coherence=0.0)":
                cann_state = {
                    "hd_decoded_heading": 0.0,
                    "grid_unwrapped_x": 0.0,
                    "grid_unwrapped_y": 0.0,
                    "hd_rates": np.zeros(64, dtype=np.float64),
                    "bump_amplitude": 0.0,
                }
            elif not use_coordinate_fix:
                # Original bugged mode
                res = cann.update_brain(u_executed=last_action, s_current=sensors)
                cann_state = {
                    "hd_decoded_heading": float(res["hd_decoded_heading"]),
                    "grid_unwrapped_x": float(res["grid_unwrapped_x"]),
                    "grid_unwrapped_y": float(res["grid_unwrapped_y"]),
                    "hd_rates": cann.hd_ring.r.copy(),
                    "bump_amplitude": float(res["hd_bump_amplitude"]),
                }
            else:
                # Coordinate fixed mode
                res = cann.update_brain(u_executed=last_action, s_current=sensors)
                hd_rel = float(res["hd_decoded_heading"]) - initial_heading
                hd_arena = math.atan2(math.sin(sp_yaw + hd_rel), math.cos(sp_yaw + hd_rel))
                dx_rel = float(res["grid_unwrapped_x"])
                dy_rel = float(res["grid_unwrapped_y"])
                dx_arena = dx_rel * math.cos(sp_yaw) - dy_rel * math.sin(sp_yaw)
                dy_arena = dx_rel * math.sin(sp_yaw) + dy_rel * math.cos(sp_yaw)
                r_hd_shifted = np.roll(cann.hd_ring.r, k_shift) if use_coherence else np.zeros(64)
                cann_state = {
                    "hd_decoded_heading": hd_arena,
                    "grid_unwrapped_x": float(sp_pos[0] + dx_arena),
                    "grid_unwrapped_y": float(sp_pos[1] + dy_arena),
                    "hd_rates": r_hd_shifted,
                    "bump_amplitude": float(res["hd_bump_amplitude"]),
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
            if (con["carl_contacts"] - con["floor_contacts"]) > 0:
                collision = True
                break

        if collision:
            colls += 1
        clrs.append(min_c)

    print(f"[{mode_name}]: Collisions = {colls}/20 ({colls/20*100:.1f}%), Mean Clr = {np.mean(clrs):.4f} m")
