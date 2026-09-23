import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import mujoco
from scipy import stats
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

LAYOUTS = [
    "layout_1_left_trap",
    "layout_2_right_trap",
    "layout_3_t_junction",
    "layout_4_corridor_slit"
]

def audit_gate3():
    hal = CarlStage1HAL()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    discrete = CARLStage2_3R1DeliberationEngine(mode="deliberative", horizon=10)

    rng = np.random.RandomState(42)
    spawns = []
    for layout in LAYOUTS:
        for i in range(5):
            if layout == "layout_1_left_trap":
                x = float(rng.uniform(-3.05, -2.95))
                y = float(rng.uniform(-0.25, -0.15))
                yaw = float(-math.pi / 2.0 + rng.uniform(-0.04, 0.04))
            elif layout == "layout_2_right_trap":
                x = float(rng.uniform(-3.45, -3.35))
                y = float(rng.uniform(-0.68, -0.62))
                yaw = float(0.0 + rng.uniform(-0.03, 0.03))
            elif layout == "layout_3_t_junction":
                x = float(rng.uniform(-0.25, -0.15))
                y = float(rng.uniform(-2.55, -2.45))
                yaw = float(math.pi + rng.uniform(-0.04, 0.04))
            else:
                x = float(rng.uniform(-2.55, -2.45))
                y = float(rng.uniform(2.20, 2.30))
                yaw = float(0.0 + rng.uniform(-0.04, 0.04))
            spawns.append((layout, [x, y], yaw))

    def run_trial(controller, spawn_pos, spawn_yaw):
        hal.reset()
        hal.data.qpos[qa:qa + 2] = spawn_pos
        hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)

        controller.initialize_pose(spawn_pos[0], spawn_pos[1], spawn_yaw)
        had_collision = False
        min_clearance = 5.0
        v_est = 0.0

        for tick in range(60):
            sensors = hal.read_sensors()
            sonars = sensors[:15]
            gyro_yaw = float(sensors[20])
            controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.03)

            min_son = float(np.min(sonars))
            if min_son < min_clearance:
                min_clearance = min_son

            act, _ = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = act[0]
            cmd_6d[1] = act[1]

            s_next, diag = hal.step(cmd_6d)
            contact_info = hal.get_carl_contact_info()
            body_contacts = contact_info["carl_contacts"] - contact_info["floor_contacts"]
            if body_contacts > 0:
                had_collision = True

            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        return had_collision, min_clearance

    print("--- Auditing Gate 3 Spawns ---")
    d_colls, m_colls = [], []
    for idx, (layout, pos, yaw) in enumerate(spawns):
        d_c, d_clr = run_trial(discrete, pos, yaw)
        m_c, m_clr = run_trial(mppi, pos, yaw)
        d_colls.append(d_c)
        m_colls.append(m_c)
        print(f"Trial {idx:02d} [{layout}]: Discrete={'COLLISION' if d_c else 'OK'} (clr={d_clr:.3f}m) | MPPI={'COLLISION' if m_c else 'OK'} (clr={m_clr:.3f}m)")

    print(f"\nTotal Discrete Collisions: {sum(d_colls)}/20 ({sum(d_colls)/20*100:.1f}%)")
    print(f"Total MPPI Collisions:     {sum(m_colls)}/20 ({sum(m_colls)/20*100:.1f}%)")

def audit_gate4():
    print("\n--- Auditing Gate 4 CANN Coupling with p-value ---")
    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    rng = np.random.RandomState(42)

    # 30 distinct sensory contexts
    diffs_left = []
    diffs_right = []
    diffs_lr = []

    r_hd_north = np.zeros(64, dtype=np.float32)
    r_hd_north[32] = 1.0; r_hd_north[31] = 0.8; r_hd_north[33] = 0.8
    r_hd_left = np.roll(r_hd_north, 16)
    r_hd_right = np.roll(r_hd_north, -16)

    cann_north = {"hd_decoded_heading": 0.0, "grid_unwrapped_x": 0.0, "grid_unwrapped_y": 0.0, "hd_rates": r_hd_north}
    cann_left = {"hd_decoded_heading": math.pi / 2.0, "grid_unwrapped_x": 0.0, "grid_unwrapped_y": 0.0, "hd_rates": r_hd_left}
    cann_right = {"hd_decoded_heading": -math.pi / 2.0, "grid_unwrapped_x": 0.0, "grid_unwrapped_y": 0.0, "hd_rates": r_hd_right}

    for i in range(30):
        sensors = rng.uniform(0.5, 2.5, 15).astype(np.float32)
        v = float(rng.uniform(0.0, 0.2))
        w = float(rng.uniform(-0.2, 0.2))
        mppi.initialize_pose(0.0, 0.0, 0.0)

        u_north, _ = mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_north)
        u_left, _ = mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_left)
        u_right, _ = mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_right)

        diffs_left.append(np.linalg.norm(u_left - u_north))
        diffs_right.append(np.linalg.norm(u_right - u_north))
        diffs_lr.append(np.linalg.norm(u_left - u_right))

    mean_lr = np.mean(diffs_lr)
    # One-sample t-test testing if mean divergence > 0.15
    # H0: mean <= 0.15, H1: mean > 0.15
    t_stat, p_val_two_sided = stats.ttest_1samp(diffs_lr, 0.15)
    p_val = p_val_two_sided / 2.0 if t_stat > 0 else 1.0 - p_val_two_sided / 2.0

    print(f"N=30 sensory contexts:")
    print(f"Mean ||u_left - u_right||: {mean_lr:.4f} m/s")
    print(f"t-statistic: {t_stat:.4f}")
    print(f"p-value (one-tailed > 0.15): {p_val:.4e}")

if __name__ == "__main__":
    audit_gate3()
    audit_gate4()
