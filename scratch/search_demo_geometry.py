import os, sys, math, mujoco
import numpy as np
import pandas as pd

REPO_ROOT = r"D:\ebca"
sys.path.insert(0, REPO_ROOT)

from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

hal = MuJoCoHardwareAbstractionLayer(os.path.join(REPO_ROOT, "world", "vessel_kinetic.xml"))
model, data = hal.model, hal.data

def eval_config(name, setup_fn, fx=1.8, fy=0.0, max_ticks=400):
    geom_names = {model.geom(i).name: i for i in range(model.ngeom)}
    print(f"\n==========================================")
    print(f"Testing Config: {name} (Food: [{fx}, {fy}])")
    print(f"==========================================")
    all_ok = True
    
    for tname in ['TRIAL_A', 'TRIAL_B']:
        for s in [42, 101, 2024]:
            mujoco.mj_resetData(model, data)
            for g_name, g_id in geom_names.items():
                if g_name.startswith('lwall_'):
                    model.geom_pos[g_id] = [10.0, 10.0, 0.25]
            if 'food' in geom_names:
                model.geom_pos[geom_names['food']] = [fx, fy, 0.12]
            
            setup_fn(model, data, geom_names, tname)
            for _ in range(50):
                mujoco.mj_step(model, data)
            
            agent = CarlAutonomousOrganismAgent(dt=0.0333)
            np.random.seed(s)
            
            absorbed = False
            abs_t = -1
            min_dfood = 99.0
            coll = 0
            min_clr = 5.0
            traj = []
            
            for tick in range(max_ticks):
                res = agent.step_cognitive_cycle(hal, food_coords=(fx, fy))
                for _ in range(3):
                    hal.step()
                tel, sens = res['telemetry'], res['sensory']
                dfood = math.sqrt((fx - tel.pos_x)**2 + (fy - tel.pos_y)**2)
                min_dfood = min(min_dfood, dfood)
                if tel.food_absorbed or dfood < 0.30:
                    absorbed = True
                    if abs_t < 0:
                        abs_t = tick
                if tel.collision_occurred:
                    coll += 1
                min_clr = min(min_clr, sens.min_obstacle_dist)
                traj.append((tel.pos_x, tel.pos_y))
                
            traj = np.array(traj)
            max_y, min_y = np.max(traj[:, 1]), np.min(traj[:, 1])
            max_disp_y = max_y if abs(max_y) > abs(min_y) else min_y
            route = 'LEFT' if max_disp_y > 0 else 'RIGHT'
            
            expected_route = 'LEFT' if tname == 'TRIAL_A' else 'RIGHT'
            run_ok = (absorbed and coll == 0 and route == expected_route)
            if not run_ok:
                all_ok = False
                
            status_str = "PASS" if run_ok else "FAIL"
            print(f"  [{tname}] Seed {s:<5} | {status_str:<4} | Abs: {str(absorbed):<5} (t={abs_t:3d}) | Dist: {min_dfood:4.2f}m | Route: {route:<5} (DispY: {max_disp_y:+5.2f}m) | Clr: {min_clr:.2f}m | Coll: {coll}")
            
    print(f"-> CONFIG {name} RESULT: {'SUCCESS (100% PASS)' if all_ok else 'FAILED'}")
    return all_ok

# Let's define a variety of obstacle geometries
# In vessel_kinetic.xml:
# lwall_v_* has size 0.05 0.9 0.25 (vertical box along Y)
# lwall_h_* has size 0.9 0.05 0.25 (horizontal box along X)

# Setup 1: Thin horizontal wall blocking right in A, left in B
def setup_1(model, data, gn, tname):
    if tname == 'TRIAL_A':
        # lwall_h_0_1 at [0.9, -0.4, 0.25] (covers x in [0.0, 1.8], y in [-0.45, -0.35])
        if 'lwall_h_0_1' in gn: model.geom_pos[gn['lwall_h_0_1']] = [0.9, -0.4, 0.25]
        # and a diagonal/corner block at [0.9, -0.8]
        if 'lwall_v_0_2' in gn: model.geom_pos[gn['lwall_v_0_2']] = [0.9, -1.3, 0.25]
    else:
        if 'lwall_h_0_1' in gn: model.geom_pos[gn['lwall_h_0_1']] = [0.9, 0.4, 0.25]
        if 'lwall_v_0_2' in gn: model.geom_pos[gn['lwall_v_0_2']] = [0.9, 1.3, 0.25]

# Setup 2: Oblique single obstacle placed at x = 0.8, y = -0.35 in A, +0.35 in B
def setup_2(model, data, gn, tname):
    if tname == 'TRIAL_A':
        if 'lwall_v_0_2' in gn: model.geom_pos[gn['lwall_v_0_2']] = [0.8, -0.35, 0.25]
    else:
        if 'lwall_v_0_2' in gn: model.geom_pos[gn['lwall_v_0_2']] = [0.8, 0.35, 0.25]

# Setup 3: Small hazard box at (0.8, -0.2) in A, (0.8, +0.2) in B
def setup_3(model, data, gn, tname):
    if tname == 'TRIAL_A':
        # horizontal wall at [0.8, -0.3]
        if 'lwall_h_0_1' in gn: model.geom_pos[gn['lwall_h_0_1']] = [0.8, -0.3, 0.25]
    else:
        if 'lwall_h_0_1' in gn: model.geom_pos[gn['lwall_h_0_1']] = [0.8, 0.3, 0.25]

# Setup 4: Obstacle at (1.0, -0.45) in A, (1.0, +0.45) in B, with food at (1.8, 0.0)
def setup_4(model, data, gn, tname):
    if tname == 'TRIAL_A':
        if 'lwall_v_0_2' in gn: model.geom_pos[gn['lwall_v_0_2']] = [1.0, -0.45, 0.25]
    else:
        if 'lwall_v_0_2' in gn: model.geom_pos[gn['lwall_v_0_2']] = [1.0, 0.45, 0.25]

# Run tests
eval_config("Config 1 (H-Wall + V-Wall)", setup_1, fx=1.8, fy=0.0)
eval_config("Config 2 (V-Wall at 0.8, +/-0.35)", setup_2, fx=1.8, fy=0.0)
eval_config("Config 3 (H-Wall at 0.8, +/-0.3)", setup_3, fx=1.8, fy=0.0)
eval_config("Config 4 (V-Wall at 1.0, +/-0.45)", setup_4, fx=1.8, fy=0.0)
