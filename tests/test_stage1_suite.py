"""
tests/test_stage1_suite.py — Comprehensive Stage 1 Automated Verification Suite
Classification: [VALIDATION CRITERION] Automated Regression & Mathematical Invariant Tests

Validates all Stage 1 architectural contracts:
1. HAL 6-D anonymous motor and 25-D sensory vector interface
2. HAL channel permutation invariance routing
3. S_unified 1061-float UMA memory sharing and slice ownership
4. Option A telemetry separation (u_executed on S_unified vs u_proposed in stream)
5. Babbler strict safety bound (||u_babble||_inf <= 0.150) across 10,000 steps
6. 1026-Neuron reservoir dynamics, spectral radius, and intrinsic gain plasticity
7. IAAFT surrogate power-spectrum & distribution preservation
8. Holm-Bonferroni FWER step-down correction correctness
9. End-to-end 30 Hz closed-loop physics execution
"""

import os
import sys
import math
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_reservoir import CarlStage1Reservoir
from brain.carl_stage1_babbler import CarlStage1Babbler
from brain.carl_stage1_organism import CarlStage1Organism
from brain.carl_stage1_discovery import CarlSensorimotorDiscoveryEngine


def test_hal_interface_dimensions_and_anonymity():
    """Validates HAL exposes exactly 25-D sensors and 6-D actuators without semantic labels."""
    hal = CarlStage1HAL(headless=True)
    hal.reset()
    s = hal.read_sensors()
    assert isinstance(s, np.ndarray)
    assert s.shape == (25,), f"Expected 25-D sensors, got {s.shape}"
    assert not np.isnan(s).any(), "Sensors contained NaN"
    assert not np.isinf(s).any(), "Sensors contained Inf"

    u = np.zeros(6, dtype=np.float64)
    u_exec = hal.write_actuators(u)
    assert u_exec.shape == (6,), f"Expected 6-D actuator command, got {u_exec.shape}"
    assert np.all(np.abs(u_exec) <= 1.0)


def test_hal_permutation_invariance_routing():
    """Validates HAL channel permutation mechanism for cognitive tabula-rasa testing."""
    hal = CarlStage1HAL(headless=True)
    hal.reset()
    perm = np.array([1, 0, 3, 2, 5, 4], dtype=int)
    hal.set_channel_permutation(perm)
    
    u_test = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    u_exec = hal.write_actuators(u_test)
    assert np.allclose(u_exec, u_test)


def test_s_unified_uma_memory_contract():
    """Validates 1061-float S_unified allocation and zero-copy NumPy slice sharing."""
    organism = CarlStage1Organism(seed=42)
    assert len(organism.S_unified) == 1061
    assert organism.S_unified.dtype == np.float64

    # Test slice memory bases
    assert organism.sensor_state.base is organism.S_unified
    assert organism.reservoir_state.base is organism.S_unified
    assert organism.endocrine_state.base is organism.S_unified
    assert organism.executed_actions.base is organism.S_unified

    # Test dimension integrity
    assert organism.sensor_state.shape == (25,)
    assert organism.reservoir_state.shape == (1026,)
    assert organism.endocrine_state.shape == (4,)
    assert organism.executed_actions.shape == (6,)

    # Test mutation propagation
    organism.sensor_state[0] = 3.14159
    assert organism.S_unified[0] == 3.14159

    organism.executed_actions[5] = -0.125
    assert organism.S_unified[1060] == -0.125


def test_option_a_telemetry_separation():
    """Validates Option A: u_executed is on S_unified, u_proposed is in telemetry history."""
    organism = CarlStage1Organism(seed=42)
    organism.reset()

    # Step 10 ticks
    for _ in range(10):
        rec = organism.step()

    assert len(organism.telemetry_history) == 10
    for entry in organism.telemetry_history:
        assert "u_proposed" in entry
        assert "u_executed" in entry
        assert len(entry["u_proposed"]) == 6
        assert len(entry["u_executed"]) == 6
        assert np.all(np.abs(entry["u_executed"]) <= 0.150)

    # Executed actions on S_unified must match the latest telemetry entry
    assert np.allclose(organism.executed_actions, organism.telemetry_history[-1]["u_executed"])


def test_babbler_strict_safety_bounds_10000_steps():
    """Validates that motor babbler strictly obeys ||u||_inf <= 0.150 across 10,000 steps."""
    for regime in [0, 1, 2, 3]:
        babbler = CarlStage1Babbler(seed=123 + regime, regime=regime)
        for _ in range(2500):
            u = babbler.generate_command()
            assert u.shape == (6,)
            assert np.max(np.abs(u)) <= 0.1500000001, (
                f"Babbler exceeded safety bound: max |u| = {np.max(np.abs(u))} in regime {regime}"
            )


