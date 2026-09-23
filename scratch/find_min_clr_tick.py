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

hal = CarlStage1HAL()
delib = CARLStage2_3R1DeliberationEngine(mode="deliberative")
cann = CarlStage2BIntegratedBrain(dt=0.030)
cann.w_rot[20] = 1.0
cann.w_fwd[15] = 1.0
cann.is_developmentally_trained = True

qa = int(hal.model.joint("spatial_identity").qposadr[0])
sp_pos = [-3.0, -0.2]
sp_yaw = -math.pi / 2.0

for arm in ["ARM-A_Intact", "ARM-C_Zeroed"]:
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

    v_est = 0.0
    last_action = np.zeros(6, dtype=np.float64)
    k_shift = int(round(sp_yaw / (2.0 * math.pi / 64.0)))

    clrs = []
    branches = []

    for t in range(80):
        sensors = hal.read_sensors()
        sonars = sensors[:15].copy()
        
        # Sonar blackout between ticks 15 and 40
        is_blackout = (15 <= t <= 40)
        if is_blackout:
            sonars[:] = 5.0

        min_sonar = float(np.min(sensors[:15]))
        clrs.append(min_sonar)

        gyro_yaw = float(sensors[20]) if len(sensors) > 20 else 0.0
        u_fwd = float(0.5 * (last_action[0] + last_action[1]))
        v_target = u_fwd * (delib.k_fwd / 0.030)
        v_est = 0.70 * v_est + 0.30 * v_target
        delib.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

        if arm == "ARM-A_Intact":
            res = cann.update_brain(u_executed=last_action, s_current=sensors)
            hd_rel = float(res["hd_decoded_heading"]) - initial_heading
            hd_arena = math.atan2(math.sin(sp_yaw + hd_rel), math.cos(sp_yaw + hd_rel))
            
            dx_rel = float(res["grid_unwrapped_x"])
            dy_rel = float(res["grid_unwrapped_y"])
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
        branches.append(tel["selected_branch"])
        last_action = action
        hal.step(action)

    print(f"[{arm}]: min clr={min(clrs):.4f} at tick {np.argmin(clrs)}")
    print(f"  ticks 10..30 clrs: {[round(c, 3) for c in clrs[10:30]]}")
    print(f"  ticks 35..55 clrs: {[round(c, 3) for c in clrs[35:55]]}")
    print(f"  ticks 60..80 clrs: {[round(c, 3) for c in clrs[60:80]]}")
