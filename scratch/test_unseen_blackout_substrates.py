"""
scratch/test_unseen_blackout_substrates.py — Test 4 substrates across the 5 unseen seeds during blackout
"""
import sys
import math
import numpy as np

sys.path.insert(0, "d:/ebca")
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.test_stage2_1b_cann import apply_stochastic_initial_pose
from brain.test_stage2_1b_r_causality import PersistentNonNeuralControl

hal = CarlStage1HAL(open_space=True)

# Frozen k_eff from Dev seeds
FROZEN_K_EFF = 4.0861

UNSEEN_SEEDS = [303, 404, 505, 606, 707]

print(f"Testing 4 Substrates on 5 Unseen Seeds with FROZEN k_eff = {FROZEN_K_EFF:+.4f}")
print("=" * 80)

for seed in UNSEEN_SEEDS:
    rng = np.random.RandomState(seed)
    apply_stochastic_initial_pose(hal, seed)

    # Brain with frozen efference
    brain = CarlStage2BIntegratedBrain(seed=seed)
    # Give it the learned w_rot (channel 20)
    w_rot = np.zeros(25)
    w_rot[20] = 1.0
    brain.w_rot = w_rot
    brain.is_developmentally_trained = True

    hal.reset()
    apply_stochastic_initial_pose(hal, seed)
    brain.reset_at_birthplace()

    u_turning = np.zeros(6)
    u_turning[0] = 0.12   # Left wheel
    u_turning[1] = -0.06  # Right wheel -> Active turning (Delta u = -0.18)

    # Substrate heading states
    theta_sub_a = 0.0  # Sensory-only CANN heading
    theta_sub_b = 0.0  # Correct efference CANN heading
    theta_sub_c = 0.0  # Inverted efference CANN heading
    theta_sub_d = 0.0  # Classical baseline heading

    # Phase 1: Normal driving (30 ticks)
    for _ in range(30):
        s, diag = hal.step(u_turning)
        brain.update_brain(u_turning, s)
        theta_sub_a = brain.hd_ring.decode_heading()
        theta_sub_b = brain.hd_ring.decode_heading()
        theta_sub_c = brain.hd_ring.decode_heading()
        theta_sub_d = (theta_sub_d + s[20] * hal.dt + math.pi) % (2.0 * math.pi) - math.pi

    gt_yaw_pre = diag["yaw"]

    # Clone HD rings for Substrates A, B, C
    ring_a = brain.hd_ring  # sensory only
    from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor
    ring_b = HeadDirectionRingAttractor(seed=seed, dt=hal.dt)
    ring_b.u = ring_a.u.copy()
    ring_b.r = ring_a.r.copy()

    ring_c = HeadDirectionRingAttractor(seed=seed, dt=hal.dt)
    ring_c.u = ring_a.u.copy()
    ring_c.r = ring_a.r.copy()

    # Phase 2: Physically Changing Blackout (90 ticks / 2.7s)
    diff_u = u_turning[1] - u_turning[0]
    omega_eff_correct = FROZEN_K_EFF * diff_u
    omega_eff_inverted = -FROZEN_K_EFF * diff_u

    for _ in range(90):
        s, diag = hal.step(u_turning)
        # Blackout: sensors are 0
        ring_a.step(0.0)
        ring_b.step(omega_eff_correct)
        ring_c.step(omega_eff_inverted)
        theta_sub_d = (theta_sub_d + omega_eff_correct * hal.dt + math.pi) % (2.0 * math.pi) - math.pi

    gt_yaw_post = diag["yaw"]

    # Decode headings
    h_a = ring_a.decode_heading()
    h_b = ring_b.decode_heading()
    h_c = ring_c.decode_heading()
    h_d = theta_sub_d

    err_a = math.degrees(abs(math.atan2(math.sin(h_a - gt_yaw_post), math.cos(h_a - gt_yaw_post))))
    err_b = math.degrees(abs(math.atan2(math.sin(h_b - gt_yaw_post), math.cos(h_b - gt_yaw_post))))
    err_c = math.degrees(abs(math.atan2(math.sin(h_c - gt_yaw_post), math.cos(h_c - gt_yaw_post))))
    err_d = math.degrees(abs(math.atan2(math.sin(h_d - gt_yaw_post), math.cos(h_d - gt_yaw_post))))

    print(f"Seed {seed:3d} (UNSEEN): Sub A (Sensory-Only) = {err_a:5.1f}° | Sub B (Correct Efference) = {err_b:5.1f}° | "
          f"Sub C (Inverted Efference) = {err_c:5.1f}° | Sub D (Classical) = {err_d:5.1f}°")
