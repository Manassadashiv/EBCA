import re
from pathlib import Path

content = Path("world/clean_arena.xml").read_text(encoding="utf-8")
pattern = re.compile(r'<geom name="food"[\s\S]*?<body name="drive_deck"')
clean_content = pattern.sub('<body name="drive_deck"', content)
print("Stripped successfully, gball_0 present:", "gball_0" in clean_content)
