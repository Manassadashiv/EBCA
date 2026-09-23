"""
tests/test_stage3_3_mppi_synthesis.py — Stage 3.3 Continuous Action Synthesis (MPPI) Benchmark Suite
Classification: [STAGE 3.3 CAPABILITY CERTIFICATION] Continuous Motor Execution Benchmark

Pre-Registered Acceptance Gates:
- Gate 1: Action Space Continuity & Dynamic Smoothness (u* in [-1, 1]^2, mean ||Du*|| <= 0.35)
- Gate 2: Real-Time Vectorized Cycle Latency (p95 <= 45.0 ms, mean <= 20.0 ms over 100 cycles)
- Gate 3: Comparative Obstacle Negotiation vs Frozen Discrete Baseline (rel reduction >= 50%, coll <= 10%, Delta C > 0)
- Gate 4: Causal CANN & Spatial Memory Multi-Objective Coupling (||Du*|| >= 0.15 m/s under CANN perturbation)
- Gate 5: Decision-Pipeline AST Anti-Cheat & Pipeline Isolation (100% clean, zero simulator coordinates)
"""

import sys
import os
import time
import math
import json
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import torch
import pytest
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

torch.set_num_threads(2)

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_mppi_deliberation import CARLStage3_3MPPIDeliberationEngine
from brain.carl_stage2_3_r1_deliberation import CARLStage2_3R1DeliberationEngine
from brain.carl_stage2_integrated_brain import CarlStage2BIntegratedBrain
import mujoco


LAYOUTS = [
    "layout_1_left_trap",
    "layout_2_right_trap",
    "layout_3_t_junction",
    "layout_4_corridor_slit",
]


def test_gate1_action_continuity_and_smoothness():
    """
    Gate 1: Action Space Continuity & Dynamic Smoothness.
    Verifies that synthesized controls are strictly continuous, bounded in [-1.0, 1.0]^2,
    and exhibit smooth trajectory transitions (mean ||Du*|| <= 0.35).
    """
    print("\n--- Running Gate 1: Action Continuity & Smoothness ---")
    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    mppi.initialize_pose(0.0, 0.0, 0.0)

    actions = []
    deltas = []
    prev_action = None

    # Run 50 steps with fluctuating corridor sensors
    for t in range(50):
        # Oscillating corridor reading
        sensors = np.ones(15, dtype=np.float32) * 1.5
        sensors[0:4] = 0.30 + 0.15 * math.sin(t * 0.15)   # right wall
        sensors[11:15] = 0.30 - 0.15 * math.sin(t * 0.15) # left wall
        sensors[6:9] = max(0.20, 1.2 - (t * 0.02))        # approaching obstacle

        u_star, tel = mppi.select_action(sensors, curr_v=0.20, curr_w=0.0)
        actions.append(u_star)

        # Check bounds
        assert np.all(u_star >= -1.0) and np.all(u_star <= 1.0), f"Action out of bounds: {u_star}"
        assert not np.any(np.isnan(u_star)), "NaN action synthesized"
        assert not np.any(np.isinf(u_star)), "Inf action synthesized"

        if prev_action is not None:
            delta = float(np.linalg.norm(u_star - prev_action))
            deltas.append(delta)
        prev_action = u_star.copy()

    actions_arr = np.array(actions)
    mean_delta = float(np.mean(deltas))
    max_delta = float(np.max(deltas))
    u_diff_std = float(np.std(actions_arr[:, 1] - actions_arr[:, 0]))

    print(f"Gate 1 Results: Mean Step Delta = {mean_delta:.4f} (Req <= 0.35)")
    print(f"Gate 1 Results: Max Step Delta = {max_delta:.4f}")
    print(f"Gate 1 Results: Steering Variance (u_diff std) = {u_diff_std:.4f}")

    assert mean_delta <= 0.35, f"Mean action delta too high (chatter): {mean_delta:.4f}"
    assert u_diff_std > 0.02, f"Steering not actively varying: std={u_diff_std:.4f}"

    return {
        "gate1_passed": True,
        "mean_step_delta": mean_delta,
        "max_step_delta": max_delta,
        "steering_std": u_diff_std
    }


