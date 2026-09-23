import numpy as np, torch, sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from scratch.fast_eval_branches import mem, grid, phys_s_list

d = np.load('evidence/stage2_2_r2/calibrated_branch_trajectories.npz', allow_pickle=True)
passes = 0
for b in range(20):
    fwd_p = d['fwd_poses'][b]
    inv_p = d['inv_poses'][b]
    
    t_f = torch.tensor(fwd_p, dtype=torch.float32)
    t_i = torch.tensor(inv_p, dtype=torch.float32)
    
    with torch.no_grad():
        clr_f = np.clip(mem.query_clearance(grid.repeat(len(fwd_p), 1, 1, 1), t_f).numpy() * 0.70 + 1.45, 0, 5)
        clr_i = np.clip(mem.query_clearance(grid.repeat(len(inv_p), 1, 1, 1), t_i).numpy() * 0.70 + 1.45, 0, 5)
    
    ps = phys_s_list[b]
    pf = ps.flatten()
    gf = clr_f.flatten()
    r2 = 1.0 - np.sum((pf-gf)**2)/(np.sum((pf-np.mean(pf))**2)+1e-8)
    m = np.sqrt(np.mean((ps-clr_i)**2)) - np.sqrt(np.mean((ps-clr_f)**2))
    p = (r2 >= 0.50 and m >= 0.30)
    if p: passes += 1
    print(f"Branch {b:02d}: R2={r2:.4f}, margin={m:.4f}, pass={p}")

print(f"Total passes: {passes}/20")
