"""
scratch/analyze_prediction_errors.py — Dissect Sub-Gate 3.2A Prediction Errors
"""

import json
from pathlib import Path
import numpy as np

p = Path("evidence/stage3_2/raw/stage3_2A_fidelity_data.json")
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

records = data["rollout_records"]

families = {
    "Straight (P01-P04)": ["P01", "P02", "P03", "P04"],
    "Arc Left (P05-P10)": ["P05", "P06", "P07", "P08", "P09", "P10"],
    "Arc Right (P11-P16)": ["P11", "P12", "P13", "P14", "P15", "P16"],
    "Pivots (P17-P19)": ["P17", "P18", "P19"],
    "Reverse (P20-P24)": ["P20", "P21", "P22", "P23", "P24"],
}

print("=========================================================================")
print("SUB-GATE 3.2A PREDICTION ERROR DISSECTION BY COMMAND FAMILY")
print("=========================================================================")

for fam_name, pids in families.items():
    fam_recs = [r for r in records if r["profile_id"] in pids]
    e_term = [r["e_term"] for r in fam_recs]
    rmse = [r["rmse_xy"] for r in fam_recs]
    e_theta = [r["e_theta"] for r in fam_recs]
    e_theta_deg = [np.degrees(r["e_theta"]) for r in fam_recs]
    
    print(f"\n--- {fam_name} (N = {len(fam_recs)}) ---")
    print(f"  Mean Pos Error:      {np.mean(e_term):.4f} m (max: {np.max(e_term):.4f} m)")
    print(f"  Mean Path RMSE:      {np.mean(rmse):.4f} m (max: {np.max(rmse):.4f} m)")
    print(f"  Mean Heading Error:  {np.mean(e_theta):.4f} rad ({np.mean(e_theta_deg):.2f} deg) (max: {np.degrees(np.max(e_theta)):.2f} deg)")

print("\n--- COASTING / MOMENTUM ANALYSIS ---")
print(f"Overall Coasting Decel R^2_v: {data['metrics']['coasting_r2_v']:.4f}")
print("P02 (straight_slow) vs P01 (straight_full) vs P20 (reverse_straight):")
for pid in ["P01", "P02", "P17", "P18", "P19"]:
    recs = [r for r in records if r["profile_id"] == pid]
    p_name = recs[0]["profile_name"]
    mean_eth = np.mean([np.degrees(r["e_theta"]) for r in recs])
    mean_epos = np.mean([r["e_term"] for r in recs])
    print(f"  {pid} ({p_name}): Pos Err = {mean_epos:.4f} m | Heading Err = {mean_eth:.2f} deg")
