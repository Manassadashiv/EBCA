import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\MANAS\.gemini\antigravity-ide\brain\43da643e-f6aa-42b1-a32a-a452535d1eb4\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
with open(r'C:\Users\MANAS\.gemini\antigravity-ide\brain\43da643e-f6aa-42b1-a32a-a452535d1eb4\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx > 554 and obj.get('type') == 'PLANNER_RESPONSE' and obj.get('content'):
            print(f"Step {idx}: {obj.get('content')[:300]}...\n")
