import sys
from pathlib import Path
import numpy as np

repo_root = Path("d:/ebca")
sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

cfg = build_50_matched_configurations()[20]
hal = CarlStage1HAL(xml_path=str(repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction.xml"))
ctrl = CARLActiveInferenceEngine(
    grid_path=str(repo_root / "world" / "stage3_4_environments" / "asymmetric_t_junction_grid.pt"),
    w_info=1.0,
    frontier_mode="macro",
    norm_mode="dimensionless"
)
ctrl.initialize_pose(cfg["spawn_pos"][0], cfg["spawn_pos"][1], cfg["spawn_yaw"])

timings = []
for tick in range(50):
    sensors = hal.read_sensors()
    u, telem = ctrl.select_action(sensors, curr_v=0.0, curr_w=float(sensors[20]))
    st = telem["stage_timings"]
    st["tick"] = tick
    timings.append(st)

# Print ticks where total_cycle_time > 30ms
print("=== TICKS WITH LATENCY > 30ms ===")
for t in timings:
    if t["total_cycle_time"] > 30.0:
        print(f"Tick {t['tick']:2d}: total={t['total_cycle_time']:.1f}ms | occ={t['occupancy_update']:.1f}ms | front={t['frontier_extraction']:.1f}ms | traj={t['trajectory_propagation']:.1f}ms | hull={t['hull_feasibility']:.1f}ms | efe={t['efe_cost_calculation']:.1f}ms")

# Summary of components for ticks >= 1
print("\n=== COMPONENT MEANS (Ticks 1-49) ===")
for k in ["occupancy_update", "frontier_extraction", "trajectory_propagation", "hull_feasibility", "efe_cost_calculation", "softmax_action_synthesis", "total_cycle_time"]:
    vals = [t[k] for t in timings[1:]]
    print(f"{k:<25}: mean={np.mean(vals):.2f}ms, p95={np.percentile(vals, 95):.2f}ms, max={np.max(vals):.2f}ms")
