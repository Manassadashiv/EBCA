import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, execute_physical_episode
)
import scipy.stats as stats

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs = generate_matched_configs(num_configs=6, seed=5301)

for mu in [0.10, 0.15, 0.20]:
    int_c = 0; abl_c = 0
    for idx in range(6):
        r_int = execute_physical_episode(configs[idx], hal, mu, "left", True)
        r_abl = execute_physical_episode(configs[idx], hal, mu, "left", False)
        if r_int["escaped"]: int_c += 1
        if r_abl["escaped"]: abl_c += 1
    print(f"mu={mu:.2f}: Intact={int_c}/6, Ablated={abl_c}/6")
