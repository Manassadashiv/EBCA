import numpy as np

d = np.load('evidence/stage2_2_r2/air_gapped_mental_rollouts.npz', allow_pickle=True)
mr7 = d['mental_rollouts'][7]
imr7 = d['inv_mental_rollouts'][7]

print("R2 air_gapped_mental_rollouts.npz Branch 7:")
print("mr7 shape:", mr7.shape)
print("imr7 shape:", imr7.shape)
print("mr7[0]:", mr7[0])
print("imr7[0]:", imr7[0])
print("diff at step 0:", imr7[0] - mr7[0])
print("diff at step -1:", imr7[-1] - mr7[-1])
print("mean diff:", np.mean(np.abs(imr7 - mr7)))
