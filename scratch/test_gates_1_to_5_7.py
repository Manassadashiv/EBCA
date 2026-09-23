import sys
sys.path.insert(0, '.')
from pathlib import Path
import json
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy import stats

from brain.carl_stage2_2_r2_modular_world_model import CARLModularPredictiveWorldModel
from brain.carl_stage1_hal import CarlStage1HAL

def compute_roc_auc(y_true, y_score) -> float:
    y_true = np.asarray(y_true).flatten()
    y_score = np.asarray(y_score).flatten()
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    n1 = len(pos)
    n0 = len(neg)
    if n1 == 0 or n0 == 0:
        return 0.5
    ranks = np.argsort(np.argsort(y_score)) + 1
    r1 = np.sum(ranks[y_true == 1])
    u = r1 - n1 * (n1 + 1) / 2.0
    return float(u / (n1 * n0))

dev_train_path = Path("evidence/stage2_2_diag/datasets/DEV_TRAIN.npz")
dev_val_path = Path("evidence/stage2_2_diag/datasets/DEV_VAL.npz")

d_train = np.load(dev_train_path)
S_train = torch.from_numpy(d_train["S"]).float()
U_train = torch.from_numpy(d_train["U"]).float()
coll_train = torch.from_numpy(d_train["collision"]).float()

d_val = np.load(dev_val_path)
S_val = torch.from_numpy(d_val["S"]).float()
U_val = torch.from_numpy(d_val["U"]).float()
coll_val = torch.from_numpy(d_val["collision"]).float()

print(f"Loaded datasets: Train {S_train.shape}, Val {S_val.shape}")

arch1 = CARLModularPredictiveWorldModel()

# Check Gate 1: Gyro and Proprio on untrained / baseline body model
s_body_val = S_val[:, :, 15:24]
test_u = U_val[:, 150:160, :]
test_body_0 = s_body_val[:, 149, :]
true_future_body = s_body_val[:, 150:160, :]

with torch.no_grad():
    pred_body_traj, _, _ = arch1.body_model.unroll(test_body_0, test_u)

true_gyro = true_future_body[:, :, 5].numpy().flatten()
pred_gyro = pred_body_traj[:, :, 5].numpy().flatten()
r2_gyro = float(1.0 - np.sum((true_gyro - pred_gyro)**2) / (np.sum((true_gyro - np.mean(true_gyro))**2) + 1e-8))

true_proprio_all = true_future_body.numpy().flatten()
pred_proprio_all = pred_body_traj.numpy().flatten()
r2_proprio = float(1.0 - np.sum((true_proprio_all - pred_proprio_all)**2) / (np.sum((true_proprio_all - np.mean(true_proprio_all))**2) + 1e-8))

print(f"Gate 1 Initial Baseline: Gyro R2 = {r2_gyro:.4f} (target >= 0.75), Proprio R2 = {r2_proprio:.4f} (target >= 0.85)")
