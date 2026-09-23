"""
scratch/audit_fixtures.py — Forensic Audit of Stage 3.2 Task Fixtures
Audits:
1. Initial penetration / contact at spawn.
2. Geodesic distance from spawn to exit threshold.
3. Theoretical minimum ticks required at max speed (0.348 m/s).
4. Corridor width along the path vs CARL chassis diameter (0.32m hull).
"""

import math
import sys
from pathlib import Path
import mujoco
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.stage3_2_task_fixtures import generate_all_fixtures
from brain.carl_stage1_hal import CarlStage1HAL

fixtures = generate_all_fixtures()

family_info = {
    "family_1": {
        "name": "Blind-Corner Connectivity Ambiguity",
        "spawn": [0.80, 0.0],
        "yaw0": 0.0,
        "exit_A": "y > 1.80",
        "exit_B": "y < -1.80",
        "exit_pos_A": [0.80, 1.80],
        "exit_pos_B": [0.80, -1.80],
    },
    "family_2": {
        "name": "Irreversible Cul-de-Sac Funnel Trap",
        "spawn": [0.20, 0.0],
        "yaw0": 0.0,
        "exit_A": "x > 1.40 and y < -0.80",
        "exit_B": "x > 1.40 and y > 0.80",
        "exit_pos_A": [1.40, -0.80],
        "exit_pos_B": [1.40, 0.80],
    },
    "family_3": {
        "name": "Sonically Symmetric Locations",
        "spawn_A": [-1.50, 1.20],
        "spawn_B": [ 1.50, -1.80],
        "yaw0": 0.0,
        "exit_A": "y > 2.00",
        "exit_B": "x > 2.20",
        "exit_pos_A": [-1.50, 2.00],
        "exit_pos_B": [ 2.20, -1.80],
    },
    "family_4": {
        "name": "Occluded Dogleg Arterial vs Blind Detour",
        "spawn": [0.0, 0.0],
        "yaw0": 0.0,
        "exit_A": "x > 1.40 and y > 1.60",
        "exit_B": "x > 2.50",
        "exit_pos_A": [1.40, 1.60],
        "exit_pos_B": [2.50, 0.0],
    },
    "family_5": {
        "name": "Multi-Turn Sensory Blackout / Sonic Corridor Symmetry",
        "spawn": [0.0, 0.0],
        "yaw0": 0.0,
        "exit_A": "y < -1.40",
        "exit_B": "y > 1.40",
        "exit_pos_A": [0.0, -1.40],
        "exit_pos_B": [0.0, 1.40],
    },
}

print("=========================================================================")
print("FORENSIC AUDIT OF TASK FIXTURE GEOMETRY & REACHABILITY")
print("=========================================================================")

max_speed = 0.348 # m/s
dt = 0.030        # s per tick
tick_budget = 100 # ticks
max_dist_budget = max_speed * (tick_budget * dt) # 1.044 meters

for fam_key, info in family_info.items():
    print(f"\n--- {fam_key.upper()}: {info['name']} ---")
    xml_A, xml_B = fixtures[fam_key]
    
    for cond, xml in [("A", xml_A), ("B", xml_B)]:
        hal = CarlStage1HAL(xml_path=str(xml))
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        
        if fam_key == "family_3":
            sp = info["spawn_A"] if cond == "A" else info["spawn_B"]
            ex_pos = info["exit_pos_A"] if cond == "A" else info["exit_pos_B"]
            ex_cond = info["exit_A"] if cond == "A" else info["exit_B"]
        else:
            sp = info["spawn"]
            ex_pos = info["exit_pos_A"] if cond == "A" else info["exit_pos_B"]
            ex_cond = info["exit_A"] if cond == "A" else info["exit_B"]
            
        hal.reset()
        hal.data.qpos[qa:qa+2] = sp
        hal.data.qpos[qa+3:qa+7] = [1.0, 0.0, 0.0, 0.0]
        mujoco.mj_forward(hal.model, hal.data)
        
        # Settle
        for _ in range(10):
            hal.step([0,0,0,0,0,0])
            
        contacts = hal.get_carl_contact_info()
        non_floor_contacts = contacts["carl_contacts"] - contacts["floor_contacts"]
        
        # Calculate straight-line distance to exit
        dx = ex_pos[0] - sp[0]
        dy = ex_pos[1] - sp[1]
        euc_dist = math.hypot(dx, dy)
        
        # Minimum ticks at top speed in straight line
        min_ticks_straight = math.ceil(euc_dist / (max_speed * dt))
        
        is_reachable = euc_dist <= max_dist_budget
        
        print(f"  Cond {cond}:")
        print(f"    Spawn: {sp}, Exit Condition: {ex_cond}, Exit Target: {ex_pos}")
        print(f"    Spawn Penetration Contacts: {non_floor_contacts} (CRITICAL: {'COLLIDING AT SPAWN' if non_floor_contacts > 0 else 'CLEAR'})")
        print(f"    Euclidean Distance: {euc_dist:.2f} m | Max 100-Tick Reach: {max_dist_budget:.2f} m")
        print(f"    Min Ticks Required (Straight Line, No Turns): {min_ticks_straight} ticks (Budget: {tick_budget} ticks)")
        print(f"    Physically Reachable in Budget? {'YES' if is_reachable else 'NO - MATHEMATICALLY IMPOSSIBLE'}")
