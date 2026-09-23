"""Sweep target_z from 0.01 to 0.06 and measure contact rates at each height.
This tells us: at what IK target height does the hand actually make contact with a floor cube?"""
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
_site_f2 = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_bot_L")

print("=" * 90)
print("  IK TARGET HEIGHT SWEEP: Contact rates vs target_z (cube on floor at Z~0.009)")
print("=" * 90)
print(f"{'target_z':>10} | {'F1':>6} {'F2':>6} {'F3':>6} | {'3F':>6} | {'F2_site_Z':>10} {'Cube_Z':>8} {'Gap_mm':>8}")
print("-" * 90)

for ik_z in [0.010, 0.015, 0.018, 0.020, 0.025, 0.030, 0.035, 0.040, 0.048, 0.060]:
    tot_f1 = tot_f2 = tot_f3 = tot_3f = tot_steps = 0
    last_f2z = last_cubez = last_gap = 0

    for ep in range(5):
        np.random.seed(ep + 800)
        mujoco.mj_resetData(model, data)
        tx = float(np.random.uniform(0.19, 0.21))
        ty = 0.0  # centered for clean measurement
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

            cube_pos = data.body("obj_cube_2").xpos.copy()
            ik_y_L = float(cube_pos[1]) + 0.016

            s_yaw, s_pitch, elbow, wrist = solve_3finger_arm_ik(float(cube_pos[0]), ik_y_L, ik_z, "L")
            clamp = 0.48 if step > 30 else 0.0
            wrist_a = float(np.clip(-s_pitch - elbow + 0.15, -1.57, 1.57))
            ctrl = [s_yaw, s_pitch, elbow, wrist_a, clamp, clamp, 0,0,0,0,0,0]
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

            if step == 100:
                last_f2z = data.site_xpos[_site_f2][2]
                last_cubez = cube_pos[2]
                last_gap = np.linalg.norm(data.site_xpos[_site_f2] - cube_pos) * 1000

    print(f"{ik_z:10.3f} | {100*tot_f1/tot_steps:5.1f}% {100*tot_f2/tot_steps:5.1f}% {100*tot_f3/tot_steps:5.1f}% | {100*tot_3f/tot_steps:5.1f}% | {last_f2z:10.4f} {last_cubez:8.4f} {last_gap:8.1f}")

print("=" * 90)
