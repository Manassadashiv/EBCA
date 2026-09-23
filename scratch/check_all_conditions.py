import json

with open("d:/ebca/evidence/stage2_1b_r3/translational_scorecard.json") as f:
    sc = json.load(f)

for c_name, c_data in sc.items():
    unseen_passes_recs = sum(1 for r in c_data["records"] if r["partition"] == "UNSEEN" and r["pass_gate"])
    all_passes_recs = sum(1 for r in c_data["records"] if r["pass_gate"])
    unseen_drifts = [r["final_drift_m"] for r in c_data["records"] if r["partition"] == "UNSEEN"]
    print(f"\n{c_name}:")
    print(f"  Unseen drifts: {unseen_drifts}")
    print(f"  Stored unseen_passes: {c_data.get('unseen_passes')} | Sum of record booleans: {unseen_passes_recs}/5")
    print(f"  Stored all_passes:    {c_data.get('all_passes')} | Sum of record booleans: {all_passes_recs}/8")
    for r in c_data["records"]:
        if r["partition"] == "UNSEEN":
            print(f"    Seed {r['seed']}: drift={r['final_drift_m']:.3f}, pass_gate={r['pass_gate']}")
