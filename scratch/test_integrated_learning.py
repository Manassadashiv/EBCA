import sys
import numpy as np
import math

sys.path.insert(0, ".")

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain

print("Testing Unsupervised Developmental Discovery of Translational Self-Model...")
hal = CarlStage1HAL(open_space=False)  # In habitat with reflective walls

for seed in [42, 101, 202]:
    rng = np.random.RandomState(seed)
    hal.reset()
    
    # Developmental approach babbling sweeps in habitat
    U_list, S_list = [], []
    for sweep in range(12):
        hal.reset()
        # Random initial orientation in habitat
        q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
        jitter_yaw = float(rng.uniform(-math.pi, math.pi))
        hal.data.qpos[q_addr + 3] = math.cos(jitter_yaw / 2.0)
        hal.data.qpos[q_addr + 6] = math.sin(jitter_yaw / 2.0)
        hal.step(np.zeros(6))
        
        base_fwd = float(rng.uniform(0.06, 0.14))
        turn_amp = float(rng.uniform(0.01, 0.03))
        for t in range(40):
            u = np.zeros(6, dtype=np.float64)
            steer = turn_amp * math.sin(t * 0.15)
            u[0] = np.clip(base_fwd - steer, -0.15, 0.15)
            u[1] = np.clip(base_fwd + steer, -0.15, 0.15)
            s, diag = hal.step(u)
            if diag["floor_contacts"] == diag["carl_contacts"]:
                U_list.append(u)
                S_list.append(s)
            else:
                break
                
    U_train = np.array(U_list)
    S_train = np.array(S_list)
    
    dt = 0.030
    fwd_u = 0.5 * (U_train[:-1, 0] + U_train[:-1, 1])
    sonar_rates = -np.diff(S_train[:, :15], axis=0) / dt
    
    corrs = []
    for j in range(15):
        val = (S_train[:-1, j] < 4.5) & (S_train[:-1, j] > 0.35)
        if np.sum(val) > 20:
            c = np.corrcoef(fwd_u[val], sonar_rates[val, j])[0, 1]
            corrs.append(c if not np.isnan(c) else -1.0)
        else:
            corrs.append(-1.0)
            
    best_sonar = int(np.argmax(corrs))
    val_pts = (S_train[:-1, best_sonar] < 4.5) & (S_train[:-1, best_sonar] > 0.35)
    rates_clean = sonar_rates[val_pts, best_sonar]
    fwd_clean = fwd_u[val_pts]
    
    # Filter non-locomoting or transient points
    valid = (rates_clean > 0.01) & (rates_clean < 0.6)
    k_trans_fit = float(np.sum(fwd_clean[valid] * rates_clean[valid]) / (np.sum(fwd_clean[valid]**2) + 1e-9))
    
    # Held-out validation on seed + 9999
    hal_val = CarlStage1HAL(open_space=False)
    rng_val = np.random.RandomState(seed + 9999)
    U_val_list, S_val_list = [], []
    for sweep in range(8):
        hal_val.reset()
        q_addr = int(hal_val.model.joint("spatial_identity").qposadr[0])
        jitter_yaw = float(rng_val.uniform(-math.pi, math.pi))
        hal_val.data.qpos[q_addr + 3] = math.cos(jitter_yaw / 2.0)
        hal_val.data.qpos[q_addr + 6] = math.sin(jitter_yaw / 2.0)
        hal_val.step(np.zeros(6))
        base_fwd = float(rng_val.uniform(0.06, 0.14))
        for t in range(40):
            u = np.zeros(6)
            u[0] = base_fwd
            u[1] = base_fwd
            s, diag = hal_val.step(u)
            if diag["floor_contacts"] == diag["carl_contacts"]:
                U_val_list.append(u)
                S_val_list.append(s)
            else:
                break
                
    U_val = np.array(U_val_list)
    S_val = np.array(S_val_list)
    fwd_val = 0.5 * (U_val[:-1, 0] + U_val[:-1, 1])
    rates_val = -np.diff(S_val[:, best_sonar], axis=0) / dt
    val_valid = (S_val[:-1, best_sonar] < 4.5) & (S_val[:-1, best_sonar] > 0.35) & (rates_val > 0.01) & (rates_val < 0.6)
    
    fwd_v = fwd_val[val_valid]
    rates_v = rates_val[val_valid]
    pred_v = k_trans_fit * fwd_v
    ss_res = float(np.sum((rates_v - pred_v)**2))
    ss_tot = float(np.sum((rates_v - np.mean(rates_v))**2))
    r2_heldout = 1.0 - ss_res / (ss_tot + 1e-9)
    corr_heldout = float(np.corrcoef(rates_v, pred_v)[0, 1]) if len(rates_v) > 2 else 0.0
    
    print(f"Seed {seed}: Discovered Sonar Channel {best_sonar} (corr={corrs[best_sonar]:.3f}) | k_trans={k_trans_fit:.4f} | Held-out R2={r2_heldout:.4f}, corr={corr_heldout:.4f}")
