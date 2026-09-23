"""
===============================================================================
  train_carl_curiosity_curriculum.py — CARL-Omega BIOMIMETIC MOTOR LEARNING
===============================================================================
  Full Biological Motor Learning Architecture:

  PATHWAY 1 — CEREBELLUM (RLS Readout):
    Supervised error correction from IK teacher. Fast, accurate imitation.
    "Copy the teacher's movement."

  PATHWAY 2 — BASAL GANGLIA (Neural Policy Head):
    Reward-driven policy optimization via dense dopamine signal.
    "Discover movements that maximize reward — even ones the teacher never taught."

  PATHWAY 3 — CEREBELLAR FORWARD MODEL:
    Predicts sensory consequences of motor commands (efference copy).
    Enables slip anticipation, curiosity-driven exploration, and motor planning.
    "If I do X, Y will happen."

  PATHWAY 4 — MPPI TRAJECTORY OPTIMIZATION:
    2,000-sample GPU parallel futures. Finds optimal trajectory through
    contact-rich dynamics via Monte Carlo sampling.

  Training Features:
    - Adaptive Residual Blending (teacher fade-out as CARL's brain matures)
    - Dense Progressive Reward Shaping (continuous, not binary)
    - Hindsight Experience Replay (HER) — learn from failures
    - Periodic Checkpointing + Graceful Ctrl+C (nothing ever lost)
    - Cerebellar slip anticipation (preemptive grip force adjustment)

  Physics Model : vessel_kinetic.xml (MuJoCo)
  Total Episodes: ENDLESS until Stage 4 mastery (safety cap: 50,000)
===============================================================================
"""

import os
import sys
import time
import math
import signal
import numpy as np
import mujoco

from brain.carl_reservoir import LiquidStateReservoir
from brain.carl_endocrine import EndocrineSystem
from brain.carl_mppi import MPPIParallelEngine
from brain.carl_mpc import SurpriseNoiseEstimator, ResidualTorqueCompensator
from brain.carl_osc_dmp import OperationalSpaceController, DynamicMovementPrimitive
from brain.carl_policy_head import NeuralPolicyHead
from brain.carl_cerebellum import CerebellarForwardModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "world", "vessel_kinetic.xml")
ARM_WEIGHTS_PATH = os.path.join(BASE_DIR, "memory", "carl_arm_weights.npz")
RESERVOIR_PATH = os.path.join(BASE_DIR, "memory", "carl_reservoir.npz")
POLICY_HEAD_PATH = os.path.join(BASE_DIR, "memory", "carl_policy_head.pt")
CEREBELLUM_PATH = os.path.join(BASE_DIR, "memory", "carl_cerebellum.pt")
CHECKPOINT_DIR = os.path.join(BASE_DIR, "memory", "checkpoints")


def solve_3finger_arm_ik(target_x: float, target_y: float, target_z: float, arm_side: str = "L") -> tuple:
    """
    Analytical Inverse Kinematics for CARL's 5-DOF arm + 3-finger tripod gripper.
    Includes Torso Leaning (Hip Roll/Pitch) to keep off-center targets in arm sweet spot.
    """
    L1, L2 = 0.12, 0.11

    # Torso Leaning active compensation:
    #   hip_roll  = lean sideways toward target Y
    #   hip_pitch = lean forward for distant X AND lean down for low Z targets
    hip_roll = float(np.clip(target_y * 1.2, -0.35, 0.35))
    z_lean = max(0.0, (0.12 - target_z)) * 1.5
    hip_pitch = float(np.clip((target_x - 0.20) * 0.8 + z_lean, -0.20, 0.40))

    H_torso = 0.145
    x_sh = -0.01 + H_torso * math.sin(hip_pitch)
    y_sh = (0.075 if arm_side == "L" else -0.075) + H_torso * math.sin(hip_roll)
    z_sh = 0.145 * math.cos(hip_pitch)

    # Adaptive hand offset and height bias calibration based on target height
    if target_z > 0.08:
        hand_offset = 0.042
        dz_bias = -0.025
    else:
        hand_offset = 0.025
        dz_bias = +0.005

    dx = target_x - x_sh
    dy = target_y - y_sh
    dz = (target_z + dz_bias) - z_sh

    # 1. Shoulder Yaw Angle (rotates inward toward target y)
    s_yaw = math.atan2(dy, dx)
    if arm_side == "L":
        s_yaw = float(np.clip(s_yaw, -0.52, 1.57))
    else:
        s_yaw = float(np.clip(s_yaw, -1.57, 0.52))

    # 2. Planar reach distance
    r_planar = math.sqrt(dx**2 + dy**2)
    dist_3d = math.sqrt(r_planar**2 + dz**2)
    d_effective = np.clip(dist_3d - hand_offset, 0.02, L1 + L2 - 0.001)

    # 3. Elbow Angle
    cos_elbow = np.clip((L1**2 + L2**2 - d_effective**2) / (2.0 * L1 * L2), -1.0, 1.0)
    elbow_angle = float(np.clip(-math.pi + math.acos(cos_elbow), -2.44, 0.0))

    # 4. Shoulder Pitch Angle (Positive points forward-downward)
    alpha = math.atan2(dz, r_planar)
    beta = math.atan2(L2 * math.sin(-elbow_angle), L1 + L2 * math.cos(-elbow_angle))
    s_pitch = float(np.clip(beta - alpha, -1.8, 1.8))

    # 5. Wrist Pitch Angle
    wrist_angle = float(np.clip(-s_pitch - elbow_angle, -1.57, 1.57))

    return s_yaw, s_pitch, elbow_angle, wrist_angle


