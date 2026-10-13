import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, execute_physical_episode
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)
for idx, cfg in enumerate(cfgs):
    res = execute_physical_episode(cfg, hal, floor_friction=0.20, torque_loss_side='none', endocrine_enabled=True)
    if res['had_collision'] or not res['escaped']:
        print(f"Ep {idx}: escaped={res['escaped']}, coll={res['had_collision']} (tick={res['collision_tick']}), ticks={res['total_ticks']}", flush=True)
    else:
        print(f"Ep {idx}: SUCCESS ({res['total_ticks']} ticks)", flush=True)
