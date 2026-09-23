import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
import numpy as np

from scratch.fast_eval_branches import true_poses_list, branches, unroll_poses_param

params = [0.0280, 0.71, 14.5, 6.0, 15.0, 7.4, 0.38, 4.0, 2.0]

for idx in [5, 7, 11, 15]:
    b = branches[idx]
    actions = b['actions']
    true_p = np.array(true_poses_list[idx])
    pred_p = np.array(unroll_poses_param(actions, params))
    
    print(f"\n================ BRANCH {idx:02d}: {b['name']} ================")
    print(f"Num steps: {len(actions)}")
    
    # compare positions and yaw
    err_pos = np.linalg.norm(true_p[:, :2] - pred_p[:, :2], axis=1)
    err_yaw = np.abs(np.unwrap(true_p[:, 2]) - np.unwrap(pred_p[:, 2]))
    
    print(f"Max pos error: {np.max(err_pos):.4f} m, Mean pos error: {np.mean(err_pos):.4f} m")
    print(f"Max yaw error: {np.degrees(np.max(err_yaw)):.2f} deg, Mean yaw error: {np.degrees(np.mean(err_yaw)):.2f} deg")
    
    # Check start and end
    print(f"Start pos: true={true_p[0, :2]}, pred={pred_p[0, :2]}")
    print(f"End pos:   true={true_p[-1, :2]}, pred={pred_p[-1, :2]}")
    print(f"End yaw:   true={np.degrees(true_p[-1, 2]):.1f} deg, pred={np.degrees(pred_p[-1, 2]):.1f} deg")
    
    # Let's inspect step by step
    print("Step-by-step preview (step, action, true_pos, pred_pos, true_yaw, pred_yaw):")
    for s in range(0, len(actions), max(1, len(actions)//5)):
        u = actions[s]
        print(f"  step {s:2d}: u=({u[0]:.2f}, {u[1]:.2f}) | true=({true_p[s,0]:.2f}, {true_p[s,1]:.2f}, {np.degrees(true_p[s,2]):.0f}°) pred=({pred_p[s,0]:.2f}, {pred_p[s,1]:.2f}, {np.degrees(pred_p[s,2]):.0f}°)")
    print(f"  final:   true=({true_p[-1,0]:.2f}, {true_p[-1,1]:.2f}, {np.degrees(true_p[-1,2]):.0f}°) pred=({pred_p[-1,0]:.2f}, {pred_p[-1,1]:.2f}, {np.degrees(pred_p[-1,2]):.0f}°)")