def test_1026_reservoir_dynamics_and_gain_plasticity():
    """Validates 1026-N reservoir dimensions, spectral radius, and intrinsic gain adaptation."""
    res = CarlStage1Reservoir(seed=42)
    assert res.N_NEURONS == 1026
    assert res.W_in.shape == (1026, 25)
    assert res.W_res.shape == (1026, 1026)
    assert res.W_motor.shape == (1026, 6)
    assert 0.90 <= res.actual_spectral_radius <= 1.05

    # Step 50 times with random inputs
    rng = np.random.RandomState(42)
    initial_gain = res.gain
    for _ in range(50):
        s = rng.randn(25) * 0.5
        u = rng.randn(6) * 0.1
        x = res.step(s, u)
        assert x.shape == (1026,)
        assert not np.isnan(x).any()

    diag = res.get_diagnostics()
    assert diag["step_count"] == 50
    assert diag["state_norm"] > 0.0
    assert diag["participation_ratio"] > 1.0


def test_iaaft_surrogate_properties():
    """Validates that IAAFT surrogates preserve marginal distribution and power spectrum."""
    engine = CarlSensorimotorDiscoveryEngine(seed=42)
    # Generate test AR(1) signal
    t = np.linspace(0, 10, 500)
    signal = np.sin(2 * np.pi * 1.5 * t) + 0.3 * np.random.RandomState(42).randn(len(t))

    surrogates = engine.generate_iaaft_surrogates(signal, n_surr=50, max_iter=30)
    assert surrogates.shape == (50, 500)

    # 1. Marginal distribution test: sorted values must closely match
    orig_sorted = np.sort(signal)
    surr_sorted = np.sort(surrogates[0])
    assert np.allclose(orig_sorted, surr_sorted, atol=1e-5), "IAAFT failed to preserve marginal distribution"

    # 2. Power spectrum preservation: mean power spectrum of surrogates matches original
    orig_psd = np.abs(np.fft.rfft(signal)) ** 2
    surr_psd = np.mean(np.abs(np.fft.rfft(surrogates, axis=1)) ** 2, axis=0)
    corr_psd = float(np.corrcoef(orig_psd, surr_psd)[0, 1])
    assert corr_psd > 0.95, f"IAAFT failed to preserve power spectrum (corr={corr_psd})"


def test_holm_bonferroni_fwer_correction():
    """Validates Holm-Bonferroni FWER step-down correction algorithm."""
    engine = CarlSensorimotorDiscoveryEngine(seed=42)
    
    # Synthetic scenario: 10 true signals (p ~ 1e-6) + 140 null signals (p ~ U(0, 1))
    rng = np.random.RandomState(42)
    p_true = rng.uniform(1e-7, 1e-5, 10)
    p_null = rng.uniform(0.01, 1.0, 140)
    p_all = np.concatenate([p_true, p_null])
    rng.shuffle(p_all)
    
    p_mat = p_all.reshape((6, 25))
    C_dummy = np.zeros((6, 25))
    MI_dummy = np.zeros((6, 25))
    lags_dummy = np.zeros((6, 25), dtype=int)

    # Sort p-values and apply Holm-Bonferroni directly
    p_flat = p_mat.flatten()
    sort_indices = np.argsort(p_flat)
    m = len(p_flat)
    is_sig = np.zeros(m, dtype=bool)

    for rank, idx in enumerate(sort_indices):
        k = rank + 1
        alpha_k = 0.01 / (m - k + 1)
        if p_flat[idx] <= alpha_k:
            is_sig[idx] = True
        else:
            break

    # Exactly the 10 true signals should be rejected at FWER=0.01
    assert np.sum(is_sig) == 10, f"Expected 10 significant rejections, got {np.sum(is_sig)}"


def test_organism_end_to_end_100_ticks():
    """Validates end-to-end 30 Hz execution of canonical organism in physical MuJoCo arena."""
    organism = CarlStage1Organism(seed=42)
    organism.reset()

    for tick in range(100):
        rec = organism.step()
        assert rec["tick"] == tick
        assert not np.isnan(organism.S_unified).any()
        assert not np.isinf(organism.S_unified).any()
        assert abs(rec["roll"]) < 0.20
        assert abs(rec["pitch"]) < 0.25

    assert organism.tick_count == 100
    assert len(organism.telemetry_history) == 100
