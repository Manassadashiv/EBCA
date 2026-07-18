"""
carl_grid_cells.py — Nobel Prize Grid Cells + Place Cells (O'Keefe & Moser 2014)

Grid cells: hexagonal firing patterns that tile all of space — the brain's GPS ruler.
Place cells: fire at specific locations — the brain's "I am HERE" neuron.

Implementation:
  - 3 grid modules (different scales + orientations) using interference model (Burgess 2007)
  - Path integration: velocity → phase update each timestep
  - 200 place cells via Hebbian competition from grid cell input
  - No ML training required — pure biophysics
"""
import math
import numpy as np


# ── Grid Cell Module ──────────────────────────────────────────────────────────
class GridCellModule:
    """
    One grid cell module. N cells with hexagonal firing pattern.
    Firing uses the 3-wave interference model:
       r(x,y) = [cos(k1·r) + cos(k2·r) + cos(k3·r)] / 3
    where k1,k2,k3 are three wave vectors at 60° spacing.
    """

    def __init__(self, scale, orientation_deg, n_cells=64, noise=0.05):
        self.scale  = scale           # spatial period in metres
        self.n      = n_cells
        self.noise  = noise

        # Three wave vectors for hexagonal pattern
        theta = math.radians(orientation_deg)
        angles = [theta + i * math.pi / 3.0 for i in range(3)]
        freq   = 2.0 * math.pi / scale
        self.K = np.array([[math.cos(a), math.sin(a)] for a in angles]) * freq  # (3, 2)

        # Each cell has a random phase offset within [0, 2π]
        self.phases = np.random.uniform(0, 2 * math.pi, (n_cells, 3))  # (N, 3)

        # Path integration phase state (tracks where the module "thinks" we are)
        self.pi_phase = np.zeros(2)   # current integrated position estimate

        # Activity vector (firing rates)
        self.activity = np.zeros(n_cells)

    def reset(self, x, y):
        """Reset path integrator to known position."""
        self.pi_phase = np.array([x, y], dtype=float)

    def integrate(self, vx, vy, dt):
        """Update internal position estimate from velocity."""
        self.pi_phase[0] += vx * dt
        self.pi_phase[1] += vy * dt

    def fire(self, x=None, y=None):
        """
        Compute grid cell firing rates.
        If x,y provided: use actual position (GPS-grounded).
        Else: use path-integrated position.
        """
        pos = np.array([x, y], dtype=float) if x is not None else self.pi_phase
        proj = self.K @ pos                # (3,) — projection onto wave vectors
        for c in range(self.n):
            phi = proj + self.phases[c]    # (3,)
            rate = (math.cos(phi[0]) + math.cos(phi[1]) + math.cos(phi[2])) / 3.0
            # Shift from [-1,1] to [0,1] and add noise
            self.activity[c] = max(0.0, (rate + 1.0) / 2.0
                                    + np.random.randn() * self.noise)
        return self.activity.copy()


