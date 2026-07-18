"""
plot_telemetry.py — Visual Proof of Emergent Cognitive Autonomy (WIT-401)
Pure Python + NumPy + Matplotlib (No pandas dependency)
"""
import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import os as _os
_FILE_DIR = _os.path.dirname(_os.path.abspath(__file__))
BASE_DIR = _os.path.dirname(_FILE_DIR)


def generate_proof():
    csv_path = os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")
    if not os.path.exists(csv_path):
        print(f"[ERROR] Telemetry file not found at {csv_path}")
        return

    # Parse headers and load columns using csv reader
    data = {}
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for h in headers:
            data[h] = []
        for row in reader:
            if not row or len(row) != len(headers):
                continue
            for h, val in zip(headers, row):
                try:
                    if h == 'surge_event':
                        data[h].append(val)
                    else:
                        data[h].append(float(val))
                except ValueError:
                    data[h].append(val)

    # Convert to numpy arrays
    for h in headers:
        if h != 'surge_event':
            data[h] = np.array(data[h])

    # Convert tick to time
    time_s = data['wall_time_s'] - data['wall_time_s'][0]

    # Set up matplotlib style for a premium modern look
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
    
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle("EBCA Emergent Autonomy Proof: CARL Simulation Run", fontsize=20, fontweight='bold', color='#1e293b')

    # ── Plot 1: 2D Trajectory (Top Left) ──────────────────────────────────
    ax1 = plt.subplot(221)
    ax1.plot(data['x'], data['y'], color='#0284c7', alpha=0.7, label='CARL Trajectory')
    # Draw walls
    ax1.axvline(-5.0, color='#ef4444', linestyle='--', alpha=0.5)
    ax1.axvline(5.0, color='#ef4444', linestyle='--', alpha=0.5)
    ax1.axhline(-5.0, color='#ef4444', linestyle='--', alpha=0.5)
    ax1.axhline(5.0, color='#ef4444', linestyle='--', alpha=0.5)
    # Highlight start
    ax1.scatter(data['x'][0], data['y'][0], color='#22c55e', s=100, zorder=5, label='Spawn Coordinate')
    # Highlight end
    ax1.scatter(data['x'][-1], data['y'][-1], color='#a855f7', s=100, zorder=5, label='Current Pose')
    ax1.set_xlim(-5.5, 5.5)
    ax1.set_ylim(-5.5, 5.5)
    ax1.set_title("1. Emergent 2D Arena Trajectory", fontsize=14, fontweight='semibold', color='#334155')
    ax1.set_xlabel("X coordinate (m)", fontsize=11)
    ax1.set_ylabel("Y coordinate (m)", fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, linestyle=':', alpha=0.6)

    # ── Plot 2: Neuromodulators (Top Right) ──────────────────────────────
    ax2 = plt.subplot(222)
    ax2.plot(time_s, data['DA'], color='#eab308', linewidth=1.5, label='Dopamine (DA)')
    ax2.plot(time_s, data['NE'], color='#f97316', linewidth=1.5, label='Norepinephrine (NE)')
    ax2.plot(time_s, data['ACh'], color='#3b82f6', linewidth=1.5, label='Acetylcholine (ACh)')
    ax2.plot(time_s, data['SHT'], color='#ec4899', linewidth=1.5, label='Serotonin (5-HT)')
    ax2.set_title("2. Endocrine Modulator Kinetics", fontsize=14, fontweight='semibold', color='#334155')
    ax2.set_xlabel("Time (seconds)", fontsize=11)
    ax2.set_ylabel("Concentration (x Baseline)", fontsize=11)
    ax2.legend(loc='upper right')
    ax2.grid(True, linestyle=':', alpha=0.6)

    # ── Plot 3: Cognitive Readout Takeover (Bottom Left) ─────────────────
    ax3 = plt.subplot(223)
    cog_total = np.abs(data['cognitive_L']) + np.abs(data['cognitive_R'])
    rfx_total = np.abs(data['reflex_L']) + np.abs(data['reflex_R'])
    
    # Custom 1D box filter rolling average with numpy
    window_size = 150
    box = np.ones(window_size) / window_size
    cog_smoothed = np.convolve(cog_total, box, mode='same')
    rfx_smoothed = np.convolve(rfx_total, box, mode='same')
    
    ax3.plot(time_s, cog_smoothed, color='#6366f1', linewidth=2, label='Reservoir Brain Steering')
    ax3.plot(time_s, rfx_smoothed, color='#ef4444', linewidth=1.5, alpha=0.6, label='Spiking LIF Reflex Override')
    ax3.set_title("3. Brain vs. Reflex Command Share (takeover)", fontsize=14, fontweight='semibold', color='#334155')
    ax3.set_xlabel("Time (seconds)", fontsize=11)
    ax3.set_ylabel("Steering Effort Magnitude", fontsize=11)
    ax3.legend(loc='upper right')
    ax3.grid(True, linestyle=':', alpha=0.6)

    # ── Plot 4: Metabolic Motivation Dynamics (Bottom Right) ──────────────
    ax4 = plt.subplot(224)
    
    # Calculate motivation on the fly
    battery = data['battery']  # scale [0, 1]
    da = data['DA']
    hunger = 1.0 + 2.0 * (1.0 - battery)
    satiation = 1.0 / np.maximum(0.5, da)
    motivation = hunger * satiation
    
    # Left axis: Battery and Food
    line1 = ax4.plot(time_s, battery * 100.0, color='#10b981', linewidth=2.0, label='Battery Level (%)')
    line2 = ax4.plot(time_s, data['food_eaten_total'] * 10.0, color='#0f172a', linestyle='--', linewidth=1.5, label='Food Eaten (x10)')
    ax4.set_title("4. Metabolic & Foraging Motivation Dynamics", fontsize=14, fontweight='semibold', color='#334155')
    ax4.set_xlabel("Time (seconds)", fontsize=11)
    ax4.set_ylabel("Battery / Food Scale", color='#10b981', fontsize=11)
    ax4.set_ylim(-5, 110)
    ax4.tick_params(axis='y', labelcolor='#10b981')
    ax4.grid(True, linestyle=':', alpha=0.6)
    
    # Right axis: Motivation
    ax4_twin = ax4.twinx()
    line3 = ax4_twin.plot(time_s, motivation, color='#ef4444', linewidth=2.0, label='Appetitive Motivation')
    ax4_twin.set_ylabel("Motivation Drive (x1)", color='#ef4444', fontsize=11)
    ax4_twin.set_ylim(0.0, 3.5)
    ax4_twin.tick_params(axis='y', labelcolor='#ef4444')
    ax4_twin.grid(False) # avoid overlapping gridlines
    
    # Combined legend
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax4.legend(lines, labels, loc='upper left')

    plt.tight_layout()
    
    # Save image
    output_path = os.path.join(BASE_DIR, "autonomous_emergence_proof.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[WIT-401] Verification plot saved to: {output_path}")

if __name__ == "__main__":
    generate_proof()
