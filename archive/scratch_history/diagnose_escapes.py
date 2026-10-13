import sys
sys.path.insert(0, ".")
from tests.run_stage3_5_complete_battery import generate_matched_configs, CarlStage1HAL, execute_physical_episode

hal = CarlStage1HAL(xml_path='world/stage3_4_environments/cul_de_sac_turning_bay.xml')
cfgs = generate_matched_configs(30, seed=5101)

for idx, cfg in enumerate(cfgs):
    res = execute_physical_episode(cfg, hal, floor_friction=0.20, torque_loss_side='none', endocrine_enabled=True)
    status = "ESCAPED" if res["escaped"] else ("COLLIDED" if res["had_collision"] else "TIMEOUT")
    print(f"Ep {idx:2d}: {status:8s} | ticks={res['total_ticks']:3d} | final_pos=({res['final_pose'][0]:.2f}, {res['final_pose'][1]:.2f}) | final_th={res['final_pose'][2]:.2f}", flush=True)
