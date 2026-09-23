"""VSU verification: test 3F contact with heavier cube (0.10kg) + wrist=0.3 override."""
import sys, numpy as np, mujoco
sys.path.append(r"d:\ebca")
from train_carl_curiosity_curriculum import solve_3finger_arm_ik

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"
model = mujoco.MjModel.from_xml_path(MODEL_PATH)
data = mujoco.MjData(model)

act_names = ["act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L",
             "act_shoulder_yaw_R", "act_shoulder_R", "act_elbow_R", "act_wrist_R", "act_grip_R", "act_grip_thumb_R"]
act_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in act_names]
_fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
_fj_qadr = model.jnt_qposadr[_fj_id]
_fj_vadr = model.jnt_dofadr[_fj_id]
_cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

print("=" * 80)
print("  VSU VERIFICATION: 3F contact with mass=0.10kg + wrist=0.3")
print("=" * 80)

total_f1 = total_f2 = total_f3 = total_3f = total_steps = 0

for ep in range(10):
    np.random.seed(ep + 1000)
    mujoco.mj_resetData(model, data)
    tx = float(np.random.uniform(0.18, 0.22))
    ty = float(np.random.uniform(-0.05, 0.05))
    tz = 0.048
    data.qpos[_cube_j_id:_cube_j_id+3] = [tx, ty, tz]
    data.qpos[_cube_j_id+3:_cube_j_id+7] = [1, 0, 0, 0]
    mujoco.mj_forward(model, data)
    home_pos = data.qpos[_fj_qadr:_fj_qadr+3].copy()
    home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()

    ep_f1 = ep_f2 = ep_f3 = ep_3f = 0

    for step in range(160):
        mujoco.mj_step(model, data)
        data.qpos[_fj_qadr:_fj_qadr+3] = home_pos
        data.qpos[_fj_qadr+3:_fj_qadr+7] = home_quat
        data.qvel[_fj_vadr:_fj_vadr+6] = 0.0

        actual_cube_z = float(data.body("obj_cube_2").xpos[2])
        target_floor_z = max(0.018, actual_cube_z + 0.009)
        t_descent = min(1.0, step / 30.0)
        current_ik_z = tz + (target_floor_z - tz) * t_descent

        s_yaw_L, s_pitch_L, elbow_L, _ = solve_3finger_arm_ik(tx, ty, current_ik_z, "L")
        wrist_L = 0.3  # Override
        clamp = 0.52 if step > 20 else 0.0

        ctrl = [s_yaw_L, s_pitch_L, elbow_L, wrist_L, clamp, clamp, 0,0,0,0,0,0]
        for idx, aid in enumerate(act_ids):
            data.ctrl[aid] = ctrl[idx]
        mujoco.mj_forward(model, data)

        tL = float(data.sensor("touch_L").data[0])
        tB = float(data.sensor("touch_bot_L").data[0])
        tT = float(data.sensor("touch_thumb_L").data[0])
        f1 = tL > 0.05; f2 = tB > 0.05; f3 = tT > 0.05
        if f1: ep_f1 += 1
        if f2: ep_f2 += 1
        if f3: ep_f3 += 1
        if f1 and f2 and f3: ep_3f += 1

    total_f1 += ep_f1; total_f2 += ep_f2; total_f3 += ep_f3; total_3f += ep_3f
    total_steps += 160
    print(f"EP {ep:2d} | target=[{tx:.3f},{ty:.3f}] | F1:{100*ep_f1/160:5.1f}% F2:{100*ep_f2/160:5.1f}% F3:{100*ep_f3/160:5.1f}% | 3F:{100*ep_3f/160:5.1f}%")

print("=" * 80)
print(f"TOTAL | F1:{100*total_f1/total_steps:5.1f}% F2:{100*total_f2/total_steps:5.1f}% F3:{100*total_f3/total_steps:5.1f}% | 3F:{100*total_3f/total_steps:5.1f}%")
print("=" * 80)
