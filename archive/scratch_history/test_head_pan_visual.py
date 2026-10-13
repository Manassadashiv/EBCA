import sys
import time
from pathlib import Path
import numpy as np

REPO_ROOT = Path("d:/ebca")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent

import math
import mujoco

hal = CarlStage1HAL(xml_path=str(REPO_ROOT / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay.xml"))
hal.reset()

spawn_x = 0.619341571228017
spawn_y = -0.023883884898782876
spawn_yaw = -1.3905515087029836

qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [spawn_x, spawn_y]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(
    dt=hal.dt,
    deliberation_mode="active_inference",
    grid_path=str(REPO_ROOT / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt")
)
agent.initialize_spatial_grounding(spawn_x, spawn_y, spawn_yaw, grid_path=str(REPO_ROOT / "world" / "stage3_4_environments" / "cul_de_sac_turning_bay_grid.pt"))

print("Running full episode test until escape or 350 ticks...")
latencies = []
escaped = False
had_collision = False

for t in range(350):
    t0 = time.perf_counter()
    res = agent.step_cognitive_cycle(hal)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    latencies.append(dt_ms)
    
    u_6d = res["action_cmd"]
    s_next, diag = hal.step(u_6d)
    
    if 25 <= t <= 55:
        telem = res.get("vision_telemetry")
        sonars = s_next[:15]
        print(f"Tick {t:03d}: pos=({diag['pos_x']:.2f}, {diag['pos_y']:.2f}), yaw={diag['yaw']:.2f}, u=({u_6d[0]:.2f}, {u_6d[1]:.2f}), fwd_sonar={np.min(sonars[6:9]):.2f}, l_sonar={sonars[12]:.2f}, r_sonar={sonars[2]:.2f}")
    elif t % 25 == 0:
        telem = res.get("vision_telemetry")
        print(f"Tick {t:03d}: pos=({diag['pos_x']:.2f}, {diag['pos_y']:.2f}), yaw={diag['yaw']:.2f}, u=({u_6d[0]:.2f}, {u_6d[1]:.2f}), pan={u_6d[2]:.2f}")

    impact = hal.get_carl_impact_info()
    if impact["damaging_impacts"] > 0:
        had_collision = True
        print(f"COLLISION at tick {t}!")
        break
        
    if diag["pos_x"] <= -0.55:
        escaped = True
        print(f"ESCAPED at tick {t}! pos_x={diag['pos_x']:.3f}, pos_y={diag['pos_y']:.3f}")
        break

print(f"Episode complete: Escaped={escaped}, Collision={had_collision}, Ticks={len(latencies)}")
print(f"Latency: Mean={np.mean(latencies):.2f} ms, p95={np.percentile(latencies, 95):.2f} ms, Max={np.max(latencies):.2f} ms")

