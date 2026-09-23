import sys
import os
sys.path.insert(0, os.path.abspath("."))
import math
import numpy as np
from brain.carl_stage2_hd_ring import HeadDirectionRingAttractor

def set_bump_heading(ring: HeadDirectionRingAttractor, target_heading: float):
    dists = np.array([abs(math.atan2(math.sin(a - target_heading), math.cos(a - target_heading))) for a in ring.angles])
    idx = int(np.argmin(dists))
    ring.u = np.zeros(ring.N_NEURONS, dtype=np.float64)
    ring.u[idx] = 1.0
    ring.r = ring._activation(ring.u)
    ring._settle_initial_attractor(steps=100)

ring = HeadDirectionRingAttractor(seed=42)
print("Testing set_bump_heading for angles:")
for target_deg in [-135, -90, -45, 0, 30, 60, 120, 170]:
    th = math.radians(target_deg)
    set_bump_heading(ring, th)
    decoded = ring.decode_heading()
    decoded_deg = math.degrees(decoded)
    err = abs(math.degrees(math.atan2(math.sin(decoded - th), math.cos(decoded - th))))
    print(f"Target: {target_deg:+4d}° | Decoded: {decoded_deg:+6.2f}° | Discretization Error: {err:.2f}°")
