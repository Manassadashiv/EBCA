"""
tests/test_reservoir.py — Unit tests for carl_reservoir.LiquidStateReservoir (LSM-211, LSM-212)

Invariants tested:
  - Reservoir state stays bounded after many steps (no NaN / Inf explosion)
  - Output y is always clamped to [-2.0, 2.0]
  - Spectral radius of W_res is ≈ target (reservoir is properly initialized)
  - RLS update increments total_rls_updates counter
  - RLS reduces prediction error over repeated identical inputs (it actually learns)
  - save / load round-trip preserves W_out and RLS update count
  - State norm is non-negative
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain'))

import pytest
import numpy as np
import tempfile
from carl_reservoir import LiquidStateReservoir


@pytest.fixture
def res():
    """Small reservoir (N=50) for fast test execution."""
    return LiquidStateReservoir(N=50, M=10, K=3, seed=0)


@pytest.fixture
def res_full():
    """Full-size reservoir matching production config."""
    return LiquidStateReservoir(N=500, M=25, K=3, seed=42)


# ── Initialization ───────────────────────────────────────────────────────────

class TestInitialization:
    def test_spectral_radius_near_target(self, res_full):
        """W_res spectral radius should be within 1% of target=1.0."""
        eigenvalues = np.linalg.eigvals(res_full.W_res)
        actual_sr = float(np.max(np.abs(eigenvalues)))
        assert abs(actual_sr - 1.0) < 0.01, f"Spectral radius {actual_sr:.4f} too far from 1.0"

    def test_initial_state_is_zero(self, res):
        assert np.allclose(res.x, 0.0), "Reservoir state should start at zero"

    def test_w_out_initialized_to_zero(self, res):
        assert np.allclose(res.W_out, 0.0), "W_out should start at zero (no prior learning)"

    def test_rls_counter_starts_at_zero(self, res):
        assert res.total_rls_updates == 0


# ── Step output bounds ───────────────────────────────────────────────────────

class TestStepBounds:
    def test_output_clamped_to_motor_range(self, res):
        """Output y must always be within [-2.0, 2.0]."""
        u = np.random.randn(10) * 100  # extreme input
        for _ in range(20):
            y = res.step(u, noise_scale=5.0, dt=0.033)
        assert np.all(y >= -2.0) and np.all(y <= 2.0), f"Output {y} out of [-2, 2]"

    def test_no_nan_after_many_steps(self, res):
        """Reservoir state must not go NaN or Inf under normal operation."""
        u = np.ones(10)
        for _ in range(500):
            y = res.step(u, noise_scale=0.1, dt=0.033)
        assert not np.any(np.isnan(res.x)), "NaN detected in reservoir state"
        assert not np.any(np.isinf(res.x)), "Inf detected in reservoir state"

    def test_no_nan_with_zero_input(self, res):
        u = np.zeros(10)
        for _ in range(100):
            y = res.step(u, noise_scale=0.0, dt=0.033)
        assert not np.any(np.isnan(res.x))

    def test_output_shape_matches_k(self, res):
        u = np.zeros(10)
        y = res.step(u)
        assert y.shape == (res.K,), f"Output shape {y.shape} != ({res.K},)"

    def test_state_norm_is_nonnegative(self, res):
        res.step(np.ones(10))
        assert res.get_state_norm() >= 0.0


# ── State boundedness ────────────────────────────────────────────────────────

class TestStateBoundedness:
    def test_state_stays_bounded_after_long_run(self, res):
        """Reservoir activity should remain finite over a long run."""
        u = np.random.randn(10)
        for _ in range(2000):
            res.step(u, noise_scale=0.02, dt=0.033)
        norm = res.get_state_norm()
        assert norm < 1e6, f"Reservoir state exploded: norm={norm:.2e}"
        assert np.isfinite(norm)


# ── RLS learning ─────────────────────────────────────────────────────────────

class TestRLS:
    def test_rls_increments_counter(self, res):
        u = np.ones(10)
        res.step(u)
        y_target = np.array([0.5, -0.3, 0.1])
        res.rls_update(y_target)
        assert res.total_rls_updates == 1

    def test_rls_reduces_prediction_error_over_time(self, res):
        """RLS should reduce error on a fixed target after repeated updates."""
        u = np.ones(10) * 0.5
        y_target = np.array([1.0, -1.0, 0.5])

        # Warm up reservoir
        for _ in range(50):
            res.step(u, noise_scale=0.0)

        # Record initial error
        res.step(u, noise_scale=0.0)
        initial_error = np.linalg.norm(y_target - res.W_out @ res.x)

        # Train 200 steps
        for _ in range(200):
            res.step(u, noise_scale=0.0)
            res.rls_update(y_target)

        final_error = np.linalg.norm(y_target - res.W_out @ res.x)
        assert final_error < initial_error, \
            f"RLS did not reduce error: initial={initial_error:.4f}, final={final_error:.4f}"

    def test_rls_does_not_produce_nan_weights(self, res):
        """W_out should never become NaN after many RLS updates."""
        u = np.random.randn(10)
        y_target = np.array([0.3, -0.5, 0.1])
        for _ in range(500):
            res.step(u, noise_scale=0.01)
            res.rls_update(y_target)
        assert not np.any(np.isnan(res.W_out)), "W_out has NaN after RLS updates"
        assert not np.any(np.isnan(res.P)), "P matrix has NaN after RLS updates"

    def test_p_matrix_stays_bounded(self, res):
        """P matrix norm should not explode."""
        u = np.ones(10)
        for _ in range(200):
            res.step(u)
            res.rls_update(np.zeros(res.K))
        p_norm = np.linalg.norm(res.P)
        assert p_norm < 1e7, f"P matrix norm exploded: {p_norm:.2e}"


# ── Save / load round-trip ───────────────────────────────────────────────────

class TestSaveLoad:
    def test_save_load_preserves_w_out(self, res):
        """After training and saving, loaded reservoir should have identical W_out."""
        u = np.ones(10)
        y_target = np.array([0.5, -0.3, 0.1])
        for _ in range(30):
            res.step(u)
            res.rls_update(y_target)
        w_out_before = res.W_out.copy()

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_res")
            res.save(path)
            res2 = LiquidStateReservoir(N=50, M=10, K=3, seed=0)
            res2.load(path + ".npz")

        assert np.allclose(w_out_before, res2.W_out), "W_out changed after save/load"

    def test_save_load_preserves_rls_count(self, res):
        u = np.ones(10)
        for _ in range(42):
            res.step(u)
            res.rls_update(np.zeros(res.K))
        assert res.total_rls_updates == 42

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_res")
            res.save(path)
            res2 = LiquidStateReservoir(N=50, M=10, K=3, seed=0)
            res2.load(path + ".npz")

        assert res2.total_rls_updates == 42

    def test_load_returns_false_if_file_missing(self, res):
        result = res.load("/nonexistent/path/reservoir.npz")
        assert result is False
