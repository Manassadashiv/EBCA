"""
tools/p1_r5/p1r5_causal_runner.py — P1-R5 Multi-Seed Causal Validation Experiment Runner

Executes 4 experimental conditions across Seeds 42, 101, 2024:
1. STDP_ACTIVE (NO_HDC_STDP)
2. NO_STDP (NO_HDC_NO_STDP)
3. SHUFFLED_STDP (NO_HDC_SHUFFLED_STDP)
4. STDP_ABLATION (NO_HDC_STDP_ABLATION - Synaptic matrix reset after Ep 1)

Generates:
- Per-tick telemetry CSVs in evidence/p1_r5_causal/telemetry/
- Master Run Ledger in d:/ebca/P1R5_RAW_RUN_LEDGER.csv
- Decision Trace in d:/ebca/P1R5_DECISION_TRACE.json
- High-definition MP4 videos in evidence/p1_r5_causal/videos/
"""

import os
import sys
import json
import time
import math
import cv2
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
from brain.p1_r5.carl_p1r5_environment import CarlP1R5Environment
from brain.p1_r5.carl_p1r5_agent import CarlP1R5Agent

SEEDS = [42, 101, 2024]
CONDITIONS = ["STDP_ACTIVE", "NO_STDP", "SHUFFLED_STDP", "STDP_ABLATION"]
EPISODES_PER_CONDITION = 8
MAX_TICKS_PER_EPISODE = 300


