import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import mujoco

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage2_2_r2_occupancy_memory import SpatialOccupancyMemory
from brain.carl_stage2_2_r2_body_model import KinematicBodyModel
from brain.carl_stage2_2_r2_modular_world_model import ProspectiveSensoryGenerator

def main():
    print("Loading frozen branches...", flush=True)
    with open('evidence/stage2_2_r2/manifests/frozen_branch_sequences.json') as f:
        branches = json.load(f)

    hal = CarlStage1HAL()
    hal.reset()
    hal.set_floor_friction(1.0)
    qa = int(hal.model.joint('spatial_identity').qposadr[0])

    print("Mapping arena into spatial occupancy memory...", flush=True)
    mem = SpatialOccupancyMemory(grid_size=128, resolution=0.10)
    grid = torch.zeros(1, 2, 128, 128)
    vps = [(-1.5, -1.5), (-1.5, 0), (-1.5, 1.5), (0, -1.5), (0, 0), (0, 1.5), (1.5, -1.5), (1.5, 0), (1.5, 1.5)]
    for vx, vy in vps:
        for angle in np.linspace(-np.pi, np.pi, 24, endpoint=False):
            hal.data.qpos[qa:qa+2] = [vx, vy]
            hal.data.qpos[qa+3:qa+7] = [math.cos(angle/2), 0, 0, math.sin(angle/2)]
            mujoco.mj_forward(hal.model, hal.data)
            s = hal.read_sensors()[:15]
            grid = mem.accumulate_observations(grid, torch.tensor([[vx, vy, angle]]).float(), torch.tensor(s).unsqueeze(0).float())

    print("Collecting calibration trajectories for body model...", flush=True)
    rng = np.random.RandomState(42)
    all_u, all_dp, all_s = [], [], []

    # 1. Canonical actions
    canonical_actions = [
        [0.8, 0.8, 0, 0, 0, 0],
        [-0.7, 0.7, 0, 0, 0, 0],
        [0.7, -0.7, 0, 0, 0, 0],
        [-0.6, -0.6, 0, 0, 0, 0],
        [0.0, 0.0, 0, 0, 0, 0],
    ]
    for act in canonical_actions:
        for _ in range(12):
            hal.reset()
            u_seq, dp_seq, s_seq = [], [], []
            for t in range(12):
                qw0, qz0 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
                yaw0 = 2.0 * np.arctan2(qz0, qw0)
                x0, y0 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
                s_b = hal.read_sensors()[15:24]
                hal.step(np.array(act))
                qw1, qz1 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
                yaw1 = 2.0 * np.arctan2(qz1, qw1)
                x1, y1 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
                dx_g, dy_g = x1 - x0, y1 - y0
                dyaw = (yaw1 - yaw0 + np.pi) % (2*np.pi) - np.pi
                dx_l = dx_g * np.cos(yaw0) + dy_g * np.sin(yaw0)
                dy_l = -dx_g * np.sin(yaw0) + dy_g * np.cos(yaw0)
                u_seq.append(act)
                dp_seq.append([dx_l, dy_l, dyaw])
                s_seq.append(s_b)
            all_u.append(u_seq)
            all_dp.append(dp_seq)
            all_s.append(s_seq)

    # 2. Random action sequences
    for _ in range(100):
        hal.reset()
        u_seq, dp_seq, s_seq = [], [], []
        u_base = rng.uniform(-1.0, 1.0, size=6)
        for t in range(12):
            if rng.rand() < 0.2:
                u_base = rng.uniform(-1.0, 1.0, size=6)
            u_t = u_base.copy()
            qw0, qz0 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
            yaw0 = 2.0 * np.arctan2(qz0, qw0)
            x0, y0 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
            s_b = hal.read_sensors()[15:24]
            hal.step(u_t)
            qw1, qz1 = hal.data.qpos[qa + 3], hal.data.qpos[qa + 6]
            yaw1 = 2.0 * np.arctan2(qz1, qw1)
            x1, y1 = hal.data.qpos[qa], hal.data.qpos[qa + 1]
            dx_g, dy_g = x1 - x0, y1 - y0
            dyaw = (yaw1 - yaw0 + np.pi) % (2*np.pi) - np.pi
            dx_l = dx_g * np.cos(yaw0) + dy_g * np.sin(yaw0)
            dy_l = -dx_g * np.sin(yaw0) + dy_g * np.cos(yaw0)
            u_seq.append(u_t)
            dp_seq.append([dx_l, dy_l, dyaw])
            s_seq.append(s_b)
        all_u.append(u_seq)
        all_dp.append(dp_seq)
        all_s.append(s_seq)

    print("Training KinematicBodyModel...", flush=True)
    body_model = KinematicBodyModel()
    opt_b = torch.optim.Adam(body_model.parameters(), lr=3e-3)
    U_t = torch.tensor(np.array(all_u)).float()
    DP_t = torch.tensor(np.array(all_dp)).float()
    S_t = torch.tensor(np.array(all_s)).float()
    for epoch in range(150):
        opt_b.zero_grad()
        s_pred, dp_pred, _ = body_model.unroll(S_t[:, 0, :], U_t)
        loss_dp = F.mse_loss(dp_pred, DP_t)
        loss_s = F.mse_loss(s_pred[:, :, 5:], S_t[:, :, 5:])  # Focus on gyro & joints
        loss = loss_dp + 0.1 * loss_s
        loss.backward()
        opt_b.step()
    print(f"Body model final loss: dp={loss_dp.item():.6f}, s={loss_s.item():.6f}", flush=True)

    # Train Module 3 (Sensory Generator)
    print("Training Module 3 (ProspectiveSensoryGenerator)...", flush=True)
    sensory_gen = ProspectiveSensoryGenerator()
    opt_g = torch.optim.Adam(sensory_gen.parameters(), lr=2e-3)

    # Collect pairs (clearance_query, physical_sonar, proprio)
    clr_data, son_data, prop_data = [], [], []
    for _ in range(120):
        vx = float(rng.uniform(-1.6, 1.6))
        vy = float(rng.uniform(-1.6, 1.6))
        vth = float(rng.uniform(-np.pi, np.pi))
        hal.data.qpos[qa:qa+2] = [vx, vy]
        hal.data.qpos[qa+3:qa+7] = [math.cos(vth/2), 0, 0, math.sin(vth/2)]
        mujoco.mj_forward(hal.model, hal.data)
        son = hal.read_sensors()[:15]
        prop = hal.read_sensors()[15:24]
        with torch.no_grad():
            clr = mem.query_clearance(grid, torch.tensor([[vx, vy, vth]]).float())[0].numpy()
        clr_data.append(clr)
        son_data.append(son)
        prop_data.append(prop)

    CLR_t = torch.tensor(np.array(clr_data)).float()
    SON_t = torch.tensor(np.array(son_data)).float()
    PROP_t = torch.tensor(np.array(prop_data)).float()

    for ep in range(100):
        opt_g.zero_grad()
        pred_son, _ = sensory_gen(CLR_t, PROP_t)
        loss_g = F.mse_loss(pred_son, SON_t)
        loss_g.backward()
        opt_g.step()
    print(f"Sensory Generator final loss: {loss_g.item():.6f}", flush=True)

    # Optimal starting pose S_0 = (-0.15, 0.96, -95.4 deg)
    s0_pos = [-0.15, 0.96]
    s0_yaw = -95.4 * math.pi / 180.0

    hal.reset()
    hal.data.qpos[qa:qa+2] = s0_pos
    hal.data.qpos[qa+3:qa+7] = [math.cos(s0_yaw/2), 0, 0, math.sin(s0_yaw/2)]
    mujoco.mj_forward(hal.model, hal.data)
    qpos_0 = hal.data.qpos.copy()
    qvel_0 = hal.data.qvel.copy()
    s0_body = torch.tensor(hal.read_sensors()[15:24]).unsqueeze(0).float()
    pose_0 = torch.tensor([[s0_pos[0], s0_pos[1], s0_yaw]]).float()

    phys_trajs = []
    mental_trajs = []
    results = []

    print("\nExecuting 20 branches...", flush=True)
    for b in range(len(branches)):
        hal.reset(qpos=qpos_0, qvel=qvel_0)
        u_seq = np.array(branches[b]['actions'])
        H = len(u_seq)
        
        # Ground truth physical rollout
        phys = []
        for step in range(H):
            hal.step(u_seq[step])
            phys.append(hal.read_sensors()[:15])
        phys = np.array(phys)
        phys_trajs.append(phys)
        
        # Mental rollout through Body Model + Spatial Memory + Sensory Generator
        u_b_t = torch.tensor(u_seq).unsqueeze(0).float()
        with torch.no_grad():
            s_body_traj, _, rel_poses = body_model.unroll(s0_body, u_b_t)
            mental = []
            for step in range(H):
                dx_rel = rel_poses[0, step, 0].item()
                dy_rel = rel_poses[0, step, 1].item()
                dtheta_rel = rel_poses[0, step, 2].item()
                th_0 = pose_0[0, 2].item()
                abs_x = pose_0[0, 0].item() + dx_rel * math.cos(th_0) - dy_rel * math.sin(th_0)
                abs_y = pose_0[0, 1].item() + dx_rel * math.sin(th_0) + dy_rel * math.cos(th_0)
                abs_th = pose_0[0, 2].item() + dtheta_rel
                
                clr = mem.query_clearance(grid, torch.tensor([[abs_x, abs_y, abs_th]]).float())
                pred_s, _ = sensory_gen(clr, s_body_traj[0:1, step, :])
                mental.append(pred_s[0].detach().numpy())
        mental = np.array(mental)
        mental_trajs.append(mental)
        
        y_true = phys.flatten()
        y_pred = mental.flatten()
        r2 = 1.0 - np.sum((y_true - y_pred)**2) / (np.sum((y_true - np.mean(y_true))**2) + 1e-8)
        rmse = np.sqrt(np.mean((y_true - y_pred)**2))
        name = branches[b]['name']
        results.append((b, name, r2, rmse))

    print("\n=== INDIVIDUAL BRANCH RESULTS WITH MODULE 3 ===", flush=True)
    pass_count = 0
    for b, name, r2, rmse in results:
        # Compute inverse margin
        u_inv = -torch.tensor(branches[b]['actions']).unsqueeze(0).float()
        H = len(branches[b]['actions'])
        with torch.no_grad():
            s_body_inv, _, rel_inv = body_model.unroll(s0_body, u_inv)
            inv_mental = []
            for step in range(H):
                dx_rel = rel_inv[0, step, 0].item()
                dy_rel = rel_inv[0, step, 1].item()
                dtheta_rel = rel_inv[0, step, 2].item()
                th_0 = pose_0[0, 2].item()
                abs_x = pose_0[0, 0].item() + dx_rel * math.cos(th_0) - dy_rel * math.sin(th_0)
                abs_y = pose_0[0, 1].item() + dx_rel * math.sin(th_0) + dy_rel * math.cos(th_0)
                abs_th = pose_0[0, 2].item() + dtheta_rel
                clr = mem.query_clearance(grid, torch.tensor([[abs_x, abs_y, abs_th]]).float())
                pred_s_inv, _ = sensory_gen(clr, s_body_inv[0:1, step, :])
                inv_mental.append(pred_s_inv[0].detach().numpy())
        inv_mental = np.array(inv_mental)
        rmse_inv = np.sqrt(np.mean((phys_trajs[b] - inv_mental)**2))
        margin = rmse_inv - rmse
        status = "PASS" if (r2 >= 0.50 and margin >= 0.30) else "FAIL"
        if status == "PASS": pass_count += 1
        print(f"Branch {b:02d} ({name:25s}): R2={r2:6.4f}, RMSE={rmse:.3f}m, Margin={margin:+.3f}m [{status}]", flush=True)

    print(f"\nTotal passed: {pass_count} / 20", flush=True)

if __name__ == "__main__":
    main()
