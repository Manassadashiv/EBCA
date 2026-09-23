import numpy as np, sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scratch.fast_eval_branches import phys_s_list

d = np.load('evidence/stage2_2_r2/air_gapped_mental_rollouts.npz', allow_pickle=True)
passes = 0
for b in range(20):
    ps = phys_s_list[b]
    pf = ps.flatten()
    mr = d['mental_rollouts'][b]
    imr = d['inv_mental_rollouts'][b]
    r2 = 1.0 - np.sum((pf - mr.flatten())**2) / (np.sum((pf - np.mean(pf))**2) + 1e-8)
    m = np.sqrt(np.mean((ps - imr)**2)) - np.sqrt(np.mean((ps - mr)**2))
    p = (r2 >= 0.50 and m >= 0.30)
    if p: passes += 1
    print(f"Branch {b:02d}: R2={r2:.4f}, margin={m:.4f}, pass={p}")

print(f"Total passes: {passes}/20")
