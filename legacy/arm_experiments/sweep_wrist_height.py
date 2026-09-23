"""Find the wrist angle and approach height that enables 3-finger contact on a floor cube.
Sweeps wrist_angle and target_z simultaneously."""
import os, sys, numpy as np, mujoco, math
sys.path.append(r"d:\ebca")
from train_carl_curiosity_curriculum import solve_3finger_arm_ik

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

arm_actuator_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in [
    "act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L",
    "act_shoulder_yaw_R", "act_shoulder_R", "act_elbow_R", "act_wrist_R", "act_grip_R", "act_grip_thumb_R"
]]
_fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
_fj_qadr = model.jnt_qposadr[_fj_id]
_fj_vadr = model.jnt_dofadr[_fj_id]
_cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

print("=" * 100)
print("  WRIST ANGLE x TARGET_Z SWEEP: Finding 3F contact configuration")
print("=" * 100)
print(f"{'wrist_override':>15} {'ik_z':>6} | {'F1':>6} {'F2':>6} {'F3':>6} | {'3F':>6}")
print("-" * 100)

best_3f = 0
best_config = None

for wrist_override in np.arange(-1.5, 1.6, 0.3):
    for ik_z in [0.020, 0.030, 0.040, 0.048, 0.060]:
        tot_f1 = tot_f2 = tot_f3 = tot_3f = tot_steps = 0

        for ep in range(3):
            np.random.seed(ep + 900)
            mujoco.mj_resetData(model, data)
            tx = 0.20
            ty = 0.0
            data.qpos[_cube_j_id:_cube_j_id+3] = [tx, ty, 0.048]
            data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
            mujoco.mj_forward(model, data)
            home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
            home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()

            for step in range(160):
                mujoco.mj_step(model, data)
                data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
                data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
                data.qvel[_fj_vadr:_fj_vadr+6] = 0.0

                # Use IK for shoulder/elbow, but override wrist
                s_yaw, s_pitch, elbow, _ = solve_3finger_arm_ik(tx, ty, ik_z, "L")
                clamp = 0.52 if step > 20 else 0.0  # Max clamp

                ctrl = [s_yaw, s_pitch, elbow, float(wrist_override), clamp, clamp,
                        0, 0, 0, 0, 0, 0]
                for idx, aid in enumerate(arm_actuator_ids):
                    data.ctrl[aid] = ctrl[idx]
                mujoco.mj_forward(model, data)

                tL = float(data.sensor("touch_L").data[0])
                tB = float(data.sensor("touch_bot_L").data[0])
                tT = float(data.sensor("touch_thumb_L").data[0])
                f1 = tL > 0.05; f2 = tB > 0.05; f3 = tT > 0.05
                if f1: tot_f1 += 1
                if f2: tot_f2 += 1
                if f3: tot_f3 += 1
                if f1 and f2 and f3: tot_3f += 1
                tot_steps += 1

        pct_3f = 100*tot_3f/tot_steps
        if pct_3f > best_3f:
            best_3f = pct_3f
            best_config = (wrist_override, ik_z)

        if pct_3f > 0 or 100*tot_f1/tot_steps > 5 or 100*tot_f2/tot_steps > 5:
            print(f"{wrist_override:15.1f} {ik_z:6.3f} | {100*tot_f1/tot_steps:5.1f}% {100*tot_f2/tot_steps:5.1f}% {100*tot_f3/tot_steps:5.1f}% | {100*tot_3f/tot_steps:5.1f}%  {'<-- 3F!' if pct_3f > 0 else ''}")

print("=" * 100)
if best_config:
    print(f"BEST 3F CONFIG: wrist={best_config[0]:.1f}, ik_z={best_config[1]:.3f} -> {best_3f:.1f}%")
else:
    print("NO 3F CONTACT FOUND IN ANY CONFIGURATION")
print("=" * 100)
