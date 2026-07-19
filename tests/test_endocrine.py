"""
tests/test_endocrine.py — Unit tests for carl_endocrine.EndocrineSystem (END-201..204)

Invariants tested:
  - All neuromodulators stay within [MIN_NM, MAX_NM] after arbitrary surges + steps
  - Decay correctly returns each modulator toward its baseline (not past it)
  - Surge updates last_surge_event with the correct label
  - get_precision_weight() always returns >= 0.1 (floor contract)
  - get_exploration_noise_scale() always returns >= 0.01 (floor contract)
  - get_behavioral_mode() returns correct mode for each input combination
  - get_hunger_drive() is monotonically decreasing with battery_level
  - get_replay_blend_weight() is in [0, 1] for all inputs
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain'))

import pytest
import numpy as np
from carl_endocrine import EndocrineSystem


@pytest.fixture
def endo():
    """Fresh EndocrineSystem at baseline."""
    return EndocrineSystem()


# ── Clamping ────────────────────────────────────────────────────────────────

class TestClamping:
    def test_no_modulator_exceeds_max_after_large_surge(self, endo):
        """Surging way past MAX_NM and stepping should still clamp to MAX_NM."""
        endo.surge_da(100.0)
        endo.surge_ne(100.0)
        endo.surge_sht(100.0)
        endo.surge_ach(100.0)
        endo.step(dt=0.033)
        assert endo.DA  <= EndocrineSystem.MAX_NM
        assert endo.NE  <= EndocrineSystem.MAX_NM
        assert endo.SHT <= EndocrineSystem.MAX_NM
        assert endo.ACh <= EndocrineSystem.MAX_NM

    def test_no_modulator_goes_below_min(self, endo):
        """Even with extreme negative values, no modulator should go below 0."""
        endo.DA  = -50.0
        endo.NE  = -50.0
        endo.SHT = -50.0
        endo.ACh = -50.0
        endo.step(dt=0.033)
        assert endo.DA  >= EndocrineSystem.MIN_NM
        assert endo.NE  >= EndocrineSystem.MIN_NM
        assert endo.SHT >= EndocrineSystem.MIN_NM
        assert endo.ACh >= EndocrineSystem.MIN_NM


# ── Decay toward baseline ────────────────────────────────────────────────────

class TestDecay:
    def test_da_decays_toward_baseline_after_surge(self, endo):
        """After a DA surge, repeated steps should bring DA closer to BASELINE_DA."""
        endo.surge_da(1.5)
        elevated = endo.DA
        for _ in range(50):
            endo.step(dt=0.033)
        assert endo.DA < elevated, "DA should decay after surge"
        assert endo.DA >= EndocrineSystem.BASELINE_DA * 0.5, "DA shouldn't undershoot baseline excessively"

    def test_ne_decays_faster_than_da(self, endo):
        """NE has higher decay constant than DA — should decay faster from equal surge."""
        endo2 = EndocrineSystem()
        endo.surge_da(1.0)
        endo2.surge_ne(1.0)
        da_start, ne_start = endo.DA, endo2.NE
        for _ in range(10):
            endo.step(dt=0.033)
            endo2.step(dt=0.033)
        da_drop = da_start - endo.DA
        ne_drop = ne_start - endo2.NE
        assert ne_drop > da_drop, "NE (DECAY=3.0) should decay faster than DA (DECAY=2.0)"

    def test_baseline_is_stable_equilibrium(self, endo):
        """At baseline values, step() should produce near-zero change."""
        da_before = endo.DA
        endo.step(dt=0.033)
        assert abs(endo.DA - da_before) < 0.001, "Baseline should be a stable fixed point"


# ── Surge labelling ──────────────────────────────────────────────────────────

class TestSurgeEvents:
    def test_surge_da_sets_event_label(self, endo):
        endo.surge_da(0.5)
        assert "DA" in endo.last_surge_event

    def test_surge_ne_sets_event_label(self, endo):
        endo.surge_ne(0.3)
        assert "NE" in endo.last_surge_event

    def test_surge_sht_sets_event_label(self, endo):
        endo.surge_sht(0.2)
        assert "5HT" in endo.last_surge_event

    def test_surge_ach_sets_event_label(self, endo):
        endo.surge_ach(0.1)
        assert "ACh" in endo.last_surge_event


# ── Precision weight ─────────────────────────────────────────────────────────

class TestPrecisionWeight:
    def test_precision_weight_always_above_floor(self, endo):
        """get_precision_weight() must always return >= 0.1."""
        # Worst case: maximize inhibitory SHT, minimize ACh and NE
        endo.SHT = EndocrineSystem.MAX_NM
        endo.ACh = EndocrineSystem.MIN_NM
        endo.NE  = EndocrineSystem.MIN_NM
        assert endo.get_precision_weight() >= 0.1

    def test_precision_weight_increases_with_ach(self, endo):
        """Higher ACh should yield higher precision weight (ACh boosts attention)."""
        endo.ACh = 0.5
        low = endo.get_precision_weight()
        endo.ACh = 2.5
        high = endo.get_precision_weight()
        assert high > low

    def test_precision_weight_decreases_with_sht(self, endo):
        """Higher 5-HT should reduce precision weight (SHT is inhibitory)."""
        endo.SHT = 0.5
        high_pi = endo.get_precision_weight()
        endo.SHT = 2.5
        low_pi = endo.get_precision_weight()
        assert low_pi < high_pi


# ── Exploration noise ────────────────────────────────────────────────────────

class TestExplorationNoise:
    def test_noise_scale_always_above_floor(self, endo):
        endo.NE = 0.0
        assert endo.get_exploration_noise_scale() >= 0.01

    def test_noise_scale_scales_with_ne(self, endo):
        endo.NE = 0.1
        low = endo.get_exploration_noise_scale()
        endo.NE = 2.0
        high = endo.get_exploration_noise_scale()
        assert high > low


# ── Behavioral mode ──────────────────────────────────────────────────────────

class TestBehavioralMode:
    def test_exploit_when_food_visible(self, endo):
        assert endo.get_behavioral_mode(battery_level=0.8, food_visible=True) == "EXPLOIT"

    def test_survive_when_battery_critical(self, endo):
        assert endo.get_behavioral_mode(battery_level=0.05, food_visible=False) == "SURVIVE"

    def test_survive_when_ne_very_high(self, endo):
        endo.NE = 2.5
        assert endo.get_behavioral_mode(battery_level=0.5, food_visible=False) == "SURVIVE"

    def test_explore_when_battery_ok_no_food(self, endo):
        assert endo.get_behavioral_mode(battery_level=0.6, food_visible=False) == "EXPLORE"

    def test_exploit_overrides_low_battery(self, endo):
        """Food visible should always return EXPLOIT, even at critical battery."""
        assert endo.get_behavioral_mode(battery_level=0.01, food_visible=True) == "EXPLOIT"


# ── Hunger drive ─────────────────────────────────────────────────────────────

class TestHungerDrive:
    def test_hunger_in_unit_range(self, endo):
        for bat in [0.0, 0.25, 0.5, 0.75, 1.0, 1.5]:
            h = endo.get_hunger_drive(bat)
            assert 0.0 <= h <= 1.0, f"hunger_drive out of [0,1] for battery={bat}"

    def test_hunger_monotonically_decreasing(self, endo):
        levels = [0.0, 0.1, 0.3, 0.5, 0.8, 1.0]
        drives = [endo.get_hunger_drive(b) for b in levels]
        for i in range(len(drives) - 1):
            assert drives[i] >= drives[i+1], "Hunger should decrease as battery increases"

    def test_full_battery_zero_hunger(self, endo):
        assert endo.get_hunger_drive(1.0) == 0.0

    def test_empty_battery_max_hunger(self, endo):
        assert endo.get_hunger_drive(0.0) == 1.0


# ── Replay blend weight ──────────────────────────────────────────────────────

class TestReplayBlendWeight:
    def test_blend_always_in_unit_range(self, endo):
        for bat in [0.0, 0.5, 1.0]:
            for nav in [0.0, 1.0, 5.0, 10.0]:
                w = endo.get_replay_blend_weight(bat, nav)
                assert 0.0 <= w <= 1.0, f"blend weight {w} out of [0,1]"

    def test_high_hunger_increases_blend(self, endo):
        """Starving CARL should follow replay more urgently."""
        low  = endo.get_replay_blend_weight(battery_level=1.0, max_nav_value=2.0)
        high = endo.get_replay_blend_weight(battery_level=0.0, max_nav_value=2.0)
        assert high > low

    def test_zero_nav_value_gives_zero_blend(self, endo):
        """No nav signal = no replay guidance, regardless of hunger."""
        assert endo.get_replay_blend_weight(battery_level=0.0, max_nav_value=0.0) == 0.0
