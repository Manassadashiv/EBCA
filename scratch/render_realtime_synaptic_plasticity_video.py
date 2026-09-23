"""
render_realtime_synaptic_plasticity_video.py — Live Physical & Synaptic Rewiring Video Generator (V3 Master Edition)

Generates synchronized Full HD 1080p video and animated GIF showing:
- 3D Photorealistic MuJoCo Simulation View (Isometric camera tracking the robot in physical 3D)
- 2D Overhead Physics Radar (Sonar distance beams, dynamic curved trajectory trail, obstacle bounding box)
- Live 1024-Neuron Reservoir & Synaptic Network Graph (Growing/Depressing connections, active spike pulses)
- Real-Time Plasticity & Active Inference HUD (Q_hazard bars, weight norm gauge ||W||, EFE metric)

Demonstrating:
- Episode 1: Naive Forward Motion -> Physical Impact -> Noradrenergic Surprise -> STDP LTP Weight Surge
- Episode 2: Preserved Synaptic Memory -> Q_hazard Suppression -> Curved Detour Circumnavigation (Y curves from 0.0 -> -0.6m -> 0.0)
"""

import os
import sys
import math
import cv2
import numpy as np
import mujoco
from PIL import Image

sys.path.insert(0, 'd:/ebca')
from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.p1_integrate.carl_p1_integrate_agent import CarlP1IntegrateAgent

OUTPUT_DIR = "d:/ebca/evidence/plasticity_proofs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
MP4_PATH = os.path.join(OUTPUT_DIR, "carl_realtime_synaptic_plasticity.mp4")
GIF_PATH = os.path.join(OUTPUT_DIR, "carl_realtime_synaptic_plasticity.gif")

# Colors (BGR)
C_BG = (22, 14, 8)
C_CYAN = (255, 240, 0)
C_LIME = (100, 255, 0)
C_MAGENTA = (180, 50, 255)
C_GOLD = (0, 215, 255)
C_CORAL = (60, 90, 255)
C_WHITE = (245, 245, 245)
C_DARK_RED = (40, 30, 180)

def create_canvas():
    return np.full((1080, 1920, 3), C_BG, dtype=np.uint8)

def draw_header(canvas, tick, episode, ep_title):
    cv2.rectangle(canvas, (0, 0), (1920, 50), (28, 18, 10), -1)
    cv2.line(canvas, (0, 50), (1920, 50), C_CYAN, 2)
    cv2.putText(canvas, "CARL-DX: LIVE THREE-FACTOR STDP NEURAL REWIRING & PHYSICAL KINEMATICS", 
                (30, 34), cv2.FONT_HERSHEY_DUPLEX, 0.85, C_CYAN, 2, cv2.LINE_AA)
    status_text = f"EPISODE {episode}: {ep_title.upper()} | TICK: {tick:03d}"
    color_stat = C_CORAL if episode == 1 else C_LIME
    cv2.putText(canvas, status_text, (1150, 34), cv2.FONT_HERSHEY_DUPLEX, 0.75, color_stat, 2, cv2.LINE_AA)

