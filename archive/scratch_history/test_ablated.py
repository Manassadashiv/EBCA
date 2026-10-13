import sys
sys.path.insert(0, ".")
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, execute_physical_episode, CarlStage1HAL

hal = CarlStage1HAL(xml_path=str(XML_PATH))
cfgs = generate_matched_configs(5, seed=6001)
for i, c in enumerate(cfgs):
    res = execute_physical_episode(c, hal, physarum_enabled=False, synergies_enabled=True)
    print(f"Ablated Ep {i+1}: Esc={res['escaped']} | Col={res['had_collision']} | Revisits={res['dead_end_revisits']} | Ticks={res['ticks']}")
