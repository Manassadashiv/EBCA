"""
tools/p1_r4/test_stabilization.py — Full Episode 1 trace of corrected STDP vs NO_STDP
"""

import sys, os, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from brain.p1_r4.carl_p1r4_environment import CarlP1R4Environment
from brain.p1_r4.carl_p1r4_agent import CarlP1R4Agent

env = CarlP1R4Environment()
env.configure_environment(1, reversal=False)
env.reset_robot_pose(0.0, 0.0, 0.0)

agent_stdp = CarlP1R4Agent(dt=0.0333, enable_stdp=True, enable_hdc_memory=False, stdp_lr=0.05, stdp_lambda=90.0)
agent_no = CarlP1R4Agent(dt=0.0333, enable_stdp=False, enable_hdc_memory=False)

print("--- Running Episode 1 (NO_HDC_STDP) ---")
records_stdp = []
for t in range(300):
    res = agent_stdp.step(env.hal, target_coords=env.food_coords)
    s = res["sensory"]
    records_stdp.append({
        "tick": t, "x": s.pos_x, "y": s.pos_y, "speed": s.speed,
        "act": res["best_action"], "pe": res["prediction_error"],
        "dw": res["stdp_dw_norm"], "wn": res["stdp_weight_norm"],
        "col": s.has_body_collision, "ltp": agent_stdp.ltp_events, "ltd": agent_stdp.ltd_events
    })
    if s.has_body_collision and t > 150:
        break

df_stdp = pd.DataFrame(records_stdp)

# Reset for NO_STDP
env.reset_robot_pose(0.0, 0.0, 0.0)
records_no = []
for t in range(300):
    res = agent_no.step(env.hal, target_coords=env.food_coords)
    s = res["sensory"]
    records_no.append({
        "tick": t, "x": s.pos_x, "y": s.pos_y, "speed": s.speed,
        "act": res["best_action"], "pe": res["prediction_error"],
        "dw": res["stdp_dw_norm"], "wn": res["stdp_weight_norm"],
        "col": s.has_body_collision
    })
    if s.has_body_collision and t > 150:
        break

df_no = pd.DataFrame(records_no)

print("\n=== STARTUP TICKS 0-10 COMPARISON ===")
for t in range(10):
    r_s = df_stdp.iloc[t]
    r_n = df_no.iloc[t]
    print(f"Tick {t:2d} | STDP Act: {r_s['act']:15s} (dW: {r_s['dw']:.6f}, ||W||: {r_s['wn']:.6f}) | NO_STDP Act: {r_n['act']:15s} | Pos: ({r_s['x']:+.3f}, {r_s['y']:+.3f})")

print("\n=== FULL TRAJECTORY SUMMARY ===")
print("STDP:    Total ticks:", len(df_stdp), "| Final Pos:", (round(df_stdp['x'].iloc[-1], 3), round(df_stdp['y'].iloc[-1], 3)), "| Final ||W||:", round(df_stdp['wn'].iloc[-1], 4), "| LTD events:", df_stdp['ltd'].iloc[-1])
print("NO_STDP: Total ticks:", len(df_no), "| Final Pos:", (round(df_no['x'].iloc[-1], 3), round(df_no['y'].iloc[-1], 3)))

# Find first non-zero dW
non_zero_dw = df_stdp[df_stdp["dw"] > 0]
if len(non_zero_dw) > 0:
    first_dw = non_zero_dw.iloc[0]
    print(f"\nFirst STDP weight update occurred at: Tick {int(first_dw['tick'])} | Pos ({first_dw['x']:.3f}, {first_dw['y']:.3f}) | PE: {first_dw['pe']:.4f} | dW: {first_dw['dw']:.6f}")
else:
    print("\nNo STDP update occurred in Episode 1.")
