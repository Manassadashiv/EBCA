import sys, math
from pathlib import Path
import numpy as np, torch, mujoco

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from tests.test_stage3_4R3_certification import build_50_matched_configurations, CarlStage1HAL, ENV1_XML, ENV2_XML
from brain.carl_active_inference import CARLActiveInferenceEngine

configs = build_50_matched_configurations()
hal1 = CarlStage1HAL(xml_path=str(ENV1_XML))
hal2 = CarlStage1HAL(xml_path=str(ENV2_XML))

for slew_rate in [0.20, 0.25, 0.30]:
    escapes = 0; collisions = 0; max_jump = 0.0
    for cfg in configs[:10]:
        hal = hal1 if cfg['env_id'] == 1 else hal2
        hal.reset()
        qa = int(hal.model.joint('spatial_identity').qposadr[0])
        sx, sy = cfg['spawn_pos']; syaw = cfg['spawn_yaw']
        hal.data.qpos[qa:qa+2] = [sx, sy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(syaw/2), 0, 0, math.sin(syaw/2)]
        mujoco.mj_forward(hal.model, hal.data)
        
        ctrl = CARLActiveInferenceEngine(grid_path=cfg['grid_path'], w_info=1.0, frontier_mode='macro', norm_mode='dimensionless')
        ctrl.max_slew_rate = slew_rate
        ctrl.initialize_pose(sx, sy, syaw)
        
        # Test ramped candidate projection
        v_est = 0.0
        prev_act = np.zeros(2)
        local_max_jump = 0.0
        
        for tick in range(220):
            sensors = hal.read_sensors()
            ctrl.update_odometry(v_wheel=v_est, w_gyro=float(sensors[20]), dt=0.030)
            u_star, telem = ctrl.select_action(sensors[:15], curr_v=v_est, curr_w=float(sensors[20]))
            
            # Record actual step jump
            jump = np.max(np.abs(u_star - prev_act))
            if jump > local_max_jump:
                local_max_jump = jump
            prev_act = u_star.copy()
            
            cmd_6d = telem.get('action_6d', np.zeros(6))
            hal.step(cmd_6d)
            q = hal.data.qpos[qa:qa+7]
            c = hal.get_carl_contact_info()
            if c['carl_contacts'] - c['floor_contacts'] > 0:
                collisions += 1; break
            if cfg['env_id'] == 1 and q[0] <= -0.55:
                escapes += 1; break
            if cfg['env_id'] == 2 and q[1] <= -1.20:
                escapes += 1; break
            v_est = 0.65*v_est + 0.35*(0.5*(cmd_6d[0]+cmd_6d[1])*0.35)
            
        if local_max_jump > max_jump:
            max_jump = local_max_jump
            
    print(f"Slew={slew_rate:.2f} -> Escapes={escapes}/10, Collisions={collisions}/10, MaxJump={max_jump:.4f}")
