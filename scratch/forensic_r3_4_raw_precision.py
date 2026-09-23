import os
import sys
import json
import math
import numpy as np

TELEMETRY_JSON = "d:/ebca/evidence/stage2_1b_r3/translational_grounding_telemetry.json"
SCORECARD_JSON = "d:/ebca/evidence/stage2_1b_r3/translational_scorecard.json"

with open(TELEMETRY_JSON, "r") as f:
    telem = json.load(f)

cond_a = telem["Condition A (Learned Translational Self-Model)"]

print("=" * 80)
print("FORENSIC R3.4: RAW UNROUNDED FLOATING-POINT AUDIT")
print("=" * 80)

for rec in cond_a:
    seed = rec["seed"]
    part = rec["partition"]
    
    # Trajectory points
    traj_gt = rec["telemetry"]["traj_gt"]
    traj_dec = rec["telemetry"]["traj_dec"]
    speeds_phys = rec["telemetry"]["speeds_phys"]
    speeds_est = rec["telemetry"]["speeds_est"]
    
    # Wander end (tick 349)
    w_gt = traj_gt[349]
    w_dec = traj_dec[349]
    
    # Compute wander travel distance
    # 1. Path length (integral of speed)
    dt = 0.030
    path_phys = sum(speeds_phys[:350]) * dt
    path_est = sum(speeds_est[:350]) * dt
    
    # 2. Euclidean displacement from birthplace at wander end
    disp_phys = math.sqrt(w_gt[0]**2 + w_gt[1]**2)
    disp_int = math.sqrt(w_dec[0]**2 + w_dec[1]**2)
    disp_err = disp_int - disp_phys
    
    # Final endpoint (homing end)
    f_gt = traj_gt[-1]
    f_dec = traj_dec[-1]
    raw_final_drift = math.sqrt(f_gt[0]**2 + f_gt[1]**2)
    
    # Error vector relative to return path
    # Wander end vector from origin: (w_gt[0], w_gt[1])
    # Final pos vector from origin: (f_gt[0], f_gt[1])
    dot_return = (f_gt[0] * w_gt[0] + f_gt[1] * w_gt[1]) / (disp_phys**2 + 1e-12)
    along_path_err = dot_return * disp_phys
    cross_track_err = abs(f_gt[0] * w_gt[1] - f_gt[1] * w_gt[0]) / (disp_phys + 1e-12)
    
    strict_pass = raw_final_drift <= 0.220000000000
    
    print(f"\nSEED {seed:3d} ({part}):")
    print(f"  Stored final_drift_m:     {rec['final_drift_m']:.6f} m")
    print(f"  Raw Recomputed Drift:     {raw_final_drift:.12f} m")
    print(f"  Stored pass_gate boolean: {rec['pass_gate']}")
    print(f"  Strict raw <= 0.220000:   {strict_pass} (delta: {raw_final_drift - 0.22:+.8f} m)")
    print(f"  Wander End Phys Disp:     {disp_phys:.6f} m")
    print(f"  Wander End Int Disp:      {disp_int:.6f} m")
    print(f"  Wander Disp Discrepancy:  {disp_err:+.6f} m ({disp_err*100.0:+.2f} cm, ratio={disp_int/disp_phys:.4f})")
    print(f"  Wander Phys Path Length:  {path_phys:.6f} m | Int Path Length: {path_est:.6f} m (diff={path_est-path_phys:+.4f} m)")
    print(f"  Homing Error Decomposition:")
    print(f"    Along-Path (Stopping):  {along_path_err:+.6f} m ({'STOPPED SHORT' if along_path_err > 0 else 'OVERSHOT'})")
    print(f"    Cross-Track (Lateral):  {cross_track_err:.6f} m")
    print(f"    Total Drift:            {math.sqrt(along_path_err**2 + cross_track_err**2):.6f} m")
