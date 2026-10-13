import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.test_stage3_4R3_certification import build_50_matched_configurations
from tests.run_stage3_4_final_200_battery import execute_episode

configs = build_50_matched_configurations()
hal_env1 = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"))
hal_env2 = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"))

escapes = 0
collisions = 0
for i, cfg in enumerate(configs):
    hal = hal_env1 if cfg["env_id"] == 1 else hal_env2
    r = execute_episode("ARM-A", cfg, hal)
    status = "ESCAPE" if r["escaped"] else ("COLLISION" if r["had_collision"] else "TRAPPED")
    if r["escaped"]: escapes += 1
    if r["had_collision"]: collisions += 1
    print(f"[{i+1:02d}/50] Cfg {cfg['config_id']:02d} (Env {cfg['env_id']}): {status} | ticks={r['ticks']}", flush=True)

print(f"\nARM-A 50-EPISODE RESULT: Escapes={escapes}/50 ({escapes/50*100:.1f}%), Collisions={collisions}/50 ({collisions/50*100:.1f}%)", flush=True)