def test_gate2_realtime_cycle_latency():
    """
    Gate 2: Real-Time Cognitive Cycle Latency.
    Evaluates execution latency over N=100 full deliberation cycles under M=128, H=15.
    Requires p95 latency <= 45.0 ms (biological clock budget <= 50 ms).
    """
    print("\n--- Running Gate 2: Real-Time Cycle Latency ---")
    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    mppi.initialize_pose(0.0, 0.0, 0.0)

    # Mock CANN state with 64-HD rates
    cann_state = {
        "hd_decoded_heading": 0.25,
        "grid_unwrapped_x": 0.0,
        "grid_unwrapped_y": 0.0,
        "hd_rates": np.random.uniform(0.0, 1.0, 64).astype(np.float32)
    }

    latencies = []
    N = 100

    for t in range(N):
        sensors = np.random.uniform(0.2, 3.0, 15).astype(np.float32)
        v_curr = float(np.random.uniform(0.0, 0.3))
        w_curr = float(np.random.uniform(-0.5, 0.5))

        t0 = time.perf_counter()
        u_star, tel = mppi.select_action(sensors, curr_v=v_curr, curr_w=w_curr, cann_state=cann_state)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

    mean_lat = float(np.mean(latencies))
    median_lat = float(np.median(latencies))
    p95_lat = float(np.percentile(latencies, 95))
    p99_lat = float(np.percentile(latencies, 99))
    max_lat = float(np.max(latencies))

    print(f"Gate 2 Latency: Mean = {mean_lat:.2f} ms (Req <= 20.0 ms)")
    print(f"Gate 2 Latency: Median = {median_lat:.2f} ms")
    print(f"Gate 2 Latency: p95 = {p95_lat:.2f} ms (Req <= 45.0 ms)")
    print(f"Gate 2 Latency: p99 = {p99_lat:.2f} ms")
    print(f"Gate 2 Latency: Max = {max_lat:.2f} ms")

    assert p95_lat <= 45.0, f"p95 latency violated real-time budget: {p95_lat:.2f} ms > 45.0 ms"
    assert mean_lat <= 20.0, f"Mean latency too slow: {mean_lat:.2f} ms > 20.0 ms"

    return {
        "gate2_passed": True,
        "mean_latency_ms": mean_lat,
        "median_latency_ms": median_lat,
        "p95_latency_ms": p95_lat,
        "p99_latency_ms": p99_lat,
        "max_latency_ms": max_lat
    }


