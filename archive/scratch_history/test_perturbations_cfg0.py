import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import execute_physical_episode, generate_matched_configs, CarlStage1HAL, XML_PATH

hal = CarlStage1HAL(xml_path=str(XML_PATH))
cfg = generate_matched_configs(1)[0]

print("--- TESTING GATE 1: Low Friction mu=0.20 ---")
res_mu = execute_physical_episode(cfg, hal, floor_friction=0.20, torque_loss_side="none", endocrine_enabled=True)
print(f"mu=0.20 -> escaped={res_mu['escaped']}, had_collision={res_mu['had_collision']}, ticks={res_mu['total_ticks']}")

print("\n--- TESTING GATE 2: 40% Left Motor Torque Loss ---")
res_torque = execute_physical_episode(cfg, hal, floor_friction=1.0, torque_loss_side="left", endocrine_enabled=True)
print(f"Torque Loss -> escaped={res_torque['escaped']}, had_collision={res_torque['had_collision']}, ticks={res_torque['total_ticks']}")

print("\n--- TESTING GATE 3: Endocrine Ablation on mu=0.20 ---")
res_abl = execute_physical_episode(cfg, hal, floor_friction=0.20, torque_loss_side="none", endocrine_enabled=False)
print(f"Endocrine Ablated -> escaped={res_abl['escaped']}, had_collision={res_abl['had_collision']}, ticks={res_abl['total_ticks']}")
