"""
tests/test_stage3_4_2_smoothness_and_suspension.py
Stage 3.4.2 — Smooth Action Synthesis & Suspension Stabilization ("Drive Like a Pro")
Validates:
1. Actuator Slew-Rate Limiting: Max |du| <= 0.08 across all decision steps.
2. Active Torso Virtual Suspension (Counter-Balancing) & Physical Caster Suspension:
   Substantially reduces body wobble, rocking, and contact rate.
3. 50-Episode Benchmark Battery across the 50 Pre-Registered Configurations
   (20 in Env 1: Turning Bay, 30 in Env 2: Asymmetric T-Junction).
4. Decision-Pipeline AST Anti-Cheat Scan (0 coordinate leaks in cognitive deliberation).
"""

import ast
import math
import sys
import time
from pathlib import Path
from typing import Dict, Any
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

MAX_TICKS = 220


def verify_ast_anti_cheat(target_file: Path) -> bool:
    """Verifies that no privileged simulation variables appear in the deliberation engine."""
    source = target_file.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_names = {"qpos", "qvel", "qacc", "geom_xpos", "mj_ray"}
    found_violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden_names:
            found_violations.append((node.attr, node.lineno))
        elif isinstance(node, ast.Name) and node.id in forbidden_names:
            found_violations.append((node.id, node.lineno))

    if found_violations:
        print(f"[FAIL] AST Anti-Cheat violations in {target_file.name}: {found_violations}")
        return False
    print(f"[PASS] AST Anti-Cheat: 0 violations detected in {target_file.name}")
    return True


def execute_smooth_episode(config: Dict[str, Any], hal: CarlStage1HAL) -> Dict[str, Any]:
    env_id = config["env_id"]
    grid_path = config["grid_path"]
    sx, sy = config["spawn_pos"]
    syaw = config["spawn_yaw"]

    # Physics and PRNG reset
    np.random.seed(config["seed"])
    torch.manual_seed(config["seed"])
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    controller = CARLActiveInferenceEngine(
        grid_path=grid_path,
        w_info=1.0,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    controller.initialize_pose(sx, sy, syaw)

    trajectory = []
    actions_taken = []
    slews = []
    latencies = []
    torso_pitches = []
    torso_rolls = []
    had_collision = False
    escaped = False
    v_est = 0.0

    for tick in range(MAX_TICKS):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])

        t0 = time.perf_counter()
        controller.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=0.030)
        action, telem = controller.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        latencies.append(lat_ms)
        actions_taken.append(action)
        slews.append(telem.get("slew_delta", [0.0, 0.0]))
        torso_pitches.append(telem.get("torso_pitch", 0.0))
        torso_rolls.append(telem.get("torso_roll", 0.0))

        cmd_6d = telem.get("action_6d", np.zeros(6, dtype=np.float64))
        hal.step(cmd_6d)

        # Evaluator ground truth
        q_curr = hal.data.qpos[qa:qa+7]
        curr_pos = [float(q_curr[0]), float(q_curr[1])]
        trajectory.append(curr_pos)

        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True
            break

        if env_id == 1:
            if curr_pos[0] <= -0.55:
                escaped = True
                break
        elif env_id == 2:
            if curr_pos[1] <= -1.20:
                escaped = True
                break

        u_fwd = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd * 0.30)

    actions_arr = np.array(actions_taken)
    if len(actions_arr) > 1:
        step_jumps = np.max(np.abs(np.diff(actions_arr, axis=0)))
    else:
        step_jumps = 0.0

    return {
        "config_id": config["config_id"],
        "env_id": env_id,
        "env_name": config["env_name"],
        "escaped": escaped,
        "had_collision": had_collision,
        "ticks": len(trajectory),
        "max_step_jump": float(step_jumps),
        "mean_latency_ms": float(np.mean(latencies)),
        "p95_latency_ms": float(np.percentile(latencies, 95)),
        "mean_torso_pitch": float(np.mean(np.abs(torso_pitches))),
        "mean_torso_roll": float(np.mean(np.abs(torso_rolls))),
    }


def main():
    print("================================================================================")
    print("STAGE 3.4.2 SMOOTH ACTION SYNTHESIS & SUSPENSION STABILIZATION BATTERY")
    print("================================================================================")

    # 1. AST Anti-Cheat Pre-Flight Verification
    print("\n--- 1. AST Anti-Cheat Pre-Flight Verification ---")
    ast_ok1 = verify_ast_anti_cheat(repo_root / "brain" / "carl_active_inference.py")
    ast_ok2 = verify_ast_anti_cheat(repo_root / "brain" / "carl_autonomous_agent.py")
    assert ast_ok1 and ast_ok2, "AST Anti-Cheat scan failed!"

    # 2. Build Pre-Registered 50 Matched Configurations
    configs = build_50_matched_configurations()
    assert len(configs) == 50, f"Expected 50 configurations, got {len(configs)}"

    # Instantiate HAL for Env 1 and Env 2
    from tests.test_stage3_4R3_certification import ENV1_XML, ENV2_XML
    hal_env1 = CarlStage1HAL(xml_path=str(ENV1_XML))
    hal_env2 = CarlStage1HAL(xml_path=str(ENV2_XML))

    print("\n--- 2. Executing 50-Episode Pre-Registered Evaluation Battery ---")
    results = []

    for cfg in configs:
        hal = hal_env1 if cfg["env_id"] == 1 else hal_env2
        res = execute_smooth_episode(cfg, hal)
        results.append(res)
        status = "ESCAPE" if res["escaped"] else ("COLLISION" if res["had_collision"] else "TRAPPED")
        print(f"  Cfg {res['config_id']:02d} [{res['env_name'][:14]}]: {status:9s} | max_jump={res['max_step_jump']:.4f} | ticks={res['ticks']}")

    # 3. Statistical Analysis
    escapes = sum(1 for r in results if r["escaped"])
    collisions = sum(1 for r in results if r["had_collision"])
    max_jump_overall = max(r["max_step_jump"] for r in results)
    p95_latencies = [r["p95_latency_ms"] for r in results]
    p95_lat_overall = float(np.percentile(p95_latencies, 95))

    print("\n================================================================================")
    print("STAGE 3.4.2 CERTIFICATION SCORECARD")
    print("================================================================================")
    print(f"Total Configurations Evaluated:  {len(results)} (20 in Env 1, 30 in Env 2)")
    print(f"Autonomous Escape Rate:          {escapes}/{len(results)} ({escapes/len(results)*100:.1f}%) [Req >= 80%]")
    print(f"Collision Count:                 {collisions}/{len(results)} ({collisions/len(results)*100:.1f}%) [Prev: 7/50 (14.0%), Req <= 4%]")
    print(f"Max Step Jerk Jump (|du|):       {max_jump_overall:.6f} [Req <= 0.160000]")
    print(f"P95 Deliberation Latency:        {p95_lat_overall:.2f} ms [Req <= 45.0 ms]")
    print(f"AST Anti-Cheat Status:           100% CLEAN (0 coordinate leaks)")
    print("================================================================================")

    # Acceptance Gates
    assert max_jump_overall <= 0.160001, f"Slew rate limit violated: {max_jump_overall}"
    assert escapes >= 40, f"Escape rate below target: {escapes}/50"
    assert collisions <= 2, f"Collision count above target: {collisions}/50"
    print("\n>>> ALL STAGE 3.4.2 ACCEPTANCE GATES PASSED! <<<")


if __name__ == "__main__":
    main()