# =============================================================================
# HINDSIGHT EXPERIENCE REPLAY (HER) BUFFER
# =============================================================================
class HindsightReplayBuffer:
    """
    Hippocampal Replay System — learns from failures by relabeling goals.

    When CARL reaches position P_actual instead of P_target:
        Original: (state, action, FAILURE, P_target)
        Relabeled: (state, action, SUCCESS, P_actual)

    "I didn't reach where I wanted, but I DID reach somewhere —
     and now I know how to reach THERE."

    References:
        - Andrychowicz et al. (2017): Hindsight Experience Replay
        - Buzsáki (2015): Hippocampal sharp-wave ripple replay
    """

    def __init__(self, max_size: int = 50000, k_relabel: int = 4):
        self.max_size = max_size
        self.k_relabel = k_relabel
        self.buffer = []
        self.episode_buffer = []  # Current episode transitions

    def start_episode(self):
        """Begin collecting transitions for a new episode."""
        self.episode_buffer = []

    def store_transition(self, state: np.ndarray, action: np.ndarray,
                         achieved_pos: np.ndarray, desired_pos: np.ndarray,
                         reward: float):
        """Store a single transition within the current episode."""
        self.episode_buffer.append({
            'state': state.copy(),
            'action': action.copy(),
            'achieved': achieved_pos.copy(),
            'desired': desired_pos.copy(),
            'reward': reward
        })

    def end_episode_and_relabel(self):
        """
        End episode and perform HER goal relabeling.
        Generates k_relabel additional "success" experiences per transition.
        """
        if len(self.episode_buffer) < 2:
            return

        # Store original transitions
        for t in self.episode_buffer:
            self._add_to_buffer(t)

        # HER: Relabel with "future" strategy
        # For each transition, pick k future achieved states as alternative goals
        for i, transition in enumerate(self.episode_buffer):
            future_indices = range(i + 1, len(self.episode_buffer))
            if len(list(future_indices)) == 0:
                continue

            # Sample k future states (or all if fewer than k)
            future_list = list(range(i + 1, len(self.episode_buffer)))
            k_actual = min(self.k_relabel, len(future_list))
            selected = np.random.choice(future_list, k_actual, replace=False)

            for future_idx in selected:
                # Relabel: the goal is now what we actually achieved at future_idx
                new_goal = self.episode_buffer[future_idx]['achieved'].copy()
                # Compute new reward: distance to relabeled goal
                dist = np.linalg.norm(transition['achieved'] - new_goal)
                new_reward = math.exp(-dist / 0.005)  # Dense reward for reaching the relabeled goal

                relabeled = {
                    'state': transition['state'].copy(),
                    'action': transition['action'].copy(),
                    'achieved': transition['achieved'].copy(),
                    'desired': new_goal,
                    'reward': new_reward
                }
                self._add_to_buffer(relabeled)

    def _add_to_buffer(self, transition: dict):
        if len(self.buffer) >= self.max_size:
            self.buffer.pop(0)
        self.buffer.append(transition)

    def sample_batch(self, batch_size: int = 32) -> list:
        """Sample a random mini-batch for offline training."""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]

    def size(self) -> int:
        return len(self.buffer)


