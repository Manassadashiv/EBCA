"""
tests/run_stage3_4R4_5_screening.py — Stage 3.4-R4.5-P2b 10-Config Screening Battery
Validates the continuous piecewise Sobol candidate generator and directional predictive
safety formulation on Configs 0-4 (Env 1) and 20-24 (Env 2).
"""
import sys
import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import torch
import mujoco

import builtins
import typing
builtins.Optional = typing.Optional
builtins.List = typing.List

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_active_inference import CARLActiveInferenceEngine
from tests.test_stage3_4R3_certification import build_50_matched_configurations

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"

EVIDENCE_DIR = repo_root / "evidence" / "canonical_reunification_step2"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR = EVIDENCE_DIR / "step2_plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

SCREENING_CONFIG_IDS = [0, 1, 2, 3, 4, 20, 21, 22, 23, 24]
MAX_TICKS = 220


def run_episode(cfg: Dict[str, Any], arm_w_info: float = 1.0) -> Dict[str, Any]:
    env_id = cfg["env_id"]
    xml_path = str(ENV1_XML if env_id == 1 else ENV2_XML)
    grid_path = str(ENV1_GRID if env_id == 1 else ENV2_GRID)

    sx, sy = cfg["spawn_pos"]
    syaw = cfg["spawn_yaw"]
    seed = cfg["seed"]

    np.random.seed(seed)
    torch.manual_seed(seed)

    hal = CarlStage1HAL(xml_path=xml_path)
    hal.reset()
    qa = int(hal.model.joint("spatial_identity").qposadr[0])
    hal.data.qpos[qa:qa+2] = [sx, sy]
    hal.data.qpos[qa+3:qa+7] = [math.cos(syaw / 2.0), 0.0, 0.0, math.sin(syaw / 2.0)]
    mujoco.mj_forward(hal.model, hal.data)

    ctrl = CARLActiveInferenceEngine(
        grid_path=grid_path,
        w_info=arm_w_info,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    ctrl.initialize_pose(sx, sy, syaw)

    had_collision = False
    escaped = False
    v_est = 0.0
    latencies = []
    heading_errors = []
    veto_fracs = []
    stagnant = 0
    max_stagnant = 0
    prev_y = sy

    reversed_ticks = 0
    max_turn_delta = 0.0
    entered_channel = False
    fwd_egress_ticks = 0
    trajectory = []

    for tick in range(MAX_TICKS):
        sensors = hal.read_sensors()
        sonars = sensors[:15]
        gyro_yaw = float(sensors[20])
        dt = ctrl.dt

        ctrl.update_odometry(v_wheel=v_est, w_gyro=gyro_yaw, dt=dt)

        t0 = time.perf_counter()
        u_star, telem = ctrl.select_action(sonars, curr_v=v_est, curr_w=gyro_yaw)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

        # Physical step in MuJoCo (Differential Drive Wheels; head locked forward for Stage 3.4)
        cmd_6d = np.zeros(6, dtype=np.float64)
        cmd_6d[0] = float(u_star[0])
        cmd_6d[1] = float(u_star[1])
        hal.step(cmd_6d)

        u_fwd_est = float(0.5 * (cmd_6d[0] + cmd_6d[1]))
        v_est = 0.70 * v_est + 0.30 * (u_fwd_est * 0.30)

        q_curr = hal.data.qpos[qa:qa+7]
        curr_x, curr_y = float(q_curr[0]), float(q_curr[1])
        curr_yaw = 2.0 * math.atan2(float(q_curr[6]), float(q_curr[3]))
        sensors = hal.read_sensors()
        sonar_min = float(np.min(sensors[:15]))
        heading_errors.append(abs(math.degrees(curr_yaw) - math.degrees(syaw)))
        veto_fracs.append(telem.get("rejected_candidates", 0) / 128.0)

        # Ground truth collision check (evaluator-only)
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True

        # Ground truth escape check
        if env_id == 1 and curr_x <= -0.55:
            escaped = True
        elif env_id == 2 and curr_y <= -1.20:
            escaped = True

        trajectory.append({
            "tick": tick,
            "x": curr_x, "y": curr_y, "yaw": curr_yaw,
            "u_L": float(u_star[0]), "u_R": float(u_star[1]),
            "sonar_min": sonar_min,
            "had_collision": had_collision,
        })

        if env_id == 1:
            u_fwd = 0.5 * (u_star[0] + u_star[1])
            if u_fwd < -0.05:
                reversed_ticks += 1
            dyaw = abs(math.atan2(math.sin(curr_yaw - syaw), math.cos(curr_yaw - syaw)))
            if dyaw > max_turn_delta:
                max_turn_delta = dyaw
            if curr_x < 0.35:
                entered_channel = True
            if entered_channel and u_fwd > 0.05:
                fwd_egress_ticks += 1
        elif env_id == 2:
            u_fwd = 0.5 * (u_star[0] + u_star[1])
            if u_fwd < -0.05:
                reversed_ticks += 1
            dyaw = abs(math.atan2(math.sin(curr_yaw - syaw), math.cos(curr_yaw - syaw)))
            if dyaw > max_turn_delta:
                max_turn_delta = dyaw
            if curr_y < -0.20 and 0.40 <= curr_x <= 1.25:
                entered_channel = True
            if entered_channel and u_fwd > 0.05:
                fwd_egress_ticks += 1

        if abs(curr_y - prev_y) < 0.005:
            stagnant += 1
            if stagnant > max_stagnant:
                max_stagnant = stagnant
        else:
            stagnant = 0
        prev_y = curr_y

        if had_collision or escaped:
            break

    if had_collision:
        outcome = "COLLISION"
    elif escaped:
        outcome = "ESCAPE"
    else:
        outcome = "TIMEOUT"

    phases = {
        "phase1_reverse": bool(reversed_ticks >= 8),
        "phase2_pivot": bool(max_turn_delta >= math.radians(60.0)),
        "phase3_channel_entry": bool(entered_channel),
        "phase4_forward_egress": bool(fwd_egress_ticks >= 8),
    }

    return {
        "config_id": cfg["config_id"],
        "env_id": env_id,
        "env_name": "Env1 (Turning Bay)" if env_id == 1 else "Env2 (T-Junction)",
        "outcome": outcome,
        "ticks_executed": tick + 1,
        "final_x": curr_x,
        "final_y": curr_y,
        "final_yaw_deg": math.degrees(curr_yaw),
        "min_sonar": float(min(p["sonar_min"] for p in trajectory)),
        "mean_latency_ms": float(np.mean(latencies)),
        "p95_latency_ms": float(np.percentile(latencies, 95)),
        "mean_candidate_veto_frac": float(np.mean(veto_fracs)),
        "phases": phases,
        "trajectory": trajectory,
    }


def generate_screening_plots(results: List[Dict[str, Any]], plots_dir: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Plot 1: Env 1 Trajectories
        fig, ax = plt.subplots(figsize=(8, 7))
        env1_results = [r for r in results if r["env_id"] == 1]
        for r in env1_results:
            xs = [p["x"] for p in r["trajectory"]]
            ys = [p["y"] for p in r["trajectory"]]
            color = "green" if r["outcome"] == "ESCAPE" else ("red" if r["outcome"] == "COLLISION" else "orange")
            ax.plot(xs, ys, color=color, alpha=0.8, lw=2.0, label=f"Cfg {r['config_id']} ({r['outcome']})")
        ax.set_title("Stage 3.4-R4.5-P2b: Env 1 (Turning Bay) Trajectories", fontsize=12, fontweight="bold")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)
        fig.tight_layout()
        fig.savefig(plots_dir / "screening_trajectories_env1.png", dpi=150)
        plt.close(fig)

        # Plot 2: Env 2 Trajectories
        fig, ax = plt.subplots(figsize=(8, 7))
        env2_results = [r for r in results if r["env_id"] == 2]
        # Draw corridor walls: x=0.50 and x=1.15 for y in [-1.5, 0.0]
        ax.plot([0.50, 0.50], [-1.5, 0.0], 'k--', lw=1.5, label="Corridor Walls")
        ax.plot([1.15, 1.15], [-1.5, 0.0], 'k--', lw=1.5)
        for r in env2_results:
            xs = [p["x"] for p in r["trajectory"]]
            ys = [p["y"] for p in r["trajectory"]]
            color = "green" if r["outcome"] == "ESCAPE" else ("red" if r["outcome"] == "COLLISION" else "orange")
            ax.plot(xs, ys, color=color, alpha=0.8, lw=2.0, label=f"Cfg {r['config_id']} ({r['outcome']})")
        ax.set_title("Stage 3.4-R4.5-P2b: Env 2 (T-Junction) Trajectories", fontsize=12, fontweight="bold")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="lower left", fontsize=8)
        fig.tight_layout()
        fig.savefig(plots_dir / "screening_trajectories_env2.png", dpi=150)
        plt.close(fig)

        # Plot 3: Latency & Diagnostics
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        lats = [r["mean_latency_ms"] for r in results]
        p95s = [r["p95_latency_ms"] for r in results]
        cfg_labels = [f"C{r['config_id']}" for r in results]
        axes[0].bar(cfg_labels, lats, color="steelblue", label="Mean")
        axes[0].scatter(cfg_labels, p95s, color="crimson", zorder=3, label="p95")
        axes[0].axhline(45.0, color="red", linestyle="--", label="Budget (45ms)")
        axes[0].set_title("Deliberation Cycle Latency per Config", fontsize=11, fontweight="bold")
        axes[0].set_ylabel("Latency (ms)")
        axes[0].legend(fontsize=8)
        axes[0].grid(True, alpha=0.3)

        min_sonars = [r["min_sonar"] for r in results]
        outcomes = [r["outcome"] for r in results]
        colors = ["green" if o == "ESCAPE" else ("red" if o == "COLLISION" else "orange") for o in outcomes]
        axes[1].bar(cfg_labels, min_sonars, color=colors)
        axes[1].axhline(0.055, color="red", linestyle="--", label="Hard Shield (0.055m)")
        axes[1].set_title("Minimum Clearance to Obstacle per Config", fontsize=11, fontweight="bold")
        axes[1].set_ylabel("Min Sonar (m)")
        axes[1].legend(fontsize=8)
        axes[1].grid(True, alpha=0.3)

        fig.tight_layout()
        fig.savefig(plots_dir / "screening_latency_and_heading_diagnostics.png", dpi=150)
        plt.close(fig)

    except Exception as e:
        print(f"Warning: plot generation failed: {e}")


