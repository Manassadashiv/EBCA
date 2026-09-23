import os
import cv2
import numpy as np

output_mp4 = r"D:\ebca\evidence\ALL_CARL_VIDEOS_COMBINED.mp4"
root_copy_mp4 = r"D:\ebca\ALL_CARL_VIDEOS_COMBINED.mp4"

# Key benchmark scenarios and replays to include in the single master film
video_candidates = [
    # 1. Navigation & Wall Avoidance Benchmarks
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_a_wall_directly_ahead.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_b_wall_at_45_deg.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_c_corridor_with_opening.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_d_dead_end_corridor.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_e_bifurcation_obstacle.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_f_moving_obstacle.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_g_narrow_passage.mp4",
    r"D:\ebca\evidence\wall_avoidance_benchmarks\scenario_h_unexpected_drop.mp4",
    
    # 2. Emergence & Multi-Seed Overnight Scenarios
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_1_open_space_locomotion_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_2_head_on_wall_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_3_angled_45_wall_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_4_corridor_with_opening_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_5_dead_end_enclosure_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_6_narrow_passage_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_7_dynamic_crossing_hazard_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_8_unexpected_drop_hazard_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_9_adversarial_random_clutter_s42.mp4",
    r"D:\ebca\evidence\overnight_20260817\benchmarks\scenario_10_corner_wedge_trap_s42.mp4",
    
    # 3. Autonomous Cognitive Replays
    r"D:\ebca\replays\active_sensing_behavior.mp4",
    r"D:\ebca\replays\action_veto_behavior.mp4",
    r"D:\ebca\replays\self_model_adaptation.mp4",
    r"D:\ebca\replays\memory_dependent_behavior.mp4",
    r"D:\ebca\replays\recovery_episode.mp4",
    r"D:\ebca\replays\complete_clean_blind_run.mp4",
]

# Filter existing files
video_files = [f for f in video_candidates if os.path.exists(f)]
print(f"Found {len(video_files)} video sequences to concatenate into single master MP4.")

TARGET_W = 1280
TARGET_H = 720
FPS = 30.0

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
os.makedirs(os.path.dirname(output_mp4), exist_ok=True)
writer = cv2.VideoWriter(output_mp4, fourcc, FPS, (TARGET_W, TARGET_H))

total_frames_written = 0

for v_idx, v_path in enumerate(video_files, 1):
    cap = cv2.VideoCapture(v_path)
    if not cap.isOpened():
        print(f"Warning: Could not open {v_path}")
        continue
        
    scene_title = os.path.splitext(os.path.basename(v_path))[0].replace("_", " ").upper()
    v_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[{v_idx}/{len(video_files)}] Processing {os.path.basename(v_path)} ({v_frame_count} frames)...")
    
    # Intro title card (15 frames = 0.5s)
    intro_card = np.zeros((TARGET_H, TARGET_W, 3), dtype=np.uint8)
    intro_card[:] = (20, 24, 30) # Dark graphite background
    # Add cyan accent line
    cv2.line(intro_card, (100, 300), (TARGET_W - 100, 300), (255, 230, 0), 3)
    cv2.putText(intro_card, f"SCENE {v_idx:02d} / {len(video_files):02d}", (100, 270),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (180, 190, 200), 2, cv2.LINE_AA)
    cv2.putText(intro_card, scene_title, (100, 360),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(intro_card, f"Source: {os.path.relpath(v_path, r'D:\ebca')}", (100, 420),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (140, 150, 160), 1, cv2.LINE_AA)
                
    for _ in range(15):
        writer.write(intro_card)
        total_frames_written += 1
        
    local_frame = 0
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
            
        local_frame += 1
        if frame.shape[1] != TARGET_W or frame.shape[0] != TARGET_H:
            frame = cv2.resize(frame, (TARGET_W, TARGET_H), interpolation=cv2.INTER_AREA)
            
        # Draw clean bottom HUD banner
        hud_overlay = frame.copy()
        cv2.rectangle(hud_overlay, (0, TARGET_H - 45), (TARGET_W, TARGET_H), (15, 18, 22), -1)
        frame = cv2.addWeighted(hud_overlay, 0.75, frame, 0.25, 0)
        
        cv2.putText(frame, f"CARL-DX COMPENDIUM | [{v_idx:02d}/{len(video_files):02d}] {scene_title}", (25, TARGET_H - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 235, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Frame {local_frame:04d}/{v_frame_count:04d}", (TARGET_W - 240, TARGET_H - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.60, (200, 200, 200), 1, cv2.LINE_AA)
                    
        writer.write(frame)
        total_frames_written += 1
        
    cap.release()

writer.release()

# Copy to root as well for easy access
import shutil
shutil.copy2(output_mp4, root_copy_mp4)

print(f"\n================================================================================")
print(f"MASTER COMBINED VIDEO GENERATED SUCCESSFULLY!")
print(f"  - Output 1: {output_mp4}")
print(f"  - Output 2: {root_copy_mp4}")
print(f"  - Total Frames: {total_frames_written:,} frames ({total_frames_written/FPS:.1f} seconds / {total_frames_written/(FPS*60):.2f} minutes)")
print(f"  - File Size: {os.path.getsize(output_mp4):,} bytes ({os.path.getsize(output_mp4)/(1024*1024):.2f} MB)")
print(f"================================================================================")
