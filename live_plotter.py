"""
live_plotter.py — Real-Time Live Dashboard for CARL Autonomous Simulation
Reads D:/ebca/memory/telemetry_autonomous.csv dynamically and updates plots every 2 seconds.
"""
import csv
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TELEMETRY_PATH = os.path.join(BASE_DIR, "memory", "telemetry_autonomous.csv")

def read_telemetry():
    if not os.path.exists(TELEMETRY_PATH):
        return None
    data = {}
    with open(TELEMETRY_PATH, 'r') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return None
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
    for h in data:
        if h != 'surge_event':
            data[h] = np.array(data[h])
    return data

def run_live_dashboard():
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig = plt.figure(figsize=(15, 9))
    fig.suptitle("EBCA Real-Time Cognitive Dashboard (Live Telemetry)", fontsize=16, fontweight='bold', color='#1e293b')

    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)

    def update(frame):
        data = read_telemetry()
        if not data or len(data.get('x', [])) < 5:
            return

        time_s = data['wall_time_s'] - data['wall_time_s'][0]

        # 1. Trajectory
        ax1.clear()
        ax1.plot(data['x'], data['y'], color='#0284c7', label='CARL Path', linewidth=1.5)
        ax1.scatter(data['x'][-1], data['y'][-1], color='#a855f7', s=100, zorder=5, label='Current Position')
        ax1.set_xlim(-5.5, 5.5)
        ax1.set_ylim(-5.5, 5.5)
        ax1.set_title("1. Live 2D Spatial Trajectory", fontsize=12, fontweight='bold')
        ax1.set_xlabel("X (m)")
        ax1.set_ylabel("Y (m)")
        ax1.legend(loc='upper right')

        # 2. Neuromodulators
        ax2.clear()
        ax2.plot(time_s, data['DA'], color='#eab308', label='DA (Reward)')
        ax2.plot(time_s, data['NE'], color='#f97316', label='NE (Surprise/Evasion)')
        ax2.plot(time_s, data['ACh'], color='#3b82f6', label='ACh (Attention)')
        ax2.plot(time_s, data['SHT'], color='#ec4899', label='5-HT (Satiety)')
        ax2.set_title("2. Live Endocrine Hormones", fontsize=12, fontweight='bold')
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Concentration")
        ax2.legend(loc='upper right')

        # 3. Brain vs Reflex Effort
        ax3.clear()
        cog_total = np.abs(data['cognitive_L']) + np.abs(data['cognitive_R'])
        rfx_total = np.abs(data['reflex_L']) + np.abs(data['reflex_R'])
        ax3.plot(time_s, cog_total, color='#6366f1', label='Reservoir Brain Command', alpha=0.8)
        ax3.plot(time_s, rfx_total, color='#ef4444', label='Reflex Command (Aversive+Appetitive)', alpha=0.7)
        ax3.set_title("3. Brain vs. Reflex Drive", fontsize=12, fontweight='bold')
        ax3.set_xlabel("Time (s)")
        ax3.legend(loc='upper right')

        # 4. Metabolic Motivation Dynamics
        ax4.clear()
        
        # Calculate motivation on the fly
        battery = data['battery']  # scale [0, 1]
        da = data['DA']
        hunger = 1.0 + 2.0 * (1.0 - battery)
        satiation = 1.0 / np.maximum(0.5, da)
        motivation = hunger * satiation
        
        # Left axis: Battery and Food
        line1 = ax4.plot(time_s, battery * 100.0, color='#10b981', linewidth=2.0, label='Battery Level (%)')
        line2 = ax4.plot(time_s, data['food_eaten_total'] * 10.0, color='#0f172a', linestyle='--', linewidth=1.5, label='Food Eaten (x10)')
        ax4.set_title("4. Metabolic & Foraging Motivation Dynamics", fontsize=12, fontweight='bold')
        ax4.set_xlabel("Time (s)")
        ax4.set_ylabel("Battery / Food Scale", color='#10b981')
        ax4.set_ylim(-5, 110)
        ax4.tick_params(axis='y', labelcolor='#10b981')
        
        # Right axis: Motivation
        ax4_twin = ax4.twinx()
        ax4_twin.clear()
        line3 = ax4_twin.plot(time_s, motivation, color='#ef4444', linewidth=2.0, label='Appetitive Motivation')
        ax4_twin.set_ylabel("Motivation Drive (x1)", color='#ef4444')
        ax4_twin.set_ylim(0.0, 3.5)
        ax4_twin.tick_params(axis='y', labelcolor='#ef4444')
        ax4_twin.grid(False) # avoid overlapping gridlines
        
        # Combined legend
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax4.legend(lines, labels, loc='upper left')

        plt.tight_layout()

    ani = FuncAnimation(fig, update, interval=2000, cache_frame_data=False)
    print("[DASHBOARD] Launching live real-time dashboard. Press Ctrl+C or close window to exit.")
    plt.show()

if __name__ == "__main__":
    run_live_dashboard()
