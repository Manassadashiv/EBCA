import math
import numpy as np

prev_w = 0.0
u_diff = 1.4
w_target = 10.7 * u_diff
dt = 0.030
dyaws = []
for t in range(10):
    next_w = 0.05 * prev_w + 0.95 * w_target
    prev_w = next_w
    dyaws.append(round(next_w * dt * 180 / math.pi, 1))

print('Predicted dyaws (deg):', dyaws)
print('Total yaw (deg):', sum(dyaws))

# MuJoCo true: [25.7, 25.7, 25.7, 25.7, 25.7, 19.7, 10.5, 10.5, 10.5, 10.5]
mu_true = [25.7, 25.7, 25.7, 25.7, 25.7, 19.7, 10.5, 10.5, 10.5, 10.5]
print('MuJoCo true dyaws:', mu_true)
print('MuJoCo true total:', sum(mu_true))
