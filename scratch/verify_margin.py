import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))

with open("scratch/test_k_fwd_margin.py") as f:
    code1 = f.read()

# Let's run test_k_fwd_margin directly for branches 18 and 19
from scratch.test_k_fwd_margin import eval_k_fwd
eval_k_fwd(0.0280, 7.0)
