import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import phys_s_list, branches, unroll_poses_param, batch_eval

loss, passes, r2s, margins = batch_eval([0.0280, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0])
print(f"Batch eval Branch 11: R2={r2s[11]:.4f}, Margin={margins[11]:.4f}")
