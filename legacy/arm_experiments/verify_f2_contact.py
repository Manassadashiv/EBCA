"""Quick contact verification: does F2 actually register force with the current IK fixes?"""
import os, sys, numpy as np, mujoco
sys.path.append(r"d:\ebca")
from train_carl_curiosity_curriculum import solve_3finger_arm_ik

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

_arm_jnt_names = [
    "shoulder_yaw_L", "shoulder_L", "elbow_L", "wrist_L", "grip_L", "grip_thumb_L",
    "shoulder_yaw_R", "shoulder_R", "elbow_R", "wrist_R", "grip_R", "grip_thumb_R"
]
arm_actuator_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in [
    "act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L",
    "act_shoulder_yaw_R", "act_shoulder_R", "act_elbow_R", "act_wrist_R", "act_grip_R", "act_grip_thumb_R"
]]

_fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
_fj_qadr = model.jnt_qposadr[_fj_id]
_fj_vadr = model.jnt_dofadr[_fj_id]
_cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

print("=" * 80)
print("  F2 CONTACT FORCE VERIFICATION (10 episodes, with all IK fixes)")
print("=" * 80)

total_f1_hits = 0
total_f2_hits = 0
total_f3_hits = 0
total_3f_hits = 0
total_steps = 0

for ep in range(10):
    np.random.seed(ep + 700)
    mujoco.mj_resetData(model, data)

    target_x = float(np.random.uniform(0.18, 0.22))
    target_y = float(np.random.uniform(-0.05, 0.05))
    target_z = 0.048

    data.qpos[_cube_j_id:_cube_j_id+3] = [target_x, target_y, target_z]
    data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]
    data.qvel[_cube_j_id:_cube_j_id+6] = 0.0
    mujoco.mj_forward(model, data)

    _chassis_home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
    _chassis_home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()

    ep_f1 = 0; ep_f2 = 0; ep_f3 = 0; ep_3f = 0; ep_steps = 0

    for step in range(160):
        mujoco.mj_step(model, data)
        data.qpos[_fj_qadr:_fj_qadr+3] = _chassis_home_pos
        data.qpos[_fj_qadr+3:_fj_qadr+7] = _chassis_home_quat
        data.qvel[_fj_vadr:_fj_vadr+6] = 0.0

        # Live cube tracking (same as training code)
        actual_cube_pos = data.body("obj_cube_2").xpos.copy()
        actual_cube_x = float(actual_cube_pos[0])
        actual_cube_y = float(actual_cube_pos[1])
        actual_cube_z = float(actual_cube_pos[2])
        target_floor_z = max(0.018, actual_cube_z + 0.009)

        t_descent = min(1.0, step / 30.0)
        current_ik_z = target_z + (target_floor_z - target_z) * t_descent
        current_ik_y_L = actual_cube_y + 0.016
        current_ik_y_R = actual_cube_y - 0.016

        s_yaw_L, s_pitch_L, elbow_L, wrist_L = solve_3finger_arm_ik(actual_cube_x, current_ik_y_L, current_ik_z, "L")
        s_yaw_R, s_pitch_R, elbow_R, wrist_R = solve_3finger_arm_ik(actual_cube_x, current_ik_y_R, current_ik_z, "R")

        clamp_val = 0.48 if step > 30 else 0.0
        wrist_L_angle = float(np.clip(-s_pitch_L - elbow_L + 0.15, -1.57, 1.57))
        wrist_R_angle = float(np.clip(-s_pitch_R - elbow_R + 0.15, -1.57, 1.57))

        ctrl = [s_yaw_L, s_pitch_L, elbow_L, wrist_L_angle, clamp_val, clamp_val,
                s_yaw_R, s_pitch_R, elbow_R, wrist_R_angle, clamp_val, clamp_val]
        for idx, aid in enumerate(arm_actuator_ids):
            data.ctrl[aid] = ctrl[idx]
        mujoco.mj_forward(model, data)

        # Read sensors
        touch_L = float(data.sensor("touch_L").data[0])
        touch_bot_L = float(data.sensor("touch_bot_L").data[0])
        touch_thumb_L = float(data.sensor("touch_thumb_L").data[0])

        f1 = touch_L > 0.05
        f2 = touch_bot_L > 0.05
        f3 = touch_thumb_L > 0.05

        if f1: ep_f1 += 1
        if f2: ep_f2 += 1
        if f3: ep_f3 += 1
        if f1 and f2 and f3: ep_3f += 1
        ep_steps += 1

    total_f1_hits += ep_f1; total_f2_hits += ep_f2; total_f3_hits += ep_f3
    total_3f_hits += ep_3f; total_steps += ep_steps

    print(f"EP {ep:2d} | F1:{100*ep_f1/ep_steps:5.1f}% F2:{100*ep_f2/ep_steps:5.1f}% F3:{100*ep_f3/ep_steps:5.1f}% | 3F:{100*ep_3f/ep_steps:5.1f}%")

print("=" * 80)
print(f"TOTAL | F1:{100*total_f1_hits/total_steps:5.1f}% F2:{100*total_f2_hits/total_steps:5.1f}% F3:{100*total_f3_hits/total_steps:5.1f}% | 3F:{100*total_3f_hits/total_steps:5.1f}%")
print("=" * 80)
