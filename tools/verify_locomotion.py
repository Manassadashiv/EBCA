"""
verify_locomotion.py — Quick headless test to verify CARL actually moves toward food.

Runs 300 ticks (~10 seconds) and checks:
1. Does CARL move from origin? (position delta > 0.5m)
2. Does food distance decrease over time? (approaching food)
3. Does CARL eat at least 1 food? (reaching the beacon)
4. Is NE panic under control? (average NE < 0.5)
"""

import sys
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from carl_simulation import CarlSimulationRunner
import math

def main():
    print("\n" + "=" * 64)
    print("  CARL-DX LOCOMOTION VERIFICATION (Headless)")
    print("=" * 64)

    runner = CarlSimulationRunner(open_space=False, headless=True)

    positions = []
    food_dists = []
    ne_values = []
    modes = []

    for tick in range(600):
        runner.step(step_physics=True)

        rx, ry, ryaw = runner.hal.get_robot_pos()
        food_pos = runner.hal.get_food_pos()
        fd = math.sqrt((rx - food_pos[0])**2 + (ry - food_pos[1])**2)

        positions.append((rx, ry))
        food_dists.append(fd)
        ne_values.append(runner.endocrine.NE)

        mode = runner.endocrine.get_behavioral_mode(
            runner.hal.battery_level,
            fd < 5.0
        )
        modes.append(mode)

        if tick % 30 == 0:
            print(f"  Tick {tick:3d}: pos=({rx:.2f},{ry:.2f}) food_dist={fd:.2f}m "
                  f"NE={runner.endocrine.NE:.2f} mode={mode} eaten={runner.food_eaten_total}")

    # Analysis
    print("\n" + "-" * 64)
    print("  VERIFICATION RESULTS")
    print("-" * 64)

    start_pos = np.array(positions[0])
    end_pos = np.array(positions[-1])
    total_displacement = np.linalg.norm(end_pos - start_pos)
    
    # Track total distance traveled (path length, not just displacement)
    total_path = 0.0
    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i-1][0]
        dy = positions[i][1] - positions[i-1][1]
        total_path += math.sqrt(dx**2 + dy**2)

    min_food_dist = min(food_dists)
    avg_ne = np.mean(ne_values)
    max_ne = max(ne_values)
    food_eaten = runner.food_eaten_total
    exploit_pct = modes.count("EXPLOIT") / len(modes) * 100.0

    results = []
    
    # Test 1: Movement
    moved = total_path > 0.5
    results.append(("MOVEMENT", moved, f"Path length: {total_path:.2f}m (need > 0.5m)"))
    
    # Test 2: Food approach
    initial_food_dist = food_dists[0]
    approached = min_food_dist < initial_food_dist * 0.6  # Got at least 40% closer
    results.append(("FOOD APPROACH", approached, 
                     f"Initial: {initial_food_dist:.2f}m -> Min: {min_food_dist:.2f}m"))
    
    # Test 3: Food eaten
    ate = food_eaten > 0
    results.append(("FOOD EATEN", ate, f"Total eaten: {food_eaten}"))
    
    # Test 4: NE stability
    stable = avg_ne < 0.5
    results.append(("NE STABILITY", stable, f"Avg NE: {avg_ne:.3f}, Max NE: {max_ne:.3f}"))
    
    # Test 5: EXPLOIT mode usage
    exploiting = exploit_pct > 50.0
    results.append(("EXPLOIT MODE", exploiting, f"EXPLOIT: {exploit_pct:.0f}% of ticks"))

    all_pass = True
    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}: {detail}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("  >>> ALL CHECKS PASSED -- CARL is locomoting and eating! <<<")
    else:
        print("  Some checks failed. See details above.")

    print(f"\n  Final stats: displacement={total_displacement:.2f}m, "
          f"path={total_path:.2f}m, eaten={food_eaten}, "
          f"rls_updates={runner.reservoir.total_rls_updates}")
    print("=" * 64)

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
