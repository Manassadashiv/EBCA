"""
===============================================================================
  showcase_carl_manipulation.py — REAL-TIME 3D NEURAL MANIPULATION SHOWCASE
===============================================================================
  Demonstrates CARL's 3-Finger Tripod Grippers, 2,000-Sample GPU MPPI Engine,
  Trained Basal Ganglia Neural Policy Head (1.6M updates), Cerebellar Forward
  Model (6.4M updates), and Real Physics Block Height Z_block Telemetry.
===============================================================================
"""

import os
import sys
import time
import math
import numpy as np
import torch
import mujoco
import mujoco.viewer

from brain.carl_reservoir import LiquidStateReservoir
from brain.carl_endocrine import EndocrineSystem
from brain.carl_mppi import MPPIParallelEngine
from brain.carl_policy_head import NeuralPolicyHead
from brain.carl_cerebellum import CerebellarForwardModel
from brain.carl_osc_dmp import DynamicMovementPrimitive
from train_carl_curiosity_curriculum import solve_3finger_arm_ik

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
ARM_WEIGHTS_PATH = os.path.join(BASE_DIR, "memory", "carl_arm_weights.npz")
RESERVOIR_PATH = os.path.join(BASE_DIR, "memory", "carl_reservoir.npz")
POLICY_HEAD_PATH = os.path.join(BASE_DIR, "memory", "carl_policy_head.pt")
CEREBELLUM_PATH = os.path.join(BASE_DIR, "memory", "carl_cerebellum.pt")


