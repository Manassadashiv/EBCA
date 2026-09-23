r"""
tools/tests/test_p0_independent_scorer.py — Unit Tests for the Hardened P0 Independent Scorer
Validates that the scorer correctly distinguishes all 12 qualification test cases.
"""

import os
import sys
import unittest
import numpy as np
import tempfile
import csv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from tools.p0_independent_scorer import evaluate_run_telemetry

def create_synthetic_csv(path: str, rows: list):
    header = [
        "tick", "timestamp_s", "pos_x", "pos_y", "yaw", "speed", "cmd_w_L", "cmd_w_R",
        "action_name", "min_obstacle_dist", "active_goal", "energy", "thermal_load",
        "curiosity_drive", "empowerment_nats", "estimated_friction", "prediction_error",
        "stuck_state", "recovery_active", "recovery_tier", "has_collision", "head_yaw"
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in rows:
            writer.writerow([r.get(k, 0) for k in header])

class TestP0IndependentScorer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_base_row(self, tick, x=0.0, y=0.0, act="STRAIGHT_FORWARD", rec=0, stuck="STUCK_IDLE", coll=0, spd=0.20, clr=2.0):
        return {
            "tick": tick,
            "timestamp_s": round(tick * 0.0333, 4),
            "pos_x": x,
            "pos_y": y,
            "yaw": 0.0,
            "speed": spd,
            "cmd_w_L": 5.0,
            "cmd_w_R": 5.0,
            "action_name": act,
            "min_obstacle_dist": clr,
            "active_goal": "GOAL_EXPLORE",
            "energy": 0.95,
            "thermal_load": 0.10,
            "curiosity_drive": 0.50,
            "empowerment_nats": 1.20,
            "estimated_friction": 2.50,
            "prediction_error": 0.05,
            "stuck_state": stuck,
            "recovery_active": rec,
            "recovery_tier": 1 if rec else 0,
            "has_collision": coll,
            "head_yaw": 0.0
        }

    # TEST 1: No collision + normal finish -> PASS
    def test_01_normal_clean_pass(self):
        csv_p = os.path.join(self.temp_dir.name, "t1.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(150)]
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T1", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "PASS")

    # TEST 2: No collision + active recovery at end -> FAIL
    def test_02_active_recovery_at_end_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t2.csv")
        rows = [self.make_base_row(i, x=i*0.005) for i in range(140)]
        rows += [self.make_base_row(i, x=1.0, act="RECOVERY_FORWARD_BREAKOUT", rec=1) for i in range(140, 150)]
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T2", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("TERMINATED_IN_ACTIVE_RECOVERY", res["gate_violations"])

    # TEST 3: No collision + excessive recovery duration (>70 ticks) -> FAIL
    def test_03_recovery_loop_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t3.csv")
        rows = [self.make_base_row(i, x=0.1) for i in range(20)]
        rows += [self.make_base_row(i, x=0.2, act="RECOVERY_SPIN_LEFT", rec=1) for i in range(20, 110)] # 90 ticks in rec
        rows += [self.make_base_row(i, x=0.5) for i in range(110, 150)]
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T3", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("EXCESSIVE_RECOVERY_DURATION", res["gate_violations"])

    # TEST 4: No collision + recovery success + normal return -> PASS
    def test_04_recovery_success_and_normal_return_pass(self):
        csv_p = os.path.join(self.temp_dir.name, "t4.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(50)]
        rows += [self.make_base_row(i, x=0.5, act="RECOVERY_REVERSE_CURVE_LEFT", rec=1) for i in range(50, 75)] # 25 ticks in rec
        rows += [self.make_base_row(i, x=0.5 + (i-75)*0.01) for i in range(75, 150)] # 75 ticks normal policy
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T4", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "PASS")

    # TEST 5: Collision -> FAIL
    def test_05_collision_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t5.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(100)]
        rows[45]["has_collision"] = 1
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T5", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("BODY_COLLISION_BREACH", res["gate_violations"])

    # TEST 6: Missing telemetry -> FAIL
    def test_06_missing_telemetry_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "non_existent.csv")
        res = evaluate_run_telemetry(csv_p, {"run_id": "T6", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")

    # TEST 7: Invalid Actuator Command -> FAIL
    def test_07_invalid_actuator_command_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t7.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(100)]
        rows[30]["cmd_w_L"] = 25.0 # Exceeds 12.0
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T7", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("INVALID_ACTUATOR_COMMAND", res["gate_violations"])

    # TEST 8: NaN State -> FAIL
    def test_08_nan_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t8.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(100)]
        rows[20]["pos_x"] = float("nan")
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T8", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("NAN_STATE", res["gate_violations"])

    # TEST 9: Inf State -> FAIL
    def test_09_inf_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t9.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(100)]
        rows[25]["speed"] = float("inf")
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T9", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("INF_STATE", res["gate_violations"])

    # TEST 10: Unresolved stuck state at end -> FAIL
    def test_10_unresolved_stuck_state_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t10.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(100)]
        rows[-1]["stuck_state"] = "STUCK_CONFIRMED"
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T10", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("UNRESOLVED_STUCK_STATE_AT_END", res["gate_violations"])

    # TEST 11: Run times out during recovery -> FAIL
    def test_11_timeout_during_recovery_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t11.csv")
        rows = [self.make_base_row(i, x=i*0.01) for i in range(80)]
        rows += [self.make_base_row(i, x=0.8, act="RECOVERY_FORWARD_BREAKOUT", rec=1) for i in range(80, 100)]
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T11", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("INCOMPLETE_RECOVERY_EPISODE", res["gate_violations"])

    # TEST 12: Detector quiet but task incomplete (0.02m disp in open space) -> FAIL
    def test_12_insufficient_task_displacement_fail(self):
        csv_p = os.path.join(self.temp_dir.name, "t12.csv")
        rows = [self.make_base_row(i, x=0.01, spd=0.01) for i in range(150)] # Stationary
        create_synthetic_csv(csv_p, rows)
        res = evaluate_run_telemetry(csv_p, {"run_id": "T12", "scenario_type": "OPEN_SPACE", "test_group": "B"})
        self.assertEqual(res["pass_fail"], "FAIL")
        self.assertIn("INSUFFICIENT_TASK_DISPLACEMENT", res["gate_violations"])

if __name__ == "__main__":
    unittest.main()
