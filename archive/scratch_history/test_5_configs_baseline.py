import sys
sys.path.insert(0, ".")
import math
import time
from tests.run_stage3_6_complete_battery import generate_matched_configs, execute_physical_episode, XML_PATH, CarlStage1HAL

configs = generate_matched_configs(5, seed=6001)
hal = CarlStage1HAL(xml_path=str(XML_PATH))

print("=== BASELINE TEST: PHYSARUM & SYNERGIES DISABLED (STAGE 3.5 MODE) ===")
for cfg in configs:
    t0 = time.perf_counter()
    res = execute_physical_episode(cfg, hal, physarum_enabled=False, synergies_enabled=False)
    t_ep = time.perf_counter() - t0
    print(f"Config {cfg['config_id']}: Escaped={res['escaped']}, Collision={res['had_collision']}, MaxPitch={res['max_pitch_rad']:.3f}, Ticks={res['ticks']}, Time={t_ep:.2f}s")
