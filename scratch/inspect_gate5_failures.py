import sys
import json
import math
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

# Load DEV_VAL
d_val = np.load('evidence/stage2_2_diag/datasets/DEV_VAL.npz')
G_val = d_val['G_grid']
V_val = d_val['V_hd']

with open('evidence/stage2_2_r2/manifests/frozen_tripartite_evaluation_pairs.json') as f:
    pairs = json.load(f)

from scratch.eval_clean_gate5 import errors_cons, errors_swap

print(f"Total pairs: {len(pairs)}")
dists = []
for k, p in enumerate(pairs):
    ep1, t1 = p['ep1'], p['t1']
    ep2, t2 = p['ep2'], p['t2']
    x1, y1 = G_val[ep1, t1]
    x2, y2 = G_val[ep2, t2]
    d = math.sqrt((x1-x2)**2 + (y1-y2)**2)
    dists.append(d)
    is_attracted = (errors_cons[k] < errors_swap[k])
    if not is_attracted:
        print(f"Failed Pair {k:2d}: ep1={ep1}, ep2={ep2} | dist={d:.3f}m | err_cons={errors_cons[k]:.3f}, err_swap={errors_swap[k]:.3f}, diff={errors_swap[k]-errors_cons[k]:.3f}")

print("\nDistance summary for attracted vs non-attracted:")
att = [dists[k] for k in range(len(pairs)) if errors_cons[k] < errors_swap[k]]
non_att = [dists[k] for k in range(len(pairs)) if errors_cons[k] >= errors_swap[k]]
print(f"Attracted (N={len(att)}): mean dist = {np.mean(att):.3f}m, min dist = {np.min(att):.3f}m")
print(f"Non-attracted (N={len(non_att)}): mean dist = {np.mean(non_att):.3f}m, min dist = {np.min(non_att):.3f}m")
