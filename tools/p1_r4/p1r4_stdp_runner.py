"""
tools/p1_r4/p1r4_stdp_runner.py — Master Campaign Runner for Phase 1-R4 STDP Plasticity

Executes the multi-episode developmental plasticity campaign:
- 3 Conditions: FULL_STDP, NO_STDP, STDP_SHUFFLED_TIMING
- 3 Seeds: 42 (Primary Gate), 101, 2024
- 8 Episodes per seed (Acquisition: 1-3 -> Persistence: 4-5 -> Reversal: 6-8)
- True 3D geometric signed distance queries on every tick (mujoco.mj_geomDistance)
- Full per-tick raw CSV telemetry logging
- HD 720p 30 FPS videos with STDP synaptic state & telemetry HUD overlay
- Produces P1R4_STDP_RAW_RUN_LEDGER.csv and P1R4_STDP_DECISION_TRACE.json
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

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from brain.p1_r4.carl_p1r4_environment import CarlP1R4Environment
from brain.p1_r4.carl_p1r4_agent import CarlP1R4Agent


CONDITIONS = ["FULL_STDP", "NO_STDP", "STDP_SHUFFLED_TIMING"]
SEEDS = [42, 101, 2024]
MAX_TICKS_PER_EPISODE = 300

ROBOT_GEOM_NAMES = [
    "chassis_bumper", "chassis_core", "chassis_shell",
    "tire_L", "tire_R", "torso_shell", "head_dome"
]


class CarlP1R4STDPRunner:
    """
    Master Runner for Phase 1-R4 STDP Synaptic Plasticity Validation Campaign.
    """
    def __init__(self, output_root: str = "evidence/p1_r4"):
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
                
        # HD 720p Renderer setup
        self.renderer = mujoco.Renderer(self.model, height=720, width=1280)
        self.cam = mujoco.MjvCamera()
        self.cam.type = mujoco.mjtCamera.mjCAMERA_TRACKING
        self.cam.trackbodyid = self.model.body("drive_deck").id
        self.cam.distance = 2.60
        self.cam.elevation = -30.0
        self.cam.azimuth = 140.0

    def compute_true_geometric_distance_and_contacts(self) -> Tuple[float, float, int, str, str, List[Dict[str, Any]]]:
        """Computes true geometric signed Euclidean separation and logs active penetration."""
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
                    active_pairs.append({
                        "geom1": g1_name,
                        "geom2": g2_name,
                        "dist": dist
                    })
                    
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
        """Renders 720p frame with full STDP synaptic & telemetry HUD overlay."""
        self.renderer.update_scene(self.data, camera=self.cam)
        rgb = self.renderer.render()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        h, w, _ = bgr.shape
        
        overlay = bgr.copy()
        cv2.rectangle(overlay, (0, 0), (w, 85), (14, 17, 23), -1)
        cv2.rectangle(overlay, (0, h - 115), (w, h), (14, 17, 23), -1)
        cv2.addWeighted(overlay, 0.85, bgr, 0.15, 0, bgr)
        
        # Header Text
        title_color = (0, 229, 255) if cond == "FULL_STDP" else ((255, 82, 82) if cond == "NO_STDP" else (255, 215, 0))
        cv2.putText(bgr, f"CARL-DX P1-R4 STDP PLASTICITY: {cond} | SEED {seed} | EPISODE {ep}", (25, 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.70, title_color, 2, cv2.LINE_AA)
        cv2.putText(bgr, f"TICK: {tick:04d} | TIME: {sim_time:5.2f}s | POSE: ({px:+.2f}, {py:+.2f}) psi={math.degrees(yaw):+5.1f}deg | ROUTE: {route_choice}",
                    (25, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (230, 237, 243), 1, cv2.LINE_AA)
        
        # Target Food Badge
        cv2.putText(bgr, f"TARGET: (2.20, 0.00) | DIST: {dist_food:.2f}m", (w - 380, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 102), 1, cv2.LINE_AA)
        
        # Bottom Line 1: STDP Synaptic Status
        stdp_txt = f"STDP SYNAPSES (154): ||W||={w_norm:.3f} | mean(W)={w_mean:+.3f} | dW={dw_norm:.4f} | LTP:{ltp} LTD:{ltd}" if cond != "NO_STDP" else "STDP SYNAPSES: DISABLED (CONTROL BASELINE)"
        cv2.putText(bgr, stdp_txt, (25, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 150), 1, cv2.LINE_AA)
        
        # Bottom Line 2: Sequence & Clearance
        cv2.putText(bgr, f"ACTION: [{sequence}] | MIN CLEARANCE: {min_geom_dist:+.4f}m ({nearest_robot} <-> {nearest_wall}) | PE: {pred_err:.3f}m/s",
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
        """Executes a single physical episode with STDP learning and logging."""
        self.env.configure_environment(episode, reversal=reversal)
        self.env.reset_robot_pose(0.0, 0.0, 0.0)
        
        # Preserve synapses across episodes within the same lifetime
        preserve_syn = (episode > 1 and condition != "NO_STDP")
        agent.reset_for_episode(episode, seed, condition, preserve_synapses=preserve_syn, preserve_hdc=True)
        
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
            
            if px > 0.35 and route_choice == "UNDECIDED":
                commitment_tick = tick
                pre_haz_y = py
                route_choice = "ROUTE_A (North)" if py > 0.00 else "ROUTE_B (South)"
                
            dist_food = float(step_res["dist_food"])
            if dist_food < 0.30 or step_res["food_absorbed"]:
                acquired = True
                acquisition_time = sim_time
                
            tick_data = {
                "episode": episode,
                "seed": seed,
                "tick": tick,
                "x": round(px, 4),
                "y": round(py, 4),
                "yaw": round(yaw, 4),
                "selected_route": route_choice,
                "selected_action": step_res["best_action"],
                "selected_sequence": step_res["best_sequence"],
                "EFE": round(step_res["best_efe"], 2),
                "prediction_error": round(float(step_res["prediction_error"]), 4),
                "stdp_dw_norm": round(float(step_res["stdp_dw_norm"]), 5),
                "stdp_weight_norm": round(float(step_res["stdp_weight_norm"]), 4),
                "stdp_mean_weight": round(float(step_res["stdp_mean_weight"]), 4),
                "stdp_weight_var": round(float(step_res["stdp_weight_var"]), 5),
                "ltp_events": agent.ltp_events,
                "ltd_events": agent.ltd_events,
                "collision_count": n_contacts,
                "min_true_clearance": round(min_geom_dist, 5),
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
            "run_id": f"P1R4_{condition}_S{seed}_EP{episode}",
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

    def execute_campaign(self) -> Dict[str, Any]:
        """Executes full P1-R4 developmental plasticity campaign."""
        print("=" * 80)
        print("STARTING CARL-DX PHASE 1-R4 STDP SYNAPTIC PLASTICITY VALIDATION CAMPAIGN")
        print("=" * 80)
        
        run_summaries = []
        
        # --- STAGE 1: SEED 42 CAUSAL GATE ---
        print("\n>>> STAGE 1: SEED 42 CAUSAL GATE (8 EPISODES PER CONDITION) <<<")
        s42_results = {}
        for cond in CONDITIONS:
            enable_stdp = (cond != "NO_STDP")
            shuffle = (cond == "STDP_SHUFFLED_TIMING")
            agent = CarlP1R4Agent(dt=0.0333, enable_stdp=enable_stdp, enable_hdc_memory=True, shuffle_stdp_timing=shuffle)
            s42_results[cond] = []
            
            for ep in range(1, 9):
                reversal = (ep >= 6)
                summary, df_ticks = self.run_single_episode(agent, cond, 42, ep, reversal=reversal, render_video=True)
                csv_path = os.path.join(self.telemetry_dir, f"{summary['run_id']}.csv")
                df_ticks.to_csv(csv_path, index=False)
                s42_results[cond].append(summary)
                run_summaries.append(summary)
                
                r = summary["route_choice"]
                w_n = summary["final_weight_norm"]
                ltp = summary["ltp_events"]
                ltd = summary["ltd_events"]
                print(f"[{cond:20s} | S42 | EP{ep} | {summary['phase']:11s}] Route: {r:17s} (y={summary['pre_haz_y']:+.2f}m) | ||W||={w_n:.3f} | LTP:{ltp:3d} LTD:{ltd:3d}")

        # Check Seed 42 Causal Gate
        full_w_change = s42_results["FULL_STDP"][-1]["cumulative_dw"]
        s42_passed = (full_w_change > 0.05 and s42_results["FULL_STDP"][1]["route_choice"] == "ROUTE_A (North)")
        
        if not s42_passed:
            print("\n" + "!" * 80)
            print("SEED 42 STDP CAUSAL GATE FAILED: Stopping campaign.")
            print("!" * 80)
            return {"status": "FAILED_AT_SEED_42"}
            
        print("\n>>> SEED 42 STDP CAUSAL GATE PASSED: Proceeding to multi-seed replication (Seeds 101 & 2024) <<<")
        
        # --- STAGE 2: SEEDS 101 & 2024 REPLICATION ---
        for seed in [101, 2024]:
            for cond in CONDITIONS:
                enable_stdp = (cond != "NO_STDP")
                shuffle = (cond == "STDP_SHUFFLED_TIMING")
                agent = CarlP1R4Agent(dt=0.0333, enable_stdp=enable_stdp, enable_hdc_memory=True, shuffle_stdp_timing=shuffle)
                
                for ep in range(1, 9):
                    reversal = (ep >= 6)
                    summary, df_ticks = self.run_single_episode(agent, cond, seed, ep, reversal=reversal, render_video=False)
                    csv_path = os.path.join(self.telemetry_dir, f"{summary['run_id']}.csv")
                    df_ticks.to_csv(csv_path, index=False)
                    run_summaries.append(summary)
                    
                    r = summary["route_choice"]
                    w_n = summary["final_weight_norm"]
                    ltp = summary["ltp_events"]
                    ltd = summary["ltd_events"]
                    print(f"[{cond:20s} | S{seed:4d} | EP{ep} | {summary['phase']:11s}] Route: {r:17s} (y={summary['pre_haz_y']:+.2f}m) | ||W||={w_n:.3f} | LTP:{ltp:3d} LTD:{ltd:3d}")

        # Save Master Run Ledger CSV
        df_runs = pd.DataFrame(run_summaries)
        ledger_path = "d:/ebca/P1R4_STDP_RAW_RUN_LEDGER.csv"
        df_runs.to_csv(ledger_path, index=False)
        print(f"\n[LEDGER SAVED] -> {ledger_path}")
        
        # Save Decision Trace JSON
        trace_path = "d:/ebca/P1R4_STDP_DECISION_TRACE.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(run_summaries, f, indent=2)
        print(f"[DECISION TRACE SAVED] -> {trace_path}")
        
        return {"status": "CAMPAIGN_COMPLETE", "total_runs": len(run_summaries)}


if __name__ == "__main__":
    runner = CarlP1R4STDPRunner()
    runner.execute_campaign()