def test_gate3_comparative_obstacle_negotiation(**kwargs):
    """
    Gate 3: Comparative Obstacle Negotiation vs Frozen Discrete Baseline.
    Compares Stage 3.3 MPPI against Stage 2 discrete controller across 20 trials (5 per layout)
    in the authentic MuJoCo physical arena.
    Pre-registered comparative acceptance criteria:
    - Relative collision reduction >= 50.0%
    - Safety ceiling: MPPI collision rate <= 10.0%
    - Delta clearance: Mean hull clearance improvement > 0
    """
    print("\n--- Running Gate 3: Comparative Obstacle Negotiation ---")
    hal = CarlStage1HAL()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])

    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    discrete = CARLStage2_3R1DeliberationEngine(mode="deliberative", horizon=10)

    # 20 deterministic spawn configurations across the 4 layouts
    rng = np.random.RandomState(42)
    trials_per_layout = 5
    spawns = []
    for layout in LAYOUTS:
        for i in range(trials_per_layout):
            if layout == "layout_1_left_trap":
                x = float(rng.uniform(-3.05, -2.95))
                y = float(rng.uniform(-0.25, -0.15))
                yaw = float(-math.pi / 2.0 + rng.uniform(-0.04, 0.04))
            elif layout == "layout_2_right_trap":
                x = float(rng.uniform(-3.45, -3.35))
                y = float(rng.uniform(-0.68, -0.62))
                yaw = float(0.0 + rng.uniform(-0.03, 0.03))
            elif layout == "layout_3_t_junction":
                x = float(rng.uniform(-0.25, -0.15))
                y = float(rng.uniform(-2.55, -2.45))
                yaw = float(math.pi + rng.uniform(-0.04, 0.04))
            else: # layout_4_corridor_slit
                x = float(rng.uniform(-2.55, -2.45))
                y = float(rng.uniform(2.20, 2.30))
                yaw = float(0.0 + rng.uniform(-0.04, 0.04))
            spawns.append((layout, [x, y], yaw))

    def run_trial(controller, spawn_pos, spawn_yaw, is_mppi: bool) -> Tuple[bool, float]:
        hal.reset()
        hal.data.qpos[qa:qa + 2] = spawn_pos
        hal.data.qpos[qa + 3:qa + 7] = [math.cos(spawn_yaw / 2.0), 0.0, 0.0, math.sin(spawn_yaw / 2.0)]
        hal.data.qvel[:] = 0.0
        mujoco.mj_forward(hal.model, hal.data)

        controller.initialize_pose(spawn_pos[0], spawn_pos[1], spawn_yaw)

        had_collision = False
        min_clearance = 5.0
        v_est = 0.0

        for tick in range(60):
            sensors = hal.read_sensors()
            sonars = sensors[:15]
            gyro_yaw = float(sensors[20])

            # Unprivileged dead-reckoning
            controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.03)

            min_son = float(np.min(sonars))
            if min_son < min_clearance:
                min_clearance = min_son

            act, tel = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)

            # Package into 6D actuation
            cmd_6d = np.zeros(6, dtype=np.float64)
            cmd_6d[0] = act[0]
            cmd_6d[1] = act[1]

            # Step physical simulation
            s_next, diag = hal.step(cmd_6d)

            # Check collision
            contact_info = hal.get_carl_contact_info()
            body_contacts = contact_info["carl_contacts"] - contact_info["floor_contacts"]
            if body_contacts > 0:
                had_collision = True

            # Update velocity estimate
            u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
            v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

        return had_collision, min_clearance

    discrete_collisions = 0
    discrete_clearances = []
    mppi_collisions = 0
    mppi_clearances = []

    print(f"Executing {len(spawns)} comparative trials...")
    for idx, (layout, pos, yaw) in enumerate(spawns):
        # 1. Discrete baseline
        d_coll, d_clr = run_trial(discrete, pos, yaw, is_mppi=False)
        if d_coll:
            discrete_collisions += 1
        discrete_clearances.append(d_clr)

        # 2. MPPI controller
        m_coll, m_clr = run_trial(mppi, pos, yaw, is_mppi=True)
        if m_coll:
            mppi_collisions += 1
        mppi_clearances.append(m_clr)

    total_trials = len(spawns)
    d_coll_rate = (discrete_collisions / total_trials) * 100.0
    m_coll_rate = (mppi_collisions / total_trials) * 100.0
    d_mean_clr = float(np.mean(discrete_clearances))
    m_mean_clr = float(np.mean(mppi_clearances))
    delta_clr = m_mean_clr - d_mean_clr

    if d_coll_rate > 0.0:
        rel_red = float(((d_coll_rate - m_coll_rate) / d_coll_rate) * 100.0)
    else:
        # If baseline had 0 collisions, any MPPI collision is worse; 0 collisions is 0% reduction
        rel_red = 0.0 if m_coll_rate == 0.0 else float(-100.0 * m_coll_rate)

    print(f"Discrete Baseline: Collision Rate = {d_coll_rate:.1f}% ({discrete_collisions}/{total_trials}), Mean Clearance = {d_mean_clr:.4f} m")
    print(f"MPPI Controller:   Collision Rate = {m_coll_rate:.1f}% ({mppi_collisions}/{total_trials}), Mean Clearance = {m_mean_clr:.4f} m")
    print(f"Comparative Metric: Relative Collision Reduction = {rel_red:.1f}% (Req >= 50.0%)")
    print(f"Comparative Metric: Delta Clearance = {delta_clr:+.4f} m (Req > 0)")
    print(f"Safety Ceiling: MPPI Collision Rate = {m_coll_rate:.1f}% (Req <= 10.0%)")

    gate3_passed = bool((m_coll_rate <= 10.0) and (rel_red >= 50.0) and (delta_clr > 0.0))
    failure_reason = None
    if not gate3_passed:
        reasons = []
        if rel_red < 50.0:
            reasons.append(f"relative collision reduction {rel_red:.1f}% < 50.0% (Discrete={discrete_collisions}, MPPI={mppi_collisions})")
        if m_coll_rate > 10.0:
            reasons.append(f"MPPI collision rate {m_coll_rate:.1f}% > 10.0%")
        if delta_clr <= 0.0:
            reasons.append(f"delta clearance {delta_clr:.4f} m <= 0")
        failure_reason = "; ".join(reasons)
        print(f"\n[!] GATE 3 FAILED PROTOCOL: {failure_reason}")

    res = {
        "gate3_passed": gate3_passed,
        "discrete_collision_rate": d_coll_rate,
        "mppi_collision_rate": m_coll_rate,
        "relative_collision_reduction_pct": rel_red,
        "discrete_mean_clearance": d_mean_clr,
        "mppi_mean_clearance": m_mean_clr,
        "delta_clearance_m": delta_clr,
        "failure_reason": failure_reason
    }

    if kwargs.get("raise_on_fail", True):
        assert gate3_passed, f"Gate 3 FAILED: {failure_reason}"

    return res


