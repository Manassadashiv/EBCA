import sys
from pathlib import Path
sys.path.insert(0, '.')

from tests.test_stage3_4R3_certification import build_50_matched_configurations, execute_episode
from brain.carl_stage1_hal import CarlStage1HAL

configs = build_50_matched_configurations()
hal1 = CarlStage1HAL(xml_path=configs[0]['xml_path'])
hal2 = CarlStage1HAL(xml_path=configs[20]['xml_path'])

for cid in [1, 16, 25, 34]:
    cfg = configs[cid]
    hal = hal2 if cfg['env_id'] == 2 else hal1
    res = execute_episode('ARM-A', cfg, hal)
    status = 'ESCAPE' if res['escaped'] else ('COLLISION' if res['had_collision'] else 'TIMEOUT')
    eid = cfg['env_id']
    ticks = res['ticks']
    pos = res['final_pos']
    print(f"Cfg {cid} (Env {eid}) -> {status} at tick {ticks}, final pos={pos}")
