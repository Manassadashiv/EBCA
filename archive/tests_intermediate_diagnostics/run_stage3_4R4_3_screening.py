"""
tests/run_stage3_4R4_3_screening.py — Stage 3.4-R4.3 Quick 10-Config Screening
Runs ARM-A on configs 0-4 (Env1) and 20-24 (Env2) to verify geodesic-gradient
heading alignment before launching the full 200-episode certification battery.
"""
import sys
import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import builtins
import typing
builtins.Optional = typing.Optional
builtins.List = typing.List
import numpy as np
import torch
import mujoco

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from brain.carl_stage1_hal import CarlStage1HAL
from brain.carl_autonomous_agent import CarlAutonomousOrganismAgent
from tests.test_stage3_4R3_certification import build_50_matched_configurations

ENV_DIR = repo_root / "world" / "stage3_4_environments"
ENV1_XML = ENV_DIR / "cul_de_sac_turning_bay.xml"
ENV1_GRID = ENV_DIR / "cul_de_sac_turning_bay_grid.pt"
ENV2_XML = ENV_DIR / "asymmetric_t_junction.xml"
ENV2_GRID = ENV_DIR / "asymmetric_t_junction_grid.pt"

EVIDENCE_DIR = repo_root / "evidence" / "canonical_reunification_step2"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR = EVIDENCE_DIR / "plots"
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

    agent = CarlAutonomousOrganismAgent(
        dt=hal.dt,
        enable_memory=True,
        deliberation_mode="active_inference",
        grid_path=grid_path,
        w_info=arm_w_info,
        frontier_mode="macro",
        norm_mode="dimensionless"
    )
    agent.initialize_spatial_grounding(sx, sy, syaw)

    had_collision = False
    escaped = False
    v_est = 0.0
    latencies = []
    heading_errors = []
    veto_fracs = []
    stagnant = 0
    max_stagnant = 0
    prev_y = sy

    # Phase tracking
    reversed_ticks = 0
    max_turn_delta = 0.0
    entered_channel = False
    fwd_egress_ticks = 0
    trajectory = []

    for tick in range(MAX_TICKS):
        t0 = time.perf_counter()
        cog_result = agent.step_cognitive_cycle(hal)
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat_ms)

        u_star = cog_result["action_cmd"][:2]
        telem = cog_result.get("delib_telemetry", {})

        # Ground truth (evaluator only - never fed to agent)
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        true_x, true_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        quat = hal.data.qpos[qa+3:qa+7]
        true_yaw = math.atan2(2.0 * (quat[0]*quat[3] + quat[1]*quat[2]),
                               1.0 - 2.0 * (quat[2]*quat[2] + quat[3]*quat[3]))

        fused_yaw = float(agent.deliberation.pose[2])
        h_err = math.degrees(abs(math.atan2(math.sin(fused_yaw - true_yaw),
                                             math.cos(fused_yaw - true_yaw))))
        heading_errors.append(h_err)

        total_cand = telem.get("mppi_samples", 128)
        rej_cand = telem.get("rejected_candidates", 0)
        veto_fracs.append(rej_cand / total_cand)

        trajectory.append({
            "tick": tick,
            "x": round(true_x, 4),
            "y": round(true_y, 4),
            "yaw": round(true_yaw, 4),
            "est_x": round(float(agent.deliberation.pose[0]), 4),
            "est_y": round(float(agent.deliberation.pose[1]), 4),
            "est_yaw": round(fused_yaw, 4),
            "h_err": round(h_err, 2),
            "lat_ms": round(lat_ms, 2),
            "u_L": round(float(u_star[0]), 3),
            "u_R": round(float(u_star[1]), 3)
        })

        # Physics step
        hal.step(cog_result["action_cmd"])

        # Post-step position for evaluator metrics
        qa = int(hal.model.joint("spatial_identity").qposadr[0])
        new_x, new_y = float(hal.data.qpos[qa]), float(hal.data.qpos[qa+1])
        u_fwd = float(0.5 * (cog_result["action_cmd"][0] + cog_result["action_cmd"][1]))
        v_est = float(agent.v_est)

        # Stagnation
        if env_id == 2:
            if new_y >= prev_y - 0.005:
                stagnant += 1
            else:
                stagnant = 0
        else:
            if abs(new_y - prev_y) < 0.005 and abs(new_x - true_x) < 0.005:
                stagnant += 1
            else:
                stagnant = 0
        max_stagnant = max(max_stagnant, stagnant)
        prev_y = new_y

        # Phase tracking
        if u_fwd < -0.05:
            reversed_ticks += 1
        new_quat = hal.data.qpos[qa+3:qa+7]
        new_yaw = math.atan2(2.0 * (new_quat[0]*new_quat[3] + new_quat[1]*new_quat[2]),
                              1.0 - 2.0 * (new_quat[2]*new_quat[2] + new_quat[3]*new_quat[3]))
        delta_th = abs(math.degrees(math.atan2(math.sin(new_yaw - syaw), math.cos(new_yaw - syaw))))
        max_turn_delta = max(max_turn_delta, delta_th)

        # Channel entry: y < -0.50 for Env2
        if env_id == 2 and new_y < -0.50:
            entered_channel = True
        elif env_id == 1 and new_y < -0.10:
            entered_channel = True

        if u_fwd > 0.05:
            fwd_egress_ticks += 1

        # Collision
        c_info = hal.get_carl_contact_info()
        wall_contacts = c_info["carl_contacts"] - c_info["floor_contacts"]
        if wall_contacts > 0:
            had_collision = True

        # Escape check
        if env_id == 2 and new_y <= -1.20:
            escaped = True
        elif env_id == 1 and new_y <= -0.10:
            escaped = True

        if had_collision or escaped:
            break

    outcome = "ESCAPE" if escaped else ("COLLISION" if had_collision else "TIMEOUT")
    lat_arr = np.array(latencies)
    herr_arr = np.array(heading_errors)
    veto_arr = np.array(veto_fracs)

    phases = {
        "phase1_reversal": reversed_ticks >= 10,
        "phase2_orientation": max_turn_delta >= 80.0,
        "phase3_channel_entry": entered_channel,
        "phase4_forward_egress": fwd_egress_ticks >= 15,
    }

    return {
        "arm": "ARM-A",
        "config_id": cfg["config_id"],
        "env_id": env_id,
        "seed": seed,
        "outcome": outcome,
        "ticks_executed": tick + 1,
        "complete_maneuver": all(phases.values()),
        "mean_latency_ms": round(float(np.mean(lat_arr)), 2),
        "p95_latency_ms": round(float(np.percentile(lat_arr, 95)), 2),
        "mean_heading_error_deg": round(float(np.mean(herr_arr)), 2),
        "max_heading_error_deg": round(float(np.max(herr_arr)), 2),
        "p95_heading_error_deg": round(float(np.percentile(herr_arr, 95)), 2),
        "min_clearance_m": round(float(np.min(lat_arr) * 0 + telem.get("min_predicted_hull_clearance", 0.0)), 4),
        "mean_candidate_veto_frac": round(float(np.mean(veto_arr)), 3),
        "max_stagnant_ticks": max_stagnant,
        "final_y": round(new_y, 4),
        "final_x": round(new_x, 4),
        "phases": phases,
        "trajectory": trajectory,
    }