def main():
    print("=" * 60)
    print("STAGE 3.4-R4.5-P2b SCREENING (10 CONFIGS, CANONICAL ORGANISM)")
    print("Continuous Sobol Candidates + Directional Predictive Safety")
    print("=" * 60)
    print()

    configs = build_50_matched_configurations()
    cfg_map = {c["config_id"]: c for c in configs}

    results = []
    for cfg_id in SCREENING_CONFIG_IDS:
        cfg = cfg_map[cfg_id]
        env_name = "Env1" if cfg["env_id"] == 1 else "Env2"
        print(f"Running config {cfg_id} ({env_name})... ", end="", flush=True)
        t0 = time.time()
        result = run_episode(cfg)
        elapsed = time.time() - t0
        print(f"{result['outcome']:10s} ticks={result['ticks_executed']:3d} final_y={result['final_y']:.3f} "
              f"lat={result['mean_latency_ms']:.1f}ms min_sonar={result['min_sonar']:.3f}m ({elapsed:.1f}s)")
        results.append(result)

    # Save
    out_file = EVIDENCE_DIR / "r4_5_screening_trials.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    env1 = [r for r in results if r["env_id"] == 1]
    env2 = [r for r in results if r["env_id"] == 2]

    print()
    print("=" * 60)
    print("R4.5-P2b SCREENING SUMMARY")
    print("=" * 60)
    print(f"Env1 ({len(env1)}): escapes={sum(1 for r in env1 if r['outcome']=='ESCAPE')}"
          f" collisions={sum(1 for r in env1 if r['outcome']=='COLLISION')}"
          f" timeouts={sum(1 for r in env1 if r['outcome']=='TIMEOUT')}")
    print(f"Env2 ({len(env2)}): escapes={sum(1 for r in env2 if r['outcome']=='ESCAPE')}"
          f" collisions={sum(1 for r in env2 if r['outcome']=='COLLISION')}"
          f" timeouts={sum(1 for r in env2 if r['outcome']=='TIMEOUT')}")
    print(f"Env2 phase3_channel_entry: {sum(1 for r in env2 if r['phases']['phase3_channel_entry'])}/{len(env2)}")

    scorecard = {
        "n_trials": len(results),
        "escapes": sum(1 for r in results if r["outcome"] == "ESCAPE"),
        "collisions": sum(1 for r in results if r["outcome"] == "COLLISION"),
        "timeouts": sum(1 for r in results if r["outcome"] == "TIMEOUT"),
        "env1_escapes": sum(1 for r in env1 if r["outcome"] == "ESCAPE"),
        "env1_collisions": sum(1 for r in env1 if r["outcome"] == "COLLISION"),
        "env1_timeouts": sum(1 for r in env1 if r["outcome"] == "TIMEOUT"),
        "env2_escapes": sum(1 for r in env2 if r["outcome"] == "ESCAPE"),
        "env2_collisions": sum(1 for r in env2 if r["outcome"] == "COLLISION"),
        "env2_timeouts": sum(1 for r in env2 if r["outcome"] == "TIMEOUT"),
        "env2_channel_entry_rate": sum(1 for r in env2 if r["phases"]["phase3_channel_entry"]) / max(1, len(env2)),
        "mean_latency_ms": round(float(np.mean([r["mean_latency_ms"] for r in results])), 2),
        "p95_latency_ms": round(float(np.max([r["p95_latency_ms"] for r in results])), 2),
    }

    sc_file = EVIDENCE_DIR / "r4_5_screening_scorecard.json"
    with open(sc_file, "w") as f:
        json.dump(scorecard, f, indent=2)

    print(f"\nSaved: {out_file}")
    print(f"Saved: {sc_file}")

    print("\nGenerating publication-quality screening plots...")
    generate_screening_plots(results, PLOTS_DIR)


if __name__ == "__main__":
    main()