# ── Place Cells ───────────────────────────────────────────────────────────────
class PlaceCellLayer:
    """
    200 place cells with integrated Hippocampal Replay Navigation.

    Each cell has a preferred location (centre) and Gaussian tuning.
    Extended with:
      - Topological adjacency graph (built from walking experience)
      - Recency timestamps (novelty tracking — when was each cell last visited?)
      - Reward values (food beacons — where was food found?)
      - Reward diffusion (hippocampal replay — propagate value backwards through graph)
      - Navigation targets (novelty-seeking and replay-guided waypoints)

    References:
      - O'Keefe & Nadel (1978): The Hippocampus as a Cognitive Map
      - Foster & Wilson (2006): Reverse replay of behavioural sequences in hippocampal place cells
      - Mattar & Daw (2018): Prioritized memory access explains planning and hippocampal replay
    """

    def __init__(self, n_place=400, arena_bounds=(-5.0, 5.0, -5.0, 5.0), sigma=0.4):
        self.n      = n_place
        self.sigma  = sigma
        self.sigma2 = sigma ** 2

        # Preferred locations uniformly distributed across actual arena
        xmin, xmax, ymin, ymax = arena_bounds
        self.centres = np.column_stack([
            np.random.uniform(xmin, xmax, n_place),
            np.random.uniform(ymin, ymax, n_place),
        ])  # (N, 2)

        # Activity
        self.activity = np.zeros(n_place)

        # ── Hippocampal Replay Navigation ──────────────────────────────
        # Topological adjacency graph: maps cell_idx → set of connected cell indices
        # Built incrementally as CARL walks — edges created on place cell transitions
        self.adjacency = {i: set() for i in range(n_place)}

        # Recency map: last tick when each cell was strongly active
        # Used for novelty computation — old cells are "novel" (worth exploring)
        self.recency = np.full(n_place, -1000, dtype=np.int64)

        # Reward values: food beacon strength at each cell
        # Stamped when CARL eats food — persistent beacons that decay very slowly
        self.reward_values = np.zeros(n_place)

        # Diffused value map: propagated reward through the graph
        # This is the "hippocampal replay" output — a gradient pointing toward food
        self.nav_values = np.zeros(n_place)

        # Persistent food memory: strongest-ever reward at each cell (never decays)
        # Provides a floor that prevents the reward map from going completely blank
        self.persistent_rewards = np.zeros(n_place)

        # Graph construction statistics
        self.total_edges = 0

    def fire_from_position(self, x, y):
        """GPS-grounded place cell firing."""
        pos = np.array([x, y])
        d2  = np.sum((self.centres - pos) ** 2, axis=1)
        self.activity = np.exp(-d2 / (2 * self.sigma2))
        return self.activity.copy()

    def decode_position(self):
        """Population vector decode: estimate (x, y) from place cell activity."""
        total = self.activity.sum()
        if total < 1e-6:
            return None, None
        x_est = float(np.dot(self.activity, self.centres[:, 0]) / total)
        y_est = float(np.dot(self.activity, self.centres[:, 1]) / total)
        return x_est, y_est

    def peak_cell(self):
        """Return the index and centre of the most active place cell."""
        idx = int(np.argmax(self.activity))
        return idx, self.centres[idx]

    # ── Graph Construction ─────────────────────────────────────────────

    def update_graph(self, old_cell: int, new_cell: int, tick: int):
        """
        Record a topological transition: CARL walked from old_cell to new_cell.
        Creates a bidirectional edge in the adjacency graph and updates recency.
        """
        if old_cell != new_cell and 0 <= old_cell < self.n and 0 <= new_cell < self.n:
            if new_cell not in self.adjacency[old_cell]:
                self.adjacency[old_cell].add(new_cell)
                self.adjacency[new_cell].add(old_cell)
                self.total_edges += 1
        # Update recency timestamp for the new active cell
        self.recency[new_cell] = tick

    def stamp_reward(self, cell_idx: int, amount: float = 1.0):
        """Stamp a food reward at the given place cell AND all nearby cells.
        Creates a wide, persistent reward zone that's hard to miss during replay diffusion."""
        if 0 <= cell_idx < self.n:
            # Stamp the exact cell strongly
            self.reward_values[cell_idx] += amount
            self.persistent_rewards[cell_idx] = max(self.persistent_rewards[cell_idx], amount)

            # Also stamp ALL cells within 1.5m radius (area beacon)
            centre = self.centres[cell_idx]
            dists = np.sqrt(np.sum((self.centres - centre) ** 2, axis=1))
            nearby_mask = dists < 1.5
            falloff = np.clip(1.0 - dists[nearby_mask] / 1.5, 0.0, 1.0)
            self.reward_values[nearby_mask] += amount * 0.5 * falloff
            self.persistent_rewards[nearby_mask] = np.maximum(
                self.persistent_rewards[nearby_mask], amount * 0.3 * falloff
            )

    # ── Hippocampal Replay: Reward Diffusion ───────────────────────────

    def diffuse_rewards(self, gamma: float = 0.9, decay: float = 0.99995, n_sweeps: int = 5):
        """
        Multi-sweep value iteration through the place cell graph.
        Propagates reward values backwards from food-stamped cells through
        connected cells, creating a navigation gradient.

        This models hippocampal sharp-wave ripple replay (Foster & Wilson, 2006):
        during quiet wakefulness, the hippocampus replays experienced trajectories
        in reverse, propagating reward information backwards through the spatial map.

        Key improvements over naive single-sweep:
          - 5 sweeps per tick: reward propagates 5 graph hops per control cycle
          - Decay 0.99995: rewards persist for ~20,000 ticks (11 minutes) not 1,000 ticks (33s)
          - Persistent floor: reward_values never drop below persistent_rewards
          - Higher gamma (0.9): signal retains 90% per hop instead of 85%

        Args:
            gamma: Discount factor (0.9 = reward drops 10% per graph hop)
            decay: Per-tick decay of standing reward stamps (very slow forgetting)
            n_sweeps: Number of value iteration sweeps per call
        """
        # Decay standing rewards very slowly
        self.reward_values *= decay

        # Persistent floor: rewards never drop below the persistent memory
        self.reward_values = np.maximum(self.reward_values, self.persistent_rewards * 0.5)

        # Multi-sweep value iteration: V(cell) = max(R(cell), γ * max(V(neighbors)))
        values = self.nav_values.copy()
        for sweep in range(n_sweeps):
            new_values = self.reward_values.copy()
            for cell_idx in range(self.n):
                neighbors = self.adjacency[cell_idx]
                if neighbors:
                    max_neighbor_val = max(values[n] for n in neighbors)
                    new_values[cell_idx] = max(new_values[cell_idx], gamma * max_neighbor_val)
            values = new_values
        self.nav_values = values

    # ── Navigation Targets ─────────────────────────────────────────────

    def get_novelty_target(self, current_cell: int, current_tick: int):
        """
        Returns the center coordinates of the most novel (least recently visited)
        neighbor of the current cell in the graph.

        Used in EXPLORE mode — drives CARL toward unvisited areas.

        Returns:
            (target_x, target_y) or None if no graph neighbors exist
        """
        neighbors = self.adjacency.get(current_cell, set())
        if not neighbors:
            return None

        # Find the neighbor with the oldest recency (most novel)
        best_cell = -1
        best_novelty = -1
        for n in neighbors:
            novelty = current_tick - self.recency[n]
            if novelty > best_novelty:
                best_novelty = novelty
                best_cell = n

        if best_cell >= 0:
            return self.centres[best_cell]
        return None

    def get_replay_target(self, current_cell: int):
        """
        Returns the center coordinates of the highest-value neighbor
        in the reward diffusion map.

        Used in SURVIVE mode — guides CARL toward remembered food locations
        through the maze, following the reward gradient.

        Returns:
            (target_x, target_y, value) or None if no gradient exists
        """
        neighbors = self.adjacency.get(current_cell, set())
        if not neighbors:
            return None

        best_cell = -1
        best_value = -1.0
        for n in neighbors:
            if self.nav_values[n] > best_value:
                best_value = self.nav_values[n]
                best_cell = n

        if best_cell >= 0 and best_value > 0.001:
            return self.centres[best_cell][0], self.centres[best_cell][1], best_value
        return None

    def get_graph_stats(self) -> dict:
        """Return statistics about the topological graph for diagnostics."""
        connected = sum(1 for i in range(self.n) if len(self.adjacency[i]) > 0)
        max_degree = max(len(self.adjacency[i]) for i in range(self.n))
        return {
            'edges': self.total_edges,
            'connected_cells': connected,
            'max_degree': max_degree,
            'max_nav_value': float(np.max(self.nav_values)),
            'mean_nav_value': float(np.mean(self.nav_values[self.nav_values > 0.001])) if np.any(self.nav_values > 0.001) else 0.0,
            'reward_cells': int(np.sum(self.reward_values > 0.01)),
            'persistent_beacons': int(np.sum(self.persistent_rewards > 0.01)),
        }


