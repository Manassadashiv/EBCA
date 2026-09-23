import json
with open("evidence/stage2_2_r2/manifests/frozen_branch_sequences.json") as f:
    branches = json.load(f)

b7 = branches[7]
print("Branch 07 actions:")
for s, a in enumerate(b7['actions']):
    print(f"step {s:2d}: u0={a[0]:.3f}, u1={a[1]:.3f}, u_fwd={0.5*(a[0]+a[1]):.3f}, u_diff={a[1]-a[0]:.3f}")
