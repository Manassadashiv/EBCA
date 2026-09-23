import sys
import os
import numpy as np
import mujoco
from PIL import Image

sys.path.insert(0, 'd:/ebca')
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=True)
hal.reset()

renderer = mujoco.Renderer(hal.model, 720, 1280)
cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.distance = 2.5
cam.elevation = -22.0

for t in range(30):
    u = np.array([0.22, 0.22, 0.0, 0.0, 0.0, 0.0])
    s, diag = hal.step(u)
    cam.lookat = [diag['pos_x'], diag['pos_y'], diag['pos_z'] + 0.15]
    cam.azimuth = 45.0 + t * 0.2

renderer.update_scene(hal.data, camera=cam)
img_array = renderer.render()
img = Image.fromarray(img_array)
img.save('d:/ebca/scratch/test_frame.png')
print('Rendered test frame saved successfully to scratch/test_frame.png!')
