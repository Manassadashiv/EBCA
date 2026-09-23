import os
import sys
import math
import numpy as np
import mujoco

sys.path.append(r"d:\ebca")

from train_carl_curiosity_curriculum import solve_3finger_arm_ik

MODEL_PATH = r"D:\ebca\world\vessel_kinetic.xml"

def measure_f2_runtime_gap():
    print("=" * 80)
    print("  CARL F2 RUNTIME GAP MEASUREMENT (10 STAGE-3 EPISODES)")
    print("=" * 80)

    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    _arm_jnt_names = [
        "shoulder_yaw_L", "shoulder_L", "elbow_L", "wrist_L", "grip_L", "grip_thumb_L",
        "shoulder_yaw_R", "shoulder_R", "elbow_R", "wrist_R", "grip_R", "grip_thumb_R"
    ]
    _arm_jnt_qaddrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in _arm_jnt_names]
    arm_actuator_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in [
        "act_shoulder_yaw_L", "act_shoulder_L", "act_elbow_L", "act_wrist_L", "act_grip_L", "act_grip_thumb_L",
        "act_shoulder_yaw_R", "act_shoulder_R", "act_elbow_R", "act_wrist_R", "act_grip_R", "act_grip_thumb_R"
    ]]

    _fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
    _fj_qadr = model.jnt_qposadr[_fj_id]
    _fj_vadr = model.jnt_dofadr[_fj_id]
    _cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

    _site_f2_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_bot_L")
    _site_f1_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_L")
    _site_f3_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_thumb_L")

    geom_cube = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "gcube_2")
    geom_f2_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_L_base")

    gaps = []

    for ep in range(10):
        np.random.seed(ep + 500)
        mujoco.mj_resetData(model, data)

        target_x = float(np.random.uniform(0.18, 0.22))
        target_y = float(np.random.uniform(-0.05, 0.05))
        target_z = 0.048

        data.qpos[_cube_j_id:_cube_j_id+3] = [target_x, target_y, target_z]
        data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]
        data.qvel[_cube_j_id:_cube_j_id+6] = 0.0
        mujoco.mj_forward(model, data)

        _chassis_home_pos  = data.qpos[_fj_qadr:_fj_qadr+3].copy()
        _chassis_home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()

        min_gap_ep = 999.0
        f2_pos_at_min = None
        cube_pos_at_min = None

        for step in range(120):
            mujoco.mj_step(model, data)

            data.qpos[_fj_qadr:_fj_qadr+3] = _chassis_home_pos
            data.qpos[_fj_qadr+3:_fj_qadr+7] = _chassis_home_quat
            data.qvel[_fj_vadr:_fj_vadr+6] = 0.0

            actual_cube_pos = data.body("obj_cube_2").xpos.copy()
            actual_cube_x = float(actual_cube_pos[0])
            actual_cube_y = float(actual_cube_pos[1])
            actual_cube_z = float(actual_cube_pos[2])

            target_floor_z = max(0.018, actual_cube_z + 0.009)
            t_descent = min(1.0, step / 30.0)
            current_ik_z = target_z + (target_floor_z - target_z) * t_descent

            s_yaw_L, s_pitch_L, elbow_L, wrist_L = solve_3finger_arm_ik(actual_cube_x, actual_cube_y + 0.016, current_ik_z, "L")
            clamp_val = 0.48 if step > 30 else 0.0
            wrist_angle = float(np.clip(-s_pitch_L - elbow_L + 0.15, -1.57, 1.57))

            ctrl_vec = np.zeros(12)
            ctrl_vec[0:6] = [s_yaw_L, s_pitch_L, elbow_L, wrist_angle, clamp_val, clamp_val]

            for idx, aid in enumerate(arm_actuator_ids):
                data.ctrl[aid] = ctrl_vec[idx]

            mujoco.mj_forward(model, data)

            pos_f2 = data.site_xpos[_site_f2_L].copy()
            pos_cube = data.body("obj_cube_2").xpos.copy()

            # Distance between F2 site and cube center (minus half cube width 8mm)
            dist_center = float(np.linalg.norm(pos_f2 - pos_cube))
            gap_surface = max(0.0, (dist_center - 0.008) * 1000.0)  # Gap in mm

            if gap_surface < min_gap_ep:
                min_gap_ep = gap_surface
                f2_pos_at_min = pos_f2
                cube_pos_at_min = pos_cube

        gaps.append(min_gap_ep)
        print(f"EP {ep:2d} | Target: [{target_x:.3f}, {target_y:.3f}] | Cube: [{cube_pos_at_min[0]:.3f}, {cube_pos_at_min[1]:.3f}, {cube_pos_at_min[2]:.3f}] | F2 Site: [{f2_pos_at_min[0]:.3f}, {f2_pos_at_min[1]:.3f}, {f2_pos_at_min[2]:.3f}] | Gap: {min_gap_ep:5.2f} mm")

    print("=" * 80)
    print(f"MEAN F2 RUNTIME GAP AT CLOSEST APPROACH : {np.mean(gaps):5.2f} mm (Min: {np.min(gaps):.2f}mm, Max: {np.max(gaps):.2f}mm)")
    print("=" * 80)

if __name__ == "__main__":
    measure_f2_runtime_gap()
