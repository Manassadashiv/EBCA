"""
tests/test_stage1_gate5_suite.py — Stage 1.5 Adversarial Embodiment Regression Suite
Classification: [REGRESSION TEST] Gate #5 Stage 1.5 Formal Verification
"""

import pytest
import numpy as np
from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_stage1_adversarial_suite import (
    run_test1_flip_and_abnormal_states,
    run_test2_causal_interventions,
    run_test3_tabula_rasa_permutation,
    run_test4_heldout_prediction_generalization,
    run_test5_counterfactual_action_divergence,
    run_test6_closed_loop_competence_benchmark,
    run_test7_traction_loss_in_situ,
    run_test8_ablation_controls,
)


@pytest.fixture(scope="module")
def shared_hal():
    return CarlStage1HAL(open_space=False)


def test_gate5_test1_abnormal_states(shared_hal):
    t1 = run_test1_flip_and_abnormal_states(shared_hal)
    assert t1["synthesis"]["wheel_spin_maintained_when_on_side"]
    assert t1["synthesis"]["locomotion_collapsed_when_on_side"]
    assert t1["synthesis"]["airborne_carl_contacts_strictly_zero"]
    assert t1["synthesis"]["airborne_has_traction_is_false"]
    assert t1["UPRIGHT"]["final_displacement_x"] > 0.20
    assert abs(t1["SIDEWAYS"]["final_displacement_x"]) < 0.10


def test_gate5_test2_causal_interventions(shared_hal):
    t2 = run_test2_causal_interventions(shared_hal)
    res = t2["actuator_5_causal_resolution"]
    assert res["is_causally_inert"]
    assert res["accel_sensitivity"] < 1e-3


def test_gate5_test3_tabula_rasa_permutation(shared_hal):
    t3 = run_test3_tabula_rasa_permutation(shared_hal)
    assert t3["drive_topology_perfectly_recovered"]
    assert t3["recovered_drive_channels"] == t3["ground_truth_scrambled_drive_channels"]


def test_gate5_test4_heldout_prediction(shared_hal):
    t4, _, _ = run_test4_heldout_prediction_generalization(shared_hal)
    assert t4["generalization_verified"]
    assert t4["heldout_error_reduction_pct"] > 10.0
    assert t4["heldout_r2_score"] > 0.0


def test_gate5_test5_counterfactual_divergence(shared_hal):
    t5 = run_test5_counterfactual_action_divergence(shared_hal)
    assert t5["directional_alignment_verified"]
    assert t5["gyro_subspace_cosine_sim_AB"] > 0.80
    assert t5["yaw_rate_sign_concordance"]
    assert t5["head_proprio_sign_concordance"]


def test_gate5_test6_competence_benchmark(shared_hal):
    canonical_drive = [0, 1]
    t6 = run_test6_closed_loop_competence_benchmark(shared_hal, canonical_drive)
    assert t6["competence_verified"]
    assert t6["prediction_branch_entered"]
    assert t6["predictive_evaluations_executed"] == 1800
    assert t6["full_carl_obstacle_collisions"] == 0
    assert t6["constant_forward_obstacle_collisions"] > 10


def test_gate5_test7_traction_loss_in_situ(shared_hal):
    t7 = run_test7_traction_loss_in_situ(shared_hal)
    assert t7["discrepancy_detection_verified"]
    assert t7["dry_false_positive_rate"] <= 0.10
    assert t7["ice_slip_detection_rate"] >= 0.70
    assert t7["mean_kinematic_slip_ice"] > 0.60
    assert t7["mean_kinematic_slip_dry"] < 0.40
    assert t7["wheel_spin_maintained_on_ice"]


def test_gate5_test8_ablation_controls(shared_hal):
    t8 = run_test8_ablation_controls(shared_hal)
    assert t8["ablation_verified"]
    assert t8["learned_candidate_discriminability"] > 0.005
    assert t8["unlearned_candidate_discriminability"] == 0.0
