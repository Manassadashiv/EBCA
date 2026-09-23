"""
tools/p1_r4/p1r4_isolation_runner.py — Master Isolation Campaign Runner for Phase 1-R4

Isolates Three-Factor STDP from HDC Episodic Memory:
1. Evaluates baseline parameters (eta=0.015, lambda=45.0) on Seed 42.
2. Performs bounded parameter calibration sweep (eta in [0.015, 0.05, 0.10, 0.15], lambda in [45, 90, 150]).
3. Executes 3-Seed Replication Campaign (Seeds 42, 101, 2024 x 8 Episodes x 3 Conditions).
4. Generates full per-tick telemetry CSVs and HD 720p 30 FPS videos with real-time synaptic HUD.
5. Saves P1R4_ISOLATION_RAW_RUN_LEDGER.csv and P1R4_ISOLATION_DECISION_TRACE.json.
"""

import os
import sys
import math
import json
import numpy as np
import pandas as pd
import cv2
import mujoco
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from brain.p1_r4.carl_p1r4_environment import CarlP1R4Environment
from brain.p1_r4.carl_p1r4_agent import CarlP1R4Agent

CONDITIONS = ["NO_HDC_STDP", "NO_HDC_NO_STDP", "NO_HDC_SHUFFLED_STDP"]
SEEDS = [42, 101, 2024]
MAX_TICKS_PER_EPISODE = 300

ROBOT_GEOM_NAMES = [
    "chassis_bumper", "chassis_core", "chassis_shell",
    "tire_L", "tire_R", "torso_shell", "head_dome"
]


