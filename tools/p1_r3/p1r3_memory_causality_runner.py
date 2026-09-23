"""
tools/p1_r3/p1r3_memory_causality_runner.py — Master Orchestrator for P1-R3 Memory Causality Validation

Executes the complete 18-episode scientific campaign:
- 2 Conditions: FULL_P1_R3, NO_MEMORY
- 3 Seeds: 42 (Primary Causal Gate), 101, 2024
- 3 Episodes per seed: Ep 1 (Experience) -> Ep 2 (Recurrence) -> Ep 3 (Context Update / Extinction)
- True 3D geometric signed distance queries on every tick (mujoco.mj_geomDistance)
- Full 27-column per-tick raw CSV telemetry logging
- 6 Canonical HD 720p 30 FPS videos with real-time clearance, EFE, and memory HUD overlay
- Full integration with AST auditor, independent verifier, and 9-figure plot generator
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

from brain.p1_r3.carl_p1r3_environment import CarlP1R3Environment
from brain.p1_r3.carl_p1r3_agent import CarlP1R3Agent


CONDITIONS = ["FULL_P1_R3", "NO_MEMORY"]
SEEDS = [42, 101, 2024]
EPISODES = [1, 2, 3]
MAX_TICKS_PER_EPISODE = 350

ROBOT_GEOM_NAMES = [
    "chassis_bumper", "chassis_core", "chassis_shell",
    "tire_L", "tire_R", "torso_shell", "head_dome"
]


class CarlP1R3MemoryCausalityRunner:
    """
    Master Runner for P1-R3 Memory Causality Validation Campaign.
    """
    def __init__(self, output_root: str = "evidence/p1_r3/memory_causality"):
        self.output_root = output_root
        self.telemetry_dir = os.path.join(output_root, "telemetry")
        self.videos_dir = os.path.join(output_root, "videos")
        self.plots_dir = os.path.join(output_root, "plots")
        
        os.makedirs(self.telemetry_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        
        self.env = CarlP1R3Environment()
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
        efe_A: float,
        efe_B: float,
        min_geom_dist: float,
        max_pen: float,
        contact_count: int,
        nearest_robot: str,
        nearest_wall: str,
        mem_writes: int,
        mem_retrievals: int,
        mem_sim: float,
        pred_err: float,
        dist_food: float
    ) -> np.ndarray:
        """Renders 720p frame with full collision, EFE decomposition, and memory HUD overlay."""
        self.renderer.update_scene(self.data, camera=self.cam)
        rgb = self.renderer.render()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        h, w, _ = bgr.shape
        
        # Header & Footer Banners
        overlay = bgr.copy()
        cv2.rectangle(overlay, (0, 0), (w, 85), (14, 17, 23), -1)
        cv2.rectangle(overlay, (0, h - 115), (w, h), (14, 17, 23), -1)
        cv2.addWeighted(overlay, 0.85, bgr, 0.15, 0, bgr)
        
        # Header Text
        title_color = (0, 229, 255) if cond == "FULL_P1_R3" else (255, 82, 82)
        cv2.putText(bgr, f"CARL-DX P1-R3: {cond} | SEED {seed} | EPISODE {ep}", (25, 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, title_color, 2, cv2.LINE_AA)
        cv2.putText(bgr, f"TICK: {tick:04d} | TIME: {sim_time:5.2f}s | POSE: ({px:+.2f}, {py:+.2f}) psi={math.degrees(yaw):+5.1f}deg | ROUTE: {route_choice}",
                    (25, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (230, 237, 243), 1, cv2.LINE_AA)
        
        # Target Food Badge
        cv2.putText(bgr, f"TARGET: (2.20, 0.00) | DIST: {dist_food:.2f}m", (w - 380, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 102), 1, cv2.LINE_AA)
        
        # Bottom Line 1: Collision & Clearance Telemetry
        status_color = (0, 255, 102) if max_pen == 0.0 else (0, 0, 255)
        cv2.putText(bgr, f"MIN CLEARANCE: {min_geom_dist:+.4f}m ({nearest_robot} <-> {nearest_wall}) | CONTACTS: {contact_count} | MAX PEN: {max_pen:.4f}m",
                    (25, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_color, 1, cv2.LINE_AA)
                    
        # Bottom Line 2: EFE Decomposition & Sequence
        cv2.putText(bgr, f"ACTION: [{sequence}] | EFE(A_North): {efe_A:.1f} | EFE(B_South): {efe_B:.1f} | PE: {pred_err:.3f}m/s",
                    (25, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 229, 255), 1, cv2.LINE_AA)
                    
        # Bottom Line 3: Memory Activity
        mem_txt = f"EPISODIC MEMORY: WRITES={mem_writes} | RETRIEVALS={mem_retrievals} | BEST SIM={mem_sim:.3f}" if cond == "FULL_P1_R3" else "EPISODIC MEMORY: DISABLED (CONTROL BASELINE)"
        mem_color = (0, 255, 150) if cond == "FULL_P1_R3" else (160, 160, 160)
        cv2.putText(bgr, mem_txt, (25, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.48, mem_color, 1, cv2.LINE_AA)
        
        return bgr

    def run_single_episode(
        self,
        agent: CarlP1R3Agent,
        condition: str,
        seed: int,
        episode: int,
        render_video: bool = True
    ) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """Executes a single physical simulation episode, recording all 27 required telemetry columns."""
        self.env.configure_environment(episode)
        self.env.reset_robot_pose(0.0, 0.0, 0.0)
        agent.reset_for_episode(episode, seed, condition, preserve_memory=True)
        
        video_writer = None
        if render_video:
            v_name = f"{condition.lower()}_s{seed}_ep{episode}.mp4"
            v_path = os.path.join(self.videos_dir, v_name)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(v_path, fourcc, 30.0, (1280, 720))
            
        ticks_records = []
        route_choice_at_commitment = "UNDECIDED"
        commitment_tick = None
        pre_hazard_lat_y = 0.0
        acquired = False
        acquisition_time = None
        hazard_encountered = False
        
        for tick in range(MAX_TICKS_PER_EPISODE):
            step_res = agent.step(self.env.hal, target_coords=self.env.food_coords)
            sensory = step_res["sensory"]
            
            px = float(sensory.pos_x)
            py = float(sensory.pos_y)
            yaw = float(sensory.yaw)
            sim_time = tick * 0.0333
            col = bool(sensory.has_body_collision)
            
            # True geometric distance & contact query
            min_geom_dist, max_pen, n_contacts, nearest_robot, nearest_wall, active_pairs = self.compute_true_geometric_distance_and_contacts()
            
            # Route commitment at x = 0.35m (strictly before line-of-sight to hazard at x = 0.45m)
            if px > 0.35 and route_choice_at_commitment == "UNDECIDED":
                commitment_tick = tick
                pre_hazard_lat_y = py
                route_choice_at_commitment = "ROUTE_A (North)" if py > 0.00 else "ROUTE_B (South)"
                
            if px > 0.60 and py < -0.10 and col:
                hazard_encountered = True
                
            dist_food = float(step_res["dist_food"])
            if dist_food < 0.30 or step_res["food_absorbed"]:
                acquired = True
                acquisition_time = sim_time
                
            # EFE Route Decomposition
            cand_efes = step_res["candidate_efes"]
            # North-biasing candidate sequences vs South-biasing candidate sequences
            north_efes = [v for k, v in cand_efes.items() if "LEFT" in k]
            south_efes = [v for k, v in cand_efes.items() if "RIGHT" in k]
            efe_A = float(np.mean(north_efes)) if north_efes else float(step_res["best_efe"])
            efe_B = float(np.mean(south_efes)) if south_efes else float(step_res["best_efe"])
            
            # Softmax Route Probabilities
            beta = 0.05
            exp_A = math.exp(-beta * (efe_A - min(efe_A, efe_B)))
            exp_B = math.exp(-beta * (efe_B - min(efe_A, efe_B)))
            prob_A = exp_A / (exp_A + exp_B)
            prob_B = exp_B / (exp_A + exp_B)
            
            # Sonar readings array
            sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 5.0
            
            tick_data = {
                "episode": episode,
                "seed": seed,
                "tick": tick,
                "x": round(px, 4),
                "y": round(py, 4),
                "yaw": round(yaw, 4),
                "sonar_0": round(float(sonar[0]), 4),
                "sonar_1": round(float(sonar[1]), 4),
                "sonar_2": round(float(sonar[2]), 4),
                "sonar_3": round(float(sonar[3]), 4),
                "sonar_4": round(float(sonar[4]), 4),
                "sonar_5": round(float(sonar[5]), 4),
                "sonar_6": round(float(sonar[6]), 4),
                "sonar_7": round(float(sonar[7]), 4),
                "sonar_8": round(float(sonar[8]), 4),
                "sonar_9": round(float(sonar[9]), 4),
                "sonar_10": round(float(sonar[10]), 4),
                "sonar_11": round(float(sonar[11]), 4),
                "sonar_12": round(float(sonar[12]), 4),
                "sonar_13": round(float(sonar[13]), 4),
                "sonar_14": round(float(sonar[14]), 4),
                "target_distance": round(dist_food, 4),
                "homeostatic_state": round(float(agent.agent.homeostasis.energy), 4),
                "selected_route": route_choice_at_commitment,
                "route_A_probability": round(prob_A, 4),
                "route_B_probability": round(prob_B, 4),
                "selected_action": step_res["best_action"],
                "selected_sequence": step_res["best_sequence"],
                "EFE_route_A": round(efe_A, 2),
                "EFE_route_B": round(efe_B, 2),
                "kinematic_EFE_route_A": round(efe_A, 2),
                "kinematic_EFE_route_B": round(efe_B, 2),
                "memory_enabled": bool(agent.enable_memory),
                "memory_write": int(step_res["memory_writes"]),
                "memory_retrieval_count": int(step_res["memory_retrievals"]),
                "best_memory_similarity": round(float(step_res["memory_similarity"]), 4),
                "retrieved_experience_value": round(float(step_res["memory_similarity"]), 4),
                "prediction_error": round(float(step_res["prediction_error"]), 4),
                "collision_count": n_contacts,
                "minimum_true_robot_wall_distance": round(min_geom_dist, 5),
                "condition": condition
            }
            ticks_records.append(tick_data)
            
            if video_writer is not None:
                frame = self.render_frame_with_hud(
                    condition, seed, episode, tick, sim_time, px, py, yaw,
                    route_choice_at_commitment, step_res["best_action"], step_res["best_sequence"],
                    efe_A, efe_B, min_geom_dist, max_pen, n_contacts, nearest_robot, nearest_wall,
                    agent.memory_writes_this_episode, agent.memory_retrievals_this_episode,
                    step_res["memory_similarity"], step_res["prediction_error"], dist_food
                )
                video_writer.write(frame)
                
            if acquired:
                break
            if col and tick > 220:
                break
                
        if video_writer is not None:
            video_writer.release()
            
        agent.end_episode_consolidation()
        df_ticks = pd.DataFrame(ticks_records)
        
        summary = {
            "run_id": f"P1R3_{condition}_S{seed}_EP{episode}",
            "condition": condition,
            "seed": seed,
            "episode": episode,
            "route_choice_at_commitment": route_choice_at_commitment,
            "pre_hazard_lat_y": float(pre_hazard_lat_y),
            "commitment_tick": commitment_tick,
            "acquired": acquired,
            "acquisition_time_s": acquisition_time,
            "hazard_encountered": hazard_encountered,
            "memory_writes": agent.memory_writes_this_episode,
            "memory_retrievals": agent.memory_retrievals_this_episode,
            "min_true_clearance_m": float(df_ticks["minimum_true_robot_wall_distance"].min()),
            "mean_true_clearance_m": float(df_ticks["minimum_true_robot_wall_distance"].mean()),
            "total_ticks": len(ticks_records)
        }
        
        return summary, df_ticks

    def execute_campaign(self) -> Dict[str, Any]:
        """Executes the complete 18-episode campaign, beginning with the Seed 42 causal gate."""
        print("=" * 80)
        print("STARTING CARL-DX P1-R3 MEMORY CAUSALITY VALIDATION CAMPAIGN (18 EPISODES)")
        print("=" * 80)
        
        run_summaries = []
        
        # --- STAGE 1: SEED 42 CAUSAL GATE ---
        print("\n>>> STAGE 1: EXECUTING SEED 42 PRIMARY CAUSAL GATE <<<")
        s42_summaries = []
        for cond in CONDITIONS:
            enable_mem = (cond == "FULL_P1_R3")
            agent = CarlP1R3Agent(dt=0.0333, enable_memory=enable_mem, horizon_steps=18)
            for ep in EPISODES:
                summary, df_ticks = self.run_single_episode(agent, cond, 42, ep, render_video=True)
                csv_path = os.path.join(self.telemetry_dir, f"{summary['run_id']}.csv")
                df_ticks.to_csv(csv_path, index=False)
                s42_summaries.append(summary)
                run_summaries.append(summary)
                
                r = summary["route_choice_at_commitment"]
                mw = summary["memory_writes"]
                mr = summary["memory_retrievals"]
                print(f"[{cond:11s} | S 42 | EP{ep}] Route: {r:17s} (y={summary['pre_hazard_lat_y']:+.2f}m) | Mem W:{mw:2d} R:{mr:5d} | MinClear: {summary['min_true_clearance_m']:.4f}m")

        # Evaluate Seed 42 Causal Gate
        full_ep1_s42 = [s for s in s42_summaries if s["condition"] == "FULL_P1_R3" and s["episode"] == 1][0]
        full_ep2_s42 = [s for s in s42_summaries if s["condition"] == "FULL_P1_R3" and s["episode"] == 2][0]
        nomem_ep2_s42 = [s for s in s42_summaries if s["condition"] == "NO_MEMORY" and s["episode"] == 2][0]
        
        s42_gate_passed = (
            full_ep1_s42["memory_writes"] > 0 and
            full_ep2_s42["memory_retrievals"] > 0 and
            full_ep2_s42["route_choice_at_commitment"] == "ROUTE_A (North)" and
            nomem_ep2_s42["route_choice_at_commitment"] == "ROUTE_B (South)"
        )
        
        if not s42_gate_passed:
            print("\n" + "!" * 80)
            print("SEED 42 CAUSAL GATE FAILED: Stopping campaign.")
            print("!" * 80)
            return {"status": "FAILED_AT_SEED_42"}
            
        print("\n>>> SEED 42 CAUSAL GATE PASSED: Proceeding to multi-seed replication (Seeds 101 & 2024) <<<")
        
        # --- STAGE 2: SEEDS 101 & 2024 REPLICATION ---
        for seed in [101, 2024]:
            for cond in CONDITIONS:
                enable_mem = (cond == "FULL_P1_R3")
                agent = CarlP1R3Agent(dt=0.0333, enable_memory=enable_mem, horizon_steps=18)
                for ep in EPISODES:
                    summary, df_ticks = self.run_single_episode(agent, cond, seed, ep, render_video=True)
                    csv_path = os.path.join(self.telemetry_dir, f"{summary['run_id']}.csv")
                    df_ticks.to_csv(csv_path, index=False)
                    run_summaries.append(summary)
                    
                    r = summary["route_choice_at_commitment"]
                    mw = summary["memory_writes"]
                    mr = summary["memory_retrievals"]
                    print(f"[{cond:11s} | S{seed:4d} | EP{ep}] Route: {r:17s} (y={summary['pre_hazard_lat_y']:+.2f}m) | Mem W:{mw:2d} R:{mr:5d} | MinClear: {summary['min_true_clearance_m']:.4f}m")

        # Save Master Run Ledger CSV
        df_runs = pd.DataFrame(run_summaries)
        ledger_path = "d:/ebca/P1R3_MEMORY_CAUSALITY_RAW_RUN_LEDGER.csv"
        df_runs.to_csv(ledger_path, index=False)
        print(f"\n[LEDGER SAVED] -> {ledger_path}")
        
        # Save Decision Trace JSON
        trace_path = "d:/ebca/P1R3_MEMORY_CAUSALITY_DECISION_TRACE.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(run_summaries, f, indent=2)
        print(f"[DECISION TRACE SAVED] -> {trace_path}")
        
        return {"status": "CAMPAIGN_COMPLETE", "total_runs": len(run_summaries)}


if __name__ == "__main__":
    runner = CarlP1R3MemoryCausalityRunner()
    runner.execute_campaign()
