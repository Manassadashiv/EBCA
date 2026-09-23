import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import numpy as np
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor

def set_bump_heading(ring: HeadDirectionRingAttractor, target_heading: float, rng: np.random.RandomState):
    dists = np.array([abs(math.atan2(math.sin(a - target_heading), math.cos(a - target_heading))) for a in ring.angles])
    idx = int(np.argmin(dists))
    ring.u = np.zeros(ring.N_NEURONS, dtype=np.float64)
    ring.u[idx] = 1.0
    # Small seeded membrane potential perturbation
    ring.u += rng.normal(0.0, 0.02, size=ring.N_NEURONS)
    ring.r = ring._activation(ring.u)
    ring._settle_initial_attractor(steps=100)

def inject_sensor_noise(s: np.ndarray, rng: np.random.RandomState) -> np.ndarray:
    s_noisy = s.copy()
    s_noisy[15:18] += rng.normal(0.0, 0.02, size=3)  # Accel
    s_noisy[18:21] += rng.normal(0.0, 0.015, size=3) # Gyro
    return s_noisy

def apply_carl_stochastic_initial_pose(hal: CarlStage1HAL, seed: int):
    rng = np.random.RandomState(seed)
    jitter_x = rng.uniform(-0.06, 0.06)
    jitter_y = rng.uniform(-0.06, 0.06)
    jitter_yaw = rng.uniform(-math.pi / 4.0, math.pi / 4.0)
    q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[q_addr] = jitter_x
    hal.data.qpos[q_addr + 1] = jitter_y
    hal.data.qpos[q_addr + 2] = 0.05291
    hal.data.qpos[q_addr + 3] = math.cos(jitter_yaw / 2.0)
    hal.data.qpos[q_addr + 4] = 0.0
    hal.data.qpos[q_addr + 5] = 0.0
    hal.data.qpos[q_addr + 6] = math.sin(jitter_yaw / 2.0)
    hal.data.qvel[:] = 0.0
    mujoco.mj_forward(hal.model, hal.data)
    hal.step(np.zeros(6))
    return jitter_x, jitter_y, jitter_yaw

hal = CarlStage1HAL(open_space=True)
frozen_k_eff = 4.0862

print("=== PROTOTYPE TEST: STOCHASTIC TASK 2 EVALUATION ===")
for seed in [303, 404, 505, 606, 707]:
    rng = np.random.RandomState(seed)
    hal.reset()
    jx, jy, jyaw = apply_carl_stochastic_initial_pose(hal, seed)
    diag0 = hal.get_diagnostics()
    yaw0 = diag0["yaw"]
    
    # Brain and Ring initialized
    brain = CarlStage2BIntegratedBrain(seed=seed)
    w_rot = np.zeros(25, dtype=np.float64)
    w_rot[20] = 1.0
    brain.w_rot = w_rot
    brain.k_eff = frozen_k_eff
    brain.use_motor_efference = True
    brain.is_developmentally_trained = True
    
    # Align initial bump to physical yaw
    set_bump_heading(brain.hd_ring, yaw0, rng)
    
    # Seed-dependent turning command: base turning command with slight seed-specific variation
    u_base_L = rng.uniform(0.10, 0.14)
    u_base_R = rng.uniform(-0.08, -0.04)
    
    # Phase 1: Normal driving (30 ticks)
    for _ in range(30):
        # Actuator noise
        u_act = np.zeros(6, dtype=np.float64)
        u_act[0] = u_base_L + rng.normal(0.0, 0.003)
        u_act[1] = u_base_R + rng.normal(0.0, 0.003)
        s, diag = hal.step(u_act)
        s_noisy = inject_sensor_noise(s, rng)
        brain.update_brain(u_act, s_noisy, is_blackout=False)
        
    heading_pre_blackout = diag["yaw"]
    h_pre_brain = brain.hd_ring.decode_heading()
    
    # Causal substrates
    ring_a = HeadDirectionRingAttractor(seed=seed, dt=hal.dt)
    ring_a.u = brain.hd_ring.u.copy()
    ring_a.r = brain.hd_ring.r.copy()
    
    ring_b = HeadDirectionRingAttractor(seed=seed, dt=hal.dt)
    ring_b.u = brain.hd_ring.u.copy()
    ring_b.r = brain.hd_ring.r.copy()
    
    ring_c = HeadDirectionRingAttractor(seed=seed, dt=hal.dt)
    ring_c.u = brain.hd_ring.u.copy()
    ring_c.r = brain.hd_ring.r.copy()
    
    theta_d = h_pre_brain
    
    # Phase 2: Blackout (90 ticks / 2.7s)
    for _ in range(90):
        u_act = np.zeros(6, dtype=np.float64)
        u_act[0] = u_base_L + rng.normal(0.0, 0.003)
        u_act[1] = u_base_R + rng.normal(0.0, 0.003)
        s, diag = hal.step(u_act)
        
        diff_u = float(u_act[1] - u_act[0])
        omega_eff_correct = float(frozen_k_eff * diff_u)
        omega_eff_inverted = float(-frozen_k_eff * diff_u)
        
        ring_a.step(0.0)
        ring_b.step(omega_eff_correct)
        ring_c.step(omega_eff_inverted)
        theta_d = (theta_d + omega_eff_correct * hal.dt + math.pi) % (2.0 * math.pi) - math.pi
        
    gt_yaw_end = diag["yaw"]
    total_rot = math.degrees(abs(math.atan2(math.sin(gt_yaw_end - heading_pre_blackout), math.cos(gt_yaw_end - heading_pre_blackout))))
    
    h_a = ring_a.decode_heading()
    h_b = ring_b.decode_heading()
    h_c = ring_c.decode_heading()
    h_d = theta_d
    
    err_a = math.degrees(abs(math.atan2(math.sin(h_a - gt_yaw_end), math.cos(h_a - gt_yaw_end))))
    err_b = math.degrees(abs(math.atan2(math.sin(h_b - gt_yaw_end), math.cos(h_b - gt_yaw_end))))
    err_c = math.degrees(abs(math.atan2(math.sin(h_c - gt_yaw_end), math.cos(h_c - gt_yaw_end))))
    err_d = math.degrees(abs(math.atan2(math.sin(h_d - gt_yaw_end), math.cos(h_d - gt_yaw_end))))
    
    print(f"Seed {seed:3d}: Start Yaw={math.degrees(yaw0):+6.1f}° | Pre-BO={math.degrees(heading_pre_blackout):+6.1f}° | "
          f"Post-BO={math.degrees(gt_yaw_end):+6.1f}° | Rot={total_rot:5.1f}° | "
          f"ErrA={err_a:5.1f}° | ErrB (Efference)={err_b:5.2f}° | ErrC (Inverted)={err_c:5.1f}° | ErrD={err_d:5.2f}°")
