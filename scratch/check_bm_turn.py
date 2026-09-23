import sys
sys.path.insert(0, '.')
import math
import numpy as np
import torch
from brain.carl_stage2_2_r2_body_model import KinematicBodyModel

body_model = KinematicBodyModel()
s0 = torch.zeros(1, 9)
u_left = torch.tensor([[-0.7, 0.7, 0, 0, 0, 0]] * 10).unsqueeze(0).float()
s_traj, dp_traj, poses = body_model.unroll(s0, u_left)

print("Body model predicted yaws (deg):", [f"{poses[0, i, 2].item()*180/math.pi:.1f}" for i in range(10)])
print("Body model predicted dyaw (deg/tick):", [f"{dp_traj[0, i, 2].item()*180/math.pi:.1f}" for i in range(10)])
