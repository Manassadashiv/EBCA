"""
scratch/test_multiscale_grid.py — Test multi-scale coprime grid modules and phase disambiguation
"""
import math
import numpy as np

lambda1 = 0.80
lambda2 = 1.15

# Common period: 23 * 0.80 = 18.40m, 16 * 1.15 = 18.40m
print(f"Common period: 23 * {lambda1} = {23 * lambda1:.2f}m, 16 * {lambda2} = {16 * lambda2:.2f}m")

def phase_disambiguation(phi1, phi2, lambda1=0.80, lambda2=1.15, max_range=9.0):
    """
    Finds consistent continuous position x in [-max_range, max_range]
    from periodic phases phi1 in [-pi, pi] and phi2 in [-pi, pi].
    """
    # Candidate positions from Module 1: x1 = (phi1 / 2pi + k1) * lambda1
    # Candidate positions from Module 2: x2 = (phi2 / 2pi + k2) * lambda2
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

# Test across true positions from -3.0m to +3.0m
true_xs = np.linspace(-3.0, 3.0, 61)
errors = []
for x in true_xs:
    # True phases
    p1 = ((x / lambda1 + 0.5) % 1.0 - 0.5) * 2.0 * math.pi
    p2 = ((x / lambda2 + 0.5) % 1.0 - 0.5) * 2.0 * math.pi
    x_hat, residual = phase_disambiguation(p1, p2, lambda1, lambda2)
    err = abs(x_hat - x)
    errors.append(err)

print(f"Max disambiguation error across [-3.0m, +3.0m]: {max(errors):.6f} m")
print(f"Mean disambiguation error: {np.mean(errors):.6f} m")