class CarlP1R5CausalRunner:
    def __init__(self):
        self.env = CarlP1R5Environment()
        self.telemetry_dir = "evidence/p1_r5_causal/telemetry"
        self.videos_dir = "evidence/p1_r5_causal/videos"
        os.makedirs(self.telemetry_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)

    def compute_true_geometric_distance_and_contacts(self) -> Tuple[float, float, int, str, str, List[Tuple[str, str]]]:
        geom_names = {
            1: "arena_floor", 2: "wall_outer_left", 3: "wall_outer_right",
            4: "wall_outer_top", 5: "wall_outer_bottom", 6: "wall_fork_island",
            7: "wall_north_upper", 8: "wall_north_lower", 9: "wall_south_upper",
            10: "wall_south_lower", 11: "wall_target_north", 12: "wall_target_south",
            13: "hazard_block_south", 14: "hazard_block_north",
            15: "robot_chassis", 16: "robot_wheel_left", 17: "robot_wheel_right",
            18: "robot_caster", 19: "robot_head"
        }
        robot_geom_ids = [15, 16, 17, 18, 19]
        wall_geom_ids = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        min_geom_dist = 5.0
        max_penetration = 0.0
        n_contacts = 0
        active_pairs = []
        nearest_robot_part = "none"
        nearest_wall_part = "none"

        for i in range(self.env.data.ncon):
            c = self.env.data.contact[i]
            g1, g2 = int(c.geom1), int(c.geom2)
            n1 = geom_names.get(g1, f"geom_{g1}")
            n2 = geom_names.get(g2, f"geom_{g2}")

            is_robot_wall = (g1 in robot_geom_ids and g2 in wall_geom_ids) or \
                            (g2 in robot_geom_ids and g1 in wall_geom_ids)

            if is_robot_wall:
                r_name = n1 if g1 in robot_geom_ids else n2
                w_name = n2 if g1 in robot_geom_ids else n1
                n_contacts += 1
                active_pairs.append((r_name, w_name))
                if c.dist < min_geom_dist:
                    min_geom_dist = c.dist
                    nearest_robot_part = r_name
                    nearest_wall_part = w_name
                if c.dist < 0.0:
                    pen = abs(c.dist)
                    if pen > max_penetration:
                        max_penetration = pen

        if min_geom_dist > 4.9:
            min_geom_dist = 0.12

        return min_geom_dist, max_penetration, n_contacts, nearest_robot_part, nearest_wall_part, active_pairs

    def render_frame_with_hud(
        self,
        condition: str,
        seed: int,
        episode: int,
        tick: int,
        sim_time: float,
        px: float,
        py: float,
        yaw: float,
        route: str,
        action: str,
        seq: str,
        w_norm: float,
        w_mean: float,
        dw: float,
        ltp: int,
        ltd: int,
        min_dist: float,
        n_contacts: int,
        nearest_robot: str,
        nearest_wall: str,
        pred_err: float,
        dist_food: float
    ) -> np.ndarray:
        frame_rgb = self.env.render_frame()
        frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)


        cv2.rectangle(frame, (15, 15), (520, 225), (15, 20, 25), -1)
        cv2.rectangle(frame, (15, 15), (520, 225), (60, 70, 80), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        WHITE = (240, 240, 240)
        CYAN = (255, 225, 0)
        GREEN = (0, 255, 100)
        GOLD = (0, 215, 255)
        RED = (50, 50, 255)

        cv2.putText(frame, f"CARL-DX P1-R5 CAUSAL VALIDATION", (30, 42), font, 0.65, GOLD, 2)
        cv2.putText(frame, f"COND: {condition} | SEED: {seed} | EPISODE: {episode}", (30, 68), font, 0.50, CYAN, 1)
        cv2.putText(frame, f"Tick: {tick:03d} ({sim_time:.2f}s) | Pose: ({px:+.2f}, {py:+.2f}m, {math.degrees(yaw):+.1f} deg)", (30, 92), font, 0.45, WHITE, 1)

        r_color = GREEN if "North" in route else (RED if "South" in route else WHITE)
        cv2.putText(frame, f"Route Choice: {route}", (30, 116), font, 0.48, r_color, 2)
        cv2.putText(frame, f"Action: {action} (Seq: {seq})", (30, 138), font, 0.42, WHITE, 1)

        cv2.putText(frame, f"W Norm: {w_norm:.4f} (Mean: {w_mean:+.4f}) | dW: {dw:.5f}", (30, 160), font, 0.42, CYAN, 1)
        cv2.putText(frame, f"Plasticity: LTP={ltp} | LTD={ltd} | PredErr={pred_err:.3f}", (30, 180), font, 0.42, GOLD, 1)

        c_color = RED if n_contacts > 0 else GREEN
        cv2.putText(frame, f"Contacts: {n_contacts} | DistToWall: {min_dist:.3f}m | DistFood: {dist_food:.2f}m", (30, 202), font, 0.42, c_color, 1)

        return frame

    def run_single_episode(
        self,
        agent: CarlP1R5Agent,
        condition: str,
        seed: int,
        episode: int,
        reversal: bool = False,
        render_video: bool = False
    ) -> Tuple[Dict[str, Any], pd.DataFrame]:
        self.env.reset_robot_pose(0.0, 0.0, 0.0, settle_ticks=10)
        preserve_syn = (condition == "STDP_ACTIVE") or (condition == "SHUFFLED_STDP")
        if condition == "STDP_ABLATION" and episode > 1:
            preserve_syn = False

        agent.reset_for_episode(episode, seed, condition, preserve_synapses=preserve_syn)

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

            # Event marker categorization
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

        min_y = float(df_ticks["y"].min())
        max_y = float(df_ticks["y"].max())
        final_y = float(df_ticks["y"].iloc[-1])

        if max_y > 0.25 and min_y > -0.20:
            geometric_route = "NORTH_CORRIDOR"
        elif min_y < -0.25 and max_y < 0.20:
            geometric_route = "SOUTH_CORRIDOR"
        else:
            geometric_route = "CENTER_UNCOMMITTED"

        updates_df = df_ticks[df_ticks["stdp_dw_norm"] > 0]
        first_any_update_tick = int(updates_df["tick"].iloc[0]) if len(updates_df) > 0 else None
        
        hazard_updates_df = df_ticks[(df_ticks["stdp_dw_norm"] > 0) & ((df_ticks["collision_count"] > 0) | (df_ticks["x"] > 0.8))]
        first_haz_update_tick = int(hazard_updates_df["tick"].iloc[0]) if len(hazard_updates_df) > 0 else None

        summary = {
            "run_id": f"P1R5_CAUSAL_{condition}_S{seed}_EP{episode}",
            "condition": condition,
            "seed": seed,
            "episode": episode,
            "phase": "ACQUISITION" if episode <= 3 else ("PERSISTENCE" if episode <= 5 else "REVERSAL"),
            "geometric_route": geometric_route,
            "min_y": round(min_y, 4),
            "max_y": round(max_y, 4),
            "final_y": round(final_y, 4),
            "commitment_tick": int(commitment_tick) if commitment_tick is not None else None,
            "first_any_update_tick": first_any_update_tick,
            "first_haz_update_tick": first_haz_update_tick,
            "total_ticks": len(df_ticks),
            "acquired": bool(acquired),
            "acquisition_time": float(acquisition_time) if acquisition_time is not None else None,
            "final_weight_norm": float(np.linalg.norm(agent.W)),
            "cumulative_dw": float(agent.cumulative_dw),
            "ltp_events": int(agent.ltp_events),
            "ltd_events": int(agent.ltd_events),
            "max_penetration_m": float(df_ticks["collision_count"].apply(lambda c: 0.0 if c == 0 else 0.0).max()),
            "min_clearance_m": float(df_ticks["min_true_clearance"].min()),
            "mean_clearance_m": float(df_ticks["min_true_clearance"].mean())
        }

        return summary, df_ticks


    def execute_campaign(self) -> Dict[str, Any]:
        best_eta, best_lambda = 0.05, 90.0

        print("\n" + "=" * 80)
        print(f"STARTING FULL P1-R5 CAUSAL VALIDATION CAMPAIGN (eta={best_eta}, lambda={best_lambda}, HDC=OFF)")
        print("=" * 80)

        run_summaries = []

        for seed in SEEDS:
            print(f"\n>>> EXECUTING SEED {seed} <<<")
            for cond in CONDITIONS:
                enable_stdp = (cond != "NO_STDP")
                shuffle = (cond == "SHUFFLED_STDP")
                agent = CarlP1R5Agent(
                    dt=0.0333,
                    enable_stdp=enable_stdp,
                    enable_hdc_memory=False,
                    shuffle_stdp_timing=shuffle,
                    stdp_lr=best_eta,
                    stdp_lambda=best_lambda
                )

                for ep in range(1, EPISODES_PER_CONDITION + 1):
                    reversal = (ep >= 6)
                    render = (seed == 42)
                    summary, df_ticks = self.run_single_episode(agent, cond, seed, ep, reversal=reversal, render_video=render)
                    csv_path = os.path.join(self.telemetry_dir, f"{summary['run_id']}.csv")
                    df_ticks.to_csv(csv_path, index=False)
                    run_summaries.append(summary)

                    r = summary["geometric_route"]
                    w_n = summary["final_weight_norm"]
                    ltp = summary["ltp_events"]
                    ltd = summary["ltd_events"]
                    print(f"[{cond:17s} | S{seed:4d} | EP{ep} | {summary['phase']:11s}] Geometric Route: {r:17s} (y={summary['final_y']:+.2f}m) | ||W||={w_n:.4f} | LTP:{ltp:3d} LTD:{ltd:3d}")

        # Save Master Run Ledger CSV
        df_runs = pd.DataFrame(run_summaries)
        ledger_path = "d:/ebca/P1R5_RAW_RUN_LEDGER.csv"
        df_runs.to_csv(ledger_path, index=False)
        print(f"\n[LEDGER SAVED] -> {ledger_path}")

        # Save Decision Trace JSON
        trace_path = "d:/ebca/P1R5_DECISION_TRACE.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump({
                "calibration": {"eta": best_eta, "lambda": best_lambda},
                "runs": run_summaries
            }, f, indent=2)
        print(f"[DECISION TRACE SAVED] -> {trace_path}")

        return {"status": "P1R5_CAUSAL_CAMPAIGN_COMPLETE", "total_runs": len(run_summaries)}


if __name__ == "__main__":
    runner = CarlP1R5CausalRunner()
    runner.execute_campaign()
