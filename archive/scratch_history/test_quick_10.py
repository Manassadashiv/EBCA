import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.test_stage3_4R3_certification import build_50_matched_configurations
from tests.test_stage3_4_2_smoothness_and_suspension import execute_smooth_episode

configs = build_50_matched_configurations()
hal_env1 = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"))
hal_env2 = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"))

escapes = 0
collisions = 0
for i in range(10):
    cfg = configs[i]
    hal = hal_env1 if cfg["env_id"] == 1 else hal_env2
    r = execute_smooth_episode(cfg, hal)
    status = "ESCAPE" if r["escaped"] else ("COLLISION" if r["had_collision"] else "TRAPPED")
    if r["escaped"]: escapes += 1
    if r["had_collision"]: collisions += 1
    print(f"Cfg {i:02d} (Env {cfg['env_id']}): {status} ticks={r['ticks']} max_jump={r['max_step_jump']:.4f} p95_lat={r['p95_latency_ms']:.2f}ms")

print(f"Summary: Escapes={escapes}/10, Collisions={collisions}/10")
