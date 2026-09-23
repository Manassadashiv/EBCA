import sys, numpy as np, math
sys.path.insert(0, ".")
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=False)
hal.reset()
q_addr = int(hal.model.joint("spatial_identity").qposadr[0])
hal.data.qpos[q_addr + 1] = 2.0
hal.data.qpos[q_addr + 3] = math.cos(math.pi / 4.0)
hal.data.qpos[q_addr + 6] = math.sin(math.pi / 4.0)
hal.step(np.zeros(6))

s = hal.read_sensors()
print("Initial sonars:", np.round(s[:15], 2))
for t in range(5):
    u = np.array([0.10, 0.10, 0, 0, 0, 0])
    s, diag = hal.step(u)
    print(f"t={t}: speed={diag['speed']:.3f}, sonars 5..9={np.round(s[5:10], 4)}")