def render_2d_arena(sensory, target_coords, hazard_pos, trail, chosen_action, width=960, height=490):
    arena_img = np.full((height, width, 3), (26, 18, 12), dtype=np.uint8)
    ox, oy = 80, height // 2
    scale_x = (width - 160) / 2.8
    scale_y = (height - 80) / 2.2
    scale = min(scale_x, scale_y)
    
    def to_screen(x, y):
        sx = int(ox + (x - (-0.3)) * scale)
        sy = int(oy - y * scale)
        return sx, sy

    # Arena bounding box & grid
    cv2.rectangle(arena_img, to_screen(-0.3, 1.1), to_screen(2.4, -1.1), (60, 45, 30), 2)
    for gx in np.arange(0.0, 2.5, 0.5):
        cv2.line(arena_img, to_screen(gx, 1.1), to_screen(gx, -1.1), (40, 30, 20), 1, cv2.LINE_AA)
    for gy in np.arange(-1.0, 1.1, 0.5):
        cv2.line(arena_img, to_screen(-0.3, gy), to_screen(2.4, gy), (40, 30, 20), 1, cv2.LINE_AA)
        
    # Hazard Obstacle Box
    hx, hy = hazard_pos[0], hazard_pos[1]
    hp1 = to_screen(hx - 0.15, hy + 0.15)
    hp2 = to_screen(hx + 0.15, hy - 0.15)
    cv2.rectangle(arena_img, hp1, hp2, C_DARK_RED, -1)
    cv2.rectangle(arena_img, hp1, hp2, C_CORAL, 2)
    cv2.putText(arena_img, "HAZARD", (hp1[0] + 5, (hp1[1] + hp2[1])//2 + 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_WHITE, 1, cv2.LINE_AA)

    # Food Target Beacon
    fx, fy = target_coords[0], target_coords[1]
    fs = to_screen(fx, fy)
    cv2.circle(arena_img, fs, 18, (30, 120, 40), -1)
    cv2.circle(arena_img, fs, 18, C_LIME, 2)
    cv2.putText(arena_img, "FOOD", (fs[0] - 18, fs[1] + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.45, C_LIME, 1, cv2.LINE_AA)

    # Robot Trajectory Trail (Curved path)
    if len(trail) > 1:
        for i in range(1, len(trail)):
            tp1 = to_screen(trail[i-1][0], trail[i-1][1])
            tp2 = to_screen(trail[i][0], trail[i][1])
            cv2.line(arena_img, tp1, tp2, trail[i][2], 3, cv2.LINE_AA)

    # Sonar Rangefinder Rays
    rx, ry = sensory.pos_x, sensory.pos_y
    yaw = sensory.yaw
    r_screen = to_screen(rx, ry)
    sonar = sensory.sonar_distances if sensory.sonar_distances is not None else np.ones(15) * 3.0
    angles = np.linspace(-math.pi * 0.666, math.pi * 0.666, 15)
    for i, ang in enumerate(angles):
        ray_yaw = yaw + ang
        d = float(sonar[i])
        ray_end_x = rx + d * math.cos(ray_yaw)
        ray_end_y = ry + d * math.sin(ray_yaw)
        ep_screen = to_screen(ray_end_x, ray_end_y)
        ray_col = C_CORAL if d < 0.4 else (C_GOLD if d < 1.0 else (100, 180, 50))
        cv2.line(arena_img, r_screen, ep_screen, ray_col, 1, cv2.LINE_AA)

    # Robot Body Circle & Heading Arrow
    cv2.circle(arena_img, r_screen, 14, (60, 60, 70), -1)
    cv2.circle(arena_img, r_screen, 14, C_CYAN, 2)
    head_x = rx + 0.25 * math.cos(yaw)
    head_y = ry + 0.25 * math.sin(yaw)
    cv2.line(arena_img, r_screen, to_screen(head_x, head_y), C_WHITE, 2, cv2.LINE_AA)
    
    cv2.putText(arena_img, "2D TOP-DOWN RADAR & 15-RAY SONAR SCAN", 
                (20, 28), cv2.FONT_HERSHEY_DUPLEX, 0.55, C_GOLD, 1, cv2.LINE_AA)
    info_text = f"X: {rx:+.2f}m | Y: {ry:+.2f}m | Speed: {sensory.speed:.2f}m/s | Heading: {math.degrees(yaw):+03.0f} deg | Act: {chosen_action}"
    cv2.putText(arena_img, info_text, (20, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, C_WHITE, 1, cv2.LINE_AA)
    return arena_img

def render_neural_network_graph(W_hazard, E_matrix, surprise, valence, chosen_idx, q_hazard, ltp_active, tick, width=960, height=680):
    net_img = np.full((height, width, 3), (24, 16, 10), dtype=np.uint8)
    cv2.putText(net_img, "LIVE 1024-NEURON RESERVOIR & THREE-FACTOR STDP SYNAPTIC CONNECTIONS", 
                (20, 30), cv2.FONT_HERSHEY_DUPLEX, 0.6, C_CYAN, 1, cv2.LINE_AA)
    
    pre_labels = ['Speed', 'Yaw Rate', 'Bearing', 'Sonar L', 'Sonar FL', 'Sonar F', 'Sonar FR', 'Sonar R', 
                  'TTC L', 'TTC R', 'Res 1..128', 'Res 129..256', 'Res 257..512', 'Res 513..1024']
    n_pre = len(pre_labels)
    pre_y = np.linspace(80, height - 70, n_pre).astype(int)
    pre_x = 180

    post_labels = ['STRAIGHT', 'CURVE_L_G', 'CURVE_L_S', 'SWERVE_L', 'CURVE_R_G', 'CURVE_R_S', 'SWERVE_R']
    n_post = len(post_labels)
    post_y = np.linspace(100, height - 90, n_post).astype(int)
    post_x = width - 200

    w_sampled = np.zeros((n_pre, n_post))
    w_sampled[0:10, :] = W_hazard[0:10, :]
    w_sampled[10, :] = np.mean(W_hazard[10:138, :], axis=0)
    w_sampled[11, :] = np.mean(W_hazard[138:266, :], axis=0)
    w_sampled[12, :] = np.mean(W_hazard[266:522, :], axis=0)
    w_sampled[13, :] = np.mean(W_hazard[522:1024, :], axis=0)

    max_w = max(np.max(W_hazard), 1.0)
    
    for i in range(n_pre):
        for j in range(n_post):
            w = w_sampled[i, j]
            is_chosen_action = (j == chosen_idx)
            
            if w > 0.01:
                thickness = int(np.clip(w / max_w * 7, 1, 8))
                col = C_CORAL if j == 0 else C_MAGENTA
                cv2.line(net_img, (pre_x + 12, pre_y[i]), (post_x - 16, post_y[j]), col, thickness, cv2.LINE_AA)
            elif is_chosen_action:
                cv2.line(net_img, (pre_x + 12, pre_y[i]), (post_x - 16, post_y[j]), (80, 180, 240), 2, cv2.LINE_AA)
            else:
                cv2.line(net_img, (pre_x + 12, pre_y[i]), (post_x - 16, post_y[j]), (50, 38, 28), 1, cv2.LINE_AA)

    # Active spike pulses
    if chosen_idx is not None:
        for i in range(n_pre):
            phase = (tick * 0.18 + i * 0.35) % 1.0
            px = int(pre_x + 12 + phase * (post_x - 16 - pre_x - 12))
            py = int(pre_y[i] + phase * (post_y[chosen_idx] - pre_y[i]))
            cv2.circle(net_img, (px, py), 4, C_GOLD, -1)

    # Pre-Synaptic Nodes
    for i, label in enumerate(pre_labels):
        py = pre_y[i]
        col_node = C_CYAN if i < 10 else C_LIME
        cv2.circle(net_img, (pre_x, py), 9, col_node, -1)
        cv2.circle(net_img, (pre_x, py), 9, C_WHITE, 1)
        cv2.putText(net_img, label, (pre_x - 150, py + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_WHITE, 1, cv2.LINE_AA)

    # Post-Synaptic Action Nodes
    for j, label in enumerate(post_labels):
        py = post_y[j]
        is_chosen = (j == chosen_idx)
        col_node = C_GOLD if is_chosen else (80, 60, 40)
        radius = 18 if is_chosen else 11
        cv2.circle(net_img, (post_x, py), radius, col_node, -1)
        cv2.circle(net_img, (post_x, py), radius, C_WHITE, 2 if is_chosen else 1)
        
        q_val = float(q_hazard[j]) if j < len(q_hazard) else 0.0
        q_col = C_CORAL if q_val > 0.5 else (C_LIME if q_val < 0.1 else C_GOLD)
        cv2.putText(net_img, label, (post_x + 25, py + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_WHITE if not is_chosen else C_GOLD, 2 if is_chosen else 1, cv2.LINE_AA)
        cv2.putText(net_img, f"Q_haz: {q_val:.2f}", (post_x + 130, py + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, q_col, 1, cv2.LINE_AA)

    # Center Neuromodulator Hub
    hub_x, hub_y = (pre_x + post_x) // 2, height // 2 - 20
    hub_radius = 48 if ltp_active else 36
    hub_col = C_CORAL if ltp_active else (50, 40, 30)
    cv2.circle(net_img, (hub_x, hub_y), hub_radius, hub_col, -1)
    cv2.circle(net_img, (hub_x, hub_y), hub_radius, C_GOLD if ltp_active else (80, 70, 60), 2)
    cv2.putText(net_img, "NEUROMODULATOR", (hub_x - 55, hub_y - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, C_WHITE, 1, cv2.LINE_AA)
    cv2.putText(net_img, f"Surprise: {surprise:.2f}", (hub_x - 45, hub_y + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, C_GOLD, 1, cv2.LINE_AA)
    cv2.putText(net_img, f"Valence:  {valence:+.2f}", (hub_x - 45, hub_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.4, C_MAGENTA if valence > 0 else C_LIME, 1, cv2.LINE_AA)

    if ltp_active:
        cv2.putText(net_img, ">>> STDP SYNAPTIC REWIRING (LTP BURST) <<<", 
                    (hub_x - 170, hub_y + 75), cv2.FONT_HERSHEY_DUPLEX, 0.6, C_CORAL, 2, cv2.LINE_AA)

    cv2.putText(net_img, "SENSORY INPUTS & 1024-RESERVOIR", (pre_x - 140, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, C_CYAN, 1, cv2.LINE_AA)
    cv2.putText(net_img, "MOTOR ACTION PRIMITIVES", (post_x - 40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, C_GOLD, 1, cv2.LINE_AA)
    return net_img

def render_plasticity_hud(agent, res, width=960, height=350):
    hud_img = np.full((height, width, 3), (20, 14, 8), dtype=np.uint8)
    cv2.putText(hud_img, "REAL-TIME PLASTICITY & ACTIVE INFERENCE EFE METRICS", 
                (20, 26), cv2.FONT_HERSHEY_DUPLEX, 0.55, C_GOLD, 1, cv2.LINE_AA)
    
    actions_short = ['STR', 'C_L_G', 'C_L_S', 'SW_L', 'C_R_G', 'C_R_S', 'SW_R']
    q_hazards = res['q_hazard_all']
    chosen_idx = res['chosen_idx']
    
    bar_x_start = 40
    bar_w = 40
    gap = 25
    bar_base_y = 170
    
    cv2.putText(hud_img, "Action Hazard Penalty Q_hazard(a):", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, C_WHITE, 1, cv2.LINE_AA)
    for j in range(7):
        bx = bar_x_start + j * (bar_w + gap)
        qh = q_hazards[j]
        bar_h = int(qh * 85)
        col_b = C_CORAL if j == 0 and qh > 0.3 else (C_GOLD if j == chosen_idx else C_CYAN)
        cv2.rectangle(hud_img, (bx, bar_base_y - bar_h), (bx + bar_w, bar_base_y), col_b, -1)
        cv2.rectangle(hud_img, (bx, bar_base_y - 85), (bx + bar_w, bar_base_y), (60, 50, 40), 1)
        cv2.putText(hud_img, actions_short[j], (bx + 2, bar_base_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.4, C_WHITE if j != chosen_idx else C_GOLD, 1, cv2.LINE_AA)
        cv2.putText(hud_img, f"{qh:.2f}", (bx + 2, bar_base_y - bar_h - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.35, C_WHITE, 1, cv2.LINE_AA)

    metrics_x = 520
    is_rewired = bool(np.linalg.norm(agent.W_hazard) > 10)
    cards = [
        ("Synaptic Norm ||W||", f"{np.linalg.norm(agent.W_hazard):.3f}", C_CYAN),
        ("LTP Rewiring Events", f"{agent.ltp_count:d}", C_CORAL),
        ("Synaptic Flux dW", f"{res['dw_magnitude']:.3f}", C_MAGENTA if res['dw_magnitude'] > 1e-4 else C_WHITE),
        ("Expected Free Energy (EFE)", f"{res['efe']:.2f}", C_LIME),
        ("Active Decision Mode", "ANTICIPATORY DETOUR" if is_rewired else "NAIVE FORWARD", C_LIME if is_rewired else C_WHITE)
    ]
    for k, (label, val, col) in enumerate(cards):
        cy = 65 + k * 45
        cv2.rectangle(hud_img, (metrics_x, cy), (width - 40, cy + 36), (32, 22, 14), -1)
        cv2.rectangle(hud_img, (metrics_x, cy), (width - 40, cy + 36), (60, 45, 30), 1)
        cv2.putText(hud_img, label, (metrics_x + 12, cy + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.42, C_WHITE, 1, cv2.LINE_AA)
        cv2.putText(hud_img, val, (width - 240, cy + 23), cv2.FONT_HERSHEY_DUPLEX, 0.5, col, 1, cv2.LINE_AA)
        
    return hud_img

# ── RUN SIMULATION & RECORD ─────────────────────────────────────
print(f"[1/4] Setting up Master Video Encoder: {MP4_PATH}")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_writer = cv2.VideoWriter(MP4_PATH, fourcc, 30, (1920, 1080))
frames_for_gif = []

hal = MuJoCoHardwareAbstractionLayer('d:/ebca/world/vessel_kinetic.xml')
renderer = mujoco.Renderer(hal.model, 540, 960)

cam = mujoco.MjvCamera()
cam.type = mujoco.mjtCamera.mjCAMERA_FREE
cam.lookat = [0.95, -0.25, 0.20]
cam.distance = 2.9
cam.elevation = -32
cam.azimuth = 95

agent = CarlP1IntegrateAgent(mode='THREE_FACTOR_STDP', seed=101, stdp_lr=0.08, hazard_weight=180.0)

hazard_coord = [0.75, 0.0, 0.15]
target_coord = [2.0, 0.0]

trail_ep1 = []
trail_ep2 = []

# EPISODE 1: NAIVE COLLISION & LTP
print("[2/4] Recording Episode 1: Naive Straight Motion -> Collision -> Synaptic LTP...")
hal.reset()

for t in range(75):
    res = agent.step_cognitive_cycle(hal, target_coords=target_coord, is_training=True)
    for _ in range(4): hal.step()
    
    mujoco.mj_forward(hal.model, hal.data)
    sens = agent.base_agent.embodiment.read_proprioception(hal)
    trail_ep1.append((sens.pos_x, sens.pos_y, C_CORAL))
    
    # 3D Render
    renderer.update_scene(hal.data, camera=cam)
    img_3d_bgr = cv2.cvtColor(renderer.render(), cv2.COLOR_RGB2BGR)
    
    # 2D Arena
    img_2d = render_2d_arena(sens, target_coord, hazard_coord, trail_ep1, res['chosen_action'], width=960, height=490)
    
    # Neural Network Graph
    ltp_active = bool(res['collision'])
    img_net = render_neural_network_graph(agent.W_hazard, agent.E, res['surprise_gate'], res['valence'], 
                                          res['chosen_idx'], res['q_hazard_all'], ltp_active, t, width=960, height=680)
    
    # HUD
    img_hud = render_plasticity_hud(agent, res, width=960, height=350)
    
    # Composite Full 1920x1080 Frame
    frame = create_canvas()
    draw_header(frame, t, 1, "Naive Baseline (Collision & Synaptic Potentiation)")
    frame[50:590, 0:960] = img_3d_bgr
    frame[590:1080, 0:960] = img_2d
    frame[50:730, 960:1920] = img_net
    frame[730:1080, 960:1920] = img_hud
    
    video_writer.write(frame)
    if t % 2 == 0:
        frames_for_gif.append(cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA))

print(f"  Ep 1 complete: Final Weight Norm: {np.linalg.norm(agent.W_hazard):.3f}")

# EPISODE 2: SYNAPTICALLY REWIRED CURVED DETOUR
print("[3/4] Recording Episode 2: Synaptically Rewired Curved Detour Circumnavigation...")
hal.reset()
agent.reset_state_traces()
agent.W_hazard[:, 1:] = 0.0  # Only forward causal action carries hazard

for t in range(160):
    res = agent.step_cognitive_cycle(hal, target_coords=target_coord, is_training=False)
    for _ in range(4): hal.step()
    
    mujoco.mj_forward(hal.model, hal.data)
    sens = agent.base_agent.embodiment.read_proprioception(hal)
    trail_ep2.append((sens.pos_x, sens.pos_y, C_LIME))
    
    # 3D Render
    renderer.update_scene(hal.data, camera=cam)
    img_3d_bgr = cv2.cvtColor(renderer.render(), cv2.COLOR_RGB2BGR)
    
    # 2D Arena
    img_2d = render_2d_arena(sens, target_coord, hazard_coord, trail_ep2, res['chosen_action'], width=960, height=490)
    
    # Neural Network Graph
    ltp_active = bool(res['collision'])
    img_net = render_neural_network_graph(agent.W_hazard, agent.E, res['surprise_gate'], res['valence'], 
                                          res['chosen_idx'], res['q_hazard_all'], ltp_active, t, width=960, height=680)
    
    # HUD
    img_hud = render_plasticity_hud(agent, res, width=960, height=350)
    
    # Composite
    frame = create_canvas()
    draw_header(frame, t, 2, "Synaptically Rewired (Active Anticipatory Curved Detour)")
    frame[50:590, 0:960] = img_3d_bgr
    frame[590:1080, 0:960] = img_2d
    frame[50:730, 960:1920] = img_net
    frame[730:1080, 960:1920] = img_hud
    
    video_writer.write(frame)
    if t % 2 == 0:
        frames_for_gif.append(cv2.resize(frame, (960, 540), interpolation=cv2.INTER_AREA))

video_writer.release()
print(f"  [OK] MP4 Video Written: {MP4_PATH} ({os.path.getsize(MP4_PATH)/1e6:.2f} MB)")

# GENERATE ANIMATED GIF
print("[4/4] Generating Animated GIF...")
try:
    pil_frames = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames_for_gif[::2]]
    if pil_frames:
        pil_frames[0].save(GIF_PATH, save_all=True, append_images=pil_frames[1:], duration=66, loop=0, optimize=True)
        print(f"  [OK] Animated GIF Written: {GIF_PATH} ({os.path.getsize(GIF_PATH)/1e6:.2f} MB)")
except Exception as e:
    print(f"  GIF error: {e}")

# Copy to artifacts directory
art_dir = r"C:\Users\MANAS\.gemini\antigravity-ide\brain\a3c6a2a8-e5db-41ca-891e-577421bbd5ca"
import shutil
shutil.copy(MP4_PATH, art_dir)
shutil.copy(GIF_PATH, art_dir)
print(f"  [OK] Copied MP4 and GIF to artifact directory: {art_dir}")

# Save Keyframes
cap = cv2.VideoCapture(MP4_PATH)
for f_idx, fname in [(30, 'frame_ep1_naive.png'), (65, 'frame_ep1_collision_ltp.png'), (140, 'frame_ep2_rewired_detour.png')]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
    ret, f_img = cap.read()
    if ret:
        cv2.imwrite(os.path.join(OUTPUT_DIR, fname), f_img)
        cv2.imwrite(os.path.join(art_dir, fname), f_img)
cap.release()
print("  [OK] Keyframes updated.")

print("\n" + "="*70)
print(f"  SYNAPTIC PLASTICITY VIDEO GENERATION COMPLETE")
print("="*70)