def test_gate4_cann_multi_objective_coupling(**kwargs):
    """
    Gate 4: Causal CANN & Spatial Memory Multi-Objective Coupling.
    Verifies that internal CANN attractor heading directly modulates continuous trajectory
    optimization (||Du*|| >= 0.15 m/s, p < 0.01).
    Evaluated across N=30 diverse sensory contexts with paired t-test against null hypothesis.
    """
    print("\n--- Running Gate 4: CANN Multi-Objective Coupling ---")
    mppi = CARLStage3_3MPPIDeliberationEngine(num_samples=128, horizon=15)
    rng = np.random.RandomState(42)

    r_hd_north = np.zeros(64, dtype=np.float32)
    r_hd_north[32] = 1.0; r_hd_north[31] = 0.8; r_hd_north[33] = 0.8
    r_hd_left = np.roll(r_hd_north, 16)
    r_hd_right = np.roll(r_hd_north, -16)

    cann_north = {"hd_decoded_heading": 0.0, "grid_unwrapped_x": 0.0, "grid_unwrapped_y": 0.0, "hd_rates": r_hd_north}
    cann_left = {"hd_decoded_heading": math.pi / 2.0, "grid_unwrapped_x": 0.0, "grid_unwrapped_y": 0.0, "hd_rates": r_hd_left}
    cann_right = {"hd_decoded_heading": -math.pi / 2.0, "grid_unwrapped_x": 0.0, "grid_unwrapped_y": 0.0, "hd_rates": r_hd_right}

    diffs_left = []
    diffs_right = []
    diffs_lr = []

    # Evaluate across N=30 distinct sensory contexts
    for _ in range(30):
        sensors = rng.uniform(0.5, 2.5, 15).astype(np.float32)
        v = float(rng.uniform(0.0, 0.2))
        w = float(rng.uniform(-0.2, 0.2))
        mppi.initialize_pose(0.0, 0.0, 0.0)

        u_north, _ = mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_north)
        u_left, _ = mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_left)
        u_right, _ = mppi.select_action(sensors, curr_v=v, curr_w=w, cann_state=cann_right)

        diffs_left.append(float(np.linalg.norm(u_left - u_north)))
        diffs_right.append(float(np.linalg.norm(u_right - u_north)))
        diffs_lr.append(float(np.linalg.norm(u_left - u_right)))

    mean_div = float(np.mean(diffs_lr))
    mean_div_north = float((np.mean(diffs_left) + np.mean(diffs_right)) / 2.0)

    # One-sample t-test testing H0: mean <= 0.15 vs H1: mean > 0.15
    t_stat, p_val_two_sided = stats.ttest_1samp(diffs_lr, 0.15)
    p_val = float(p_val_two_sided / 2.0 if t_stat > 0 else 1.0 - p_val_two_sided / 2.0)

    print(f"Gate 4 Mean Divergence ||u_left - u_right|| = {mean_div:.4f} m/s (Req >= 0.15 m/s)")
    print(f"Gate 4 Perturbation from North: Left={np.mean(diffs_left):.4f} m/s, Right={np.mean(diffs_right):.4f} m/s")
    print(f"Gate 4 Statistical Test: t-statistic = {t_stat:.4f}, p-value = {p_val:.4e} (Req p < 0.01)")

    gate4_passed = bool((mean_div >= 0.15) and (p_val < 0.01))
    if kwargs.get("raise_on_fail", True):
        assert gate4_passed, f"Gate 4 FAILED: mean_div={mean_div:.4f} (req >= 0.15), p_val={p_val:.4e} (req < 0.01)"

    return {
        "gate4_passed": gate4_passed,
        "mean_divergence_ms": mean_div_north,
        "cann_divergence_left": float(np.mean(diffs_left)),
        "cann_divergence_right": float(np.mean(diffs_right)),
        "cann_divergence_left_right": mean_div,
        "t_statistic": float(t_stat),
        "p_value": p_val
    }


