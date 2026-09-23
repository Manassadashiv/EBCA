import sys
import numpy as np
import math

sys.path.insert(0, ".")

from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=False)

for seed in [42, 101, 202]:
    rng = np.random.RandomState(seed)
    fwd_cmds_all = []
    rates_all = []
    
    # 8 exploratory approach sweeps towards perimeter walls
    for sweep in range(8):
        hal.reset()
        q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[q_addr] = float(rng.uniform(-1.0, 1.0))
        hal.data.qpos[q_addr + 1] = 2.0  # North wall is at y = 5.0
        hal.data.qpos[q_addr + 2] = 0.05291
        
        yaw = math.pi / 2.0 + float(rng.uniform(-0.15, 0.15))
        hal.data.qpos[q_addr + 3] = math.cos(yaw / 2.0)
        hal.data.qpos[q_addr + 6] = math.sin(yaw / 2.0)
        hal.step(np.zeros(6))
        
        sweep_u = []
        sweep_s = []
        fwd_speed = float(rng.uniform(0.06, 0.14))
        for t in range(30):
            u = np.zeros(6)
            u[0] = fwd_speed + rng.normal(0, 0.003)
            u[1] = fwd_speed + rng.normal(0, 0.003)
            s, diag = hal.step(u)
            if s[7] > 0.4:
                sweep_u.append(u)
                sweep_s.append(s)
            else:
                break
                
        if len(sweep_u) > 5:
            U_sw = np.array(sweep_u)
            S_sw = np.array(sweep_s)
            fwd_sw = 0.5 * (U_sw[:-1, 0] + U_sw[:-1, 1])
            rate_sw = -np.diff(S_sw[:, :15], axis=0) / hal.dt
            fwd_cmds_all.append(fwd_sw)
            rates_all.append(rate_sw)
            
    all_fwd = np.concatenate(fwd_cmds_all)
    all_rates = np.concatenate(rates_all, axis=0)
    
    corrs = [np.corrcoef(all_fwd, all_rates[:, j])[0, 1] for j in range(15)]
    best_ch = int(np.argmax(corrs))
    k_trans_fit = float(np.sum(all_fwd * all_rates[:, best_ch]) / (np.sum(all_fwd**2) + 1e-9))
    
    print(f"Seed {seed}: Discovered Channel={best_ch} (corr={corrs[best_ch]:.4f}) | k_trans={k_trans_fit:.4f}")
