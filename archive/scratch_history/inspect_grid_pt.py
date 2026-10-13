import torch, numpy as np

data = torch.load('world/stage3_4_environments/cul_de_sac_turning_bay_grid.pt')
print("Keys:", data.keys() if isinstance(data, dict) else type(data))
if isinstance(data, dict):
    for k, v in data.items():
        if hasattr(v, 'shape'):
            print(k, v.shape, type(v))
        else:
            print(k, type(v))
elif hasattr(data, 'shape'):
    print("Tensor shape:", data.shape)
