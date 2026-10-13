import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.test_stage3_4R3_certification import build_50_matched_configurations
from tests.test_stage3_4_2_smoothness_and_suspension import execute_smooth_episode
import tests.test_stage3_4_2_smoothness_and_suspension as test_mod

configs = build_50_matched_configurations()
hal_env2 = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"))

test_mod.MAX_TICKS = 280
escapes = 0
for cfg_id in range(20, 30):
    cfg = configs[cfg_id]
    r = execute_smooth_episode(cfg, hal_env2)
    status = "ESCAPE" if r["escaped"] else ("COLLISION" if r["had_collision"] else "TRAPPED")
    if r["escaped"]: escapes += 1
    print(f"Cfg {cfg_id} (Env 2, 280 tk): {status} | ticks={r['ticks']} | jump={r['max_step_jump']:.4f}")

print(f"Escapes in Configs 20-29: {escapes}/10")