# =============================================================================
# MAIN TRAINING LOOP
# =============================================================================
def run_curiosity_curriculum_training(max_episodes: int = 50000, fresh_start: bool = False):
    print("=" * 75)
    print("  CARL-Omega BIOMIMETIC 4-STAGE MOTOR LEARNING ENGINE")
    print("  [Dual-Pathway: Cerebellar RLS + Basal Ganglia Policy Head]")
    print("  [Cerebellar Forward Model + MPPI + HER + Dense Rewards]")
    print(f"  Physics Model : {MODEL_PATH}")
    print("  Mode          : ENDLESS CONVERGENCE (Terminates ONLY upon Stage 4 Mastery)")
    print("  Safety Cap    : {:,} episodes".format(max_episodes))
    print(f"  Fresh Start   : {fresh_start}")
    print("=" * 75)

    # ── 1. Load Physics & Brain Modules ───────────────────────────────────
    model = mujoco.MjModel.from_xml_path(MODEL_PATH)
    data = mujoco.MjData(model)

    # Pathway 1: Cerebellum (RLS reservoir readout)
    reservoir = LiquidStateReservoir(N=500, K=14)
    if os.path.exists(RESERVOIR_PATH):
        reservoir.load(RESERVOIR_PATH)

    # Pathway 2: Basal Ganglia (Neural Policy Head)
    policy_head = NeuralPolicyHead(lr=3e-4)

    # Pathway 3: Cerebellar Forward Model
    cerebellum = CerebellarForwardModel(lr=1e-3)

    if fresh_start:
        archive_dir = os.path.join(BASE_DIR, "memory", "archive_single_sensor_checkpoint")
        os.makedirs(archive_dir, exist_ok=True)
        for fname in ["carl_arm_weights.npz", "carl_policy_head.pt", "carl_cerebellum.pt"]:
            src = os.path.join(BASE_DIR, "memory", fname)
            if os.path.exists(src):
                import shutil
                shutil.copy2(src, os.path.join(archive_dir, fname))
        print(f"\033[93m[FRESH START] Archived contaminated weights to {archive_dir}\033[0m")
        print("\033[92m[FRESH START] Initialized clean policy head and cerebellum weights for multi-touch training.\033[0m")
    else:
        if os.path.exists(ARM_WEIGHTS_PATH):
            reservoir.load_arm_weights(ARM_WEIGHTS_PATH)
        if os.path.exists(POLICY_HEAD_PATH):
            policy_head.load(POLICY_HEAD_PATH)
        if os.path.exists(CEREBELLUM_PATH):
            cerebellum.load(CEREBELLUM_PATH)

    # Neuromodulatory system
    endocrine = EndocrineSystem()

    # Pathway 4: MPPI trajectory optimization
    mppi_engine = MPPIParallelEngine(num_samples=2000, horizon=50)
    surprise_estimator = SurpriseNoiseEstimator(surprise_threshold=0.015)
    residual_compensator = ResidualTorqueCompensator(kp=15.0, kd=1.2)
    osc_controller = OperationalSpaceController(kp=80.0, kv=12.0)

    # Hindsight Experience Replay
    her_buffer = HindsightReplayBuffer(max_size=50000, k_relabel=4)

    # Actuator resolution
    arm_actuator_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
                        for name in reservoir.ARM_ACTUATOR_NAMES]

    # ── Pre-cache MuJoCo IDs (avoids 720+ string lookups per episode) ─────
    _fj_spatial_id   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "spatial_identity")
    _fj_spatial_vadr = model.jnt_dofadr[_fj_spatial_id]
    _fj_spatial_qadr = model.jnt_qposadr[_fj_spatial_id]
    _hip_roll_id    = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "act_hip_roll")
    _hip_pitch_id   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, "act_hip_pitch")
    _site_touch_L   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_L")
    _site_thumb_L   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_thumb_L")
    _site_touch_R   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_R")
    _site_thumb_R   = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "touch_site_thumb_R")
    _cube_j_id      = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "fj_cube_2")]

    _arm_joint_names = [
        "shoulder_yaw_L", "shoulder_L", "elbow_L", "wrist_L", "grip_L", "grip_thumb_L",
        "shoulder_yaw_R", "shoulder_R", "elbow_R", "wrist_R", "grip_R", "grip_thumb_R",
    ]
    _arm_jnt_qaddrs = [model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in _arm_joint_names]

    # ── 2. Training State ─────────────────────────────────────────────────
    start_time = time.time()
    reach_errors = []
    grasp_successes = []
    lift_successes = []

    stage_id = 1
    stage_names = {
        1: "1. Surface Touch Exploration",
        2: "2. Handshake / High-Five Trick",
        3: "3. Sub-Centimeter Floor Grasping",
        4: "4. 3-Finger High Air Lift Task Fulfillment"
    }

    # Adaptive Residual Blending Schedule (teacher fade-out)
    # Start with near-pure teacher; brain earns authority via stage progression
    stage_alpha = {1: 0.95, 2: 0.85, 3: 0.60, 4: 0.30}

    rolling_reach_errs = []
    rolling_grasp_rates = []
    rolling_lift_rates = []
    rolling_true_3f_rates = []
    rolling_drop_rates = []

    f1_rates = []
    f2_rates = []
    f3_rates = []
    simul_3f_rates = []
    true_s4_successes = []

    best_reach_err = 999.0
    interrupted = False

    # ── 3. Graceful Ctrl+C Handler (SIGINT) ───────────────────────────────
    def handle_interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True
        print("\n\033[93m[CTRL+C] Graceful shutdown initiated. Saving all weights...\033[0m")

    signal.signal(signal.SIGINT, handle_interrupt)

    # ── 4. Checkpoint Save Function ───────────────────────────────────────
    def save_checkpoint(ep_num, reason="periodic"):
        """Save ALL model weights + training state."""
        os.makedirs(CHECKPOINT_DIR, exist_ok=True)

        reservoir.save_arm_weights(ARM_WEIGHTS_PATH)
        reservoir.save(RESERVOIR_PATH)
        policy_head.save(POLICY_HEAD_PATH)
        cerebellum.save(CEREBELLUM_PATH)

        # Save training state for resume capability
        state_path = os.path.join(CHECKPOINT_DIR, "training_state.npz")
        np.savez(state_path,
                 episode=ep_num,
                 stage_id=stage_id,
                 rolling_reach_errs=np.array(rolling_reach_errs[-100:]),
                 rolling_grasp_rates=np.array(rolling_grasp_rates[-100:]),
                 rolling_lift_rates=np.array(rolling_lift_rates[-100:]),
                 best_reach_err=best_reach_err)

        print(f"\033[96m[CHECKPOINT] Saved at episode {ep_num} ({reason}) — Stage {stage_id}, "
              f"Best Reach: {best_reach_err:.2f}mm\033[0m")

    # ── 5. ENDLESS CONVERGENCE TRAINING LOOP ──────────────────────────────
    ep = 0
    while True:
        if interrupted:
            save_checkpoint(ep, reason="Ctrl+C interrupt")
            break

        ep += 1
        if ep > max_episodes:
            print(f"\n[SAFETY CAP] Reached {max_episodes} episodes. Saving and exiting.")
            save_checkpoint(ep, reason="safety cap")
            break

        mujoco.mj_resetData(model, data)

        # ── Calibrated Mastery Gates (ground-truth MuJoCo site measurement) ─
        if len(rolling_reach_errs) >= 10:
            recent_10_reach = rolling_reach_errs[-10:]
            recent_10_true_3f = rolling_true_3f_rates[-10:]
            recent_10_lift = rolling_lift_rates[-10:]
            recent_10_drop = rolling_drop_rates[-10:]

            # Stage 1: Ground-truth reach ~15-25mm via position actuator dynamics
            reach_gate_1 = all(err < 25.0 for err in recent_10_reach)
            # Stage 2: Centered Y=0 targets allow tighter precision
            reach_gate_2 = all(err < 20.0 for err in recent_10_reach)
            # Stage 3: True 3-finger tripod grasp rate must be >= 75%
            grasp_gate = all(rate >= 0.75 for rate in recent_10_true_3f)
            # Stage 4: Air lift rate >= 70% and drop rate <= 10%
            lift_gate = all(rate >= 0.70 for rate in recent_10_lift) and all(drop <= 0.10 for drop in recent_10_drop)

            if stage_id == 1 and reach_gate_1:
                stage_id = 2
                rolling_reach_errs.clear()
                rolling_grasp_rates.clear()
                rolling_lift_rates.clear()
                rolling_true_3f_rates.clear()
                rolling_drop_rates.clear()
                save_checkpoint(ep, reason="Stage 1 MASTERED")
                print(f"\n\033[92m{'='*75}\n  [MASTERY] Stage 1 Complete! Sub-25mm Reach for 10 CONSECUTIVE episodes!"
                      f"\n  Advancing to Stage 2: Handshake Trick | Teacher alpha: {stage_alpha[2]:.0%}"
                      f"\n{'='*75}\033[0m\n")

            elif stage_id == 2 and reach_gate_2:
                stage_id = 3
                rolling_reach_errs.clear()
                rolling_grasp_rates.clear()
                rolling_lift_rates.clear()
                rolling_true_3f_rates.clear()
                rolling_drop_rates.clear()
                save_checkpoint(ep, reason="Stage 2 MASTERED")
                print(f"\n\033[92m{'='*75}\n  [MASTERY] Stage 2 Complete! Sub-20mm Handshake for 10 CONSECUTIVE episodes!"
                      f"\n  Advancing to Stage 3: Floor Grasping | Teacher alpha: {stage_alpha[3]:.0%}"
                      f"\n{'='*75}\033[0m\n")

            elif stage_id == 3 and grasp_gate:
                stage_id = 4
                rolling_reach_errs.clear()
                rolling_grasp_rates.clear()
                rolling_lift_rates.clear()
                rolling_true_3f_rates.clear()
                rolling_drop_rates.clear()
                save_checkpoint(ep, reason="Stage 3 MASTERED")
                print(f"\n\033[92m{'='*75}\n  [MASTERY] Stage 3 Complete! >=75% True 3-Finger Grasp Rate for 10 CONSECUTIVE episodes!"
                      f"\n  Advancing to Stage 4: Air Lift | Teacher alpha: {stage_alpha[4]:.0%}"
                      f"\n{'='*75}\033[0m\n")

            elif stage_id == 4 and lift_gate:
                save_checkpoint(ep, reason="ALL 4 STAGES MASTERED")
                print(f"\n\033[92m{'='*75}")
                print(f"  [STAR] CURRICULUM MASTERY COMPLETE [STAR]")
                print(f"  All 4 stages fully mastered in {ep} episodes!")
                print(f"  Total training time: {time.time() - start_time:.1f} seconds")
                print(f"{'='*75}\033[0m\n")
                break

        stage_name = stage_names[stage_id]
        alpha = stage_alpha[stage_id]  # Teacher blending weight

        # ── Stage-Specific 3D Target Selection ────────────────────────
        if stage_id == 1:
            # Tightened to arm's dexterous sweet spot (torso leaning handles the rest)
            target_x = np.random.uniform(0.18, 0.23)
            target_y = np.random.uniform(-0.07, 0.07)
            target_z = 0.12
        elif stage_id == 2:
            target_x = np.random.uniform(0.18, 0.22)
            target_y = 0.0
            target_z = 0.15
        elif stage_id == 3:
            target_x = np.random.uniform(0.18, 0.22)
            target_y = np.random.uniform(-0.05, 0.05)
            target_z = 0.048
        else:
            target_x = np.random.uniform(0.18, 0.22)
            target_y = np.random.uniform(-0.05, 0.05)
            target_z = 0.048

        # Place target cube via freejoint qpos
        data.qpos[_cube_j_id:_cube_j_id+3] = [target_x, target_y, target_z]
        data.qpos[_cube_j_id+3:_cube_j_id+7] = [1.0, 0.0, 0.0, 0.0]

        # Episode telemetry
        ep_min_reach_err = 999.0
        ep_grasped = False
        ep_lifted = False
        ep_was_dropped = False
        ep_dense_reward = 0.0
        ep_prev_reach_err = 999.0
        target_3d = np.array([target_x, target_y, target_z])

        consecutive_3f_steps = 0
        ep_f1_hits = 0
        ep_f2_hits = 0
        ep_f3_hits = 0
        ep_simul_3f_hits = 0

        # HER episode start
        her_buffer.start_episode()

        # Save chassis home position for full lock during manipulation
        _chassis_home_pos  = data.qpos[_fj_spatial_qadr:_fj_spatial_qadr+3].copy()
        _chassis_home_quat = data.qpos[_fj_spatial_qadr+3:_fj_spatial_qadr+7].copy()

        for step in range(160):
            if interrupted:
                break

            mujoco.mj_step(model, data)

            # ── CHASSIS BRAKE: lock position + zero velocity ──────────
            data.qpos[_fj_spatial_qadr:_fj_spatial_qadr+3] = _chassis_home_pos
            data.qpos[_fj_spatial_qadr+3:_fj_spatial_qadr+7] = _chassis_home_quat
            data.qvel[_fj_spatial_vadr:_fj_spatial_vadr+6] = 0.0

            endocrine.step(0.033)

            # Current joint positions & actuator state
            current_qpos = np.array([data.qpos[adr] for adr in _arm_jnt_qaddrs])

            # ── DYNAMIC IK Z-DESCENT (X/Y use spawn coords) ──────────
            actual_cube_z = float(data.body("obj_cube_2").xpos[2])
            target_floor_z = max(0.018, actual_cube_z + 0.009)

            if stage_id == 3:
                t_descent = min(1.0, step / 30.0)
                current_ik_z = target_z + (target_floor_z - target_z) * t_descent
            elif stage_id == 4:
                if step > 50:
                    t_ramp = min(1.0, (step - 50) / 40.0)
                    current_ik_z = target_floor_z + (0.16 - target_floor_z) * t_ramp
                else:
                    t_descent = min(1.0, step / 30.0)
                    current_ik_z = target_z + (target_floor_z - target_z) * t_descent
            else:
                current_ik_z = target_z

            # ── PATHWAY 1: IK Teacher Joint Targets ───────────────────
            s_yaw_L, s_pitch_L, elbow_L, wrist_L = solve_3finger_arm_ik(target_x, target_y, current_ik_z, "L")
            s_yaw_R, s_pitch_R, elbow_R, wrist_R = solve_3finger_arm_ik(target_x, target_y, current_ik_z, "R")

            # Stage 3+: override wrist to empirically optimal floor-grasp orientation (8.0% peak 3F)
            if stage_id >= 3:
                wrist_L = 0.5
                wrist_R = 0.5

            # Activate finger closure from Stage 2 onwards (max clamp 0.52 rad)
            clamp_val = 0.52 if stage_id >= 2 and step > 20 else 0.0

            teacher_targets = np.array([
                s_yaw_L, s_pitch_L, elbow_L, wrist_L, clamp_val, clamp_val,
                s_yaw_R, s_pitch_R, elbow_R, wrist_R, clamp_val, clamp_val
            ])

            # ── PATHWAY 4: GPU MPPI Trajectory Optimization ──────────
            u_mppi = mppi_engine.optimize_trajectory(
                current_qpos, teacher_targets, target_3d,
                {"DA": endocrine.DA, "NE": endocrine.NE}
            )

            # Read touch sensors for all 3 fingers on Left and Right arms
            try:
                touch_L = float(data.sensor("touch_L").data[0])
                touch_R = float(data.sensor("touch_R").data[0])
                touch_bot_L = float(data.sensor("touch_bot_L").data[0])
                touch_bot_R = float(data.sensor("touch_bot_R").data[0])
                touch_thumb_L = float(data.sensor("touch_thumb_L").data[0])
                touch_thumb_R = float(data.sensor("touch_thumb_R").data[0])
            except Exception:
                touch_L = data.sensordata[0] if len(data.sensordata) > 0 else 0.0
                touch_R = data.sensordata[1] if len(data.sensordata) > 1 else 0.0
                touch_thumb_L = data.sensordata[2] if len(data.sensordata) > 2 else 0.0
                touch_thumb_R = data.sensordata[3] if len(data.sensordata) > 3 else 0.0
                touch_bot_L = data.sensordata[4] if len(data.sensordata) > 4 else 0.0
                touch_bot_R = data.sensordata[5] if len(data.sensordata) > 5 else 0.0
            touch_sensors = np.array([touch_L, touch_R])

            # ── PATHWAY 2: Basal Ganglia Neural Policy Correction ─────
            policy_correction = policy_head.compute_correction(
                reservoir.x, target_3d, current_qpos, touch_sensors
            )
            policy_target = teacher_targets + policy_correction

            # ── ADAPTIVE RESIDUAL BLENDING ────────────────────────────
            brain_output = 0.5 * u_mppi + 0.5 * policy_target
            blended_ctrl = alpha * teacher_targets + (1.0 - alpha) * brain_output

            raw_ctrl = np.clip(
                blended_ctrl,
                [r[0] for r in reservoir.ARM_CTRL_RANGES],
                [r[1] for r in reservoir.ARM_CTRL_RANGES]
            )

            # ── PATHWAY 3: Cerebellar Forward Model (True Efference Copy) ──
            # Single-pass prediction using actual executed motor command (raw_ctrl)
            cerebellar_pred = cerebellum.predict_next_state(
                current_qpos, raw_ctrl, touch_sensors, target_3d
            )

            # Preemptive grip force adjustment from cerebellar slip risk
            grip_L_adjust = cerebellum.get_grip_force_adjustment(
                cerebellar_pred['slip_risk'], clamp_val
            )
            grip_R_adjust = grip_L_adjust  # Symmetric adjustment

            final_ctrl = raw_ctrl.copy()
            if stage_id >= 3 and step > 35:
                final_ctrl[4] = min(0.52, final_ctrl[4] + grip_L_adjust)
                final_ctrl[5] = min(0.52, final_ctrl[5] + grip_L_adjust)
                final_ctrl[10] = min(0.52, final_ctrl[10] + grip_R_adjust)
                final_ctrl[11] = min(0.52, final_ctrl[11] + grip_R_adjust)

            # Write to MuJoCo arm actuators + Torso Leaning hips
            for idx, aid in enumerate(arm_actuator_ids):
                data.ctrl[aid] = final_ctrl[idx]

            z_lean_ctrl = max(0.0, (0.12 - target_z)) * 1.5
            if _hip_roll_id >= 0:
                data.ctrl[_hip_roll_id] = float(np.clip(target_y * 1.2, -0.35, 0.35))
            if _hip_pitch_id >= 0:
                data.ctrl[_hip_pitch_id] = float(np.clip((target_x - 0.20) * 0.8 + z_lean_ctrl, -0.20, 0.40))

            # ── PATHWAY 1: Reservoir Spiking + RLS Learning ───────────
            u_sensory = np.zeros(reservoir.M)
            u_sensory[0] = target_x
            u_sensory[1] = target_y
            u_sensory[2] = target_z
            u_sensory[10] = touch_L
            u_sensory[11] = touch_R
            reservoir.step(u_sensory)

            if step > 20:
                reservoir.rls_update_arm(teacher_targets)

            # ── MEASURE GROUND-TRUTH END-EFFECTOR POSITION FROM MUJOCO ──
            mujoco.mj_forward(model, data)  # Ensure site positions are up-to-date

            claw_center_L = (data.site_xpos[_site_touch_L] + data.site_xpos[_site_thumb_L]) / 2.0
            claw_center_R = (data.site_xpos[_site_touch_R] + data.site_xpos[_site_thumb_R]) / 2.0
            t_arr = np.array([target_x, target_y, target_z])

            err_L = float(np.linalg.norm(claw_center_L - t_arr)) * 1000.0
            err_R = float(np.linalg.norm(claw_center_R - t_arr)) * 1000.0
            reach_err_mm = min(err_L, err_R)
            ep_min_reach_err = min(ep_min_reach_err, reach_err_mm)

            # ── DENSE PROGRESSIVE REWARD SHAPING ──────────────────────
            # (NOT binary — continuous reward gradient)

            # 1. Reach reward: exponential proximity bonus (scaled for ground-truth ~15-25mm)
            reward_reach = math.exp(-reach_err_mm / 15.0)

            # 2. Improvement delta reward: did we get closer?
            reward_delta = max(0.0, (ep_prev_reach_err - reach_err_mm) * 0.1)
            ep_prev_reach_err = reach_err_mm

            # 3. Sustained 3-Finger Tripod Enclosure Condition & Grasp Reward
            f1_hit_L = touch_L > 0.02
            f2_hit_L = touch_bot_L > 0.02
            f3_hit_L = touch_thumb_L > 0.02

            f1_hit_R = touch_R > 0.02
            f2_hit_R = touch_bot_R > 0.02
            f3_hit_R = touch_thumb_R > 0.02

            f1_hit = f1_hit_L or f1_hit_R
            f2_hit = f2_hit_L or f2_hit_R
            f3_hit = f3_hit_L or f3_hit_R

            if f1_hit: ep_f1_hits += 1
            if f2_hit: ep_f2_hits += 1
            if f3_hit: ep_f3_hits += 1

            simul_3f_step = (f1_hit_L and f2_hit_L and f3_hit_L) or (f1_hit_R and f2_hit_R and f3_hit_R)
            if simul_3f_step:
                ep_simul_3f_hits += 1
                consecutive_3f_steps += 1
                if consecutive_3f_steps >= 15:  # 0.15s sustained hold (timestep = 0.01s)
                    ep_grasped = True
            else:
                consecutive_3f_steps = 0

            # 3. Grasp reward: geometric mean (multiplicative AND-gate) + progressive multi-finger touch bonus
            reward_finger_progress = 0.1 * (min(1.0, touch_L / 0.05) + min(1.0, touch_bot_L / 0.05) + min(1.0, touch_thumb_L / 0.05)) if stage_id >= 3 else 0.0

            reward_grasp = 0.0
            if (f1_hit_L and f2_hit_L and f3_hit_L) or (f1_hit_R and f2_hit_R and f3_hit_R):
                forces = [max(touch_L, 1e-6), max(touch_bot_L, 1e-6), max(touch_thumb_L, 1e-6)]
                reward_grasp = (forces[0] * forces[1] * forces[2]) ** (1.0 / 3.0)
            else:
                reward_grasp = 0.0

            # 4. Lift height reward: continuous height bonus
            reward_lift = 0.0
            if stage_id == 4 and ep_grasped and step > 70:
                cube_z = data.body("obj_cube_2").xpos[2]
                if cube_z > 0.06:
                    reward_lift = float(np.clip((cube_z - 0.048) / 0.06, 0.0, 1.0))
                    if cube_z > 0.10:
                        ep_lifted = True
                if ep_lifted and step > 120 and cube_z < 0.04:
                    ep_was_dropped = True

            # 5. Smoothness penalty: penalize jerky movements
            jerk_penalty = -0.005 * float(np.sum((final_ctrl - current_qpos)**2))

            # 6. Active tactile retention bonus during lift
            reward_retention = 2.0 if (consecutive_3f_steps >= 15 and step > 50) else 0.0

            # 7. Rotation penalty during lift phase (penalize twisting/wobble)
            cube_quat = data.qpos[_cube_j_id+3:_cube_j_id+7]
            rot_angle = 2.0 * math.acos(float(np.clip(abs(cube_quat[0]), 0.0, 1.0)))
            reward_rot_penalty = -0.5 * rot_angle if (ep_grasped and step > 50) else 0.0

            # Composite dense reward
            step_reward = reward_reach + reward_delta + reward_finger_progress + reward_grasp * 2.0 + reward_lift * 3.0 + reward_retention + reward_rot_penalty + jerk_penalty
            ep_dense_reward += step_reward

            # ── ENDOCRINE MODULATION ──────────────────────────────────
            if reward_grasp > 0.3:
                da_amount = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0}[stage_id]
                endocrine.trigger_dopamine_treat(da_amount * reward_grasp, f"STAGE_{stage_id}_GRASP")

            if reward_lift > 0.5:
                endocrine.trigger_dopamine_treat(3.0, "AIR LIFT TASK FULFILLMENT")

            # Curiosity signal from cerebellar prediction error
            curiosity = cerebellum.get_curiosity_signal()
            if curiosity > 0.5:
                endocrine.NE = float(np.clip(endocrine.NE + curiosity * 0.2, 0.0, 3.0))

            # Anti-Laziness penalty: only penalize if arm is NOT reaching (near-zero pitch)
            if abs(s_pitch_L) < 0.02 and abs(s_pitch_R) < 0.02 and step > 40:
                endocrine.trigger_heavy_penalty("ARM STALLING — NOT REACHING")

            # ── PATHWAY 3: Cerebellar Learning (climbing fiber error) ─
            actual_pos_error = claw_center_L - t_arr
            pred_error = cerebellum.update_with_actual(touch_sensors, actual_pos_error)

            # ── PATHWAY 2: Basal Ganglia Policy Head Training ─────────
            # Train on dense reward signal, modulated by dopamine
            if step > 20 and step % 4 == 0:
                # The correction that was actually used
                actual_correction = final_ctrl - alpha * teacher_targets
                policy_head.train_step(
                    reservoir.x, target_3d, current_qpos, touch_sensors,
                    reward=step_reward,
                    actual_outcome=actual_correction,
                    dopamine=endocrine.DA
                )

            # ── HER: Store transition ─────────────────────────────────
            achieved_pos = claw_center_L
            if step % 10 == 0:
                her_state = np.concatenate([current_qpos, touch_sensors])
                her_buffer.store_transition(her_state, final_ctrl, achieved_pos, target_3d, step_reward)

        # ── END OF EPISODE ────────────────────────────────────────────
        f1_rate_ep = (ep_f1_hits / 160.0) * 100.0
        f2_rate_ep = (ep_f2_hits / 160.0) * 100.0
        f3_rate_ep = (ep_f3_hits / 160.0) * 100.0
        simul_3f_rate_ep = (ep_simul_3f_hits / 160.0) * 100.0
        true_s4_ep = 1.0 if (ep_grasped and ep_lifted and not ep_was_dropped) else 0.0

        reach_errors.append(ep_min_reach_err)
        grasp_successes.append(1.0 if ep_grasped else 0.0)
        lift_successes.append(1.0 if ep_lifted else 0.0)
        f1_rates.append(f1_rate_ep)
        f2_rates.append(f2_rate_ep)
        f3_rates.append(f3_rate_ep)
        simul_3f_rates.append(simul_3f_rate_ep)
        true_s4_successes.append(true_s4_ep)

        rolling_reach_errs.append(ep_min_reach_err)
        rolling_grasp_rates.append(1.0 if ep_grasped else 0.0)
        rolling_lift_rates.append(1.0 if ep_lifted else 0.0)
        rolling_true_3f_rates.append(1.0 if ep_grasped else 0.0)
        rolling_drop_rates.append(1.0 if ep_was_dropped else 0.0)

        best_reach_err = min(best_reach_err, ep_min_reach_err)

        # HER: Relabel failed episode goals
        her_buffer.end_episode_and_relabel()

        # HER: Offline replay training for policy head
        if her_buffer.size() >= 64 and ep % 5 == 0:
            batch = her_buffer.sample_batch(32)
            for sample in batch:
                policy_head.train_step(
                    reservoir.x, sample['desired'], sample['state'][:12],
                    sample['state'][12:14] if len(sample['state']) > 13 else np.zeros(2),
                    reward=sample['reward'],
                    actual_outcome=sample['action'],
                    dopamine=endocrine.DA
                )

        # ── PERIODIC LOGGING ──────────────────────────────────────────
        if ep % 25 == 0:
            f1_pct = np.mean(f1_rates[-25:])
            f2_pct = np.mean(f2_rates[-25:])
            f3_pct = np.mean(f3_rates[-25:])
            simul_3f_pct = np.mean(simul_3f_rates[-25:])
            grasp_pct = np.mean(grasp_successes[-25:]) * 100.0
            lift_pct = np.mean(lift_successes[-25:]) * 100.0
            true_s4_pct = np.mean(true_s4_successes[-25:]) * 100.0

            print(f"[EP {ep:5d}] Stage {stage_id}: {stage_name:<30} | "
                  f"F1:{f1_pct:4.1f}% F2:{f2_pct:4.1f}% F3:{f3_pct:4.1f}% | "
                  f"3F:{simul_3f_pct:4.1f}% | Grasp:{grasp_pct:4.1f}% | Lift:{lift_pct:4.1f}% | TRUE_STAGE4:{true_s4_pct:4.1f}%")

        # ── PERIODIC CHECKPOINT (every 100 episodes) ──────────────────
        if ep % 100 == 0:
            save_checkpoint(ep, reason="periodic")

        # Best model checkpoint
        if ep_min_reach_err < best_reach_err + 0.01 and ep > 10:
            if ep_min_reach_err < 5.0:  # Only save "best" if reasonably good
                best_path = os.path.join(CHECKPOINT_DIR, "best_arm_weights.npz")
                reservoir.save_arm_weights(best_path)

    # ── FINAL SAVE ────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print("=" * 75)
    print(f"  BIOMIMETIC MOTOR LEARNING COMPLETE ({elapsed:.1f}s elapsed, {ep} episodes)")
    print(f"  Final 3D Reach Precision : {np.mean(reach_errors[-50:]):.2f} mm")
    print(f"  Final Tactile Grasp Rate : {np.mean(grasp_successes[-50:])*100.0:.1f}%")
    print(f"  Final Air Lift Rate      : {np.mean(lift_successes[-50:])*100.0:.1f}%")
    print(f"  Policy Head Updates      : {policy_head.total_updates}")
    print(f"  Cerebellar Updates       : {cerebellum.total_updates}")
    print(f"  HER Buffer Size          : {her_buffer.size()}")
    print("=" * 75)

    save_checkpoint(ep, reason="final")
    print(f"[SUCCESS] All weights exported to {os.path.join(BASE_DIR, 'memory')}")


if __name__ == "__main__":
    run_curiosity_curriculum_training()
