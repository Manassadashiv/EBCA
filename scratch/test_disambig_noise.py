import math
import numpy as np

def phase_disambiguation(phi1, phi2, lambda1=0.80, lambda2=1.15, max_range=9.0):
    k1_min = int(np.floor(-max_range / lambda1)) - 1
    k1_max = int(np.ceil(max_range / lambda1)) + 1
    k2_min = int(np.floor(-max_range / lambda2)) - 1
    k2_max = int(np.ceil(max_range / lambda2)) + 1

    best_dist = 1e9
    best_x = 0.0

    for k1 in range(k1_min, k1_max + 1):
        x1 = (phi1 / (2.0 * math.pi) + k1) * lambda1
        if abs(x1) > max_range + 0.5:
            continue
        for k2 in range(k2_min, k2_max + 1):
            x2 = (phi2 / (2.0 * math.pi) + k2) * lambda2
            diff = abs(x1 - x2)
            if diff < best_dist:
                best_dist = diff
                best_x = 0.5 * (x1 + x2)

    return best_x, best_dist

lambda1 = 0.80
lambda2 = 1.15

# Let's test at x = 1.20m (past the 0.80m torus boundary)
for noise_deg in [0, 1, 2, 5, 8, 10, 15, 20]:
    noise_rad = math.radians(noise_deg)
    x = 1.20
    p1 = ((x / lambda1 + 0.5) % 1.0 - 0.5) * 2.0 * math.pi + noise_rad
    p2 = ((x / lambda2 + 0.5) % 1.0 - 0.5) * 2.0 * math.pi
    x_hat, res = phase_disambiguation(p1, p2, lambda1, lambda2, max_range=9.0)
    print(f"Noise {noise_deg:2d} deg ({noise_rad*lambda1/(2*math.pi)*100:4.2f} cm): x_hat = {x_hat:6.3f}m, diff = {abs(x_hat - x):6.3f}m, residual = {res:6.4f}m")
