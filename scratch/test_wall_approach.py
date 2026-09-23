import sys
import numpy as np
import math

sys.path.insert(0, ".")

from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=False)

for seed in [42, 101, 202]:
    rng = np.random.RandomState(seed)
    U_list = []
    S_list = []
    
    # 8 exploratory approach sweeps towards perimeter walls
    for sweep in range(8):
        hal.reset()
        # Place robot at distance 2.0m from North wall, facing North (yaw = pi/2)
        q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
        hal.data.qpos[q_addr] = rng.uniform(-1.0, 1.0)
        hal.data.qpos[q_addr + 1] = 2.0  # North wall is at y = 5.0
        hal.data.qpos[q_addr + 2] = 0.05291
        
        # Heading roughly towards north wall (+/- 15 deg)
        yaw = math.pi / 2.0 + rng.uniform(-0.25, 0.25)
        hal.data.qpos[q_addr + 3] = math.cos(yaw / 2.0)
        hal.data.qpos[q_addr + 6] = math.sin(yaw / 2.0)
        hal.step(np.zeros(6))
        
        fwd_speed = rng.uniform(0.06, 0.14)
        for t in range(30):
            u = np.zeros(6)
            u[0] = fwd_speed + rng.normal(0, 0.005)
            u[1] = fwd_speed + rng.normal(0, 0.005)
            s, diag = hal.step(u)
            if s[7] > 0.4:
                U_list.append(u)
                S_list.append(s)
            else:
                break
                
    U_arr = np.array(U_list)
    S_arr = np.array(S_list)
    dt = 0.030
    fwd_u = 0.5 * (U_arr[:-1, 0] + U_arr[:-1, 1])
    sonar_rates = -np.diff(S_arr[:, :15], axis=0) / dt
    
    corrs = [np.corrcoef(fwd_u, sonar_rates[:, j])[0, 1] for j in range(15)]
    best_ch = int(np.argmax(corrs))
    k_trans_fit = float(np.sum(fwd_u * sonar_rates[:, best_ch]) / (np.sum(fwd_u**2) + 1e-9))
    
    print(f"Seed {seed}: Best Sonar Channel={best_ch} (corr={corrs[best_ch]:.3f}) | k_trans={k_trans_fit:.4f}")
