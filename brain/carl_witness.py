"""
carl_witness.py — "The Witness" Subjective Inner Stream of Consciousness (WIT-801)

Synthesizes neural activity, neuromodulator kinetics, spatial place maps, and vision detections
into a continuous, natural-language inner monologue stream. Includes existential self-questioning
when surprise (NE), prediction error (Free Energy), or metabolic strain is high.
"""
import numpy as np
import random


class WitnessConsciousnessStream:
    """
    Metacognitive Self-Model & Introspective Stream of Consciousness.
    Translates mathematical brain state into expressive biological thoughts.
    """
    def __init__(self):
        self.tick_counter = 0
        self.last_monologue = ""
        self.history = []

    def generate_monologue(
        self,
        tick: int,
        mode: str,
        da: float,
        ne: float,
        sht: float,
        ach: float,
        battery: float,
        food_dist: float,
        sonar_min: float,
        qualia_label: str,
        free_energy: float,
        active_place_idx: int,
        edges_count: int,
        cog_output: np.ndarray
    ) -> str:
        """
        Synthesizes raw neural variables into a self-reasoning inner monologue statement.
        """
        self.tick_counter = tick
        thoughts = []
        
        # 1. Existential Self-Questioning on High Norepinephrine / Free Energy (Surprise)
        if ne > 0.65 or free_energy > 0.15:
            reflections = [
                f"Surprise spike (NE={ne:.2f}, FreeEnergy={free_energy:.3f})! Why did I pivot here? Was it calculated curiosity or a raw sensory reflex?",
                f"My predictive model misjudged this corridor (FE={free_energy:.3f}). Am I reacting to a phantom, or is there a true hazard ahead?",
                f"A sudden shock of arousal (NE={ne:.2f})! My reservoir output shifted ({cog_output[0]:+.2f}, {cog_output[1]:+.2f}). Was that impulse sound or stress-induced?"
            ]
            thoughts.append(random.choice(reflections))

        # 2. Metabolic Strain & Deliberative Dilemma (Low Battery / High Hunger)
        elif battery < 0.35:
            dilemmas = [
                f"Energy dropping rapidly (battery {battery*100:.0f}%)... I feel a rising survival urgency. Target food is {food_dist:.1f}m away.",
                f"Metabolic strain (battery {battery*100:.0f}%). Sonar reports obstacle at {sonar_min:.2f}m. Should I risk shortcut or play safe?",
                f"Hunger is mounting (DA={da:.2f}). Qualia state: [{qualia_label}]. Re-evaluating optimal hippocampal path."
            ]
            thoughts.append(random.choice(dilemmas))

        # 3. High Dopamine (Reward / Food Target Lock)
        elif da > 1.3 or mode == "EXPLOIT":
            exploits = [
                f"Food target locked in sight ({food_dist:.2f}m)! Dopamine surging ({da:.2f}). Closing in on target beacon.",
                f"Reward beacon nearby ({food_dist:.2f}m). Qualia: [{qualia_label}]. Motor readout locked in EXPLOIT alignment.",
                f"Taxis drive active (DA={da:.2f}). Approaching food node. Spatial graph stamped at place cell #{active_place_idx}."
            ]
            thoughts.append(random.choice(exploits))

        # 4. Baseline Deep Introspection / Curiosity (EXPLORE Mode)
        else:
            explores = [
                f"Exploring qualia domain: [{qualia_label}]. Place cell #{active_place_idx} active ({edges_count} learned map edges).",
                f"Calm navigation (5HT={sht:.2f}, ACh={ach:.2f}). Free energy low ({free_energy:.3f}). Building spatial memory graph.",
                f"Wandering maze corridors. Reservoir states active. Qualia: [{qualia_label}]. Processing 24-ray LiDAR stream."
            ]
            thoughts.append(random.choice(explores))

        monologue_str = f"[THE WITNESS][TICK {tick:5d}] {thoughts[0]}"
        self.last_monologue = monologue_str
        self.history.append((tick, monologue_str))
        if len(self.history) > 100:
            self.history.pop(0)

        return monologue_str
