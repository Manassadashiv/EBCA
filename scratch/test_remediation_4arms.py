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

# Test first 5 configs of layout_1_left_trap
l1_configs = [c for c in configs if c["layout_id"] == "layout_1_left_trap"]

arms = ["ARM-A_Intact", "ARM-B_Frozen", "ARM-C_Zeroed", "ARM-D_Shuffled"]
results = {arm: {"colls": 0, "clrs": []} for arm in arms}

for trial_idx, cfg in enumerate(l1_configs):
    sp_pos = cfg["pos"]
    sp_yaw = cfg["yaw"]
    spec = TASK_SPECS[cfg["layout_id"]]
    max_ticks = spec["max_ticks"]
    blackout_start, blackout_end = spec["blackout_range"]
    ep_seed = cfg["seed"] * 1000 + trial_idx
    rng_ep = np.random.RandomState(ep_seed)
    P_ep_hd = rng_ep.permutation(64)

    print(f"\n--- TRIAL {trial_idx} (Seed 2001, {cfg['layout_id']}) ---")

    for arm in arms:
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
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
        initial_x = float(initial_res["grid_unwrapped_x"])
        initial_y = float(initial_res["grid_unwrapped_y"])
        k_shift = int(round(sp_yaw / (2.0 * math.pi / 64.0)))

        v_est = 0.0
        last_action = np.zeros(6, dtype=np.float64)
        min_sonar_rec = 10.0
        collision = False
        coll_tick = -1

        for t in range(max_ticks):
            sensors = hal.read_sensors()
            sonars = sensors[:15].copy()
            min_sonar_rec = min(min_sonar_rec, float(np.min(sensors[:15])))

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
                hd_arena = math.atan2(math.sin(sp_yaw + hd_rel), math.cos(sp_yaw + hd_rel))
                dx_rel = float(res["grid_unwrapped_x"]) - initial_x
                dy_rel = float(res["grid_unwrapped_y"]) - initial_y
                dx_arena = dx_rel * math.cos(sp_yaw) - dy_rel * math.sin(sp_yaw)
                dy_arena = dx_rel * math.sin(sp_yaw) + dy_rel * math.cos(sp_yaw)
                r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
                cann_state = {
                    "hd_decoded_heading": hd_arena,
                    "grid_unwrapped_x": float(sp_pos[0] + dx_arena),
                    "grid_unwrapped_y": float(sp_pos[1] + dy_arena),
                    "hd_rates": r_hd_shifted,
                    "bump_amplitude": float(res["hd_bump_amplitude"]),
                }
            elif arm == "ARM-B_Frozen":
                r_hd_shifted = np.roll(cann.hd_ring.r, k_shift)
                cann_state = {
                    "hd_decoded_heading": sp_yaw,
                    "grid_unwrapped_x": float(sp_pos[0]),
                    "grid_unwrapped_y": float(sp_pos[1]),
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
            elif arm == "ARM-D_Shuffled":
                res = cann.update_brain(u_executed=last_action, s_current=sensors)
                dx_rel = float(res["grid_unwrapped_x"]) - initial_x
                dy_rel = float(res["grid_unwrapped_y"]) - initial_y
                dx_arena = dx_rel * math.cos(sp_yaw) - dy_rel * math.sin(sp_yaw)
                dy_arena = dx_rel * math.sin(sp_yaw) + dy_rel * math.cos(sp_yaw)
                r_shuf = cann.hd_ring.r[P_ep_hd].copy()
                r_shuf_shifted = np.roll(r_shuf, k_shift)
                cann_state = {
                    "hd_decoded_heading": float(rng_ep.uniform(-math.pi, math.pi)),
                    "grid_unwrapped_x": float(sp_pos[0] + dx_arena),
                    "grid_unwrapped_y": float(sp_pos[1] + dy_arena),
                    "hd_rates": r_shuf_shifted,
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
                coll_tick = t
                break

        if collision:
            results[arm]["colls"] += 1
        results[arm]["clrs"].append(min_sonar_rec)

        res_str = f"COLLISION at tick {coll_tick}" if collision else "SURVIVED"
        print(f"  [{arm:16s}]: {res_str:22s} | min_sonar={min_sonar_rec:.4f} m")

print("\n" + "=" * 50)
print("5-TRIAL SUMMARY (Layout 1):")
for arm in arms:
    coll_pct = results[arm]["colls"] / 5.0 * 100.0
    mean_clr = np.mean(results[arm]["clrs"])
    print(f"  {arm:16s}: Collisions={results[arm]['colls']}/5 ({coll_pct:.1f}%), Mean Clr={mean_clr:.4f} m")
