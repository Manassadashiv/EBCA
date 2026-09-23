"""
tools/p1_r4/test_episode2_recurrence.py — Test STDP vs NO_STDP vs SHUFFLED_STDP on Episode 1 and 2
"""

import sys, os, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from brain.p1_r4.carl_p1r4_environment import CarlP1R4Environment
from brain.p1_r4.carl_p1r4_agent import CarlP1R4Agent

env = CarlP1R4Environment()

def run_condition_2ep(cond_name, enable_stdp=True, shuffle=False, lr=0.05, lam=90.0):
    env.configure_environment(1, reversal=False)
    env.reset_robot_pose(0.0, 0.0, 0.0)
    agent = CarlP1R4Agent(dt=0.0333, enable_stdp=enable_stdp, enable_hdc_memory=False, shuffle_stdp_timing=shuffle, stdp_lr=lr, stdp_lambda=lam)
    
    # --- EPISODE 1 ---
    ep1_route = "UNDECIDED"
    ep1_lat_y = 0.0
    ep1_first_dw_tick = None
    ep1_first_dw_pos = None
    
    for t in range(300):
        res = agent.step(env.hal, target_coords=env.food_coords)
        s = res["sensory"]
        if s.pos_x > 0.35 and ep1_route == "UNDECIDED":
            ep1_lat_y = s.pos_y
            ep1_route = "ROUTE_A (North)" if s.pos_y > 0.0 else "ROUTE_B (South)"
        if res["stdp_dw_norm"] > 0 and ep1_first_dw_tick is None:
            ep1_first_dw_tick = t
            ep1_first_dw_pos = (round(s.pos_x, 3), round(s.pos_y, 3))
        if s.has_body_collision and t > 150:
            break
            
    ep1_w_norm = np.linalg.norm(agent.W)
    ep1_ltd = agent.ltd_events
    
    # --- EPISODE 2 ---
    env.configure_environment(2, reversal=False)
    env.reset_robot_pose(0.0, 0.0, 0.0)
    agent.reset_for_episode(2, 42, cond_name, preserve_synapses=(enable_stdp and not shuffle), preserve_hdc=False)
    
    ep2_route = "UNDECIDED"
    ep2_lat_y = 0.0
    ep2_commit_tick = None
    
    for t in range(300):
        res = agent.step(env.hal, target_coords=env.food_coords)
        s = res["sensory"]
        if s.pos_x > 0.35 and ep2_route == "UNDECIDED":
            ep2_commit_tick = t
            ep2_lat_y = s.pos_y
            ep2_route = "ROUTE_A (North)" if s.pos_y > 0.0 else "ROUTE_B (South)"
        if s.has_body_collision and t > 150:
            break
            
    print(f"[{cond_name:21s}] Ep1: {ep1_route:16s} (First dW at Tick {ep1_first_dw_tick}, Pos {ep1_first_dw_pos}, LTD: {ep1_ltd}) -> Ep2: {ep2_route:16s} (y={ep2_lat_y:+.3f}m at Tick {ep2_commit_tick})")

print("=== FORENSIC VALIDATION: 2-EPISODE COMPARISON ACROSS CONDITIONS ===")
run_condition_2ep("NO_HDC_STDP", enable_stdp=True, shuffle=False)
run_condition_2ep("NO_HDC_NO_STDP", enable_stdp=False, shuffle=False)
run_condition_2ep("NO_HDC_SHUFFLED_STDP", enable_stdp=True, shuffle=True)
