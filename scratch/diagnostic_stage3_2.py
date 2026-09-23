import json

with open("evidence/stage3_2/raw/stage3_2_raw_trials.json") as f:
    trials = json.load(f)

for t in trials:
    for arm in ["ARM-I", "ARM-A"]:
        if t["arms"][arm]["success"]:
            print("Success:", t["pair_id"], t["family"], t["condition"], arm, "ticks:", t["arms"][arm]["ticks_survived"], "dist:", round(t["arms"][arm]["distance_m"], 3))
