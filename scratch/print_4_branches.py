import json
b = json.load(open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json'))
for i in [5, 7, 11, 15]:
    u_L = [round(x[0], 2) for x in b[i]['actions']]
    u_R = [round(x[1], 2) for x in b[i]['actions']]
    u_f = [round(0.5*(x[0]+x[1]), 2) for x in b[i]['actions']]
    u_d = [round(x[1]-x[0], 2) for x in b[i]['actions']]
    print(f"\nBranch {i:02d} ({b[i]['name']}): H={len(b[i]['actions'])}")
    print(f"u_fwd:  {u_f}")
    print(f"u_diff: {u_d}")