def generate_screening_plots(results: List[Dict[str, Any]], plots_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    env1_results = [r for r in results if r["env_id"] == 1]
    env2_results = [r for r in results if r["env_id"] == 2]

    # --- Plot 1: Env 1 Trajectories ---
    fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
    ax.set_title("Canonical Organism (Active Inference) - Env 1: Turning Bay Trajectories", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")
    ax.grid(True, linestyle="--", alpha=0.5)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, res in enumerate(env1_results):
        traj = res.get("trajectory", [])
        if not traj:
            continue
        xs = [pt["x"] for pt in traj]
        ys = [pt["y"] for pt in traj]
        cfg_id = res["config_id"]
        outcome = res["outcome"]
        c = colors[i % len(colors)]
        ax.plot(xs, ys, label=f"Cfg {cfg_id} ({outcome}, {res['ticks_executed']}t)", color=c, lw=2.0, alpha=0.85)
        ax.plot(xs[0], ys[0], marker="o", color="green", markersize=6)
        end_marker = "s" if outcome == "ESCAPE" else ("x" if outcome == "COLLISION" else "v")
        ax.plot(xs[-1], ys[-1], marker=end_marker, color=c, markersize=8)

    ax.plot([], [], marker="o", color="green", linestyle="None", label="Start")
    ax.plot([], [], marker="s", color="black", linestyle="None", label="End (Escape)")
    ax.plot([], [], marker="x", color="black", linestyle="None", label="End (Collision/Timeout)")
    ax.axhline(y=-0.10, color="gray", linestyle=":", label="Escape Goal (y <= -0.10m)")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    plt.tight_layout()
    p1 = plots_dir / "screening_trajectories_env1.png"
    plt.savefig(p1, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {p1}")

    # --- Plot 2: Env 2 Trajectories ---
    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    ax.set_title("Canonical Organism (Active Inference) - Env 2: Asymmetric T-Junction Trajectories", fontsize=12, fontweight="bold")
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")
    ax.grid(True, linestyle="--", alpha=0.5)

    colors2 = ["#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#3366cc"]
    for i, res in enumerate(env2_results):
        traj = res.get("trajectory", [])
        if not traj:
            continue
        xs = [pt["x"] for pt in traj]
        ys = [pt["y"] for pt in traj]
        cfg_id = res["config_id"]
        outcome = res["outcome"]
        c = colors2[i % len(colors2)]
        ax.plot(xs, ys, label=f"Cfg {cfg_id} ({outcome}, {res['ticks_executed']}t)", color=c, lw=2.0, alpha=0.85)
        ax.plot(xs[0], ys[0], marker="o", color="green", markersize=6)
        end_marker = "s" if outcome == "ESCAPE" else ("x" if outcome == "COLLISION" else "v")
        ax.plot(xs[-1], ys[-1], marker=end_marker, color=c, markersize=8)

    ax.plot([], [], marker="o", color="green", linestyle="None", label="Start")
    ax.plot([], [], marker="s", color="black", linestyle="None", label="End (Escape)")
    ax.plot([], [], marker="x", color="black", linestyle="None", label="End (Collision/Timeout)")
    ax.axhline(y=-0.50, color="orange", linestyle="--", label="Channel Entry (y < -0.50m)")
    ax.axhline(y=-1.20, color="green", linestyle=":", label="Escape Goal (y <= -1.20m)")
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    plt.tight_layout()
    p2 = plots_dir / "screening_trajectories_env2.png"
    plt.savefig(p2, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {p2}")

    # --- Plot 3: Latency & Heading Diagnostics ---
    fig, (ax_lat, ax_head) = plt.subplots(1, 2, figsize=(14, 5), dpi=150)

    cfg_labels = [f"C{r['config_id']}\n(E{r['env_id']})" for r in results]
    x_pos = np.arange(len(results))

    mean_lats = [r["mean_latency_ms"] for r in results]
    p95_lats = [r["p95_latency_ms"] for r in results]

    ax_lat.bar(x_pos - 0.18, mean_lats, width=0.35, label="Mean Latency (ms)", color="#3498db")
    ax_lat.bar(x_pos + 0.18, p95_lats, width=0.35, label="p95 Latency (ms)", color="#e74c3c")
    ax_lat.axhline(y=20.0, color="blue", linestyle="--", label="Mean Budget (20 ms)")
    ax_lat.axhline(y=45.0, color="red", linestyle="--", label="p95 Budget (45 ms)")
    ax_lat.set_xticks(x_pos)
    ax_lat.set_xticklabels(cfg_labels, fontsize=9)
    ax_lat.set_ylabel("Latency (ms)")
    ax_lat.set_title("Canonical Cognitive Cycle Latency per Config", fontweight="bold")
    ax_lat.legend(loc="upper left", fontsize=8.5)
    ax_lat.grid(True, linestyle=":", alpha=0.6)

    mean_herrs = [r["mean_heading_error_deg"] for r in results]
    p95_herrs = [r["p95_heading_error_deg"] for r in results]

    ax_head.bar(x_pos - 0.18, mean_herrs, width=0.35, label="Mean Heading Error (°)", color="#2ecc71")
    ax_head.bar(x_pos + 0.18, p95_herrs, width=0.35, label="p95 Heading Error (°)", color="#f39c12")
    ax_head.set_xticks(x_pos)
    ax_head.set_xticklabels(cfg_labels, fontsize=9)
    ax_head.set_ylabel("Heading Error (degrees)")
    ax_head.set_title("CANN / Odometry Heading Error vs MuJoCo Truth", fontweight="bold")
    ax_head.legend(loc="upper left", fontsize=8.5)
    ax_head.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    p3 = plots_dir / "screening_latency_and_heading_diagnostics.png"
    plt.savefig(p3, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {p3}")


def main():
    print("=" * 60)
    print("STAGE 3.4-R4.3 SCREENING (10 CONFIGS, CANONICAL ORGANISM)")
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
              f"lat={result['mean_latency_ms']:.1f}ms veto={result['mean_candidate_veto_frac']:.2f} "
              f"phases={result['phases']} ({elapsed:.1f}s)")
        results.append(result)

    # Save
    out_file = EVIDENCE_DIR / "r4_3_screening_trials.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    env1 = [r for r in results if r["env_id"] == 1]
    env2 = [r for r in results if r["env_id"] == 2]

    print()
    print("=" * 60)
    print("SCREENING SUMMARY")
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

    sc_file = EVIDENCE_DIR / "r4_3_screening_scorecard.json"
    with open(sc_file, "w") as f:
        json.dump(scorecard, f, indent=2)

    print(f"\nSaved: {out_file}")
    print(f"Saved: {sc_file}")

    print("\nGenerating publication-quality screening plots...")
    generate_screening_plots(results, PLOTS_DIR)


if __name__ == "__main__":
    main()
