import json
with open('C:/Users/MANAS/.gemini/antigravity-ide/brain/1d6c0136-2579-4735-9f74-30a0f23ea678/.system_generated/logs/transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx is not None and 11100 <= idx <= 11116:
            print(f"STEP {idx}: {obj.get('type')}")
            if 'tool_calls' in obj:
                for tc in obj['tool_calls']:
                    print(f"  CALL: {tc['name']}")
                    if tc['name'] == 'write_to_file':
                        print(f"    TargetFile: {tc['args'].get('TargetFile')}")
                        desc = tc['args'].get('Description', '')
                        print(f"    Desc: {desc}")
