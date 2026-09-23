import sys
import math
from pathlib import Path
import numpy as np

repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
import mujoco

from tests.test_stage3_1_cann_causal_battery import TASK_SPECS, generate_spawn_configs

hal = CarlStage1HAL()
cann = CarlStage2BIntegratedBrain(dt=0.030)
cann.w_rot[20] = 1.0
cann.w_fwd[15] = 1.0
cann.is_developmentally_trained = True

configs = generate_spawn_configs(2001)
cfg = configs[0]

cann.reset_at_birthplace()
spawn_sensors = hal.read_sensors()
initial_res = cann.update_brain(u_executed=np.zeros(6), s_current=spawn_sensors)

init_x = float(initial_res["grid_unwrapped_x"])
init_y = float(initial_res["grid_unwrapped_y"])
init_hd = float(initial_res["hd_decoded_heading"])

print(f"Spawn pos: {cfg['pos']}, Spawn yaw: {math.degrees(cfg['yaw']):.1f} deg")
print(f"CANN initial readout at spawn: x={init_x:.4f} m, y={init_y:.4f} m, hd={math.degrees(init_hd):.1f} deg")

# Compute the offset that ARM-A was adding at t=0
spawn_yaw = cfg["yaw"]
dx_arena_raw = init_x * math.cos(spawn_yaw) - init_y * math.sin(spawn_yaw)
dy_arena_raw = init_x * math.sin(spawn_yaw) + init_y * math.cos(spawn_yaw)
cann_pos_raw = [cfg["pos"][0] + dx_arena_raw, cfg["pos"][1] + dy_arena_raw]
print(f"ARM-A raw cann_pos at t=0: [{cann_pos_raw[0]:.4f}, {cann_pos_raw[1]:.4f}]")
error_dist = math.hypot(cann_pos_raw[0] - cfg["pos"][0], cann_pos_raw[1] - cfg["pos"][1])
print(f"Spurious initial position error in ARM-A: {error_dist:.4f} meters!")
