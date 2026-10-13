import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, XML_PATH, execute_physical_episode

hal = CarlStage1HAL(xml_path=str(XML_PATH))
cfgs = generate_matched_configs(5, seed=5301)

intact_escapes = 0
ablation_escapes = 0

for i, cfg in enumerate(cfgs):
    r_int = execute_physical_episode(cfg, hal, floor_friction=0.20, endocrine_enabled=True)
    r_abl = execute_physical_episode(cfg, hal, floor_friction=0.20, endocrine_enabled=False)
    print(f"Cfg {i:2d}: Intact: esc={r_int['escaped']} ticks={r_int['total_ticks']} | Ablated: esc={r_abl['escaped']} ticks={r_abl['total_ticks']}")
    if r_int['escaped']: intact_escapes += 1
    if r_abl['escaped']: ablation_escapes += 1

print(f"Summary: Intact: {intact_escapes}/5 | Ablated: {ablation_escapes}/5")
