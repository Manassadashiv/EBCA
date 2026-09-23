import os
import sys
import time
import math
import numpy as np
import torch
import mujoco

sys.path.append(r"d:\ebca")

from brain.carl_reservoir import LiquidStateReservoir
from brain.carl_endocrine import EndocrineSystem
from brain.carl_mppi import MPPIParallelEngine
from brain.carl_policy_head import NeuralPolicyHead
from brain.carl_cerebellum import CerebellarForwardModel
from brain.carl_osc_dmp import DynamicMovementPrimitive
from train_carl_curiosity_curriculum import solve_3finger_arm_ik

BASE_DIR = r"D:\ebca"
MODEL_PATH = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
ARM_WEIGHTS_PATH = os.path.join(BASE_DIR, "memory", "carl_arm_weights.npz")
RESERVOIR_PATH = os.path.join(BASE_DIR, "memory", "carl_reservoir.npz")
POLICY_HEAD_PATH = os.path.join(BASE_DIR, "memory", "carl_policy_head.pt")
CEREBELLUM_PATH = os.path.join(BASE_DIR, "memory", "carl_cerebellum.pt")


def run_grasp_diagnosis():
    print("=" * 80)
    print("  CARL STAGE-4 GRASP DIAGNOSTIC — FROZEN CHECKPOINT EVALUATION (20 SEEDS)")
    print("=" * 80)

    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load frozen checkpoint models
    reservoir = LiquidStateReservoir(N=500, K=14)
    if os.path.exists(RESERVOIR_PATH):
        reservoir.load(RESERVOIR_PATH)
    if os.path.exists(ARM_WEIGHTS_PATH):
        reservoir.load_arm_weights(ARM_WEIGHTS_PATH)

    policy_head = NeuralPolicyHead(device=device)
    if os.path.exists(POLICY_HEAD_PATH):
        checkpoint = torch.load(POLICY_HEAD_PATH, map_location=device, weights_only=False)
        state_dict = checkpoint["model_state_dict"] if (isinstance(checkpoint, dict) and "model_state_dict" in checkpoint) else checkpoint
        policy_head.load_state_dict(state_dict)
    policy_head.eval()

    cerebellum = CerebellarForwardModel(device=device)
    if os.path.exists(CEREBELLUM_PATH):
        checkpoint_c = torch.load(CEREBELLUM_PATH, map_location=device, weights_only=False)
        state_dict_c = checkpoint_c["model_state_dict"] if (isinstance(checkpoint_c, dict) and "model_state_dict" in checkpoint_c) else checkpoint_c
        cerebellum.load_state_dict(state_dict_c)
    cerebellum.eval()

    mppi_engine = MPPIParallelEngine(num_samples=2000, horizon=50)

    _arm_jnt_names = [
        "shoulder_yaw_L", "shoulder_L", "elbow_L", "wrist_L", "grip_L", "grip_thumb_L",
        "shoulder_yaw_R", "shoulder_R", "elbow_R", "wrist_R", "grip_R", "grip_thumb_R"
    ]
    _arm_jnt_qaddrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in _arm_jnt_names]
    arm_actuator_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in reservoir.ARM_ACTUATOR_NAMES]

    _fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
    _fj_qadr = model.jnt_qposadr[_fj_id]
    _fj_vadr = model.jnt_dofadr[_fj_id]

    _cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

    geom_f1_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_L_tip")
    geom_f2_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_L_base")
    geom_f3_L = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_L_thumb_tip")

    geom_f1_R = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_R_tip")
    geom_f2_R = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_R_base")
    geom_f3_R = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "finger_R_thumb_tip")

    geom_cube = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "gcube_2")

    # Metrics storage over 20 fixed-seed episodes
    f1_contacts_total = 0
    f2_contacts_total = 0
    f3_contacts_total = 0
    three_finger_contacts_total = 0
    total_timesteps_evaluated = 0

    ep_longest_3f_runs = []
    ep_max_cube_heights = []
    ep_rotations_at_peak = []
    ep_drops = []
    ep_lift_successes = []

    num_episodes = 20
    episode_length = 160
    CONTACT_FORCE_THRESHOLD = 0.02  # 0.02 N threshold for contact

    for seed in range(num_episodes):
        np.random.seed(seed + 1000)
        torch.manual_seed(seed + 1000)

        mujoco.mj_resetData(model, data)

        # Stage 4 target selection
        target_x = float(np.random.uniform(0.18, 0.22))
        target_y = float(np.random.uniform(-0.05, 0.05))
        target_z = 0.048
        target_3d = np.array([target_x, target_y, target_z])

        data.qpos[_cube_j_id:_cube_j_id+3] = [target_x, target_y, target_z]
        data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]
        data.qvel[_cube_j_id:_cube_j_id+6] = 0.0
        mujoco.mj_forward(model, data)

        _chassis_home_pos  = data.qpos[_fj_qadr:_fj_qadr+3].copy()
        _chassis_home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()

        endocrine = EndocrineSystem()

        current_3f_run = 0
        max_3f_run = 0
        ep_max_h = 0.0
        ep_rot_at_peak = 0.0
        was_lifted_during_ep = False
        was_dropped_after_lift = False

        for step in range(episode_length):
            mujoco.mj_step(model, data)

            data.qpos[_fj_qadr:_fj_qadr+3] = _chassis_home_pos
            data.qpos[_fj_qadr+3:_fj_qadr+7] = _chassis_home_quat
            data.qvel[_fj_vadr:_fj_vadr+6] = 0.0

            endocrine.step(0.033)

            current_qpos = np.array([data.qpos[adr] for adr in _arm_jnt_qaddrs])

            if step > 50:
                t_ramp = min(1.0, (step - 50) / 40.0)
                current_ik_z = target_z + (0.16 - target_z) * t_ramp
            else:
                current_ik_z = target_z

            s_yaw_L, s_pitch_L, elbow_L, wrist_L = solve_3finger_arm_ik(target_x, target_y, current_ik_z, "L")
            s_yaw_R, s_pitch_R, elbow_R, wrist_R = solve_3finger_arm_ik(target_x, target_y, current_ik_z, "R")

            clamp_val = 0.48 if step > 30 else 0.0

            teacher_targets = np.array([
                s_yaw_L, s_pitch_L, elbow_L, wrist_L, clamp_val, clamp_val,
                s_yaw_R, s_pitch_R, elbow_R, wrist_R, clamp_val, clamp_val
            ])

            u_mppi = mppi_engine.optimize_trajectory(current_qpos, teacher_targets, target_3d, {"DA": endocrine.DA, "NE": endocrine.NE})

            try:
                touch_L = float(data.sensor("touch_L").data[0])
                touch_R = float(data.sensor("touch_R").data[0])
            except Exception:
                touch_L = data.sensordata[0] if len(data.sensordata) > 0 else 0.0
                touch_R = data.sensordata[1] if len(data.sensordata) > 1 else 0.0
            touch_sensors = np.array([touch_L, touch_R])

            policy_correction = policy_head.compute_correction(reservoir.x, target_3d, current_qpos, touch_sensors)
            policy_target = teacher_targets + policy_correction

            brain_output = 0.5 * u_mppi + 0.5 * policy_target
            blended_ctrl = 0.30 * teacher_targets + 0.70 * brain_output
            raw_ctrl = np.clip(blended_ctrl, [r[0] for r in reservoir.ARM_CTRL_RANGES], [r[1] for r in reservoir.ARM_CTRL_RANGES])

            cerebellar_pred = cerebellum.predict_next_state(current_qpos, raw_ctrl, touch_sensors, target_3d)
            grip_L_adjust = cerebellum.get_grip_force_adjustment(cerebellar_pred['slip_risk'], clamp_val)

            final_ctrl = raw_ctrl.copy()
            if step > 35:
                final_ctrl[4] = min(0.52, final_ctrl[4] + grip_L_adjust)
                final_ctrl[5] = min(0.52, final_ctrl[5] + grip_L_adjust)
                final_ctrl[10] = min(0.52, final_ctrl[10] + grip_L_adjust)
                final_ctrl[11] = min(0.52, final_ctrl[11] + grip_L_adjust)

            for idx, aid in enumerate(arm_actuator_ids):
                data.ctrl[aid] = final_ctrl[idx]

            # Measure Contact Forces per finger for Left arm (and Right arm)
            f1_force = 0.0
            f2_force = 0.0
            f3_force = 0.0

            # Read site sensors for F1 (Top), F2 (Bottom/Anvil), and F3 (Thumb)
            try:
                f1_force = max(0.0, float(data.sensor("touch_L").data[0]))
            except Exception: pass

            try:
                f2_force = max(0.0, float(data.sensor("touch_bot_L").data[0]))
            except Exception: pass

            try:
                f3_force = max(0.0, float(data.sensor("touch_thumb_L").data[0]))
            except Exception: pass

            f1_hit = f1_force > CONTACT_FORCE_THRESHOLD
            f2_hit = f2_force > CONTACT_FORCE_THRESHOLD
            f3_hit = f3_force > CONTACT_FORCE_THRESHOLD
            simultaneous_3f = f1_hit and f2_hit and f3_hit

            total_timesteps_evaluated += 1
            if f1_hit: f1_contacts_total += 1
            if f2_hit: f2_contacts_total += 1
            if f3_hit: f3_contacts_total += 1
            if simultaneous_3f: three_finger_contacts_total += 1

            if simultaneous_3f:
                current_3f_run += 1
                max_3f_run = max(max_3f_run, current_3f_run)
            else:
                current_3f_run = 0

            # Cube height and rotation
            cube_pos = data.body("obj_cube_2").xpos.copy()
            cube_z = float(cube_pos[2])
            cube_quat = data.qpos[_cube_j_id+3:_cube_j_id+7].copy()
            rot_deg = float(np.degrees(2.0 * math.acos(np.clip(abs(cube_quat[0]), 0.0, 1.0))))

            if cube_z > ep_max_h:
                ep_max_h = cube_z
                ep_rot_at_peak = rot_deg

            if cube_z > 0.10:
                was_lifted_during_ep = True

            if was_lifted_during_ep and step > 120 and cube_z < 0.04:
                was_dropped_after_lift = True

        ep_longest_3f_runs.append(max_3f_run)
        ep_max_cube_heights.append(ep_max_h)
        ep_rotations_at_peak.append(ep_rot_at_peak)
        ep_drops.append(1.0 if was_dropped_after_lift else 0.0)
        ep_lift_successes.append(1.0 if ep_max_h > 0.10 else 0.0)

        print(f"Seed {seed:2d} | Max H: {ep_max_h*100:5.1f}cm | Longest 3F Run: {max_3f_run:3d} steps | Drops: {was_dropped_after_lift}")

    # Aggregate Statistics
    f1_rate = (f1_contacts_total / total_timesteps_evaluated) * 100.0
    f2_rate = (f2_contacts_total / total_timesteps_evaluated) * 100.0
    f3_rate = (f3_contacts_total / total_timesteps_evaluated) * 100.0
    three_finger_rate = (three_finger_contacts_total / total_timesteps_evaluated) * 100.0
    mean_3f_duration = float(np.mean(ep_longest_3f_runs))
    lift_success_rate = float(np.mean(ep_lift_successes)) * 100.0
    mean_rotation = float(np.mean(ep_rotations_at_peak))
    drop_rate = float(np.mean(ep_drops)) * 100.0

    print("\n" + "=" * 80)
    print("STEP 2 DIAGNOSTIC AGGREGATE RESULTS (VERBATIM):")
    print("=" * 80)
    print(f"  F1 Contact Rate (Top Finger)       : {f1_rate:5.1f}%")
    print(f"  F2 Contact Rate (Bottom Finger)    : {f2_rate:5.1f}%")
    print(f"  F3 Contact Rate (Thumb Finger)     : {f3_rate:5.1f}%")
    print(f"  Simultaneous 3-Finger Contact Rate  : {three_finger_rate:5.1f}%")
    print(f"  Mean Longest 3-Finger Run (Steps)  : {mean_3f_duration:5.1f} timesteps")
    print(f"  Lift Success Rate (>10cm)          : {lift_success_rate:5.1f}%")
    print(f"  Mean Cube Rotation at Peak Height  : {mean_rotation:5.1f} degrees")
    print(f"  Post-Lift Drop Rate                : {drop_rate:5.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    run_grasp_diagnosis()
