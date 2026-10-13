import sys
sys.path.insert(0, ".")
import math
import time
from tests.run_stage3_6_complete_battery import generate_matched_configs, execute_physical_episode, XML_PATH, CarlStage1HAL
from brain.carl_physarum import CarlPhysarumRoutingEngine

# Apply the downsampling fix to CarlPhysarumRoutingEngine class
def fixed_update_occupancy(self, occ_grid_128, thresh=0.35):
    if occ_grid_128.ndim == 3:
        occ = occ_grid_128[0]
    else:
        occ = occ_grid_128
    factor = occ.shape[0] // self.grid_dim
    down = occ.reshape(self.grid_dim, factor, self.grid_dim, factor).mean(axis=(1, 3))
    self.obstacle_mask = down > thresh

CarlPhysarumRoutingEngine.update_occupancy = fixed_update_occupancy

configs = generate_matched_configs(5, seed=6001)
hal = CarlStage1HAL(xml_path=str(XML_PATH))

print("=== TESTING 5 CONFIGS WITH EXECUTE_PHYSICAL_EPISODE ===")
for cfg in configs:
    t0 = time.perf_counter()
    res = execute_physical_episode(cfg, hal, physarum_enabled=True, synergies_enabled=True)
    t_ep = time.perf_counter() - t0
    print(f"Config {cfg['config_id']}: Escaped={res['escaped']}, Collision={res['had_collision']}, MaxPitch={res['max_pitch_rad']:.3f}, Ticks={res['ticks']}, Time={t_ep:.2f}s")
