import json
with open("evidence/stage3_4_final/stage3_4_raw_trials.json") as f:
    trials = json.load(f)

for t in trials:
    if t["config_id"] == 20 and t["arm"] == "ARM-A":
        traj = t["trajectory"]
        for i in range(0, min(45, len(traj)), 5):
            print(f"t={i:03d} pos=({traj[i][0]:.3f},{traj[i][1]:.3f})")
        break
