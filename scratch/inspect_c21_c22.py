import json

with open("d:/ebca/evidence/stage3_4R4_3/r4_3_channel_entry_forensics_full.json") as f:
    data = json.load(f)

cfg22 = [r for r in data if r["config_id"] == 22][0]
print("=== CONFIG 22 TICKS 55-87 ===")
print(f"{'tick':<4} | {'x':<7} | {'y':<7} | {'yaw':<7} | {'v_est':<6} | {'gyro_w':<6} | {'d_L':<5} | {'d_R':<5} | {'d_min':<5} | {'veto':<5} | {'th_des':<6} | {'contacts':<8}")
for t in cfg22["ticks_trace"][55:87]:
    print(f"{t['tick']:4d} | {t['x']:7.4f} | {t['y']:7.4f} | {t['yaw_deg']:7.1f} | {t['v_est']:6.3f} | {t['gyro_w']:6.3f} | {t['d_L']:5.3f} | {t['d_R']:5.3f} | {t['d_min']:5.3f} | {t['veto_frac']:5.2f} | {t['th_des_deg']:6.1f} | {t['wall_contacts']:8d}")

cfg21 = [r for r in data if r["config_id"] == 21][0]
print("\n=== CONFIG 21 TICKS 115-145 ===")
print(f"{'tick':<4} | {'x':<7} | {'y':<7} | {'yaw':<7} | {'v_est':<6} | {'gyro_w':<6} | {'d_L':<5} | {'d_R':<5} | {'d_min':<5} | {'veto':<5} | {'th_des':<6} | {'contacts':<8}")
for t in cfg21["ticks_trace"][115:145]:
    print(f"{t['tick']:4d} | {t['x']:7.4f} | {t['y']:7.4f} | {t['yaw_deg']:7.1f} | {t['v_est']:6.3f} | {t['gyro_w']:6.3f} | {t['d_L']:5.3f} | {t['d_R']:5.3f} | {t['d_min']:5.3f} | {t['veto_frac']:5.2f} | {t['th_des_deg']:6.1f} | {t['wall_contacts']:8d}")
