"""
tests/stage3_2R_task_fixtures.py — Stage 3.2-R Non-LOS Task Family Fixtures
Classification: [STAGE 3.2-R FIXTURE] Authoritative Task Geometries for Non-LOS Equivalence & Evaluation

Defines 5 genuine non-LOS task families satisfying observational equivalence:
- Family 1: Blind-Corner Distal-Connectivity Ambiguity
- Family 2: Irreversible Cul-de-Sac Funnel Trap (Spawn at x=-0.40m, 0 contacts)
- Family 3: Sonically Symmetric Locations (P1 vs P2) with Divergent Optimal Actions
- Family 4: Occluded Dogleg Arterial vs Blind Detour
- Family 5: Multi-Turn Sensory Blackout / Sonic Corridor Symmetry
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

ENV_DIR = repo_root / "world" / "stage3_2R_environments"


def generate_all_fixtures() -> Dict[str, Tuple[Path, Path]]:
    """Returns the 5 task family environments located in world/stage3_2R_environments."""
    fixtures = {
        "family_1": (ENV_DIR / "family1_condA.xml", ENV_DIR / "family1_condB.xml"),
        "family_2": (ENV_DIR / "family2_condA.xml", ENV_DIR / "family2_condB.xml"),
        "family_3": (ENV_DIR / "family3_layout.xml", ENV_DIR / "family3_layout.xml"),
        "family_4": (ENV_DIR / "family4_condA.xml", ENV_DIR / "family4_condB.xml"),
        "family_5": (ENV_DIR / "family5_layout.xml", ENV_DIR / "family5_layout.xml"),
    }
    for fam, (pA, pB) in fixtures.items():
        assert pA.exists(), f"Missing fixture: {pA}"
        assert pB.exists(), f"Missing fixture: {pB}"
    return fixtures


if __name__ == "__main__":
    fixtures = generate_all_fixtures()
    print("Stage 3.2-R Fixtures Verified:")
    for fam, (pA, pB) in fixtures.items():
        print(f"  {fam}: A={pA.name}, B={pB.name}")
