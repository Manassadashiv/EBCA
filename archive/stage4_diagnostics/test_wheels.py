import mujoco, numpy as np
from tests.run_stage4_1_complete_battery import XML_PATH
from brain.carl_stage1_hal import CarlStage1HAL
hal = CarlStage1HAL(xml_path=str(XML_PATH))
hal.reset()
_, d0 = hal.step(np.zeros(6))
yaw0 = d0['yaw']
for _ in range(10):
    _, d = hal.step(np.array([1.0, -1.0, 0, 0, 0, 0]))
print(f"Wheel 0=+1, Wheel 1=-1: yaw went from {yaw0:.4f} to {d['yaw']:.4f}, diff = {d['yaw'] - yaw0:.4f}")

hal.reset()
_, d0 = hal.step(np.zeros(6))
yaw0 = d0['yaw']
for _ in range(10):
    _, d = hal.step(np.array([-1.0, +1.0, 0, 0, 0, 0]))
print(f"Wheel 0=-1, Wheel 1=+1: yaw went from {yaw0:.4f} to {d['yaw']:.4f}, diff = {d['yaw'] - yaw0:.4f}")
