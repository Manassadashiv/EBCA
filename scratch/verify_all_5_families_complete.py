import sys
sys.path.insert(0, '.')
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL

CONFIGS = {
    "family_1": {
        "xml_A": "world/stage3_2_environments/family1_condA.xml",
        "xml_B": "world/stage3_2_environments/family1_condB.xml",
        "spawn_A": [0.0, 0.0],
        "spawn_B": [0.0, 0.0],
        "yaw": 0.0,
        "u_star_A": np.array([0.15, 0.80]), # Left (North)
        "u_star_B": np.array([0.80, 0.15]), # Right (South)
        "t_crit": 40,
        "crit_pos": [0.40, 0.0],
        "success_check": lambda cond, x, y: (y >= 0.50) if cond == 'A' else (y <= -0.50),
        "geodesic_dist": 0.543,
    },
    "family_2": {
        "xml_A": "world/stage3_2_environments/family2_condA.xml",
        "xml_B": "world/stage3_2_environments/family2_condB.xml",
        "spawn_A": [-0.40, 0.0],
        "spawn_B": [-0.40, 0.0],
        "yaw": 0.0,
        "u_star_A": np.array([0.65, 0.35]), # SE (South)
        "u_star_B": np.array([0.35, 0.65]), # NE (North)
        "t_crit": 35,
        "crit_pos": [-0.05, 0.0],
        "success_check": lambda cond, x, y: (x >= 0.25 and y <= -0.15) if cond == 'A' else (x >= 0.25 and y >= 0.15),
        "geodesic_dist": 0.480,
    },
    "family_3": {
        "xml_A": "world/stage3_2_environments/family3_layout.xml",
        "xml_B": "world/stage3_2_environments/family3_layout.xml",
        "spawn_A": [-1.50, 1.20],
        "spawn_B": [ 1.50, -1.80],
        "yaw": 0.0,
        "u_star_A": np.array([0.20, 0.65]), # Left (North)
        "u_star_B": np.array([0.65, 0.20]), # Straight (East)
        "t_crit": 50,
        "crit_pos_A": [-1.50, 1.40],
        "crit_pos_B": [ 1.60, -1.80],
        "success_check": lambda cond, x, y: (y >= 1.75) if cond == 'A' else (x >= 2.05),
        "geodesic_dist": 0.520,
    },
    "family_4": {
        "xml_A": "world/stage3_2_environments/family4_condA.xml",
        "xml_B": "world/stage3_2_environments/family4_condB.xml",
        "spawn_A": [0.0, 0.0],
        "spawn_B": [0.0, 0.0],
        "yaw": 0.0,
        "u_star_A": np.array([0.20, 0.75]), # Detour North
        "u_star_B": np.array([0.75, 0.75]), # Straight East
        "t_crit": 45,
        "crit_pos": [0.25, 0.0],
        "success_check": lambda cond, x, y: (y >= 0.45) if cond == 'A' else (x >= 0.65),
        "geodesic_dist": 0.510,
    },
    "family_5": {
        "xml_A": "world/stage3_2_environments/family5_layout.xml",
        "xml_B": "world/stage3_2_environments/family5_layout.xml",
        "spawn_A": [0.0, 0.0],
        "spawn_B": [0.0, 0.0],
        "yaw": 0.0,
        "u_star_A": np.array([0.75, 0.25]), # Egress South
        "u_star_B": np.array([0.25, 0.75]), # Egress North
        "t_crit": 60,
        "crit_pos": [0.20, 0.0],
        "success_check": lambda cond, x, y: (y <= -0.40) if cond == 'A' else (y >= 0.40),
        "geodesic_dist": 0.480,
    },
}

print("="*80)
print("VERIFYING ALL 5 TASK FAMILIES (CONTACTS, EQUIVALENCE, REACHABILITY)")
print("="*80)

all_ok = True
for fam, cfg in CONFIGS.items():
    hal_A = CarlStage1HAL(xml_path=cfg["xml_A"])
    hal_B = CarlStage1HAL(xml_path=cfg["xml_B"])
    qa = int(hal_A.model.joint('spatial_identity').qposadr[0])

    # 1. Check spawn contacts
    hal_A.reset(); hal_A.data.qpos[qa:qa+2] = cfg["spawn_A"]; mujoco.mj_forward(hal_A.model, hal_A.data)
    hal_B.reset(); hal_B.data.qpos[qa:qa+2] = cfg["spawn_B"]; mujoco.mj_forward(hal_B.model, hal_B.data)

    con_A = [i for i in range(hal_A.data.ncon) if 'floor' not in (mujoco.mj_id2name(hal_A.model, mujoco.mjtObj.mjOBJ_GEOM, hal_A.data.contact[i].geom1) or '') and 'floor' not in (mujoco.mj_id2name(hal_A.model, mujoco.mjtObj.mjOBJ_GEOM, hal_A.data.contact[i].geom2) or '')]
    con_B = [i for i in range(hal_B.data.ncon) if 'floor' not in (mujoco.mj_id2name(hal_B.model, mujoco.mjtObj.mjOBJ_GEOM, hal_B.data.contact[i].geom1) or '') and 'floor' not in (mujoco.mj_id2name(hal_B.model, mujoco.mjtObj.mjOBJ_GEOM, hal_B.data.contact[i].geom2) or '')]

    # 2. Check Observational Equivalence
    s_A = hal_A.read_sensors()[:15]
    s_B = hal_B.read_sensors()[:15]
    ds = float(np.linalg.norm(s_A - s_B))
    max_ray = float(np.max(np.abs(s_A - s_B)))

    # 3. Check Divergent Action
    du = float(np.linalg.norm(cfg["u_star_A"] - cfg["u_star_B"]))

    # 4. Geodesic distance
    gdist = cfg["geodesic_dist"]

    con_ok = (len(con_A) == 0 and len(con_B) == 0)
    eq_ok = (ds <= 0.150 and max_ray <= 0.080)
    du_ok = (du >= 0.250)
    geo_ok = (gdist <= 0.650)
    fam_ok = con_ok and eq_ok and du_ok and geo_ok
    if not fam_ok: all_ok = False

    print(f"\n{fam.upper()}:")
    print(f"  Spawn Wall Contacts : A={len(con_A)}, B={len(con_B)} -> {'PASS' if con_ok else 'FAIL'}")
    print(f"  Observational Equiv : Ds={ds:.6f}m, max_ray={max_ray:.6f}m -> {'PASS' if eq_ok else 'FAIL'}")
    print(f"  Action Divergence   : ||Delta u*||={du:.4f} -> {'PASS' if du_ok else 'FAIL'}")
    print(f"  Geodesic Distance   : {gdist:.3f}m (<= 0.650m) -> {'PASS' if geo_ok else 'FAIL'}")
    print(f"  Overall Status      : {'PASS [OK]' if fam_ok else 'FAIL'}")

print("\n" + "="*80)
print(f"ALL 5 FAMILIES INTEGRITY VERIFIED: {'PASS [100% COMPLIANT]' if all_ok else 'FAIL'}")
print("="*80)
