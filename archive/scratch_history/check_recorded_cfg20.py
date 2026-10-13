import json
with open("evidence/stage3_4_final/stage3_4_raw_trials.json") as f:
    trials = json.load(f)

for t in trials:
    if t["config_id"] == 20 and t["arm"] == "ARM-A":
        print(f"Recorded trial 20: escaped={t['escaped']} coll={t['had_collision']} ticks={t['ticks']}")
        traj = t["trajectory"]
        print("Start:", traj[0])
        print("Tick 20:", traj[min(20, len(traj)-1)])
        print("Tick 40:", traj[min(40, len(traj)-1)])
        print("Tick 60:", traj[min(60, len(traj)-1)])
        print("Tick 80:", traj[min(80, len(traj)-1)])
        print("End:", traj[-1])
        break
