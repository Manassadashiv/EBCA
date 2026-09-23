"""
carl_epigenetics.py — Darwinian Epigenetic Evolution Engine (EPI-1001)

Evaluates lifetime fitness at the end of each organism lifespan (food eaten, path efficiency, survival duration).
Inherits and mutates reservoir sparsity masks, spectral radius (rho), and R-STDP learning rates across generations,
serializing epigenetic lineage into the persistent GIS state file.
"""
import numpy as np


class EpigeneticEvolutionEngine:
    """
    Cross-Generational Epigenetic Evolution Engine.
    """
    def __init__(self):
        self.generation = 1
        self.fitness_history = []
        self.best_fitness = 0.0
        
        # Epigenetic Hyperparameters (evolved across generations)
        self.spectral_radius = 1.00
        self.sparsity = 0.15
        self.r_stdp_lr = 0.0002
        self.tau_reservoir = 0.10

    def evaluate_lifespan_fitness(
        self,
        lifetime_ticks: int,
        food_eaten: int,
        distance_m: float,
        place_edges: int
    ) -> float:
        """
        Computes the Epigenetic Fitness Score for the completed lifespan.
        Fitness = 100 * food_eaten + 0.1 * place_edges + 0.01 * distance_m + 0.001 * lifetime_ticks
        """
        fitness = (
            100.0 * food_eaten +
            0.1 * place_edges +
            0.01 * distance_m +
            0.001 * lifetime_ticks
        )
        
        self.fitness_history.append(fitness)
        if fitness > self.best_fitness:
            self.best_fitness = fitness
            
        print(f"[EPI-1001] Lifespan #{self.generation} Fitness Score: {fitness:.2f} (Best: {self.best_fitness:.2f})")
        return fitness

    def evolve_next_generation(self, last_fitness: float) -> dict:
        """
        Mutates epigenetic parameters based on fitness performance.
        Higher fitness preserves parameters; lower fitness increases mutation range.
        """
        self.generation += 1
        
        # Mutation strength is inversely proportional to fitness relative to best
        mutation_scale = 0.05 if last_fitness >= self.best_fitness else 0.15
        rng = np.random.RandomState(self.generation)
        
        # Mutate Spectral Radius [0.85, 1.15]
        self.spectral_radius = float(np.clip(
            self.spectral_radius + rng.randn() * mutation_scale * 0.1,
            0.85, 1.15
        ))
        
        # Mutate Sparsity [0.10, 0.25]
        self.sparsity = float(np.clip(
            self.sparsity + rng.randn() * mutation_scale * 0.02,
            0.10, 0.25
        ))
        
        # Mutate R-STDP Learning Rate [0.0001, 0.0010]
        self.r_stdp_lr = float(np.clip(
            self.r_stdp_lr + rng.randn() * mutation_scale * 0.0001,
            0.0001, 0.0010
        ))
        
        print(f"[EPI-1001] Evolved Generation #{self.generation} Epigenetics: "
              f"spectral_radius={self.spectral_radius:.4f}, "
              f"sparsity={self.sparsity:.3f}, "
              f"r_stdp_lr={self.r_stdp_lr:.6f}")
              
        return {
            "generation": self.generation,
            "spectral_radius": self.spectral_radius,
            "sparsity": self.sparsity,
            "r_stdp_lr": self.r_stdp_lr,
            "best_fitness": self.best_fitness
        }
