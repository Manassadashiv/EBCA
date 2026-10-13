"""
brain/p1_integrate/render_synchronized_video.py
================================================
Renders a synchronized side-by-side video and animated GIF:
  LEFT: MuJoCo 3D Physics Simulation of CARL approaching & colliding with the obstacle.
  RIGHT: Real-time Brain State (1024-Neuron Reservoir Heatmap, Noradrenaline Surge, Eligibility, Synaptic Weight Delta, Hazard Likelihood).
"""

import os
import sys
import math
import json
import numpy as np
import mujoco
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
from PIL import Image

sys.path.insert(0, "d:/ebca")
from brain.carl_reflex_laboratory import MuJoCoHardwareAbstractionLayer
from brain.p1_integrate.carl_p1_integrate_agent import CarlP1IntegrateAgent

XML_PATH = "d:/ebca/world/vessel_kinetic.xml"
OUTPUT_DIR = "C:/Users/MANAS/.gemini/antigravity-ide/brain/a3c6a2a8-e5db-41ca-891e-577421bbd5ca"


def render_synchronized_animation(n_frames: int = 100):
    print("Initializing MuJoCo Offscreen Renderer & P1-Integrate Agent...")
    hal = MuJoCoHardwareAbstractionLayer(XML_PATH)
    model = hal.model
    data = hal.data

    # Offscreen renderer
    renderer = mujoco.Renderer(model, height=480, width=540)

    # Set camera
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat = np.array([1.0, 0.0, 0.2])
    camera.distance = 2.8
    camera.elevation = -35.0
    camera.azimuth = 135.0

    # Place hazard cube at (1.0, 0.0, 0.15)
    bid = model.body("hazard_cube").id
    model.body_pos[bid] = np.array([1.0, 0.0, 0.15])

    agent = CarlP1IntegrateAgent(mode="THREE_FACTOR_STDP", seed=101)
    hal.reset()

    frames = []
    video_writer = None
    mp4_path = os.path.join(OUTPUT_DIR, "p1_integrate_synchronized_brain_physics.mp4")
    gif_path = os.path.join(OUTPUT_DIR, "p1_integrate_synchronized_brain_physics.gif")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(mp4_path, fourcc, 15, (1080, 480))

    print(f"Generating {n_frames} synchronized frames...")
    
    reservoir_history = []
    q_hazard_history = []
    surprise_history = []
    dw_history = []
    
    for frame_idx in range(n_frames):
        res = agent.step_cognitive_cycle(hal, target_coords=(2.2, 0.0))
        for _ in range(3):
            hal.step()

        # 1. Render Left Side: MuJoCo Physics 3D Scene
        renderer.update_scene(data, camera)
        sim_rgb = renderer.render()  # (480, 540, 3)

        # Draw overlay text on 3D view
        cv2.putText(sim_rgb, f"MuJoCo Physics | Tick: {frame_idx:03d}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        status_text = "STATUS: CRASH / LEARNING" if res["collision"] else "STATUS: DRIVING"
        status_color = (0, 0, 255) if res["collision"] else (0, 255, 120)
        cv2.putText(sim_rgb, status_text, (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
        cv2.putText(sim_rgb, f"Action: {res['chosen_action']}", (15, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

        # 2. Render Right Side: Live Neural State Dashboard
        reservoir_history.append(agent.x[:64].copy())
        if len(reservoir_history) > 30: reservoir_history.pop(0)
        q_hazard_history.append(res["q_hazard_chosen"])
        surprise_history.append(res["surprise_gate"])
        dw_history.append(res["dw_magnitude"])

        fig, (ax_res, ax_signals) = plt.subplots(2, 1, figsize=(5.4, 4.8), dpi=100, facecolor='#0f111a')
        for ax in (ax_res, ax_signals):
            ax.set_facecolor('#1a1c29')
            ax.tick_params(colors='white', labelsize=8)
            for s in ax.spines.values(): s.set_color('#444a66')

        # Top Right: Reservoir State Matrix
        res_mat = np.array(reservoir_history).T # (64, T)
        ax_res.imshow(res_mat, aspect='auto', cmap='plasma', vmin=-1.0, vmax=1.0)
        ax_res.set_title("1024-Neuron Reservoir Activity (Top 64)", color='white', fontsize=10, pad=4)
        ax_res.set_ylabel("Neurons", color='white', fontsize=8)

        # Bottom Right: Neuromodulation & Hazard Prediction Traces
        t_axis = list(range(len(q_hazard_history)))
        ax_signals.plot(t_axis, surprise_history, color='#ffcc00', label="Noradrenaline / Surprise", linewidth=1.8)
        ax_signals.plot(t_axis, q_hazard_history, color='#ff5722', label="P(Hazard | x_t)", linewidth=2.0)
        ax_signals.plot(t_axis, dw_history, color='#00e5ff', label="||ΔW|| Plasticity", linewidth=1.5, linestyle='--')
        ax_signals.set_title("Real-Time Neuromodulation & Synaptic Plasticity", color='white', fontsize=10, pad=4)
        ax_signals.set_ylim(-0.05, 1.1)
        ax_signals.set_xlabel("Recent Ticks", color='white', fontsize=8)
        ax_signals.legend(loc='upper left', fontsize=7, facecolor='#1a1c29', edgecolor='#444a66', labelcolor='white')
        ax_signals.grid(True, color='#2d3148', linestyle=':')

        fig.tight_layout()
        fig.canvas.draw()
        brain_rgba = np.asarray(fig.canvas.buffer_rgba())
        brain_rgb = brain_rgba[:, :, :3]
        plt.close(fig)

        # Resize brain dashboard to exactly match sim height (480, 540)
        brain_rgb = cv2.resize(brain_rgb, (540, 480))

        # Composite side-by-side: (480, 1080, 3)
        combined_frame = np.hstack([sim_rgb, brain_rgb])
        
        # Write to video (BGR for OpenCV)
        video_writer.write(cv2.cvtColor(combined_frame, cv2.COLOR_RGB2BGR))
        
        # Sample frames for GIF (every 2nd frame)
        if frame_idx % 2 == 0:
            frames.append(Image.fromarray(combined_frame))

    video_writer.release()
    print(f"Saved Synchronized Video: {mp4_path}")

    if frames:
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=66, loop=0)
        print(f"Saved Synchronized GIF: {gif_path}")


if __name__ == "__main__":
    render_synchronized_animation(n_frames=100)
