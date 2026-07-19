"""
tests/test_grid_cells.py — Unit tests for carl_grid_cells (Nobel Prize GPS + Hippocampal Replay)

Modules tested:
  GridCellModule   — hexagonal firing, path integration, reset
  PlaceCellLayer   — firing, decode, graph construction, reward diffusion, nav targets
  HippocampalNavigator — full step, novelty, uncertainty, theta gating

Invariants tested:
  - Grid cell activity is always in [0, ~1] range (no negative rates)
  - Place cell activity sums to a positive value at any valid position
  - decode_position() returns near-actual position for strong firing
  - update_graph() correctly builds bidirectional edges
  - diffuse_rewards() propagates reward to neighbours (value > 0 in connected cells)
  - nav_values never go negative after diffusion
  - stamp_reward() creates persistent beacons that survive decay
  - get_novelty_target() returns a valid centre (not None) for a connected cell
  - HippocampalNavigator.step() returns dict with required keys and bounded values
  - Uncertainty is in [0, 1]
  - Novelty is in [0, 1]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain'))

import pytest
import math
import numpy as np
from carl_grid_cells import GridCellModule, PlaceCellLayer, HippocampalNavigator


# ── GridCellModule ────────────────────────────────────────────────────────────

class TestGridCellModule:
    @pytest.fixture
    def gcm(self):
        return GridCellModule(scale=1.0, orientation_deg=0, n_cells=32, noise=0.0)

    def test_firing_rates_non_negative(self, gcm):
        act = gcm.fire(x=0.5, y=0.5)
        assert np.all(act >= 0.0), "Grid cell firing rates must be non-negative"

    def test_firing_rates_bounded(self, gcm):
        """Max rate with noise=0 is 1.0 (when all three waves align)."""
        act = gcm.fire(x=0.0, y=0.0)
        # With noise=0, max possible rate = 1.0
        assert np.all(act <= 1.01), "Grid cell rates should not exceed 1.0 significantly"

    def test_output_shape(self, gcm):
        act = gcm.fire(x=1.0, y=2.0)
        assert act.shape == (32,)

    def test_path_integration_accumulates(self, gcm):
        """integrate() should move pi_phase by vx*dt, vy*dt."""
        gcm.reset(0.0, 0.0)
        gcm.integrate(vx=1.0, vy=0.5, dt=1.0)
        assert abs(gcm.pi_phase[0] - 1.0) < 1e-9
        assert abs(gcm.pi_phase[1] - 0.5) < 1e-9

    def test_reset_sets_pi_phase(self, gcm):
        gcm.integrate(1.0, 1.0, 10.0)
        gcm.reset(2.5, 3.1)
        assert abs(gcm.pi_phase[0] - 2.5) < 1e-9
        assert abs(gcm.pi_phase[1] - 3.1) < 1e-9

    def test_fire_without_position_uses_pi_phase(self, gcm):
        gcm.reset(1.0, 1.0)
        act_pi   = gcm.fire()           # uses pi_phase
        act_gps  = gcm.fire(1.0, 1.0)  # uses GPS
        # Should be similar (same position, noise=0)
        assert np.allclose(act_pi, act_gps, atol=0.05)

    def test_firing_rate_formula_bounded(self, gcm):
        """
        The 3-wave interference formula produces values in [-1, 1] before shift.
        After shift to [0, 1] and noise=0, all rates must be in [0, 1].
        """
        gcm2 = GridCellModule(scale=1.0, orientation_deg=0, n_cells=32, noise=0.0)
        for x in np.linspace(-3, 3, 10):
            for y in np.linspace(-3, 3, 10):
                act = gcm2.fire(x, y)
                assert np.all(act >= 0.0), f"Negative rate at ({x:.1f},{y:.1f})"
                assert np.all(act <= 1.01), f"Rate > 1 at ({x:.1f},{y:.1f})"


class GridCellModuleNoiseZero(GridCellModule):
    """Helper: zero-noise module for deterministic tests."""
    def fire(self, x=None, y=None, noise=None):
        pos = np.array([x, y], dtype=float) if x is not None else self.pi_phase
        proj = self.K @ pos
        act = np.zeros(self.n)
        for c in range(self.n):
            phi = proj + self.phases[c]
            rate = (math.cos(phi[0]) + math.cos(phi[1]) + math.cos(phi[2])) / 3.0
            act[c] = max(0.0, (rate + 1.0) / 2.0)
        return act


# ── PlaceCellLayer ────────────────────────────────────────────────────────────

class TestPlaceCellLayer:
    @pytest.fixture
    def pcl(self):
        np.random.seed(0)
        return PlaceCellLayer(n_place=100, arena_bounds=(-5, 5, -5, 5), sigma=0.4)

    def test_firing_is_non_negative(self, pcl):
        act = pcl.fire_from_position(0.0, 0.0)
        assert np.all(act >= 0.0)

    def test_firing_sums_positive(self, pcl):
        act = pcl.fire_from_position(0.0, 0.0)
        assert act.sum() > 0.0, "At least some place cells should fire at any valid position"

    def test_decode_position_near_input(self, pcl):
        """Population vector decode should recover approximately the input position."""
        x_true, y_true = 1.5, -2.0
        pcl.fire_from_position(x_true, y_true)
        x_dec, y_dec = pcl.decode_position()
        assert x_dec is not None and y_dec is not None
        assert abs(x_dec - x_true) < 1.5, f"Decoded x={x_dec:.2f} far from true x={x_true}"
        assert abs(y_dec - y_true) < 1.5, f"Decoded y={y_dec:.2f} far from true y={y_true}"

    def test_peak_cell_returns_valid_index(self, pcl):
        pcl.fire_from_position(2.0, 2.0)
        idx, centre = pcl.peak_cell()
        assert 0 <= idx < pcl.n
        assert centre.shape == (2,)

    def test_decode_returns_none_when_no_activity(self, pcl):
        pcl.activity = np.zeros(pcl.n)
        x, y = pcl.decode_position()
        assert x is None and y is None

    # ── Graph construction ───────────────────────────────────────────────

    def test_update_graph_creates_bidirectional_edge(self, pcl):
        pcl.update_graph(old_cell=0, new_cell=1, tick=10)
        assert 1 in pcl.adjacency[0]
        assert 0 in pcl.adjacency[1]

    def test_update_graph_ignores_self_transition(self, pcl):
        pcl.update_graph(old_cell=5, new_cell=5, tick=10)
        assert 5 not in pcl.adjacency[5]

    def test_update_graph_increments_edge_count(self, pcl):
        before = pcl.total_edges
        pcl.update_graph(0, 3, 1)
        pcl.update_graph(3, 7, 2)
        assert pcl.total_edges == before + 2

    def test_duplicate_edge_not_double_counted(self, pcl):
        pcl.update_graph(0, 1, 1)
        before = pcl.total_edges
        pcl.update_graph(0, 1, 2)  # same edge again
        assert pcl.total_edges == before, "Duplicate edge should not increment count"

    # ── Reward stamping ──────────────────────────────────────────────────

    def test_stamp_reward_sets_positive_value(self, pcl):
        pcl.stamp_reward(cell_idx=10, amount=5.0)
        assert pcl.reward_values[10] > 0.0

    def test_stamp_reward_sets_persistent_beacon(self, pcl):
        pcl.stamp_reward(cell_idx=10, amount=5.0)
        assert pcl.persistent_rewards[10] > 0.0

    def test_persistent_beacon_survives_heavy_decay(self, pcl):
        """After many diffusion steps, the persistent beacon should keep reward_values positive."""
        pcl.stamp_reward(cell_idx=10, amount=5.0)
        for _ in range(500):
            pcl.diffuse_rewards(gamma=0.9, decay=0.99995, n_sweeps=1)
        # reward_values should be floored by persistent_rewards * 0.5
        assert pcl.reward_values[10] > 0.0, "Persistent beacon should keep reward alive"

    # ── Reward diffusion ─────────────────────────────────────────────────

    def test_diffusion_propagates_to_neighbours(self, pcl):
        """After stamping cell 0 and connecting cells 0-1, cell 1 should get nav_value > 0."""
        pcl.update_graph(0, 1, 1)
        pcl.update_graph(1, 2, 2)
        pcl.stamp_reward(cell_idx=0, amount=3.0)
        pcl.diffuse_rewards(gamma=0.9, decay=1.0, n_sweeps=5)
        assert pcl.nav_values[1] > 0.0, "nav_value should propagate to cell 1"
        assert pcl.nav_values[2] > 0.0, "nav_value should propagate to cell 2"

    def test_nav_values_never_negative(self, pcl):
        pcl.stamp_reward(0, 1.0)
        for _ in range(20):
            pcl.diffuse_rewards()
        assert np.all(pcl.nav_values >= 0.0), "nav_values must never be negative"

    def test_reward_decays_over_time(self, pcl):
        pcl.reward_values[5] = 10.0
        pcl.persistent_rewards[5] = 0.0   # no floor
        before = pcl.reward_values[5]
        for _ in range(100):
            pcl.diffuse_rewards(decay=0.99)
        assert pcl.reward_values[5] < before, "reward_values should decay over time"

    # ── Navigation targets ───────────────────────────────────────────────

    def test_get_novelty_target_returns_none_when_no_neighbours(self, pcl):
        result = pcl.get_novelty_target(current_cell=0, current_tick=100)
        assert result is None, "Should return None for isolated cell with no graph edges"

    def test_get_novelty_target_returns_centre_when_connected(self, pcl):
        pcl.update_graph(0, 1, 1)
        result = pcl.get_novelty_target(current_cell=0, current_tick=100)
        assert result is not None
        assert result.shape == (2,)

    def test_get_replay_target_returns_none_when_no_nav_signal(self, pcl):
        result = pcl.get_replay_target(current_cell=0)
        assert result is None

    def test_get_replay_target_returns_best_neighbour(self, pcl):
        pcl.update_graph(0, 1, 1)
        pcl.update_graph(0, 2, 2)
        pcl.nav_values[1] = 0.5
        pcl.nav_values[2] = 2.0  # cell 2 is better
        result = pcl.get_replay_target(current_cell=0)
        assert result is not None
        x, y, val = result
        assert abs(x - pcl.centres[2][0]) < 1e-9, "Should return centre of best-value neighbour"

    # ── Graph stats ──────────────────────────────────────────────────────

    def test_get_graph_stats_has_required_keys(self, pcl):
        stats = pcl.get_graph_stats()
        for key in ['edges', 'connected_cells', 'max_degree', 'max_nav_value', 'reward_cells']:
            assert key in stats, f"Missing key '{key}' in graph stats"

    def test_graph_stats_edges_match_total_edges(self, pcl):
        pcl.update_graph(0, 1, 1)
        pcl.update_graph(1, 2, 2)
        stats = pcl.get_graph_stats()
        assert stats['edges'] == pcl.total_edges


# ── HippocampalNavigator ──────────────────────────────────────────────────────

class TestHippocampalNavigator:
    @pytest.fixture
    def nav(self):
        np.random.seed(1)
        return HippocampalNavigator()

    def test_step_returns_required_keys(self, nav):
        result = nav.step(0.0, 0.0, 0.1, 0.0, 0.033, learn=False)
        for key in ['grid', 'place', 'x_est', 'y_est', 'uncertainty', 'novelty', 'theta']:
            assert key in result, f"Missing key '{key}' in step output"

    def test_uncertainty_in_unit_range(self, nav):
        for x, y in [(0, 0), (2.5, -1.0), (-4.0, 4.0)]:
            result = nav.step(x, y, 0.0, 0.0, 0.033, learn=False)
            u = result['uncertainty']
            assert 0.0 <= u <= 1.0, f"Uncertainty {u} out of [0, 1] at ({x}, {y})"

    def test_novelty_in_unit_range(self, nav):
        for _ in range(10):
            result = nav.step(0.0, 0.0, 0.0, 0.0, 0.033, learn=False)
        assert 0.0 <= result['novelty'] <= 1.0

    def test_novelty_decreases_with_repeated_visits(self, nav):
        """Visiting the same location repeatedly should reduce novelty."""
        nav.step(1.0, 1.0, 0.0, 0.0, 0.033, learn=False)
        first = nav.novelty
        for _ in range(20):
            nav.step(1.0, 1.0, 0.0, 0.0, 0.033, learn=False)
        assert nav.novelty < first, "Novelty should decrease with repeated visits"

    def test_theta_gate_in_unit_range(self, nav):
        for _ in range(30):
            result = nav.step(0.0, 0.0, 0.0, 0.0, 0.033)
            assert 0.0 <= result['theta'] <= 1.0, f"Theta gate {result['theta']} out of [0, 1]"

    def test_grid_output_shape(self, nav):
        result = nav.step(0.0, 0.0, 0.0, 0.0, 0.033, learn=False)
        expected_n_grid = sum(m.n for m in nav.modules)
        assert result['grid'].shape == (expected_n_grid,)

    def test_reset_clears_uncertainty(self, nav):
        for _ in range(10):
            nav.step(0.0, 0.0, 1.0, 1.0, 0.033)
        nav.reset(0.0, 0.0)
        assert nav.uncertainty == 1.0

    def test_theta_learning_rate_in_valid_range(self, nav):
        for _ in range(20):
            nav.step(0.5, 0.5, 0.0, 0.0, 0.033)
            lam = nav.theta_learning_rate()
            assert 0.970 <= lam <= 0.999, f"theta_learning_rate {lam} out of [0.970, 0.999]"

    def test_curiosity_boost_increases_with_novelty(self, nav):
        nav.novelty = 0.0
        low = nav.curiosity_boost(0.5)
        nav.novelty = 1.0
        high = nav.curiosity_boost(0.5)
        assert high > low, "Curiosity boost should increase with novelty"
