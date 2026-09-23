"""
scratch/test_f1_extended_budget.py — Test Family 1 under Realistic Budget (250 ticks = 7.5s)
"""

import sys
import math
from pathlib import Path
import numpy as np

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.stage3_2_task_fixtures import generate_all_fixtures
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine

fixtures = generate_all_fixtures()
xml_A, _ = fixtures["family_1"]
grid_p = "world/stage3_2_environments/family1_condA_grid.pt"

hal = CarlStage1HAL(xml_path=str(xml_A))
engine = CARLStage2_3R1DeliberationEngine(grid_path=grid_p, mode="deliberative")
qa = int(hal.model.joint("spatial_identity").qposadr[0])

hal.reset()
hal.data.qpos[qa:qa+2] = [0.80, 0.0]
hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
for _ in range(10):
    hal.step(np.zeros(6))

engine.initialize_pose(0.80, 0.0, 0.0)

v_est = 0.0
last_u = np.zeros(6)
success = False
collision = False

print("Running Family 1 Cond A with 250 ticks budget...")
for t in range(250):
    sensors = hal.read_sensors()
    sonars = sensors[:15]
    gyro_yaw = float(sensors[20])

    u_fwd = float(0.5 * (last_u[0] + last_u[1]))
    v_target = u_fwd * (engine.k_fwd / 0.030)
    v_est = 0.70 * v_est + 0.30 * v_target
    engine.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)

    action, telem = engine.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
    last_u = action
    hal.step(action)

    cur_x, cur_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])

    contacts = hal.get_carl_contact_info()
    if (contacts["carl_contacts"] - contacts["floor_contacts"]) > 0:
        collision = True
        print(f"Collision at tick {t+1} at pos ({cur_x:.2f}, {cur_y:.2f})!")
        break

    if cur_y > 1.80:
        success = True
        print(f"SUCCESS at tick {t+1}! Final pos: ({cur_x:.2f}, {cur_y:.2f})")
        break

    if (t + 1) % 25 == 0:
        print(f"Tick {t+1}: pos=({cur_x:.2f}, {cur_y:.2f}), selected={telem.get('selected_branch', 'N/A')}")

if not success and not collision:
    print(f"Timeout at tick 250! Final pos: ({cur_x:.2f}, {cur_y:.2f})")
