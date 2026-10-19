"""
tests/test_stage6_1_structural_plasticity.py — Stage 6.1 Structural Plasticity Verification Suite
Tests:
1. Dynamic Distress-Gated Synaptogenesis
2. NREM SWR Sleep Spine Pruning & Synaptic Downscaling
3. Engram Preservation (Zero Catastrophic Forgetting R^2 >= 0.98)
4. Strict Metabolic Resource Bounds (K_max ceiling)
5. Execution Speed & AST Quarantine Isolation
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import os
import ast
import time
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from brain.carl_structural_plasticity import CarlStructuralPlasticityEngine


def test_ast_quarantine():
    """Verify absolute decision-pipeline isolation (zero simulator coordinate leaks)."""
    target = REPO_ROOT / "brain" / "carl_structural_plasticity.py"
    tree = ast.parse(target.read_text(encoding="utf-8"))
    forbidden = {"qpos", "qvel", "qacc", "geom_xpos", "mj_ray"}
    leaks = [n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in forbidden]
    assert len(leaks) == 0, f"Quarantine violation in {target.name}: {leaks}"


def test_distress_gated_synaptogenesis():
    """Verifies that high co-activation during distress sprouts new synapses."""
    engine = CarlStructuralPlasticityEngine(pre_size=16, post_size=4, initial_density=0.20, seed=42)
    initial_edges = engine.num_active_edges

    # Pick an initially unformed edge
    vacant = np.argwhere(engine.M == 0)
    assert len(vacant) > 0
    target_pre, target_post = vacant[0]

    x_pre = np.zeros(16)
    x_pre[target_pre] = 1.0
    y_post = np.zeros(4)
    y_post[target_post] = 1.0

    # 1. Quiescent period (distress = 0.0) -> No sprouting
    for _ in range(10):
        engine.step_awake_plasticity(x_pre, y_post, distress_level=0.05, reward_rpe=0.0)
    assert engine.M[target_pre, target_post] == 0, "Sprouting occurred without distress!"

    # 2. Elevated distress (distress = 0.85) -> Sprouting triggers
    for _ in range(15):
        engine.step_awake_plasticity(x_pre, y_post, distress_level=0.85, reward_rpe=0.5)

    assert engine.M[target_pre, target_post] == 1, "Failed to sprout new synaptic edge!"
    assert engine.W[target_pre, target_post] > 0.0, "Sprouted edge has zero initial weight!"
    assert engine.num_active_edges > initial_edges


def test_nrem_sleep_spine_pruning():
    """Verifies that dormant synapses are pruned during sleep consolidation."""
    engine = CarlStructuralPlasticityEngine(pre_size=16, post_size=4, initial_density=0.50, seed=101)
    
    # Artificially set an active edge to zero utilization
    active = np.argwhere(engine.M == 1)
    assert len(active) > 4
    prune_target = active[0]
    p_i, p_j = prune_target[0], prune_target[1]

    engine.W[p_i, p_j] = 0.001
    engine.U_util[p_i, p_j] = 0.001  # below epsilon_prune (0.015)

    res = engine.consolidate_nrem_sleep_pruning()
    assert res["pruned_count"] >= 1, "Failed to prune dormant synapse during sleep!"
    assert engine.M[p_i, p_j] == 0, "Dormant synapse still active in connectivity mask!"
    assert engine.W[p_i, p_j] == 0.0, "Pruned synaptic weight is non-zero!"


def test_engram_protection_zero_forgetting():
    """Verifies that marked engrams are protected from pruning and maintain R^2 >= 0.98."""
    engine = CarlStructuralPlasticityEngine(pre_size=16, post_size=4, initial_density=0.40, seed=777)
    
    # Establish a primary motor skill (engram)
    engram_pre = 3
    engram_post = 1
    engine.M[engram_pre, engram_post] = 1
    engine.W[engram_pre, engram_post] = 0.75
    engine.mark_engram_protection(engram_pre, engram_post, protect=True)

    # Record initial output for test stimulus
    stim = np.zeros(16)
    stim[engram_pre] = 1.0
    initial_drive = engine.forward_pass(stim)

    # Force low utilization on the engram connection
    engine.U_util[engram_pre, engram_post] = 0.0001

    # Sleep consolidation should NOT prune the protected engram
    engine.consolidate_nrem_sleep_pruning()
    assert engine.M[engram_pre, engram_post] == 1, "Protected engram was pruned!"

    # Output correlation
    retained_drive = engine.forward_pass(stim)
    corr = np.corrcoef(initial_drive, retained_drive)[0, 1]
    r_squared = float(corr ** 2) if not np.isnan(corr) else 1.0
    assert r_squared >= 0.98, f"Catastrophic forgetting observed! R^2 = {r_squared:.4f} < 0.98"


def test_metabolic_resource_ceiling():
    """Verifies that total active edges never exceed k_max_edges through competitive remodeling."""
    k_max = 20
    engine = CarlStructuralPlasticityEngine(pre_size=16, post_size=4, initial_density=0.30, k_max_edges=k_max, seed=888)
    
    # Fill up to k_max
    for _ in range(50):
        rand_pre = np.random.rand(16)
        rand_post = np.random.rand(4)
        engine.step_awake_plasticity(rand_pre, rand_post, distress_level=0.95, reward_rpe=0.8)

    assert engine.num_active_edges <= k_max, f"Metabolic edge limit violated: {engine.num_active_edges} > {k_max}"
    assert np.linalg.norm(engine.W) <= engine.w_frobenius_max, "Frobenius norm ceiling violated!"


def test_execution_latency():
    """Verifies sub-millisecond execution latency."""
    engine = CarlStructuralPlasticityEngine(pre_size=32, post_size=8, seed=42)
    latencies = []
    x = np.random.rand(32)
    y = np.random.rand(8)

    for _ in range(100):
        t0 = time.perf_counter()
        engine.step_awake_plasticity(x, y, distress_level=0.5, reward_rpe=0.2)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    mean_ms = np.mean(latencies)
    p95_ms = np.percentile(latencies, 95)
    print(f"\n[LATENCY] CarlStructuralPlasticityEngine Mean: {mean_ms:.3f} ms, p95: {p95_ms:.3f} ms")
    assert p95_ms < 1.0, f"Latency too high: p95 = {p95_ms:.3f} ms >= 1.0 ms"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
