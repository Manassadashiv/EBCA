import sys
import os
import numpy as np

sys.path.insert(0, 'd:/ebca')
from brain.carl_stage1_hal import CarlStage1HAL

hal = CarlStage1HAL(open_space=True)
hal.reset()

max_roll = 0.0
max_pitch = 0.0

for t in range(360):
    if t < 60:
        # Phase 1: Forward commute
        u = np.array([0.22, 0.22, 0.0, 0.0, 0.0, 0.0])
    elif t < 120:
        # Phase 2: Left turn + head pan left
        u = np.array([0.12, 0.26, 0.5, 0.0, 0.0, 0.0])
    elif t < 180:
        # Phase 3: Right turn + head pan right
        u = np.array([0.26, 0.12, -0.5, 0.0, 0.0, 0.0])
    elif t < 240:
        # Phase 4: Forward commute + neck tilt
        u = np.array([0.24, 0.24, 0.0, 0.4, 0.0, 0.0])
    elif t < 300:
        # Phase 5: Controlled pivot turn
        u = np.array([0.16, -0.16, 0.0, 0.0, 0.0, 0.0])
    else:
        # Phase 6: Forward cruise
        u = np.array([0.25, 0.25, 0.0, 0.0, 0.0, 0.0])

    s, diag = hal.step(u)
    roll_deg = abs(np.degrees(diag['roll']))
    pitch_deg = abs(np.degrees(diag['pitch']))
    max_roll = max(max_roll, roll_deg)
    max_pitch = max(max_pitch, pitch_deg)

    if t % 30 == 0:
        print(f"t={t:03d} | pos=({diag['pos_x']:+5.2f}, {diag['pos_y']:+5.2f}) | yaw={np.degrees(diag['yaw']):+6.1f}° | speed={diag['speed']:.3f} m/s | roll={roll_deg:.2f}° | pitch={pitch_deg:.2f}° | contacts={diag['ncon']}")

print(f"\nCompleted 360 ticks! Peak Roll: {max_roll:.2f}°, Peak Pitch: {max_pitch:.2f}°")
