"""
test_gis_and_memory.py — Unit Tests for GIS-901, HDC-102, and CIG-301

Validates:
1. GIS-901 state save/load round-tripping for all persistent cognitive subsystems.
2. HDC-102 10,000-D bipolar binding, bundling, orthogonality, and similarity retrieval.
3. CIG-301 constraint evaluation and compound failure risk factor calculations.
"""

import os
import sys
import tempfile
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from brain.carl_gis import GlobalIntegratedStateManager
from brain.carl_hdc import HolographicEpisodicMemory
from brain.carl_cig import ConstraintInteractionGraph
from brain.carl_reservoir import LiquidStateReservoir
from brain.carl_grid_cells import HippocampalNavigator
from brain.carl_physarum import PhysarumMaze


def test_hdc_bipolar_binding_and_bundling():
    hdc = HolographicEpisodicMemory(dimension=1000, n_places=20, seed=42)

    # 1. Bipolar values strictly in {-1, +1}
    assert np.all(np.isin(hdc.place_bases, [-1.0, 1.0]))
    assert np.all(np.isin(hdc.sonar_bases, [-1.0, 1.0]))

    # 2. Binding (⊗) is self-inverse: A ⊗ B ⊗ B == A
    a = hdc.place_bases[0]
    b = hdc.sonar_bases[0]
    bound = hdc.bind(a, b)
    unbound = hdc.bind(bound, b)
    assert np.allclose(unbound, a)

    # 3. Bundling produces {-1, +1} result
    bundle = hdc.bundle([a, b, hdc.place_bases[1]])
    assert np.all(np.isin(bundle, [-1.0, 1.0]))

    # 4. Episode encoding and recording
    sonar = np.ones(24) * 2.5
    endocrine = np.array([1.2, 0.3, 0.8, 0.5])
    assert hdc.record_place_transition(0, sonar, endocrine) is True
    # Duplicate immediate place transition should be ignored (event-driven safeguard)
    assert hdc.record_place_transition(0, sonar, endocrine) is False
    assert hdc.episode_count == 1

    # 5. Query similarity
    ep_vec = hdc.encode_episode(0, sonar, endocrine)
    sim = hdc.query_similarity(ep_vec)
    assert sim > 0.5  # High cosine similarity to stored memory


def test_cig_constraint_evaluation_and_risk():
    cig = ConstraintInteractionGraph(num_constraints=4, learning_rate=0.1)

    # No constraint active
    flags = cig.evaluate_constraints(min_sonar=3.0, battery_level=0.9, motor_commands=np.array([1.0, 1.0]), current_velocity=0.5)
    assert not np.any(flags)
    assert cig.get_risk_factor() == 0.0

    # Obstacle proximity alone
    flags = cig.evaluate_constraints(min_sonar=0.15, battery_level=0.9, motor_commands=np.array([1.0, 1.0]), current_velocity=0.5)
    assert bool(flags[0]) is True
    assert cig.get_risk_factor() == 0.0  # Single constraint alone has low compound risk

    # Simultaneous Obstacle Proximity + Low Battery + Motor Saturation
    flags = cig.evaluate_constraints(min_sonar=0.15, battery_level=0.10, motor_commands=np.array([32.0, 32.0]), current_velocity=0.0)
    assert np.sum(flags) >= 3
    risk = cig.get_risk_factor()
    assert risk > 0.5
    assert cig.co_occurrences > 0


def test_gis_roundtrip_persistence():
    with tempfile.TemporaryDirectory() as tmp_dir:
        gis = GlobalIntegratedStateManager(save_dir=tmp_dir)
        filepath = os.path.join(tmp_dir, "test_gis_state.npz")

        res = LiquidStateReservoir(N=100, M=37, K=3, seed=42)
        res.W_out[0, 5] = 4.25
        res.total_rls_updates = 33

        hip = HippocampalNavigator()
        hip.places.stamp_reward(10, 8.5)

        phys = PhysarumMaze(rows=10, cols=10)
        phys.D_h[0, 0] = 7.5

        cig = ConstraintInteractionGraph(num_constraints=4)
        cig.A_CIG[0, 1] = 0.85

        hdc = HolographicEpisodicMemory(dimension=500, n_places=20)
        hdc.M_spatial += np.ones(500)
        hdc.episode_count = 12

        # Save
        saved = gis.save_state(
            filepath=filepath,
            reservoir=res,
            hippocampus=hip,
            physarum=phys,
            cig=cig,
            hdc=hdc,
            stats={"current_tick": 250, "food_eaten": 5, "distance_traveled": 18.2}
        )
        assert saved is True
        assert os.path.exists(filepath)

        # Create fresh blank instances to restore into
        res_new = LiquidStateReservoir(N=100, M=37, K=3, seed=99)
        hip_new = HippocampalNavigator()
        phys_new = PhysarumMaze(rows=10, cols=10)
        cig_new = ConstraintInteractionGraph(num_constraints=4)
        hdc_new = HolographicEpisodicMemory(dimension=500, n_places=20)

        # Load
        loaded = gis.load_state(
            filepath=filepath,
            reservoir=res_new,
            hippocampus=hip_new,
            physarum=phys_new,
            cig=cig_new,
            hdc=hdc_new
        )
        assert loaded is True

        # Verify exact round-trip restorations
        assert res_new.W_out[0, 5] == res.W_out[0, 5]
        assert res_new.total_rls_updates == res.total_rls_updates
        assert hip_new.places.reward_values[10] == hip.places.reward_values[10]
        assert phys_new.D_h[0, 0] == phys.D_h[0, 0]
        assert cig_new.A_CIG[0, 1] == cig.A_CIG[0, 1]
        assert hdc_new.episode_count == hdc.episode_count
        assert gis.total_lifetime_food == 5
