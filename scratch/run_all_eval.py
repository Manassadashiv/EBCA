import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import batch_eval, branches

params = [0.0280, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]
loss, passes, r2s, margins = batch_eval(params)

print(f"Total Passes: {passes}/20")
for i in range(20):
    b_pass = (r2s[i] >= 0.50 and margins[i] >= 0.30)
    mark = "PASS" if b_pass else "FAIL"
    print(f"Branch {i:02d} ({branches[i]['name']:<20s}): R2={r2s[i]:.4f}, Margin={margins[i]:.4f} -> {mark}")
