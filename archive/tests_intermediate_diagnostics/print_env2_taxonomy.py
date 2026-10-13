import json

with open("evidence/stage3_4R4_1/env2_failure_taxonomy.json") as f:
    tax = json.load(f)

print("=== ENV 2 FAILURE TAXONOMY SUMMARY ===")
for t in tax:
    cid = t["config_id"]
    arm = t["arm"]
    term = t["termination_reason"]
    fc = t["failure_class"]
    pt = t["final_pose_true"]
    pe = t["final_pose_est"]
    he = t["final_heading_err_deg"]
    mf = t["selected_macro_frontier_final"]
    df = t["dist_to_frontier_final"]
    print(f"Cfg {cid:02d} | {arm:5s} | Term: {term:8s} | Class: {fc:30s} | True: {pt} | Est: {pe} | HErr: {he:5.1f} deg | Front: {mf} | dFront: {df}")
