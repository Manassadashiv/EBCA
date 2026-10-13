import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.test_stage3_4R3_certification import build_50_matched_configurations
from tests.run_stage3_4_final_200_battery import execute_episode

cfgs = build_50_matched_configurations()
hal = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"))

for i in range(5):
    r = execute_episode("ARM-A", cfgs[i], hal)
    print(f"Cfg {i}: escaped={r['escaped']} coll={r['had_collision']} ticks={r['ticks']}")