# ── Full Hippocampal Navigation System ───────────────────────────────────────
class HippocampalNavigator:
    """
    Integrates grid cells + place cells into a unified navigation system.
    Provides:
      - Path integration (dead reckoning from velocity)
      - Position estimation (even without GPS)
      - Uncertainty quantification (how confident is the navigation?)
      - Remapping signal (detects if the robot is in a familiar vs novel location)
    """

    def __init__(self):
        # Three grid modules: Nobel-Prize-winning multi-scale architecture
        self.modules = [
            GridCellModule(scale=0.8,  orientation_deg=0,  n_cells=64),
            GridCellModule(scale=1.2,  orientation_deg=30, n_cells=64),
            GridCellModule(scale=1.8,  orientation_deg=60, n_cells=64),
        ]
        self.n_grid   = sum(m.n for m in self.modules)  # 192 total

        self.places   = PlaceCellLayer(n_place=400)

        # Grid-to-place weights (learned online)
        self.W_gp = np.random.randn(400, self.n_grid) * 0.01

        # Running position estimate (from path integration)
        self.x_est = 0.4
        self.y_est = 0.4

        # Theta oscillation (4-8 Hz, gates plasticity)
        self.theta_phase = 0.0
        self.theta_freq  = 6.0   # Hz

        # Navigation uncertainty (0=certain, 1=lost)
        self.uncertainty = 1.0

        # Spatial novelty signal (high = never been here)
        self.novelty     = 1.0

        # Visit count map for uncertainty
        self.visit_map   = {}

    def reset(self, x, y):
        """Called at episode start — anchor all modules to known position."""
        for m in self.modules:
            m.reset(x, y)
        self.x_est = x
        self.y_est = y
        self.uncertainty = 1.0

    # ── Per-step update ───────────────────────────────────────
    def step(self, x_actual, y_actual, vx, vy, dt, learn=True):
        """
        Full hippocampal update.

        Args:
            x_actual, y_actual: GPS position (from MuJoCo)
            vx, vy: velocity (from MuJoCo sensor)
            dt: timestep
            learn: whether to update weights

        Returns:
            dict with grid_activity, place_activity, x_est, y_est, uncertainty, novelty, theta
        """
        # ── Theta oscillation ─────────────────────────────────
        self.theta_phase = (self.theta_phase + 2*math.pi * self.theta_freq * dt) % (2*math.pi)
        theta_gate = 0.5 + 0.5 * math.cos(self.theta_phase)  # 0→1 at peak

        # ── Grid cell path integration ────────────────────────
        for m in self.modules:
            m.integrate(vx, vy, dt)

        # ── Grid cell firing (GPS-grounded every step) ────────
        grid_acts = []
        for m in self.modules:
            # Use actual position to keep grid cells calibrated
            act = m.fire(x_actual, y_actual)
            grid_acts.append(act)
        grid_vec = np.concatenate(grid_acts)  # (192,)

        # ── Place cell firing from position ───────────────────
        place_act = self.places.fire_from_position(x_actual, y_actual)

        # ── Path integration estimate (from grid phase only) ──
        pi_estimates = []
        for m in self.modules:
            pi_estimates.append(m.pi_phase.copy())
        pi_mean = np.mean(pi_estimates, axis=0)
        pi_error = math.sqrt((pi_mean[0]-x_actual)**2 + (pi_mean[1]-y_actual)**2)

        # ── Hebbian grid-to-place learning (at theta peak) ────
        if learn and theta_gate > 0.8:
            # Oja's rule: maintain unit-length weight vectors
            outer = np.outer(place_act, grid_vec)            # (200, 192)
            self.W_gp += 0.002 * theta_gate * (outer - place_act[:, None] * self.W_gp)
            self.W_gp = np.clip(self.W_gp, -2.0, 2.0)

        # ── Position estimate from place cells ────────────────
        x_pc, y_pc = self.places.decode_position()
        if x_pc is not None:
            # Blend GPS + place cell decode
            self.x_est = 0.9 * x_actual + 0.1 * x_pc
            self.y_est = 0.9 * y_actual + 0.1 * y_pc

        # ── Uncertainty ───────────────────────────────────────
        # Low when place cells fire strongly and path integration error is small
        peak_rate  = float(np.max(place_act))
        self.uncertainty = float(np.clip(
            (1.0 - peak_rate) * 0.7 + min(pi_error / 2.0, 1.0) * 0.3, 0., 1.))

        # ── Novelty ───────────────────────────────────────────
        key = (int(x_actual * 2), int(y_actual * 2))  # 0.5m bins
        self.visit_map[key] = self.visit_map.get(key, 0) + 1
        self.novelty = float(np.clip(1.0 / math.log1p(self.visit_map[key]), 0., 1.))

        return {
            'grid': grid_vec,
            'place': place_act,
            'x_est': self.x_est,
            'y_est': self.y_est,
            'uncertainty': self.uncertainty,
            'novelty': self.novelty,
            'theta': theta_gate,
            'pi_error': pi_error,
        }

    # ── Learning rate gated by theta ─────────────────────────
    def theta_learning_rate(self, base_lam=0.990):
        """
        At theta peak: high plasticity (lower lambda = more learning).
        At theta trough: consolidation (higher lambda = slower forgetting).
        """
        theta_gate = 0.5 + 0.5 * math.cos(self.theta_phase)
        return float(np.clip(base_lam - theta_gate * 0.012, 0.970, 0.999))

    # ── Curiosity boost from novelty ─────────────────────────
    def curiosity_boost(self, base_curiosity):
        """
        Novelty amplifies curiosity — drives exploration of unfamiliar areas.
        This is the ACh-mediated novelty signal from the locus coeruleus.
        """
        return float(np.clip(base_curiosity * (1.0 + self.novelty * 0.8), 0.05, 1.0))

    # ── Danger prediction from place cell memory ─────────────
    def predict_danger_at(self, x, y, danger_memory):
        """
        Given a location, use place cells to estimate danger
        from spatial memory (what the robot associates with that location).
        """
        place_at_target = self.places.fire_from_position(x, y)
        # danger_memory: (200,) vector — danger value associated with each place cell
        return float(np.dot(place_at_target, danger_memory) / (np.sum(place_at_target) + 1e-6))

    def update_place_danger(self, danger_memory, x, y, danger_val):
        """Update the place cell danger association at current location."""
        place_act = self.places.fire_from_position(x, y)
        danger_memory += 0.05 * place_act * (danger_val - danger_memory)
        return np.clip(danger_memory, 0.0, 1.0)
