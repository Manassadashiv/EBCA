import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, execute_physical_episode

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)

res_list = [execute_physical_episode(cfg, hal, floor_friction=0.20, torque_loss_side='none', endocrine_enabled=True) for cfg in cfgs]
esc = sum(1 for r in res_list if r['escaped'])
coll = sum(1 for r in res_list if r['had_collision'])
print(f"Gate 1 Final Evaluation: Escapes: {esc}/30 ({esc/30*100:.1f}%), Collisions: {coll}/30 ({coll/30*100:.1f}%)")
