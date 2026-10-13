"""
carl_gemini_er.py — High-Level Gemini 1.5 ER (Embodied Reasoning) Cortex for CARL-DX

Combines cloud-based Gemini 1.5 Pro / Flash vision-language-action reasoning
with local on-device Fallback Layer (Layer 6 World Model).

Features:
- Submits camera frame snapshots + telemetry to Gemini 1.5 Pro/Flash
- Generates high-level spatial strategy & introspective monologue ("The Witness")
- Graceful local fallback if offline or no GEMINI_API_KEY present.
"""

import os
import json
import base64
import time
import numpy as np

class GeminiEmbodiedReasoner:
    def __init__(self, api_key: str = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.enabled = False

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                self.enabled = True
                print(f"[GEMINI-ER] Initialized Gemini 1.5 ER Cortex ({self.model_name})")
            except Exception as e:
                print(f"[GEMINI-ER] Gemini API init warning: {e}. Using local World Model fallback.")
        else:
            print("[GEMINI-ER] No GEMINI_API_KEY found. Operating in Local World Model Fallback Mode.")

    def reason(self, image_bytes: bytes, telemetry: dict) -> dict:
        """
        Query Gemini 1.5 ER with camera frame + sensor telemetry.
        Returns dict with strategic goal, wall risk, and monologue.
        """
        if not self.enabled:
            return self._local_fallback(telemetry)

        prompt = f"""
You are the Embodied Reasoning (ER) Cortex for CARL-DX, a cyber-companion robot.
Telemetry:
- Battery: {telemetry.get('battery', 1.0):.2f}
- Dopamine (DA): {telemetry.get('da', 1.0):.2f}
- Noradrenaline (NE): {telemetry.get('ne', 0.1):.2f}
- Min Wall Distance: {telemetry.get('min_wall_dist', 5.0):.2f}m
- Current Qualia State: {telemetry.get('qualia', 'Exploring')}

Analyze the visual frame and telemetry. Respond ONLY in valid JSON format:
{{
  "thought": "short stream-of-consciousness monologue",
  "recommended_action": "EXPLOIT_FOOD" | "AVOID_WALL" | "EXPLORE_MAZE",
  "wall_risk": float (0.0 to 1.0)
}}
"""
        try:
            import google.generativeai as genai
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            response = self.model.generate_content([prompt, image_part])
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            parsed = json.loads(text)
            return parsed
        except Exception as e:
            print(f"[GEMINI-ER] Fallback trigger (API error: {e})")
            return self._local_fallback(telemetry)

    def _local_fallback(self, telemetry: dict) -> dict:
        """Local rule-based / World Model fallback when offline."""
        min_wall = telemetry.get('min_wall_dist', 5.0)
        da = telemetry.get('da', 1.0)
        
        if min_wall < 1.2:
            return {
                "thought": "Wall detected within 1.2m safety zone. Initiating smooth repelling arc.",
                "recommended_action": "AVOID_WALL",
                "wall_risk": min(1.0, (1.2 - min_wall) / 1.2)
            }
        elif da > 0.8:
            return {
                "thought": "Reward target locked. Accelerating along optimal trajectory.",
                "recommended_action": "EXPLOIT_FOOD",
                "wall_risk": 0.0
            }
        else:
            return {
                "thought": "Exploring maze corridors. Monitoring 24-ray LiDAR stream.",
                "recommended_action": "EXPLORE_MAZE",
                "wall_risk": 0.0
            }
