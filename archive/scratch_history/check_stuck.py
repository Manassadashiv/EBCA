import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from tests.test_stage3_4R3_certification import build_50_matched_configurations
from tests.run_stage3_4_final_200_battery import execute_episode
import tests.run_stage3_4_final_200_battery as battery_mod

cfgs = build_50_matched_configurations()
cfg0 = cfgs[0]
hal = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"))
battery_mod.MAX_TICKS = 300
r = execute_episode("ARM-A", cfg0, hal)
traj = r["trajectory"]
for t in range(100, len(traj), 20):
    print(f"Tick {t}: pos={traj[t]}")
