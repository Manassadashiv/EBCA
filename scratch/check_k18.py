import math
import numpy as np

pose_x = -0.151
pose_y = 0.960
pose_yaw = 17.6 * math.pi / 180.0
r_hull = 0.14
sonar_angles = np.linspace(-2.0944, 2.0944, 15, endpoint=True)

angle_4 = pose_yaw + sonar_angles[4]
ox = pose_x + r_hull * math.cos(angle_4)
oy = pose_y + r_hull * math.sin(angle_4)

radii = np.linspace(0.05, 5.0, 80)
for k in [17, 18, 19, 20]:
    r = radii[k]
    px = ox + r * math.cos(angle_4)
    py = oy + r * math.sin(angle_4)
    g_x = (px + 6.4) / 0.10
    g_y = (py + 6.4) / 0.10
    print(f"k={k}: r={r:.3f}m -> px={px:+.3f}, py={py:+.3f}, grid=({g_x:.1f}, {g_y:.1f})")
