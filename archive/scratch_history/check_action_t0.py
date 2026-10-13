import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations
import numpy as np, math

cfgs = build_50_matched_configurations()
cfg = cfgs[20]
hal = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"))
ctrl = CARLActiveInferenceEngine(grid_path=cfg["grid_path"], w_info=1.0)
ctrl.initialize_pose(*cfg["spawn_pos"], cfg["spawn_yaw"])
sensors = hal.read_sensors()
sonars = sensors[:15]
action, telem = ctrl.select_action(sonars, curr_v=0.0, curr_w=0.0)
print("u_target (before slew):", telem.get("u_target", "not saved"))
print("selected_action (after slew):", action)
print("slew delta:", telem.get("slew_delta"))
