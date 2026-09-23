import sys
from pathlib import Path
repo_root = Path('.').resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scratch.optimize_branch_kinematics import eval_params, p_init, branches

loss, passes, r2s, margins = eval_params(p_init)
print(f"Total passes: {passes}/20, loss={loss:.4f}")
for i in range(len(branches)):
    b_pass = (r2s[i] >= 0.50 and margins[i] >= 0.30)
    print(f"Branch {i:02d} ({branches[i]['name']:<20s}): R2={r2s[i]:.4f}, Margin={margins[i]:.4f}, Pass={b_pass}")
