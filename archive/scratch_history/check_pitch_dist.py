import sys
sys.path.insert(0, ".")
import math
import numpy as np
from tests.run_stage3_6_complete_battery import generate_matched_configs, XML_PATH, GRID_PATH, CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
import mujoco

cfg = generate_matched_configs(5, seed=6001)[1] # Config 1 (escaped cleanly in 240 ticks)
sx, sy = cfg["spawn_pos"]
syaw = cfg["spawn_yaw"]

hal = CarlStage1HAL(xml_path=str(XML_PATH))
hal.reset()
qa = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[qa:qa + 2] = [sx, sy]
hal.data.qpos[qa + 3:qa + 7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
mujoco.mj_forward(hal.model, hal.data)

agent = CarlAutonomousOrganismAgent(
    dt=hal.dt,
    deliberation_mode="active_inference",
    grid_path=str(GRID_PATH)
)
agent.initialize_spatial_grounding(sx, sy, syaw, grid_path=str(GRID_PATH))

pitches = []
for tick in range(250):
    res = agent.step_cognitive_cycle(hal)
    u_cmd = res["action_cmd"]
    s_next, diag = hal.step(u_cmd)
    
    qx = float(hal.data.qpos[qa])
    qy = float(hal.data.qpos[qa + 1])
    pitch = abs(float(diag["pitch"]))
    pitches.append((tick, pitch, qx, qy, u_cmd[0], u_cmd[1]))
    if qx <= -0.55:
        break

# Sort by pitch descending
pitches.sort(key=lambda x: x[1], reverse=True)
print("Top 10 highest pitch ticks:")
for t, p, x, y, ul, ur in pitches[:10]:
    print(f"t={t:03d} | pitch={p:.4f} rad ({math.degrees(p):.1f} deg) | pos=({x:.2f}, {y:.2f}) | cmd=({ul:.2f}, {ur:.2f})")

print(f"\nMean pitch: {np.mean([p[1] for p in pitches]):.4f} rad")
print(f"p95 pitch:  {np.percentile([p[1] for p in pitches], 95):.4f} rad")
print(f"p50 pitch:  {np.median([p[1] for p in pitches]):.4f} rad")
