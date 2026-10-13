import sys
from pathlib import Path
repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from tests.run_stage3_5_complete_battery import (
    generate_matched_configs, CarlStage1HAL, XML_PATH, CarlAutonomousOrganismAgent, GRID_PATH
)
import math, mujoco, numpy as np

# Modify method in CarlActiveInferenceEngine
from brain.carl_active_inference import CARLActiveInferenceEngine

old_eval = CARLActiveInferenceEngine._evaluate_expected_free_energy

def patched_eval(self, poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, curr_sensors, cann_state=None, margin_scale=1.0):
    g_total, debug_info = old_eval(self, poses_x, poses_y, poses_th, u_batch, c_x, c_y, c_th, curr_sensors, cann_state, margin_scale)
    return g_total, debug_info

hal = CarlStage1HAL(xml_path=str(XML_PATH), headless=True)
configs = generate_matched_configs(num_configs=20, seed=5201)

print("Testing with longitudinal corridor heading patch:")
# Let's test the patch directly in carl_active_inference by testing Ep 1, 2, 6, 8, 11, 15