def test_gate5_ast_anti_cheat():
    """
    Gate 5: Decision-Pipeline AST Anti-Cheat & Isolation Invariant.
    Verifies that carl_mppi_deliberation.py contains ZERO simulator imports
    and ZERO lookups of privileged attributes.
    """
    print("\n--- Running Gate 5: Decision-Pipeline AST Anti-Cheat ---")
    mppi_file = REPO_ROOT / "brain" / "carl_mppi_deliberation.py"
    assert mppi_file.exists(), f"Missing file: {mppi_file}"

    with open(mppi_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(mppi_file))

    forbidden_modules = {"mujoco"}
    forbidden_attrs = {"geom_xpos", "mj_ray", "qpos", "qvel", "qacc"}

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in forbidden_modules:
                    violations.append(f"Line {node.lineno}: Forbidden import '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module in forbidden_modules:
                violations.append(f"Line {node.lineno}: Forbidden from-import '{node.module}'")
        elif isinstance(node, ast.Attribute):
            if node.attr in forbidden_attrs:
                violations.append(f"Line {node.lineno}: Forbidden attribute access '{node.attr}'")

    print(f"AST Scan on {mppi_file.name}: {len(violations)} violations found")
    if violations:
        for v in violations:
            print(f"  VIOLATION: {v}")

    assert len(violations) == 0, f"AST anti-cheat violations detected in MPPI deliberation: {violations}"

    return {
        "gate5_passed": True,
        "ast_violations_count": len(violations)
    }


def run_full_stage3_3_benchmark():
    """Executes the complete pre-registered Stage 3.3 benchmark suite and compiles evidence scorecard."""
    print("========================================================================================")
    print("                 CARL-DX STAGE 3.3 MPPI BENCHMARK EXECUTION SUITE                       ")
    print("========================================================================================")

    results = {}
    # Gate 5 first (Integrity scan)
    results["gate5"] = test_gate5_ast_anti_cheat()

    # Gate 1: Action continuity
    results["gate1"] = test_gate1_action_continuity_and_smoothness()

    # Gate 2: Real-time latency
    results["gate2"] = test_gate2_realtime_cycle_latency()

    # Gate 4: CANN multi-objective coupling
    results["gate4"] = test_gate4_cann_multi_objective_coupling(raise_on_fail=False)

    # Gate 3: Comparative obstacle negotiation
    results["gate3"] = test_gate3_comparative_obstacle_negotiation(raise_on_fail=False)

    all_passed = all(g.get(f"{k}_passed", False) for k, g in results.items())

    scorecard = {
        "milestone": "Stage 3.3 Continuous Action Synthesis (MPPI)",
        "protocol_id": "CARL-STAGE3-3-MPPI-PROTO-2026-09-13",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "certification_verdict": "CERTIFIED SUCCESSFUL (PASS) ✅" if all_passed else "FAILED CLOSED ❌",
        "gates": results
    }

    # Save scorecard
    out_dir = REPO_ROOT / "evidence" / "stage3_3"
    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard_path = out_dir / "stage3_3_scorecard.json"
    with open(scorecard_path, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    print("\n========================================================================================")
    print(f"FINAL STAGE 3.3 CERTIFICATION VERDICT: {scorecard['certification_verdict'].encode('ascii', 'replace').decode('ascii')}")
    print(f"Scorecard saved to: {scorecard_path}")
    print("========================================================================================")

    return scorecard


if __name__ == "__main__":
    run_full_stage3_3_benchmark()
