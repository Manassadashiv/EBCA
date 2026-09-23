import json
from pathlib import Path

# Load slide dump
with open(r"d:\ebca\scratch\full_deck_45_dump.json", "r", encoding="utf-8") as f:
    deck = json.load(f)

print(f"Loaded {len(deck)} slides")
