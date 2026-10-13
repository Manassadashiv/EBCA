import json
with open("evidence/stage3_4_final/stage3_4_raw_trials.json") as f:
    trials = json.load(f)

for t in trials:
    if t["config_id"] == 20 and t["arm"] == "ARM-A":
        for k in ["u_star", "action", "selected_action"]:
            if k in t:
                print(k, t[k][:5])
        # If not saved per step, let's see keys
        print("Keys in trial:", list(t.keys()))
        break
