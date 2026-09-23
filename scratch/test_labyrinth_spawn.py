import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
import mujoco
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory

hal = CarlStage1HAL(open_space=False, headless=True)
hal.reset()
qa = int(hal.model.joint('spatial_identity').qposadr[0])
print("Physical initial qpos:", hal.data.qpos[qa:qa+3])

# Let's inspect sonars at spawn:
s = hal.read_sensors()
sonars = s[:15]
print("Spawn sonars:", np.round(sonars, 2))
