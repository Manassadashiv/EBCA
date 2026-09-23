"""
scratch/test_all_families_extended.py — Test All 5 Task Families with K=24 Controller
Tests whether ARM-I can navigate from spawn to exit if given an adequate budget (300 ticks = 9.0s).
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

# Test 1 representative trial per condition for all 5 families
tasks = [
    ("family_1", "A", "world/stage3_2_environments/family1_condA_grid.pt", [0.80, 0.0], 0.0),
    ("family_1", "B", "world/stage3_2_environments/family1_condB_grid.pt", [0.80, 0.0], 0.0),
    ("family_2", "A", "world/stage3_2_environments/family2_condA_grid.pt", [0.20, 0.0], 0.0),
    ("family_2", "B", "world/stage3_2_environments/family2_condB_grid.pt", [0.20, 0.0], 0.0),
    ("family_3", "A", "world/stage3_2_environments/family3_layout_grid.pt", [-1.50, 1.20], 0.0),
    ("family_3", "B", "world/stage3_2_environments/family3_layout_grid.pt", [ 1.50, -1.80], 0.0),
    ("family_4", "A", "world/stage3_2_environments/family4_condA_grid.pt", [0.0, 0.0], 0.0),
    ("family_4", "B", "world/stage3_2_environments/family4_condB_grid.pt", [0.0, 0.0], 0.0),
    ("family_5", "A", "world/stage3_2_environments/family5_layout_grid.pt", [0.0, 0.0], 0.0),
    ("family_5", "B", "world/stage3_2_environments/family5_layout_grid.pt", [0.0, 0.0], 0.0),
]

def check_goal(fam_key, cond, x, y):
    if fam_key == "family_1":
        return (y > 1.80) if cond == "A" else (y < -1.80)
    elif fam_key == "family_2":
        return (x > 1.40 and y < -0.80) if cond == "A" else (x > 1.40 and y > 0.80)
    elif fam_key == "family_3":
        return (y > 2.00) if cond == "A" else (x > 2.20)
    elif fam_key == "family_4":
        return (x > 1.40 and y > 1.60) if cond == "A" else (x > 2.50)
    elif fam_key == "family_5":
        return (y < -1.40) if cond == "A" else (y > 1.40)
    return False

print("=========================================================================")
print("EVALUATING ARM-I ON ALL 5 TASK FAMILIES (BUDGET: 300 TICKS = 9.0 SECONDS)")
print("=========================================================================")

for fam_key, cond, grid_p, sp, yaw0 in tasks:
    xml_A, xml_B = fixtures[fam_key]
    xml = xml_A if cond == "A" else xml_B
    
    hal = CarlStage1HAL(xml_path=str(xml))
    engine = CARLStage2_3R1DeliberationEngine(grid_path=grid_p, mode="deliberative")
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    
    hal.reset()
    hal.data.qpos[qa:qa+2] = sp
    hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
    for _ in range(10):
        hal.step(np.zeros(6))
        
    engine.initialize_pose(sp[0], sp[1], yaw0)
    
    v_est = 0.0
    last_u = np.zeros(6)
    success = False
    collision = False
    
    for t in range(300):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])
        
        u_fwd = float(0.5 * (last_u[0] + last_u[1]))
        v_target = u_fwd * (engine.k_fwd / 0.030)
        v_est = 0.70 * v_est + 0.30 * v_target
        engine.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        
        action, _ = engine.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        last_u = action
        hal.step(action)
        
        cur_x, cur_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        
        contacts = hal.get_carl_contact_info()
        if (contacts["carl_contacts"] - contacts["floor_contacts"]) > 0:
            collision = True
            break
            
        if check_goal(fam_key, cond, cur_x, cur_y):
            success = True
            break
            
    status = "SUCCESS" if success else ("COLLISION" if collision else "TIMEOUT")
    print(f"{fam_key.upper()} Cond {cond}: {status} at tick {t+1} | Final Pos=({cur_x:.2f}, {cur_y:.2f}) | Dist={math.hypot(cur_x - sp[0], cur_y - sp[1]):.2f}m")
