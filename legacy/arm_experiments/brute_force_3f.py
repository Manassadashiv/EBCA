"""Brute-force prove whether 3F contact is physically possible at all.
Manually set joints to place hand directly on the cube and max-clamp fingers."""
import sys, numpy as np, mujoco
sys.path.append(r"d:\ebca")

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

# Get joint/actuator IDs
jnt_names = ["shoulder_yaw_L", "shoulder_L", "elbow_L", "wrist_L", "grip_L", "grip_thumb_L"]
jnt_qaddrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in jnt_names]
act_names = ["act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L"]
act_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in act_names]

_fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
_fj_qadr = model.jnt_qposadr[_fj_id]
_fj_vadr = model.jnt_dofadr[_fj_id]
_cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

_site_f1 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_L")
_site_f2 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_bot_L")
_site_f3 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_thumb_L")

print("=" * 90)
print("  BRUTE-FORCE 3F CONTACT TEST")
print("  Testing all (shoulder_pitch x elbow x wrist) combos with max finger clamp")
print("=" * 90)

# Place cube directly in front, on floor
cube_x, cube_y, cube_z = 0.20, 0.0, 0.048
best_3f = 0
best_config = None

for s_pitch in np.arange(0.0, 1.8, 0.2):
    for elbow in np.arange(-2.4, 0.1, 0.3):
        for wrist in np.arange(-1.5, 1.6, 0.3):
            mujoco.mj_resetData(model, data)
            
            # Place cube
            data.qpos[_cube_j_id:_cube_j_id+3] = [cube_x, cube_y, cube_z]
            data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
            
            # Lock chassis
            home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
            home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()
            
            f1_total = f2_total = f3_total = f3f_total = 0
            
            for step in range(80):
                # Set joint targets
                ctrl = [0.0, s_pitch, elbow, wrist, 0.52, 0.52]
                for idx, aid in enumerate(act_ids):
                    data.ctrl[aid] = ctrl[idx]
                
                mujoco.mj_step(model, data)
                data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
                data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
                data.qvel[_fj_vadr:_fj_vadr+6] = 0.0
                
                tL = float(data.sensor("touch_L").data[0])
                tB = float(data.sensor("touch_bot_L").data[0])
                tT = float(data.sensor("touch_thumb_L").data[0])
                
                f1 = tL > 0.05; f2 = tB > 0.05; f3 = tT > 0.05
                if f1: f1_total += 1
                if f2: f2_total += 1
                if f3: f3_total += 1
                if f1 and f2 and f3: f3f_total += 1
            
            pct_3f = 100 * f3f_total / 80
            pct_f1 = 100 * f1_total / 80
            pct_f2 = 100 * f2_total / 80
            pct_f3 = 100 * f3_total / 80
            
            if pct_3f > best_3f:
                best_3f = pct_3f
                best_config = (s_pitch, elbow, wrist)
            
            if pct_3f > 0:
                print(f"  s_pitch={s_pitch:5.1f} elbow={elbow:5.1f} wrist={wrist:5.1f} | F1:{pct_f1:5.1f}% F2:{pct_f2:5.1f}% F3:{pct_f3:5.1f}% | 3F:{pct_3f:5.1f}% ***")
            elif pct_f2 > 10:
                print(f"  s_pitch={s_pitch:5.1f} elbow={elbow:5.1f} wrist={wrist:5.1f} | F1:{pct_f1:5.1f}% F2:{pct_f2:5.1f}% F3:{pct_f3:5.1f}% | 3F:{pct_3f:5.1f}% (F2 hit!)")

print("=" * 90)
if best_config:
    print(f"BEST 3F: s_pitch={best_config[0]:.1f} elbow={best_config[1]:.1f} wrist={best_config[2]:.1f} -> {best_3f:.1f}%")
    
    # Run best config one more time and print positions
    mujoco.mj_resetData(model, data)
    data.qpos[_cube_j_id:_cube_j_id+3] = [cube_x, cube_y, cube_z]
    data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
    home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
    home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()
    
    for step in range(80):
        ctrl = [0.0, best_config[0], best_config[1], best_config[2], 0.52, 0.52]
        for idx, aid in enumerate(act_ids):
            data.ctrl[aid] = ctrl[idx]
        mujoco.mj_step(model, data)
        data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
        data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
        data.qvel[_fj_vadr:_fj_vadr+6] = 0.0
    
    mujoco.mj_forward(model, data)
    print(f"\nAt best config (step 80):")
    print(f"  Cube:    {data.body('obj_cube_2').xpos}")
    print(f"  F1 site: {data.site_xpos[_site_f1]}")
    print(f"  F2 site: {data.site_xpos[_site_f2]}")
    print(f"  F3 site: {data.site_xpos[_site_f3]}")
    print(f"  touch_L={data.sensor('touch_L').data[0]:.3f} touch_bot_L={data.sensor('touch_bot_L').data[0]:.3f} touch_thumb_L={data.sensor('touch_thumb_L').data[0]:.3f}")
else:
    print("NO 3F CONTACT FOUND - hand geometry may not support floor-level 3F grasps")
    print("\nChecking: does F2 EVER register contact in ANY configuration?")
    # Quick check: any F2 at all?
    f2_found = False
    for s_pitch in np.arange(0.0, 1.8, 0.1):
        for elbow in np.arange(-2.4, 0.1, 0.1):
            for wrist in np.arange(-1.5, 1.6, 0.1):
                mujoco.mj_resetData(model, data)
                data.qpos[_cube_j_id:_cube_j_id+3] = [cube_x, cube_y, cube_z]
                data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
                home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
                home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()
                for step in range(60):
                    ctrl = [0.0, s_pitch, elbow, wrist, 0.52, 0.52]
                    for idx, aid in enumerate(act_ids):
                        data.ctrl[aid] = ctrl[idx]
                    mujoco.mj_step(model, data)
                    data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
                    data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
                    data.qvel[_fj_vadr:_fj_vadr+6] = 0.0
                    tB = float(data.sensor("touch_bot_L").data[0])
                    if tB > 0.05:
                        print(f"  F2 CONTACT! s_pitch={s_pitch:.1f} elbow={elbow:.1f} wrist={wrist:.1f} step={step} force={tB:.3f}N")
                        f2_found = True
                        break
                if f2_found:
                    break
            if f2_found:
                break
        if f2_found:
            break
    if not f2_found:
        print("  F2 NEVER registers contact with the cube in ANY joint configuration.")
        print("  The bottom anvil finger cannot physically reach the cube.")
print("=" * 90)