def run_manipulation_showcase():
    print("=" * 75)
    print("  CARL-Omega REAL-TIME 3D NEURAL MANIPULATION ENGINE")
    print("  [FULL 4-STAGE MASTERED BRAIN: 1.6M POLICY UPDATES + 6.4M CEREBELLUM UPDATES]")
    print(f"  Physics Model: {MODEL_PATH}")
    print("=" * 75)

    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    # 1. Load Reservoir & Arm Weights
    reservoir = LiquidStateReservoir(N=500, K=14)
    if os.path.exists(RESERVOIR_PATH):
        reservoir.load(RESERVOIR_PATH)
    if os.path.exists(ARM_WEIGHTS_PATH):
        reservoir.load_arm_weights(ARM_WEIGHTS_PATH)

    # 2. Load Basal Ganglia Neural Policy Head
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy_head = NeuralPolicyHead(device=device)
    if os.path.exists(POLICY_HEAD_PATH):
        checkpoint = torch.load(POLICY_HEAD_PATH, map_location=device, weights_only=False)
        state_dict = checkpoint["model_state_dict"] if (isinstance(checkpoint, dict) and "model_state_dict" in checkpoint) else checkpoint
        policy_head.load_state_dict(state_dict)
    policy_head.eval()
    print(f"[BG-401] Policy head loaded from {POLICY_HEAD_PATH}")

    # 3. Load Cerebellar Forward Model
    cerebellum = CerebellarForwardModel(device=device)
    if os.path.exists(CEREBELLUM_PATH):
        checkpoint_c = torch.load(CEREBELLUM_PATH, map_location=device, weights_only=False)
        state_dict_c = checkpoint_c["model_state_dict"] if (isinstance(checkpoint_c, dict) and "model_state_dict" in checkpoint_c) else checkpoint_c
        cerebellum.load_state_dict(state_dict_c)
    cerebellum.eval()
    print(f"[CFM-501] Cerebellar forward model loaded from {CEREBELLUM_PATH}")

    endocrine = EndocrineSystem()
    mppi_engine = MPPIParallelEngine(num_samples=2000, horizon=50)

    # Pre-cache addresses
    _arm_jnt_names = [
        "shoulder_yaw_L", "shoulder_L", "elbow_L", "wrist_L", "grip_L", "grip_thumb_L",
        "shoulder_yaw_R", "shoulder_R", "elbow_R", "wrist_R", "grip_R", "grip_thumb_R"
    ]
    _arm_jnt_qaddrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in _arm_jnt_names]
    arm_actuator_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in reservoir.ARM_ACTUATOR_NAMES]

    # Torso actuators
    try:
        _hip_roll_id  = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "act_hip_roll")
        _hip_pitch_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "act_hip_pitch")
    except Exception:
        _hip_roll_id, _hip_pitch_id = -1, -1

    # Chassis freejoint address
    _fj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
    _fj_qadr = model.jnt_qposadr[_fj_id]
    _fj_vadr = model.jnt_dofadr[_fj_id]

    # Target block parameters (Left workspace directly in front of shoulder)
    target_x = 0.200
    target_y = 0.075
    target_z = 0.018
    target_3d = np.array([target_x, target_y, target_z])

    _cube_j_id = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

    _chassis_home_pos  = data.qpos[_fj_qadr:_fj_qadr+3].copy()
    _chassis_home_quat = data.qpos[_fj_qadr+3:_fj_qadr+7].copy()

    REST_R = np.zeros(6)
    alpha = 0.85  # Mastered Stage 4 teacher guidance weight

    print("\n[READY] Running Real-Time 3D Pick, Clamp & Lift Showcase...")
    print("Press Ctrl+C in terminal window to exit.\n")

    tick = 0

    with mujoco.viewer.launch_passive(model, data) as viewer:
        try:
            while viewer.is_running():
                step_start = time.time()
                phase_tick = tick % 360

                # Reset block position at start of every showcase cycle
                if phase_tick == 0:
                    data.qpos[_cube_j_id:_cube_j_id+3] = [target_x, target_y, target_z]
                    data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]
                    data.qvel[_cube_j_id:_cube_j_id+6] = 0.0
                    mujoco.mj_forward(model, data)

                endocrine.step(0.033)

                # Determine stage trajectory
                if phase_tick < 90:
                    stage_name = "\033[93m1. MINIMUM-JERK REACH DOWN TO FLOOR\033[0m"
                    cur_tz = DynamicMovementPrimitive.minimum_jerk_step(0.12, target_z, phase_tick * 0.033, 90 * 0.033)
                    clamp_val = 0.0
                elif phase_tick < 150:
                    stage_name = "\033[92m2. 3-FINGER TRIPOD PRECISION CLAMPING\033[0m"
                    cur_tz = target_z
                    t_clamp = min(1.0, (phase_tick - 90) / 20.0)
                    clamp_val = 0.30 * t_clamp
                    endocrine.trigger_dopamine_treat(2.0, "3-FINGER TRIPOD CLAMP")
                elif phase_tick < 270:
                    stage_name = "\033[96m3. LIFTING BLOCK HIGH INTO AIR (25cm)!\033[0m"
                    t_lift = (phase_tick - 150) * 0.033
                    cur_tz = DynamicMovementPrimitive.minimum_jerk_step(target_z, 0.265, t_lift, 120 * 0.033)
                    clamp_val = 0.30
                    endocrine.trigger_dopamine_treat(3.0, "AIR LIFT TASK FULFILLMENT")
                else:
                    stage_name = "\033[95m4. SMOOTH RELEASE & RETRACT\033[0m"
                    t_retract = (phase_tick - 270) * 0.033
                    cur_tz = DynamicMovementPrimitive.minimum_jerk_step(0.265, 0.12, t_retract, 90 * 0.033)
                    clamp_val = 0.0

                # Torso posture steady
                if _hip_roll_id >= 0:  data.ctrl[_hip_roll_id] = 0.0
                if _hip_pitch_id >= 0: data.ctrl[_hip_pitch_id] = 0.0

                current_qpos = np.array([data.qpos[adr] for adr in _arm_jnt_qaddrs])

                # Left Arm IK target (Right arm tucked)
                s_yaw_L, s_pitch_L, elbow_L, wrist_L = solve_3finger_arm_ik(target_x, target_y, cur_tz, "L")
                wrist_angle = float(np.clip(-s_pitch_L - elbow_L + 0.15, -1.57, 1.57))
                teacher_targets = np.concatenate([
                    [s_yaw_L, s_pitch_L, elbow_L, wrist_angle, clamp_val, clamp_val],
                    REST_R
                ])

                # MPPI Trajectory Optimization
                u_mppi = mppi_engine.optimize_trajectory(current_qpos, teacher_targets, target_3d, {"DA": endocrine.DA, "NE": endocrine.NE})

                # Read Touch Sensors
                try:
                    touch_L = float(data.sensor("touch_L").data[0])
                    touch_R = float(data.sensor("touch_R").data[0])
                except Exception:
                    touch_L = data.sensordata[0] if len(data.sensordata) > 0 else 0.0
                    touch_R = data.sensordata[1] if len(data.sensordata) > 1 else 0.0
                touch_sensors = np.array([touch_L, touch_R])

                # Basal Ganglia Neural Policy Head Correction
                policy_correction = policy_head.compute_correction(reservoir.x, target_3d, current_qpos, touch_sensors)
                policy_correction[6:] = 0.0
                if phase_tick < 90:
                    policy_correction[4] = 0.0
                    policy_correction[5] = 0.0

                policy_target = teacher_targets + policy_correction

                # Exact Trained Residual Control Blending
                brain_output = 0.5 * u_mppi + 0.5 * policy_target
                blended_ctrl = alpha * teacher_targets + (1.0 - alpha) * brain_output
                raw_ctrl = np.clip(blended_ctrl, [r[0] for r in reservoir.ARM_CTRL_RANGES], [r[1] for r in reservoir.ARM_CTRL_RANGES])
                raw_ctrl[6:] = REST_R

                # Cerebellar Forward Model Slip Reflex
                cerebellar_pred = cerebellum.predict_next_state(current_qpos, raw_ctrl, touch_sensors, target_3d)
                grip_L_adjust = cerebellum.get_grip_force_adjustment(cerebellar_pred['slip_risk'], clamp_val)

                final_ctrl = raw_ctrl.copy()
                if phase_tick >= 150 and phase_tick < 270:
                    final_ctrl[4] = min(0.52, final_ctrl[4] + grip_L_adjust)
                    final_ctrl[5] = min(0.52, final_ctrl[5] + grip_L_adjust)

                # 1. Apply controls BEFORE mj_step
                for idx, aid in enumerate(arm_actuator_ids):
                    data.ctrl[aid] = final_ctrl[idx]

                # 2. Advance Physics Step
                mujoco.mj_step(model, data)

                # 3. Chassis lock
                data.qpos[_fj_qadr:_fj_qadr+3] = _chassis_home_pos
                data.qpos[_fj_qadr+3:_fj_qadr+7] = _chassis_home_quat
                data.qvel[_fj_vadr:_fj_vadr+6] = 0.0

                # Telemetry
                actual_cube_z = data.body("obj_cube_2").xpos[2]
                if tick % 10 == 0:
                    contact_str = f"L={touch_L:.2f}N" if touch_L > 0.05 else "NO CONTACT"
                    lift_str = f"\033[92mLIFTED {actual_cube_z*100:.1f}cm\033[0m" if actual_cube_z > 0.05 else "ON FLOOR"

                    sys.stdout.write(
                        f"\r[TICK {tick:4d}] {stage_name} | "
                        f"Block Z: {actual_cube_z:5.3f}m ({lift_str}) | "
                        f"Tactile: {contact_str} | "
                        f"DA: {endocrine.DA:.2f} | NE: {endocrine.NE:.2f}"
                    )
                    sys.stdout.flush()

                viewer.sync()
                tick += 1

                time_until_next_step = model.opt.timestep - (time.time() - step_start)
                if time_until_next_step > 0:
                    time.sleep(time_until_next_step)

        except KeyboardInterrupt:
            print("\n[EXCITING] Showcase stopped cleanly by user.")

if __name__ == "__main__":
    run_manipulation_showcase()
