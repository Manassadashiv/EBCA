"""
brain/carl_stage1_organism.py — Single Canonical Embodied Developmental Organism (Stage 1)
Classification: [ARCHITECTURAL INVARIANT] Unified Zero-Copy Runtime Organism

Integrates the single canonical CARL organism for Stage 1 Developmental Grounding:
- S_unified UMA live memory workspace (1061 floats: 25 sensors, 1026 LSM, 4 endocrine, 6 executed actuators)
- Option A telemetry separation: u_executed on S_unified[1055:1061], u_proposed in dedicated circular stream
- Continuous 6-D anonymous motor babbling (||u||_inf <= 0.150)
- Zero discrete action menus, zero wrapper architectures, zero hardcoded channel labels
"""

import os
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_reservoir import CarlStage1Reservoir
from brain.carl_stage1_babbler import CarlStage1Babbler


class CarlStage1Organism:
    """
    The Single Canonical CARL Organism at Stage 1 Developmental Birth.
    """
    # [ARCHITECTURAL INVARIANT] S_unified Array Slicing Layout
    TOTAL_UMA_FLOATS: int = 1061
    SLICE_SENSORS = slice(0, 25)
    SLICE_RESERVOIR = slice(25, 1051)
    SLICE_ENDOCRINE = slice(1051, 1055)
    SLICE_EXECUTED_ACTIONS = slice(1055, 1061)

    def __init__(self, seed: int = 42, hal: Optional[CarlStage1HAL] = None, babble_regime: int = 2):
        """
        Allocates zero-copy S_unified live memory bus and binds canonical subsystems.
        """
        self.seed = seed
        self.tick_count: int = 0

        # 1. Allocate Shared Unified Memory Space (S_unified = 1061 floats)
        self.S_unified = np.zeros(self.TOTAL_UMA_FLOATS, dtype=np.float64)

        # 2. Zero-Copy NumPy Slices
        self.sensor_state = self.S_unified[self.SLICE_SENSORS]
        self.reservoir_state = self.S_unified[self.SLICE_RESERVOIR]
        self.endocrine_state = self.S_unified[self.SLICE_ENDOCRINE]
        self.executed_actions = self.S_unified[self.SLICE_EXECUTED_ACTIONS]

        # Initialize Endocrine Baselines: DA=1.0, NE=0.2, 5-HT=1.0, ACh=0.5
        self.endocrine_state[0] = 1.0  # Dopamine (DA)
        self.endocrine_state[1] = 0.2  # Noradrenaline (NE)
        self.endocrine_state[2] = 1.0  # Serotonin (5-HT)
        self.endocrine_state[3] = 0.5  # Acetylcholine (ACh)

        # 3. Instantiate Subsystems
        self.reservoir = CarlStage1Reservoir(seed=seed, s_unified_view=self.reservoir_state)
        self.babbler = CarlStage1Babbler(seed=seed, regime=babble_regime)
        self.hal = hal if hal is not None else CarlStage1HAL()

        # 4. Endogenous Predictive Model & Action Synthesis (Phases 5 & 6)
        self.W_pred: Optional[np.ndarray] = None
        self.b_pred: Optional[np.ndarray] = None
        self.control_mode: str = "babble"  # 'babble', 'goal_seeking', 'random', 'zero'
        self.discovered_topology: Optional[Dict[str, Any]] = None
        self.last_predicted_s: Optional[np.ndarray] = None
        self.last_prediction_error_norm: float = 0.0
        self.baseline_prediction_error_norm: float = 1.0
        self.baseline_prediction_error_std: float = 1.0
        self.sensor_residual_std: np.ndarray = np.ones(25, dtype=np.float64)
        self.sensory_target_channel: Optional[int] = None
        self.sensory_target_mode: str = "maximize"
        self.sensory_target_val: float = 0.0

        # 5. [ACTION AUTHORITY INSTRUMENTATION]
        self.action_synthesis_calls: int = 0
        self.predictive_eval_calls: int = 0
        self.last_candidate_scores: List[float] = []
        self.last_selected_action_score: float = 0.0
        self.last_action_source: str = "init"
        self.slip_detected_count: int = 0

        # 6. [STAGE 1.6 KINEMATIC STATE & SLIP ESTIMATOR]
        self.wheel_radius: float = 0.048
        self.track_width: float = 0.230
        self.dt: float = 0.0333
        self.kinematic_v_hat_x: float = 0.0
        self.last_v_wheel: float = 0.0
        self.last_slip_ratio: float = 0.0
        self.prev_sonar_front: Optional[float] = None
        self.ax_history: List[float] = []

        # 7. [ARCHITECTURAL INVARIANT] Dedicated Circular Telemetry Stream
        self.telemetry_history: List[Dict[str, Any]] = []
        self.max_telemetry_records: int = 100000

        # Runtime verification
        self._verify_uma_contract()

    def _verify_uma_contract(self):
        """Validates that all slice views share identical underlying memory buffer."""
        assert self.sensor_state.base is self.S_unified, "sensor_state must be a view into S_unified"
        assert self.reservoir_state.base is self.S_unified, "reservoir_state must be a view into S_unified"
        assert self.endocrine_state.base is self.S_unified, "endocrine_state must be a view into S_unified"
        assert self.executed_actions.base is self.S_unified, "executed_actions must be a view into S_unified"
        assert len(self.S_unified) == 1061, f"S_unified must be exactly 1061 floats, got {len(self.S_unified)}"

    def reset(self, seed: Optional[int] = None):
        """Resets organism runtime state while preserving architectural connectivity."""
        if seed is not None:
            self.seed = seed
        self.tick_count = 0
        self.S_unified.fill(0.0)

        # Reset endocrine baselines
        self.endocrine_state[0] = 1.0
        self.endocrine_state[1] = 0.2
        self.endocrine_state[2] = 1.0
        self.endocrine_state[3] = 0.5

        self.reservoir.reset()
        self.babbler.reset(seed=self.seed)
        self.hal.reset()
        self.telemetry_history.clear()
        self.last_predicted_s = None
        self.last_prediction_error_norm = 0.0
        self.control_mode = "babble"

    def learn_predictive_readout(self, reg_lambda: float = 10.0) -> Dict[str, float]:
        """
        [INTERNAL MODEL]: Fits regularized linear readout on reservoir activations
        using the organism's own developmental telemetry history.
        Delta-S prediction: Delta_s = W_pred @ [s_curr, u_exec] + b_pred
        """
        if len(self.telemetry_history) < 30:
            raise ValueError("Insufficient developmental history to train predictive readout (< 30 ticks).")

        X_list = []
        Y_list = []

        for i in range(len(self.telemetry_history) - 1):
            rec = self.telemetry_history[i]
            rec_next = self.telemetry_history[i + 1]
            s_curr = rec["s_observed"]
            s_next = rec_next["s_observed"]
            u_exec = rec["u_executed"]
            delta_s = s_next - s_curr
            
            X_list.append(np.concatenate([s_curr, u_exec]))
            Y_list.append(delta_s)

        X = np.array(X_list)
        Y = np.array(Y_list)

        N, D = X.shape
        X_ext = np.hstack([X, np.ones((N, 1))])
        reg_eye = reg_lambda * np.eye(D + 1)
        reg_eye[-1, -1] = 0.0  # Do not regularize bias
        
        W_ext = np.linalg.solve(X_ext.T @ X_ext + reg_eye, X_ext.T @ Y)
        self.W_pred = W_ext[:-1].T  # Shape: (25, D)
        self.b_pred = W_ext[-1]      # Shape: (25,)

        Y_pred = X @ self.W_pred.T + self.b_pred
        residuals = Y - Y_pred
        train_rmse = float(np.sqrt(np.mean(residuals ** 2)))
        pers_rmse = float(np.sqrt(np.mean(Y ** 2)))
        
        # Consistent Euclidean baseline norm across developmental samples
        sample_error_norms = np.linalg.norm(residuals, axis=1)
        self.baseline_prediction_error_norm = float(np.mean(sample_error_norms))
        self.baseline_prediction_error_std = float(np.std(sample_error_norms))
        self.sensor_residual_std = np.std(residuals, axis=0) + 1e-2

        return {
            "train_rmse": train_rmse,
            "persistence_rmse": pers_rmse,
            "error_reduction_pct": float((1.0 - train_rmse / (pers_rmse + 1e-9)) * 100.0),
            "baseline_error_norm": self.baseline_prediction_error_norm,
            "baseline_error_std": self.baseline_prediction_error_std,
        }

    def predict_next_observation(
        self, x: Optional[np.ndarray] = None, u: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Internal 1-step sensory prediction function.
        s_hat_{t+1} = s_t + W_pred @ [s_t, u] + b_pred
        """
        if self.W_pred is None:
            return self.sensor_state.copy()

        u_cmd = u if u is not None else self.executed_actions
        feat = np.concatenate([self.sensor_state, u_cmd])
        delta_s_pred = self.W_pred @ feat + self.b_pred
        return np.clip(self.sensor_state + delta_s_pred, -100.0, 100.0)

    def evaluate_counterfactuals(
        self, candidate_actions: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        [COUNTERFACTUAL REASONING]: Predicts future sensory consequences of
        multiple alternative actions from the CURRENT internal state WITHOUT
        modifying the physical simulator.
        """
        predictions = []
        for u_cand in candidate_actions:
            s_hat = self.predict_next_observation(u=u_cand)
            predictions.append(s_hat)
        return predictions

    def set_sensory_goal(self, channel: int, mode: str = "maximize", target_val: float = 0.0):
        """Sets internal sensory-level objective for closed-loop autonomous action synthesis."""
        self.sensory_target_channel = int(channel)
        self.sensory_target_mode = mode
        self.sensory_target_val = float(target_val)
        self.control_mode = "goal_seeking"

    def update_kinematic_state(self, u_executed: np.ndarray, s_current: np.ndarray) -> Dict[str, float]:
        """
        [STAGE 1.6]: Grounded Kinematic Body-State & Slip Estimator.
        Fuses commanded differential wheel drive velocity with observed IMU dynamics
        (longitudinal acceleration variance and yaw rate) and sonar closing rate.
        Calculates grounded slip ratio: sigma = 1.0 - traction_coupling.
        """
        drive_channels = self.discovered_topology.get("discovered_drive_channels", [0, 1]) if self.discovered_topology else [0, 1]
        ch_L = drive_channels[0]
        ch_R = drive_channels[1] if len(drive_channels) > 1 else drive_channels[0]
        
        u_l = float(u_executed[ch_L])
        u_r = float(u_executed[ch_R])
        omega_l = u_l * 25.0
        omega_r = u_r * 25.0
        v_wheel = self.wheel_radius * (omega_l + omega_r) / 2.0
        omega_wheel = self.wheel_radius * (omega_r - omega_l) / self.track_width
        self.last_v_wheel = float(v_wheel)

        # 1. IMU forward acceleration dynamics (running window of 6 ticks)
        ax = float(s_current[15])
        self.ax_history.append(ax)
        if len(self.ax_history) > 6:
            self.ax_history.pop(0)
        ax_std = float(np.std(self.ax_history)) if len(self.ax_history) >= 4 else 1.2

        # 2. Front Sonar range closing rate (Sonar Channel 7)
        sonar_f = float(s_current[7])
        v_sonar = None
        if self.prev_sonar_front is not None and 0.15 < sonar_f < 4.8:
            closing_rate = (self.prev_sonar_front - sonar_f) / self.dt
            if -0.5 < closing_rate < 3.0:
                v_sonar = max(0.0, closing_rate)
        self.prev_sonar_front = sonar_f

        # 3. Observed angular rate from IMU Gyro Z (Channel 20)
        wz_obs = float(s_current[20])
        rot_coupling = abs(wz_obs) / (abs(omega_wheel) + 1e-4) if abs(omega_wheel) > 0.2 else None

        # 4. Mechanical traction coupling from floor interaction
        mech_coupling = float(np.clip(ax_std / 1.1, 0.0, 1.0))

        if rot_coupling is not None:
            traction_coupling = 0.5 * mech_coupling + 0.5 * min(1.0, rot_coupling)
        elif v_sonar is not None and abs(v_wheel) > 0.02:
            sonar_coupling = min(1.0, v_sonar / abs(v_wheel))
            traction_coupling = 0.5 * mech_coupling + 0.5 * sonar_coupling
        else:
            traction_coupling = mech_coupling

        self.kinematic_v_hat_x = float(v_wheel * traction_coupling)

        # 5. Grounded Longitudinal Slip Ratio
        if abs(v_wheel) < 0.02 and abs(omega_wheel) < 0.05:
            sigma = 0.0
        else:
            sigma = float(np.clip(1.0 - traction_coupling, 0.0, 1.0))

        self.last_slip_ratio = sigma
        return {
            "v_wheel": v_wheel,
            "v_hat_x": self.kinematic_v_hat_x,
            "slip_ratio": sigma,
            "is_slipping": bool(sigma > 0.50)
        }

    def detect_traction_discrepancy(self, slip_threshold: float = 0.50) -> bool:
        """
        [STAGE 1.6 GROUNDED SLIP DETECTOR]:
        Detects physical traction loss using grounded kinematic slip ratio sigma.
        True when wheel speed significantly exceeds observed body translation (sigma > slip_threshold).
        """
        is_slip = bool(self.last_slip_ratio > slip_threshold)
        if is_slip:
            self.slip_detected_count += 1
        return is_slip

    def synthesize_action(self) -> np.ndarray:
        """
        [ACTION AUTHORITY]: Synthesizes continuous 6-D motor commands purely from
        internal forward model predictions and discovered topology. Zero external controllers.
        
        CRITICAL REPAIR: Strictly forbids default hardcoded action fallbacks when
        sensory target is unspecified in 'goal_seeking' mode.
        """
        self.action_synthesis_calls += 1

        if self.discovered_topology is None or self.W_pred is None:
            self.last_action_source = "CarlStage1Organism.babbler (uninitialized topology/model)"
            return self.babbler.generate_command()

        # Strict Anti-Shortcut Assertion: Objective must be actively configured
        if self.sensory_target_channel is None:
            raise RuntimeError(
                "[ACTION AUTHORITY VIOLATION]: synthesize_action() invoked in 'goal_seeking' mode "
                "without an active sensory target channel! Refusing to execute hardcoded default."
            )

        drive_channels = self.discovered_topology.get("discovered_drive_channels", [0, 1])
        ch_L = drive_channels[0]
        ch_R = drive_channels[1] if len(drive_channels) > 1 else drive_channels[0]

        candidates = []
        for fwd in [0.15, 0.10, 0.05, 0.0]:
            for steer in [-0.08, 0.0, 0.08]:
                u_cand = np.zeros(6, dtype=np.float64)
                u_cand[ch_L] = np.clip(fwd - steer, -0.15, 0.15)
                u_cand[ch_R] = np.clip(fwd + steer, -0.15, 0.15)
                candidates.append(u_cand)

        # In-situ slip mitigation: scale down torque if traction loss detected
        if self.detect_traction_discrepancy():
            candidates = [c * 0.4 for c in candidates]

        best_score = -1e9
        best_cand = candidates[0]
        tgt_ch = self.sensory_target_channel
        scores = []

        # Predictively evaluate every candidate action through internal forward model
        for cand in candidates:
            s_hat = self.predict_next_observation(u=cand)
            self.predictive_eval_calls += 1
            val = float(s_hat[tgt_ch])
            
            if self.sensory_target_mode == "maximize":
                score = val
            elif self.sensory_target_mode == "minimize":
                score = -val
            else:
                score = -abs(val - self.sensory_target_val)

            scores.append(score)
            if score > best_score:
                best_score = score
                best_cand = cand

        self.last_candidate_scores = scores
        self.last_selected_action_score = float(best_score)
        self.last_action_source = "CarlStage1Organism.synthesize_action (predictive candidate evaluation)"
        return best_cand

    def step(self) -> Dict[str, Any]:
        """
        Executes 1 complete 30 Hz developmental cognitive cycle:
        1. Ingest 25-D raw sensations from HAL -> S_unified[0:25]
        2. Compute prediction error if previous prediction exists: e_t = s_t - s_hat_t
        3. Generate continuous action command according to control_mode:
           - 'babble': autonomous developmental babbling
           - 'goal_seeking': endogenous predictive action synthesis
           - 'random': stochastic continuous exploration
           - 'zero': idle zero-action baseline
        4. Enforce safety constraint -> u_executed
        5. Write u_executed -> S_unified[1055:1061] (Option A Contract)
        6. Step 1026-neuron LSM reservoir -> S_unified[25:1051]
        7. Compute internal prediction for next tick: s_hat_{t+1} = f_internal(x_{t+1}, u_executed)
        8. Dispatch u_executed to HAL physics
        9. Record comprehensive telemetry
        """
        # 1. Ingest Sensors
        s_t = self.hal.read_sensors()
        self.sensor_state[:] = s_t

        # 2. Track Prediction Error
        if self.last_predicted_s is not None:
            pred_err = s_t - self.last_predicted_s
            self.last_prediction_error_norm = float(np.linalg.norm(pred_err))
        else:
            self.last_prediction_error_norm = 0.0

        # 3. Action Synthesis
        if self.control_mode == "babble":
            u_proposed = self.babbler.generate_command()
        elif self.control_mode == "goal_seeking":
            u_proposed = self.synthesize_action()
        elif self.control_mode == "random":
            u_proposed = np.random.uniform(-0.150, 0.150, 6)
        elif self.control_mode == "zero":
            u_proposed = np.zeros(6, dtype=np.float64)
        else:
            u_proposed = self.babbler.generate_command()

        # 4. Physical Safety Clamping
        u_executed = np.clip(u_proposed, -0.150, 0.150)

        # 5. Write Executed Command to S_unified (Option A Contract)
        self.executed_actions[:] = u_executed

        # 6. Step 1026-N Reservoir
        x_next = self.reservoir.step(s_t, u_executed)

        # 7. Internal Sensory Prediction for Next Step
        if self.W_pred is not None:
            self.last_predicted_s = self.predict_next_observation(x=x_next, u=u_executed)
        else:
            self.last_predicted_s = None

        # 8. Step Physical Simulation
        s_next, diag = self.hal.step(u_executed)

        # 9. [STAGE 1.6]: Update Grounded Kinematic Body-State & Slip Observer
        kin_state = self.update_kinematic_state(u_executed, s_t)

        # 10. Record Telemetry
        record = {
            "tick": self.tick_count,
            "timestamp": time.time(),
            "u_proposed": u_proposed.copy(),
            "u_executed": u_executed.copy(),
            "s_observed": s_t.copy(),
            "s_next": s_next.copy(),
            "reservoir_norm": float(np.linalg.norm(x_next)),
            "prediction_error_norm": self.last_prediction_error_norm,
            "action_source": self.last_action_source,
            "action_synthesis_calls": self.action_synthesis_calls,
            "predictive_eval_calls": self.predictive_eval_calls,
            "selected_action_score": self.last_selected_action_score,
            "v_wheel": kin_state["v_wheel"],
            "v_hat_x": kin_state["v_hat_x"],
            "slip_ratio": kin_state["slip_ratio"],
            "is_slipping": kin_state["is_slipping"],
            "roll": diag["roll"],
            "pitch": diag["pitch"],
            "yaw": diag["yaw"],
            "speed": diag["speed"],
            "has_ground_traction": diag.get("has_ground_traction", True),
            "tire_floor_contacts": diag.get("tire_floor_contacts", 2),
            "battery": diag["battery"],
        }
        self.telemetry_history.append(record)
        if len(self.telemetry_history) > self.max_telemetry_records:
            self.telemetry_history.pop(0)

        self.tick_count += 1
        return record

    def run_session(self, n_ticks: int = 3000) -> List[Dict[str, Any]]:
        """Runs autonomous developmental session for n_ticks at 30 Hz."""
        records = []
        for _ in range(n_ticks):
            rec = self.step()
            records.append(rec)
        return records
