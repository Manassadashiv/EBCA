"""
carl_gis.py — Global Integrated State Manager (GIS-901)

Implements persistent disk-backed storage for CARL's compounding lifelong memory:
- Reservoir readout weights (W_out, P covariance matrix, total RLS updates)
- Hippocampal spatial graph (place centres, nav values, reward beacons, visit timestamps)
- Physarum slime-mold tube conductivity matrices (D_h, D_v)
- Constraint Interaction Graph (CIG) co-occurrence matrices
- Cumulative lifetime statistics (food eaten, run duration, lifetime ticks)

References:
  - EBCA Master Roadmap Pillar II (Constraint-Driven Computational Ecology)
  - Technical Specifications Section 11 (GIS-901)
"""

import os
import time
import numpy as np


class GlobalIntegratedStateManager:
    """
    Manages persistent state serialization across multiple simulation sessions (GIS-901).
    Ensures zero loss of learned topological paths, synaptic weights, and hazard memories.
    """

    def __init__(self, save_dir: str = None):
        if save_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            save_dir = os.path.join(base_dir, "memory")
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.default_file = os.path.join(self.save_dir, "carl_gis_state.npz")
        self.session_count = 0
        self.total_lifetime_ticks = 0
        self.total_lifetime_food = 0
        self.total_distance_traveled = 0.0

    def save_state(self, filepath: str = None,
                   reservoir=None,
                   hippocampus=None,
                   physarum=None,
                   cig=None,
                   hdc=None,
                   stats: dict = None) -> bool:
        """
        Serializes all cognitive subsystems into a single compressed NumPy archive.
        """
        path = filepath or self.default_file
        temp_path = path + ".tmp.npz"
        payload = {
            "version": "2.0-DX",
            "saved_at": time.time(),
            "session_count": self.session_count + 1,
            "total_lifetime_ticks": self.total_lifetime_ticks + (stats.get("current_tick", 0) if stats else 0),
            "total_lifetime_food": self.total_lifetime_food + (stats.get("food_eaten", 0) if stats else 0),
            "total_distance_m": self.total_distance_traveled + (stats.get("distance_traveled", 0.0) if stats else 0.0)
        }

        # 1. Reservoir Weights
        if reservoir is not None:
            payload["res_W_out"] = reservoir.W_out
            payload["res_P"] = reservoir.P
            payload["res_total_rls_updates"] = reservoir.total_rls_updates

        # 2. Hippocampal Place Map & Replay Graph
        if hippocampus is not None and hasattr(hippocampus, "places"):
            places = hippocampus.places
            payload["hip_centres"] = places.centres
            payload["hip_nav_values"] = places.nav_values
            payload["hip_reward_values"] = places.reward_values
            payload["hip_persistent_rewards"] = places.persistent_rewards
            payload["hip_recency"] = places.recency
            payload["hip_total_edges"] = places.total_edges
            # Serialize adjacency graph edges as (u, v) pairs
            edges = []
            for u, neighbors in places.adjacency.items():
                for v in neighbors:
                    edges.append((int(u), int(v)))
            payload["hip_edges"] = np.array(edges, dtype=np.int32) if edges else np.zeros((0, 2), dtype=np.int32)

        # 3. Physarum Slime-Mold Conductivity
        if physarum is not None and hasattr(physarum, "D_h"):
            payload["phys_D_h"] = physarum.D_h
            payload["phys_D_v"] = physarum.D_v
            payload["phys_obstacle"] = physarum.obstacle

        # 4. Constraint Interaction Graph (CIG)
        if cig is not None and hasattr(cig, "A_CIG"):
            payload["cig_A_matrix"] = cig.A_CIG
            payload["cig_co_occurrences"] = cig.co_occurrences

        # 5. Holographic Episodic Memory (HDC)
        if hdc is not None and hasattr(hdc, "M_spatial"):
            payload["hdc_M_spatial"] = hdc.M_spatial
            payload["hdc_M_aversion"] = hdc.M_aversion
            payload["hdc_episode_count"] = hdc.episode_count
            payload["hdc_aversion_count"] = hdc.aversion_count

        try:
            np.savez_compressed(temp_path, **payload)
            if os.path.exists(path):
                os.remove(path)
            os.rename(temp_path, path)
            print(f"[GIS-901] Successfully saved Global Integrated State to {os.path.basename(path)} "
                  f"(Session: {payload['session_count']}, Lifetime Ticks: {payload['total_lifetime_ticks']})")
            return True
        except Exception as e:
            print(f"[ERROR][GIS-901] Failed to save state to {path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def load_state(self, filepath: str = None,
                   reservoir=None,
                   hippocampus=None,
                   physarum=None,
                   cig=None,
                   hdc=None) -> bool:
        """
        Restores brain weights, spatial graphs, and lifelong stats from disk.
        """
        path = filepath or self.default_file
        if not os.path.exists(path):
            print(f"[GIS-901] No existing state file found at {path}. Starting fresh organism lifespan.")
            return False

        try:
            data = np.load(path, allow_pickle=True)
            self.session_count = int(data.get("session_count", 0))
            self.total_lifetime_ticks = int(data.get("total_lifetime_ticks", 0))
            self.total_lifetime_food = int(data.get("total_lifetime_food", 0))
            self.total_distance_traveled = float(data.get("total_distance_m", 0.0))

            # 1. Restore Reservoir
            if reservoir is not None and "res_W_out" in data:
                reservoir.W_out = data["res_W_out"].copy()
                reservoir.P = data["res_P"].copy()
                reservoir.total_rls_updates = int(data["res_total_rls_updates"])

            # 2. Restore Hippocampus
            if hippocampus is not None and hasattr(hippocampus, "places") and "hip_centres" in data:
                places = hippocampus.places
                saved_n = len(data["hip_centres"])
                if saved_n == places.n:
                    places.centres = data["hip_centres"].copy()
                    places.nav_values = data["hip_nav_values"].copy()
                    places.reward_values = data["hip_reward_values"].copy()
                    if "hip_persistent_rewards" in data:
                        places.persistent_rewards = data["hip_persistent_rewards"].copy()
                    if "hip_recency" in data:
                        places.recency = data["hip_recency"].copy()
                    if "hip_total_edges" in data:
                        places.total_edges = int(data["hip_total_edges"])
                    if "hip_edges" in data:
                        edges = data["hip_edges"]
                        places.adjacency = {i: set() for i in range(places.n)}
                        for u, v in edges:
                            places.adjacency[int(u)].add(int(v))

            # 3. Restore Physarum
            if physarum is not None and "phys_D_h" in data:
                if physarum.D_h.shape == data["phys_D_h"].shape:
                    physarum.D_h = data["phys_D_h"].copy()
                    physarum.D_v = data["phys_D_v"].copy()
                    physarum.obstacle = data["phys_obstacle"].copy()

            # 4. Restore CIG
            if cig is not None and "cig_A_matrix" in data:
                if cig.A_CIG.shape == data["cig_A_matrix"].shape:
                    cig.A_CIG = data["cig_A_matrix"].copy()
                    cig.co_occurrences = int(data["cig_co_occurrences"])

            # 5. Restore HDC
            if hdc is not None and "hdc_M_spatial" in data:
                hdc.M_spatial = data["hdc_M_spatial"].copy()
                hdc.episode_count = int(data["hdc_episode_count"])
                if "hdc_M_aversion" in data:
                    hdc.M_aversion = data["hdc_M_aversion"].copy()
                    hdc.aversion_count = int(data["hdc_aversion_count"])

            print(f"[GIS-901] Loaded Global Integrated State (Lifespan #{self.session_count}, "
                  f"Total Prior Food: {self.total_lifetime_food}, Ticks: {self.total_lifetime_ticks})")
            return True
        except Exception as e:
            print(f"[ERROR][GIS-901] Failed to load state from {path}: {e}")
            return False
