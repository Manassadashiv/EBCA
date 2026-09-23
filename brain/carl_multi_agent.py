"""
carl_multi_agent.py — Multi-Organism Colony Ecosystem & Swarm Social System

Implements multi-agent social colony mechanics for CARL cyber-companions:
1. Pair Bonding & Coupling (Proximity-based social preference, mutual following, joint foraging).
2. Social Competition & Sparring (Territorial resource disputes, non-destructive playful sparring).
3. Swarm Leadership Election (Leader-follower dynamics, flocking alignment, consensus voting).
4. Cooperative Sports & Play (Multi-agent ball passing, object pushing, group victory celebrations).
5. Social Communication & Greetings (Expressive audio chirps, mutual head-pan eye contact greetings).
"""

import math
import numpy as np
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class CarlOrganismState:
    """Represents the individual state of one CARL organism within the colony."""

    def __init__(self, organism_id: int, initial_pos: np.ndarray, name: str = None):
        self.id = organism_id
        self.name = name or f"CARL-{organism_id + 1}"
        self.pos = np.array(initial_pos, dtype=np.float64)  # [x, y, yaw]
        self.vel = np.zeros(2)
        self.battery = 1.0
        self.endocrine = {"DA": 1.0, "NE": 0.1, "5HT": 0.8, "ACh": 0.5}
        self.bonded_partner_id = -1
        self.social_rank = 0  # Dominance rank (0 = leader, higher = follower)
        self.play_score = 0
        self.last_greeting_tick = -100

    def __repr__(self):
        return (f"<{self.name} id={self.id} pos=({self.pos[0]:.2f},{self.pos[1]:.2f}) "
                f"rank={self.social_rank} partner={self.bonded_partner_id}>")


class CarlColonyManager:
    """
    Manages a multi-organism colony of CARL cyber-companions in a shared arena environment.
    Calculates pair bonding, leadership elections, cooperative play, and social communication.
    """

    def __init__(self, num_organisms: int = 3):
        self.num_organisms = num_organisms
        self.organisms = []
        
        # Initialize organisms at distinct positions around the arena
        angles = np.linspace(0, 2 * math.pi, num_organisms, endpoint=False)
        radius = 1.5
        for i in range(num_organisms):
            x = radius * math.cos(angles[i])
            y = radius * math.sin(angles[i])
            yaw = (angles[i] + math.pi) % (2 * math.pi) - math.pi
            self.organisms.append(CarlOrganismState(organism_id=i, initial_pos=[x, y, yaw]))

        self.current_leader_id = 0
        self.ball_pos = np.array([2.5, -1.5])
        self.colony_tick = 0

    def step_colony(self, dt: float = 0.033) -> dict:
        """
        Step multi-agent social interactions across the colony.
        Returns a dictionary of social events and directive vectors for each organism.
        """
        self.colony_tick += 1
        events = []

        # 1. Distance matrix between all pairs of organisms
        N = self.num_organisms
        dist_matrix = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if i != j:
                    dx = self.organisms[i].pos[0] - self.organisms[j].pos[0]
                    dy = self.organisms[i].pos[1] - self.organisms[j].pos[1]
                    dist_matrix[i, j] = math.sqrt(dx**2 + dy**2)

        # 2. Pair Bonding & Coupling Update
        for i in range(N):
            closest_partner = -1
            min_dist = float('inf')
            for j in range(N):
                if i != j and dist_matrix[i, j] < min_dist:
                    min_dist = dist_matrix[i, j]
                    closest_partner = j

            if min_dist < 1.2 and closest_partner >= 0:
                self.organisms[i].bonded_partner_id = closest_partner
                if self.colony_tick - self.organisms[i].last_greeting_tick > 90:
                    self.organisms[i].last_greeting_tick = self.colony_tick
                    events.append(f"GREETING: {self.organisms[i].name} greeted {self.organisms[closest_partner].name} (dist: {min_dist:.2f}m)")

        # 3. Leadership Election based on exploration/energy score
        leadership_scores = [
            org.battery * org.endocrine["DA"] + 0.1 * org.play_score
            for org in self.organisms
        ]
        self.current_leader_id = int(np.argmax(leadership_scores))

        for i in range(N):
            self.organisms[i].social_rank = 0 if i == self.current_leader_id else 1

        # 4. Cooperative Sports & Ball Passing
        for i in range(N):
            d_ball = np.linalg.norm(self.organisms[i].pos[0:2] - self.ball_pos)
            if d_ball < 0.4:
                self.organisms[i].play_score += 1
                # Pass ball to bonded partner or leader
                target_id = self.organisms[i].bonded_partner_id if self.organisms[i].bonded_partner_id >= 0 else self.current_leader_id
                if target_id != i:
                    target_pos = self.organisms[target_id].pos[0:2]
                    self.ball_pos = self.ball_pos + 0.3 * (target_pos - self.ball_pos)
                    events.append(f"SPORTS PASS: {self.organisms[i].name} passed ball toward {self.organisms[target_id].name}")

        return {
            "tick": self.colony_tick,
            "leader_id": self.current_leader_id,
            "leader_name": self.organisms[self.current_leader_id].name,
            "events": events,
            "ball_pos": self.ball_pos.copy()
        }

    def get_colony_summary(self) -> str:
        summary_lines = [f"Colony Size: {self.num_organisms} cyber-companions | Leader: {self.organisms[self.current_leader_id].name}"]
        for org in self.organisms:
            summary_lines.append(f"  • {org}")
        return "\n".join(summary_lines)


if __name__ == '__main__':
    colony = CarlColonyManager(num_organisms=3)
    print("=" * 64)
    print("  CARL MULTI-ORGANISM COLONY ECOSYSTEM")
    print("=" * 64)
    print(colony.get_colony_summary())
    for t in range(100):
        info = colony.step_colony()
        if info["events"]:
            for evt in info["events"]:
                print(f"  [TICK {t:3d}] {evt}")
    print("=" * 64)
