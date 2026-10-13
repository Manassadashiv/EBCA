import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, execute_physical_episode
)

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs = generate_matched_configs(num_configs=20, seed=5301)

# Check Pair 13 (right loss) and Pair 17 (right loss)
for idx in [13, 17]:
    cfg = configs[idx]
    r_int = execute_physical_episode(cfg, hal, 0.20, "right", True)
    r_abl = execute_physical_episode(cfg, hal, 0.20, "right", False)
    print(f"Ep {idx}: Intact={'ESC' if r_int['escaped'] else 'NO'} (ticks={r_int['total_ticks']}, coll={r_int['had_collision']}) | Abl={'ESC' if r_abl['escaped'] else 'NO'} (ticks={r_abl['total_ticks']}, coll={r_abl['had_collision']})")
