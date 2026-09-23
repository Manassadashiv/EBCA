"""
brain/carl_stage2_spatial_controller.py — Stage 2.1A-R Emergent Spatial Agent
Classification: [DEVELOPMENTAL COGNITION] Unsupervised Vestibular Discovery & Closed-Loop Homing

Core Capabilities:
1. Unsupervised Vestibular Discovery:
   Identifies the rotational yaw gyro channel from anonymous sensor vectors by computing
   cross-correlation with differential wheel actuation (u_R - u_L). Zero hardcoded indices.
2. Endogenous Closed-Loop Spatial Navigation:
   Maintains internal dead-reckoning state (x, y, theta) and synthesizes motor commands
   to execute wander exploration and autonomous return-to-birthplace (homing).
3. Traction-Gated Drift Rejection:
   Freezes dead reckoning during slip discrepancies to preserve homing vector integrity.
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from brain.carl_stage2_dead_reckoning import DeadReckoningModule


def discover_vestibular_channel(
    U: np.ndarray,
    S: np.ndarray,
    drive_channels: Tuple[int, int] = (0, 1)
) -> Tuple[int, float, float]:
    """
    Discovers which sensor channel corresponds to rotational yaw velocity from babbling data.
    Differential drive (u_R - u_L) produces odd-symmetric rotational acceleration about Z.
    Across all anonymous sensor channels, the yaw gyro has the dominant signed correlation.

    Args:
        U: (T, 6) Actuator command history from developmental babbling.
        S: (T, 25) Anonymous sensor observation history.
        drive_channels: Discovered bilateral locomotion channels (left, right).

    Returns:
        (best_channel, sign, correlation)
    """
    ch_L, ch_R = drive_channels[0], drive_channels[1]
    diff_u = U[:, ch_R] - U[:, ch_L]
    diff_u_norm = (diff_u - np.mean(diff_u)) / (np.std(diff_u) + 1e-9)
    S_norm = (S - np.mean(S, axis=0)) / (np.std(S, axis=0) + 1e-9)

    corrs = [float(np.mean(diff_u_norm * S_norm[:, j])) for j in range(S.shape[1])]
    best_j = int(np.argmax(np.abs(corrs)))
    sign = float(np.sign(corrs[best_j]))
    return best_j, sign, float(corrs[best_j])


class CarlSpatialAgent:
    """
    Endogenous spatial agent for Stage 2.1A-R.
    Controls motor output, discovers vestibular sensors, and performs closed-loop homing.
    """

    def __init__(
        self,
        dt: float = 0.030,
        drive_channels: Tuple[int, int] = (0, 1),
        yaw_channel: Optional[int] = None,
        yaw_sign: float = 1.0,
    ):
        self.dt = dt
        self.drive_channels = drive_channels
        self.yaw_channel = yaw_channel
        self.yaw_sign = yaw_sign

        self.dr = DeadReckoningModule(dt=dt)
        self.dr.slip_gate_enabled = True

        self.mode = "idle"  # "idle", "wander", "homing"
        self.tick_count = 0

    def set_discovered_vestibular(self, channel: int, sign: float):
        """Sets the discovered vestibular sensor channel and sign."""
        self.yaw_channel = channel
        self.yaw_sign = sign

    def reset_spatial_state(self):
        """Zeros out dead-reckoning state at birthplace."""
        self.dr.reset()
        self.tick_count = 0
        self.mode = "idle"

    def update_sensors_and_odometry(
        self,
        s_current: np.ndarray,
        kinematic_state: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Updates internal dead reckoning using discovered sensor channel and Stage 1.6 kinematics.
        """
        assert self.yaw_channel is not None, "Vestibular channel must be discovered before odometry update"
        raw_wz = float(s_current[self.yaw_channel])
        wz_signal = raw_wz * self.yaw_sign

        rec = self.dr.update(
            v_hat_x=kinematic_state["v_hat_x"],
            omega_z=wz_signal,
            slip_ratio=kinematic_state["slip_ratio"]
        )
        self.tick_count += 1
        return rec

    def compute_wander_action(self, tick: int, seed_offset: float = 0.0) -> np.ndarray:
        """
        Generates pseudo-random exploratory wander commands.
        """
        fwd = 0.12 + 0.02 * math.cos(tick * 0.08 + seed_offset)
        steer = 0.07 * math.sin(tick * 0.14 + seed_offset)
        u = np.zeros(6, dtype=np.float64)
        u[self.drive_channels[0]] = np.clip(fwd - steer, -0.15, 0.15)
        u[self.drive_channels[1]] = np.clip(fwd + steer, -0.15, 0.15)
        return u

    def compute_homing_action(self) -> Tuple[np.ndarray, bool, float]:
        """
        Computes closed-loop steering command to steer toward birthplace (0, 0)
        using internal dead-reckoning belief.

        Returns:
            (u_action, is_home, distance_to_home)
        """
        dx_home = -self.dr.x
        dy_home = -self.dr.y
        dist_home = math.sqrt(dx_home**2 + dy_home**2)

        # Stop condition: internal belief within 5 cm of origin
        if dist_home <= 0.05:
            return np.zeros(6, dtype=np.float64), True, dist_home

        target_heading = math.atan2(dy_home, dx_home)
        heading_err = target_heading - self.dr.theta
        heading_err = math.atan2(math.sin(heading_err), math.cos(heading_err))

        # Closed-loop heading P-controller
        steer = np.clip(1.6 * heading_err, -0.10, 0.10)
        fwd = 0.11 if abs(heading_err) < 0.45 else 0.02

        u = np.zeros(6, dtype=np.float64)
        u[self.drive_channels[0]] = np.clip(fwd - steer, -0.15, 0.15)
        u[self.drive_channels[1]] = np.clip(fwd + steer, -0.15, 0.15)

        return u, False, dist_home
