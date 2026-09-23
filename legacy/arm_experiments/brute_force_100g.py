"""Brute-force with 100g cube: find the joint config that gives 3F contact."""
import sys, numpy as np, mujoco
sys.path.append(r"d:\ebca")

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

act_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in [
    "act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L",
    "act_shoulder_yaw_R", "act_shoulder_R", "act_elbow_R", "act_wrist_R", "act_grip_R", "act_grip_thumb_R"
]]
_fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
_fj_qadr = model.jnt_qposadr[_fj_id]
_fj_vadr = model.jnt_dofadr[_fj_id]
_cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

# Verify cube mass
geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "gcube_2")
body_id = model.geom_bodyid[geom_id]
print(f"Cube body mass: {model.body_mass[body_id]:.3f} kg")

print("=" * 90)
print("  BRUTE-FORCE 3F (100g cube) — fine grid around best region")
print("=" * 90)

best_3f = 0; best_config = None
results = []

for s_yaw in [0.0, -0.3, 0.3]:
    for s_pitch in np.arange(0.8, 1.8, 0.1):
        for elbow in np.arange(-0.6, 0.1, 0.1):
            for wrist in np.arange(-0.3, 0.9, 0.1):
                mujoco.mj_resetData(model, data)
                data.qpos[_cube_j_id:_cube_j_id+3] = [0.20, 0.0, 0.048]
                data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
                home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
                home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()
                
                f1t = f2t = f3t = f3ft = 0
                for step in range(100):
                    ctrl = [s_yaw, s_pitch, elbow, wrist, 0.52, 0.52, 0,0,0,0,0,0]
                    for idx, aid in enumerate(act_ids):
                        data.ctrl[aid] = ctrl[idx]
                    mujoco.mj_step(model, data)
                    data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
                    data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
                    data.qvel[_fj_vadr:_fj_vadr+6] = 0.0
                    
                    tL = float(data.sensor("touch_L").data[0])
                    tB = float(data.sensor("touch_bot_L").data[0])
                    tT = float(data.sensor("touch_thumb_L").data[0])
                    if tL > 0.05: f1t += 1
                    if tB > 0.05: f2t += 1
                    if tT > 0.05: f3t += 1
                    if tL > 0.05 and tB > 0.05 and tT > 0.05: f3ft += 1
                
                p3f = 100*f3ft/100
                if p3f > best_3f:
                    best_3f = p3f
                    best_config = (s_yaw, s_pitch, elbow, wrist)
                if p3f > 0:
                    print(f"  *** 3F={p3f:5.1f}% | yaw={s_yaw:.1f} pitch={s_pitch:.1f} elbow={elbow:.1f} wrist={wrist:.1f} | F1={100*f1t/100:.0f}% F2={100*f2t/100:.0f}% F3={100*f3t/100:.0f}%")

print("=" * 90)
if best_config:
    print(f"BEST: yaw={best_config[0]:.1f} pitch={best_config[1]:.1f} elbow={best_config[2]:.1f} wrist={best_config[3]:.1f} -> 3F={best_3f:.1f}%")
else:
    print("STILL NO 3F. Trying wider search with s_yaw sweep...")
    # Ultra-wide search
    for s_yaw in np.arange(-1.5, 1.6, 0.3):
        for s_pitch in np.arange(0.0, 1.8, 0.3):
            for elbow in np.arange(-2.4, 0.1, 0.3):
                for wrist in np.arange(-1.5, 1.6, 0.3):
                    mujoco.mj_resetData(model, data)
                    data.qpos[_cube_j_id:_cube_j_id+3] = [0.20, 0.0, 0.048]
                    data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
                    home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
                    home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()
                    f3ft = 0
                    for step in range(80):
                        ctrl = [s_yaw, s_pitch, elbow, wrist, 0.52, 0.52, 0,0,0,0,0,0]
                        for idx, aid in enumerate(act_ids):
                            data.ctrl[aid] = ctrl[idx]
                        mujoco.mj_step(model, data)
                        data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
                        data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
                        data.qvel[_fj_vadr:_fj_vadr+6] = 0.0
                        tL = float(data.sensor("touch_L").data[0])
                        tB = float(data.sensor("touch_bot_L").data[0])
                        tT = float(data.sensor("touch_thumb_L").data[0])
                        if tL > 0.05 and tB > 0.05 and tT > 0.05: f3ft += 1
                    if f3ft > 0:
                        print(f"  *** 3F={100*f3ft/80:.1f}% | yaw={s_yaw:.1f} pitch={s_pitch:.1f} elbow={elbow:.1f} wrist={wrist:.1f}")
                        if 100*f3ft/80 > best_3f:
                            best_3f = 100*f3ft/80
                            best_config = (s_yaw, s_pitch, elbow, wrist)
    if best_config:
        print(f"\nBEST WIDE: yaw={best_config[0]:.1f} pitch={best_config[1]:.1f} elbow={best_config[2]:.1f} wrist={best_config[3]:.1f} -> 3F={best_3f:.1f}%")
    else:
        print("\nNO 3F CONTACT IN ANY CONFIGURATION. The XML hand geometry cannot produce simultaneous 3-finger floor grasps.")
print("=" * 90)
