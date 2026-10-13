import json
with open("evidence/stage3_4_final/stage3_4_raw_trials.json") as f:
    trials = json.load(f)
for t in trials:
    if t.get("arm") == "ARM-A" and t.get("env_id") == 1:
        print(f"Cfg {t['config_id']:02d}: escaped={t['escaped']} coll={t['had_collision']} ticks={t['ticks']}")
