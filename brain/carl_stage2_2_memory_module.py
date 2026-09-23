"""
brain/carl_stage2_2_memory_module.py — Learned Spatial-Attentive Environmental Memory Module
Classification: [NEURAL COGNITIVE SUBSTRATE] Condition F Learned World Memory

Implements an explicit, learned environmental memory substrate that satisfies all pre-experimental invariants:
1. Strict Data Provenance:
   Memory is written and read EXCLUSIVELY using:
   - Past sensory history S_{1:t}
   - Past actions U_{1:t-1}
   - Internal dead-reckoned spatial state [x_hat_t, y_hat_t, cos(theta_hat), sin(theta_hat)]
2. Prohibited Data Sources:
   Zero access to MuJoCo model, data.qpos, data.geom_xpos, true obstacle maps, or simulator collision trees.
3. Neural Addressing:
   Key-value soft-attention memory buffer M in R^{K x d_m} (K=64 slots, d_m=64).
   Keys are projected from internal dead-reckoned spatial pose.
   Values are projected from sensorimotor experience [S_t, U_t].
"""

import math
from typing import Tuple, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class LearnedSpatialEnvironmentalMemory(nn.Module):
    """
    Episodic / Spatial Key-Value Memory Module.
    Associates internal spatial coordinates with historical sensory returns.
    """
    def __init__(
        self,
        num_slots: int = 64,
        mem_dim: int = 64,
        sensory_dim: int = 25,
        action_dim: int = 6,
        pose_dim: int = 4  # [x_hat, y_hat, cos(theta), sin(theta)]
    ):
        super().__init__()
        self.num_slots = num_slots
        self.mem_dim = mem_dim
        self.pose_dim = pose_dim

        # Query projection: projects internal pose into memory query space
        self.q_proj = nn.Linear(pose_dim, mem_dim)

        # Key projection: projects internal pose into memory key space
        self.k_proj = nn.Linear(pose_dim, mem_dim)

        # Value projection: projects sensory observation and action into value space
        self.v_proj = nn.Linear(sensory_dim + action_dim, mem_dim)

        # Write gate: decides how strongly to update memory slots
        self.gate_proj = nn.Linear(mem_dim * 2, 1)

        # Output projection for retrieved memory context
        self.out_proj = nn.Linear(mem_dim, mem_dim)

    def init_memory(self, batch_size: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Initializes blank episodic memory buffer at start of episode.
        Returns:
            keys: (B, K, mem_dim)
            values: (B, K, mem_dim)
        """
        keys = torch.zeros(batch_size, self.num_slots, self.mem_dim, device=device)
        values = torch.zeros(batch_size, self.num_slots, self.mem_dim, device=device)
        return keys, values

    def read(
        self,
        pose: torch.Tensor,
        keys: torch.Tensor,
        values: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Reads from spatial memory using internal dead-reckoned pose as query.
        Args:
            pose: (B, pose_dim)
            keys: (B, K, mem_dim)
            values: (B, K, mem_dim)
        Returns:
            context: (B, mem_dim)
            attn_weights: (B, K)
        """
        # q: (B, mem_dim) -> (B, 1, mem_dim)
        q = self.q_proj(pose).unsqueeze(1)

        # Scaled dot-product attention
        # scores: (B, 1, K)
        scores = torch.bmm(q, keys.transpose(1, 2)) / math.sqrt(self.mem_dim)
        attn_weights = F.softmax(scores, dim=-1)  # (B, 1, K)

        # Retrieved context: (B, 1, mem_dim) -> (B, mem_dim)
        context = torch.bmm(attn_weights, values).squeeze(1)
        context = self.out_proj(context)

        return context, attn_weights.squeeze(1)

    def write(
        self,
        pose: torch.Tensor,
        sensory_action: torch.Tensor,
        keys: torch.Tensor,
        values: torch.Tensor,
        slot_idx: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Writes sensorimotor experience into memory at spatial location.
        Args:
            pose: (B, pose_dim)
            sensory_action: (B, sensory_dim + action_dim)
            keys: (B, K, mem_dim)
            values: (B, K, mem_dim)
            slot_idx: optional circular slot index (0..K-1)
        Returns:
            updated_keys, updated_values
        """
        B = pose.shape[0]
        k_new = self.k_proj(pose)  # (B, mem_dim)
        v_new = self.v_proj(sensory_action)  # (B, mem_dim)

        if slot_idx is not None:
            # Deterministic ring write into specific slot
            idx = slot_idx % self.num_slots
            keys_up = keys.clone()
            values_up = values.clone()
            keys_up[:, idx, :] = k_new
            values_up[:, idx, :] = v_new
            return keys_up, values_up
        else:
            # Soft attentive write into most similar or least updated slot
            q = k_new.unsqueeze(1)
            scores = torch.bmm(q, keys.transpose(1, 2)) / math.sqrt(self.mem_dim)
            write_weights = F.softmax(scores, dim=-1).transpose(1, 2)  # (B, K, 1)

            # Gate
            combined = torch.cat([k_new, v_new], dim=-1)
            gate = torch.sigmoid(self.gate_proj(combined)).unsqueeze(1)  # (B, 1, 1)

            keys_up = keys * (1.0 - write_weights * gate) + (write_weights * gate) * k_new.unsqueeze(1)
            values_up = values * (1.0 - write_weights * gate) + (write_weights * gate) * v_new.unsqueeze(1)
            return keys_up, values_up
