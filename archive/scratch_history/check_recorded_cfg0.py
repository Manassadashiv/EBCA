import json
with open("evidence/stage3_4_final/stage3_4_raw_trials.json") as f:
    trials = json.load(f)

for t in trials:
    if t["config_id"] == 0 and t["arm"] == "ARM-A":
        print(f"Recorded trial 0: escaped={t['escaped']} coll={t['had_collision']} ticks={t['ticks']}")
        traj = t["trajectory"]
        print("Start:", traj[0])
        print("Tick 20:", traj[min(20, len(traj)-1)])
        print("Tick 50:", traj[min(50, len(traj)-1)])
        print("Tick 100:", traj[min(100, len(traj)-1)])
        print("End:", traj[-1])
        break