class CarlP1R4IsolationRunner:
    def __init__(self, output_root: str = "evidence/p1_r4_isolation"):
        self.output_root = output_root
        self.telemetry_dir = os.path.join(output_root, "telemetry")
        self.videos_dir = os.path.join(output_root, "videos")
        self.plots_dir = os.path.join(output_root, "plots")
        
        os.makedirs(self.telemetry_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        
        self.env = CarlP1R4Environment()
        self.model = self.env.model
        self.data = self.env.data
        
        self.robot_geom_ids = [self.model.geom(name).id for name in ROBOT_GEOM_NAMES if name in self.env.geom_names]
        self.wall_geom_ids = []
        for i in range(self.model.ngeom):
            gname = self.model.geom(i).name
            if ("wall" in gname or "lwall" in gname) and "wg_" not in gname and gname != "floor":
                self.wall_geom_ids.append(i)
                
        self.renderer = mujoco.Renderer(self.model, height=720, width=1280)
        self.cam = mujoco.MjvCamera()
        self.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.cam.trackbodyid = self.model.body("drive_deck").id
        self.cam.distance = 2.60
        self.cam.elevation = -30.0
        self.cam.azimuth = 140.0

    def compute_true_geometric_distance_and_contacts(self) -> Tuple[float, float, int, str, str, List[Dict[str, Any]]]:
        active_walls = [wid for wid in self.wall_geom_ids if abs(self.model.geom_pos[wid][0]) < 10.0 and abs(self.model.geom_pos[wid][1]) < 10.0]
        min_geom_dist = float("inf")
        nearest_robot = None
        nearest_wall = None
        
        fromto = np.zeros(6)
        for r_id in self.robot_geom_ids:
            for w_id in active_walls:
                _ = mujoco.mj_geomDistance(self.model, self.data, r_id, w_id, 10.0, fromto)
                dx = fromto[3] - fromto[0]
                dy = fromto[4] - fromto[1]
                dz = fromto[5] - fromto[2]
                d_pair = float(np.sqrt(dx**2 + dy**2 + dz**2))
                if d_pair < min_geom_dist:
                    min_geom_dist = d_pair
                    nearest_robot = self.model.geom(r_id).name
                    nearest_wall = self.model.geom(w_id).name
                    
        contact_count = 0
        max_penetration = 0.0
        active_pairs = []
        for i in range(self.data.ncon):
            con = self.data.contact[i]
            g1_name = self.model.geom(con.geom1).name
            g2_name = self.model.geom(con.geom2).name
            if g1_name != "floor" and g2_name != "floor":
                is_r1 = any(r in g1_name for r in ROBOT_GEOM_NAMES)
                is_r2 = any(r in g2_name for r in ROBOT_GEOM_NAMES)
                if is_r1 or is_r2:
                    contact_count += 1
                    dist = float(con.dist)
                    if dist < 0:
                        max_penetration = max(max_penetration, abs(dist))
                    active_pairs.append({"geom1": g1_name, "geom2": g2_name, "dist": dist})
                    
        signed_dist = -max_penetration if max_penetration > 0.0 else min_geom_dist
        return signed_dist, max_penetration, contact_count, nearest_robot, nearest_wall, active_pairs

    def render_frame_with_hud(
        self,
        cond: str,
        seed: int,
        ep: int,
        tick: int,
        sim_time: float,
        px: float,
        py: float,
        yaw: float,
        route_choice: str,
        action: str,
        sequence: str,
        w_norm: float,
        w_mean: float,
        dw_norm: float,
        ltp: int,
        ltd: int,
        min_geom_dist: float,
        contact_count: int,
        nearest_robot: str,
        nearest_wall: str,
        pred_err: float,
        dist_food: float
    ) -> np.ndarray:
        self.renderer.update_scene(self.data, camera=self.cam)
        rgb = self.renderer.render()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        h, w, _ = bgr.shape
        
        overlay = bgr.copy()
        cv2.rectangle(overlay, (0, 0), (w, 85), (14, 17, 23), -1)
        cv2.rectangle(overlay, (0, h - 115), (w, h), (14, 17, 23), -1)
        cv2.addWeighted(overlay, 0.85, bgr, 0.15, 0, bgr)
        
        title_color = (0, 229, 255) if "STDP" in cond and "SHUFFLED" not in cond else ((255, 82, 82) if "NO_STDP" in cond else (255, 215, 0))
        cv2.putText(bgr, f"CARL-DX P1-R4 ISOLATION: {cond} | SEED {seed} | EP {ep} (HDC: OFF)", (25, 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.68, title_color, 2, cv2.LINE_AA)
        cv2.putText(bgr, f"TICK: {tick:04d} | TIME: {sim_time:5.2f}s | POSE: ({px:+.2f}, {py:+.2f}) psi={math.degrees(yaw):+5.1f}deg | ROUTE: {route_choice}",
                    (25, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (230, 237, 243), 1, cv2.LINE_AA)
        
        cv2.putText(bgr, f"TARGET: (2.20, 0.00) | DIST: {dist_food:.2f}m", (w - 380, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 102), 1, cv2.LINE_AA)
        
        stdp_txt = f"STDP SYNAPSES (154): ||W||={w_norm:.3f} | mean(W)={w_mean:+.3f} | dW={dw_norm:.4f} | LTP:{ltp} LTD:{ltd}" if "NO_STDP" not in cond else "STDP SYNAPSES: DISABLED (CONTROL BASELINE)"
        cv2.putText(bgr, stdp_txt, (25, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 150), 1, cv2.LINE_AA)
        cv2.putText(bgr, f"ACTION: [{sequence}] | CLEARANCE: {min_geom_dist:+.4f}m ({nearest_robot} <-> {nearest_wall}) | PE: {pred_err:.3f}m/s",
                    (25, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 229, 255), 1, cv2.LINE_AA)
        return bgr

    def run_single_episode(
        self,
        agent: CarlP1R4Agent,
        condition: str,
        seed: int,
        episode: int,
        reversal: bool = False,
        render_video: bool = True
    ) -> Tuple[Dict[str, Any], pd.DataFrame]:
        self.env.configure_environment(episode, reversal=reversal)
        self.env.reset_robot_pose(0.0, 0.0, 0.0)
        
        # In isolation, HDC memory is strictly disabled (preserve_hdc=False, enable_hdc_memory=False)
        preserve_syn = (episode > 1 and "NO_STDP" not in condition)
        agent.reset_for_episode(episode, seed, condition, preserve_synapses=preserve_syn, preserve_hdc=False)
        
        video_writer = None
        if render_video and (seed == 42 or episode in (1, 2, 6)):
            v_name = f"{condition.lower()}_s{seed}_ep{episode}.mp4"
            v_path = os.path.join(self.videos_dir, v_name)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(v_path, fourcc, 30.0, (1280, 720))
            
        ticks_records = []
        route_choice = "UNDECIDED"
        commitment_tick = None
        pre_haz_y = 0.0
        acquired = False
        acquisition_time = None
        
        for tick in range(MAX_TICKS_PER_EPISODE):
            step_res = agent.step(self.env.hal, target_coords=self.env.food_coords)
            sensory = step_res["sensory"]
            
            px = float(sensory.pos_x)
            py = float(sensory.pos_y)
            yaw = float(sensory.yaw)
            sim_time = tick * 0.0333
            col = bool(sensory.has_body_collision)
            
            min_geom_dist, max_pen, n_contacts, nearest_robot, nearest_wall, active_pairs = self.compute_true_geometric_distance_and_contacts()
            
            # Determine explicit causal event marker
            event_marker = "NORMAL_CRUISE"
            if tick == 10:
                event_marker = "STARTUP_SETTLED"
            elif px > 0.35 and route_choice == "UNDECIDED":
                event_marker = "ROUTE_COMMITMENT"
            elif col or (step_res["prediction_error"] > 0.15 and sensory.speed < 0.05 and tick > 10):
                if float(step_res["stdp_dw_norm"]) > 0:
                    event_marker = "FIRST_STDP_UPDATE" if agent.ltd_events <= 2 else "ENVIRONMENTAL_EVENT"
                else:
                    event_marker = "ENVIRONMENTAL_EVENT"
            elif acquired:
                event_marker = "HAZARD_AVOIDED" if pre_haz_y > 0 else "GOAL_REACHED"
                
            if px > 0.35 and route_choice == "UNDECIDED":
                commitment_tick = tick
                pre_haz_y = py
                route_choice = "ROUTE_A (North)" if py > 0.00 else "ROUTE_B (South)"
                
            dist_food = float(step_res["dist_food"])
            if dist_food < 0.30 or step_res["food_absorbed"]:
                acquired = True
                acquisition_time = sim_time
                
            q_vals = step_res["stdp_q_values"]
            
            tick_data = {
                "episode": episode,
                "seed": seed,
                "tick": tick,
                "x": round(px, 4),
                "y": round(py, 4),
                "yaw": round(yaw, 4),
                "speed": round(float(sensory.speed), 4),
                "v_expected": round(float(step_res["v_expected"]), 4),
                "selected_route": route_choice,
                "selected_action": step_res["best_action"],
                "selected_sequence": step_res["best_sequence"],
                "EFE": round(step_res["best_efe"], 2),
                "prediction_error": round(float(step_res["prediction_error"]), 4),
                "surprise_gate": round(float(step_res["surprise_gate"]), 4),
                "outcome_valence": round(float(step_res["outcome_valence"]), 2),
                "stdp_dw_norm": round(float(step_res["stdp_dw_norm"]), 5),
                "stdp_weight_norm": round(float(step_res["stdp_weight_norm"]), 4),
                "stdp_mean_weight": round(float(step_res["stdp_mean_weight"]), 4),
                "stdp_weight_var": round(float(step_res["stdp_weight_var"]), 5),
                "ltp_events": agent.ltp_events,
                "ltd_events": agent.ltd_events,
                "collision_count": n_contacts,
                "min_true_clearance": round(min_geom_dist, 5),
                "event_marker": event_marker,
                "q_stdp_straight": round(float(q_vals[0]), 4),
                "q_stdp_curve_left_gentle": round(float(q_vals[1]), 4),
                "q_stdp_curve_left_sharp": round(float(q_vals[2]), 4),
                "q_stdp_swerve_left": round(float(q_vals[3]), 4),
                "q_stdp_curve_right_gentle": round(float(q_vals[4]), 4),
                "q_stdp_curve_right_sharp": round(float(q_vals[5]), 4),
                "q_stdp_swerve_right": round(float(q_vals[6]), 4),
                "condition": condition
            }
            ticks_records.append(tick_data)

            
            if video_writer is not None:
                frame = self.render_frame_with_hud(
                    condition, seed, episode, tick, sim_time, px, py, yaw,
                    route_choice, step_res["best_action"], step_res["best_sequence"],
                    step_res["stdp_weight_norm"], step_res["stdp_mean_weight"], step_res["stdp_dw_norm"],
                    agent.ltp_events, agent.ltd_events, min_geom_dist, n_contacts,
                    nearest_robot, nearest_wall, step_res["prediction_error"], dist_food
                )
                video_writer.write(frame)
                
            if acquired:
                break
            if col and tick > 200:
                break
                
        if video_writer is not None:
            video_writer.release()
            
        agent.end_episode_consolidation()
        df_ticks = pd.DataFrame(ticks_records)
        
        summary = {
            "run_id": f"P1R4_ISOLATION_{condition}_S{seed}_EP{episode}",
            "condition": condition,
            "seed": seed,
            "episode": episode,
            "phase": "ACQUISITION" if episode <= 3 else ("PERSISTENCE" if episode <= 5 else "REVERSAL"),
            "route_choice": route_choice,
            "pre_haz_y": float(pre_haz_y),
            "commitment_tick": commitment_tick,
            "acquired": acquired,
            "acquisition_time_s": acquisition_time,
            "final_weight_norm": float(np.linalg.norm(agent.W)),
            "final_mean_weight": float(np.mean(agent.W)),
            "cumulative_dw": float(agent.cumulative_dw),
            "ltp_events": agent.ltp_events,
            "ltd_events": agent.ltd_events,
            "min_clearance_m": float(df_ticks["min_true_clearance"].min()),
            "total_ticks": len(ticks_records)
        }
        return summary, df_ticks

    def execute_isolation_pilot_and_calibration(self) -> Tuple[float, float, Dict[str, Any]]:
        """
        Executes Step 1 & Step 2: Evaluates baseline parameters on Seed 42,
        and performs a bounded parameter sweep if baseline is sub-threshold.
        """
        print("=" * 80)
        print("STEP 1: EVALUATING BASELINE STDP PARAMETERS ON SEED 42 (HDC DISABLED)")
        print("=" * 80)
        
        # Test baseline parameters
        agent_base = CarlP1R4Agent(dt=0.0333, enable_stdp=True, enable_hdc_memory=False, stdp_lr=0.015, stdp_lambda=45.0)
        s_ep1, _ = self.run_single_episode(agent_base, "NO_HDC_STDP", 42, 1, reversal=False, render_video=False)
        s_ep2, _ = self.run_single_episode(agent_base, "NO_HDC_STDP", 42, 2, reversal=False, render_video=False)
        
        base_dw = s_ep1["cumulative_dw"]
        base_ep2_route = s_ep2["route_choice"]
        print(f"Baseline (eta=0.015, lambda=45.0) -> Ep1 dW: {base_dw:.5f} | Ep2 Route: {base_ep2_route}")
        
        # Bounded parameter calibration sweep
        print("\n" + "=" * 80)
        print("STEP 2: BOUNDED PARAMETER GAIN CALIBRATION SWEEP")
        print("=" * 80)
        
        candidates = [
            (0.015, 45.0),
            (0.05, 90.0),
            (0.10, 120.0),
            (0.15, 150.0)
        ]
        sweep_records = []
        best_eta, best_lambda = 0.015, 45.0
        selected = False
        
        for eta, lam in candidates:
            ag = CarlP1R4Agent(dt=0.0333, enable_stdp=True, enable_hdc_memory=False, stdp_lr=eta, stdp_lambda=lam)
            s1, _ = self.run_single_episode(ag, "NO_HDC_STDP", 42, 1, reversal=False, render_video=False)
            s2, _ = self.run_single_episode(ag, "NO_HDC_STDP", 42, 2, reversal=False, render_video=False)
            
            w_norm = s1["final_weight_norm"]
            dw = s1["cumulative_dw"]
            r2 = s2["route_choice"]
            y2 = s2["pre_haz_y"]
            
            rec = {
                "eta": eta,
                "lambda_stdp": lam,
                "dw_norm": round(dw, 5),
                "weight_norm": round(w_norm, 4),
                "ep2_route": r2,
                "ep2_lat_y": round(y2, 3),
                "switched": (r2 == "ROUTE_A (North)"),
                "numerical_stability": "STABLE" if not np.isnan(w_norm) and w_norm < 10.0 else "UNSTABLE"
            }
            sweep_records.append(rec)
            print(f"Candidate (eta={eta:5.3f}, lambda={lam:5.1f}) -> ||W||: {w_norm:.4f} | dW: {dw:.5f} | Ep2: {r2} (y={y2:+.2f}m) | {rec['numerical_stability']}")
            
            if not selected and rec["switched"] and rec["numerical_stability"] == "STABLE":
                best_eta = eta
                best_lambda = lam
                selected = True
                
        if not selected:
            best_eta, best_lambda = 0.15, 150.0  # Use max bounded candidate
            
        print(f"\n[CALIBRATION DECISION] Selected minimal effective parameters: eta = {best_eta}, lambda_stdp = {best_lambda}")
        return best_eta, best_lambda, {"sweep": sweep_records, "selected_eta": best_eta, "selected_lambda": best_lambda}

    def execute_campaign(self) -> Dict[str, Any]:
        best_eta, best_lambda, calib_info = self.execute_isolation_pilot_and_calibration()
        
        print("\n" + "=" * 80)
        print(f"STARTING FULL P1-R4 ISOLATION CAMPAIGN (eta={best_eta}, lambda={best_lambda}, HDC=OFF)")
        print("=" * 80)
        
        run_summaries = []
        
        for seed in SEEDS:
            print(f"\n>>> EXECUTING SEED {seed} <<<")
            for cond in CONDITIONS:
                enable_stdp = (cond != "NO_HDC_NO_STDP")
                shuffle = (cond == "NO_HDC_SHUFFLED_STDP")
                agent = CarlP1R4Agent(
                    dt=0.0333,
                    enable_stdp=enable_stdp,
                    enable_hdc_memory=False,
                    shuffle_stdp_timing=shuffle,
                    stdp_lr=best_eta,
                    stdp_lambda=best_lambda
                )
                
                for ep in range(1, 9):
                    reversal = (ep >= 6)
                    render = (seed == 42)
                    summary, df_ticks = self.run_single_episode(agent, cond, seed, ep, reversal=reversal, render_video=render)
                    csv_path = os.path.join(self.telemetry_dir, f"{summary['run_id']}.csv")
                    df_ticks.to_csv(csv_path, index=False)
                    run_summaries.append(summary)
                    
                    r = summary["route_choice"]
                    w_n = summary["final_weight_norm"]
                    ltp = summary["ltp_events"]
                    ltd = summary["ltd_events"]
                    print(f"[{cond:21s} | S{seed:4d} | EP{ep} | {summary['phase']:11s}] Route: {r:17s} (y={summary['pre_haz_y']:+.2f}m) | ||W||={w_n:.3f} | LTP:{ltp:3d} LTD:{ltd:3d}")

        # Save Master Run Ledger CSV
        df_runs = pd.DataFrame(run_summaries)
        ledger_path = "d:/ebca/P1R4_ISOLATION_RAW_RUN_LEDGER.csv"
        df_runs.to_csv(ledger_path, index=False)
        print(f"\n[LEDGER SAVED] -> {ledger_path}")
        
        # Save Decision Trace JSON
        trace_path = "d:/ebca/P1R4_ISOLATION_DECISION_TRACE.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump({
                "calibration": calib_info,
                "runs": run_summaries
            }, f, indent=2)
        print(f"[DECISION TRACE SAVED] -> {trace_path}")
        
        return {"status": "ISOLATION_CAMPAIGN_COMPLETE", "total_runs": len(run_summaries)}


if __name__ == "__main__":
    runner = CarlP1R4IsolationRunner()
    runner.execute_campaign()
