import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, execute_physical_episode
)

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs_g2 = generate_matched_configs(num_configs=20, seed=5201)

for idx, cfg in enumerate(configs_g2):
    side = "left" if idx % 2 == 0 else "right"
    res = execute_physical_episode(
        config=cfg,
        hal=hal,
        floor_friction=1.0,
        torque_loss_side=side,
        endocrine_enabled=True
    )
    status = "ESCAPED" if res["escaped"] else ("COLLIDED" if res["had_collision"] else "TIMEOUT")
    print(f"Ep {idx:2d} ({side:5s}): {status:8s} ticks={res['total_ticks']:3d} final_pose={res['final_pose']}")
