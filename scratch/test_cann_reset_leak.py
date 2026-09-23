import sys
import math
from pathlib import Path
import numpy as np

repo_root = Path("d:/ebca")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain

cann = CarlStage2BIntegratedBrain(dt=0.030)
print("Initial decoded heading:", math.degrees(cann.hd_ring.decode_heading()))

# Simulate turning for 50 ticks
for _ in range(50):
    cann.hd_ring.step(omega_input=1.5)

print("Decoded heading after turning:", math.degrees(cann.hd_ring.decode_heading()))

# Call reset_at_birthplace
cann.reset_at_birthplace()
print("Decoded heading after reset_at_birthplace():", math.degrees(cann.hd_ring.decode_heading()))
print("Birth HD phase recorded:", math.degrees(cann.birth_hd_phase))

# Check bump position in hd_ring.r
angles_hd = np.linspace(-math.pi, math.pi, 64, endpoint=False)
peak_idx = np.argmax(cann.hd_ring.r)
print(f"Peak neuron index in hd_ring: {peak_idx} (angle = {math.degrees(angles_hd[peak_idx]):.1f} deg)")
print(f"At birth, peak index was: 32 (angle = 0.0 deg)")
print(f"Is hd_ring.r reset back to 32? {peak_idx == 32}")
