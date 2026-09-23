"""Check all embedded images for dark backgrounds and convert if needed."""
import numpy as np
from PIL import Image
from pathlib import Path

EVIDENCE_DIR = Path(r"D:\ebca\evidence")

# All images actually embedded in the deck
embedded_images = [
    EVIDENCE_DIR / "jntuh_logo.png",
    EVIDENCE_DIR / "stage1_safety_sweep_phase_space.png",
    EVIDENCE_DIR / "stage1_discovery_heatmap.png",
    EVIDENCE_DIR / "figure1_friction_gradient_sweep_white.png",
    EVIDENCE_DIR / "figure1_physical_vs_internal_trajectory_white.png",
    EVIDENCE_DIR / "figure7_hd_bump_dynamics.png",
    EVIDENCE_DIR / "stage2_2_grounded" / "figures" / "fig1_counterfactual_branching.png",
    EVIDENCE_DIR / "carl_stage2_3_empirical_benchmark_white.png",
]

print("=" * 70)
print("IMAGE BACKGROUND AUDIT")
print("=" * 70)

needs_fix = []
for img_path in embedded_images:
    if not img_path.exists():
        print(f"  MISSING: {img_path.name}")
        continue
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img)
    
    # Sample corners (10x10 patches)
    corners = [
        arr[:10, :10],       # top-left
        arr[:10, -10:],      # top-right
        arr[-10:, :10],      # bottom-left
        arr[-10:, -10:],     # bottom-right
    ]
    corner_means = [c.mean() for c in corners]
    avg_corner = np.mean(corner_means)
    overall_mean = arr.mean()
    
    is_dark = avg_corner < 128
    status = "DARK BG - NEEDS FIX" if is_dark else "OK (white/light bg)"
    print(f"  {img_path.name:50s} corner_avg={avg_corner:.1f}  overall={overall_mean:.1f}  -> {status}")
    if is_dark:
        needs_fix.append(img_path)

print("-" * 70)
if needs_fix:
    print(f"Found {len(needs_fix)} images needing white-background conversion:")
    for p in needs_fix:
        print(f"  -> {p}")
    
    # Convert dark images to white background
    for img_path in needs_fix:
        img = Image.open(img_path).convert("RGB")
        arr = np.array(img, dtype=np.float64)
        
        # Invert: 255 - pixel
        inverted = 255.0 - arr
        
        # Contrast stretch to use full range
        lo, hi = np.percentile(inverted, [1, 99])
        if hi > lo:
            stretched = np.clip((inverted - lo) / (hi - lo) * 255, 0, 255)
        else:
            stretched = inverted
        
        out = Image.fromarray(stretched.astype(np.uint8))
        
        # Save with _white suffix
        out_path = img_path.parent / (img_path.stem + "_white" + img_path.suffix)
        out.save(str(out_path), dpi=(300, 300))
        print(f"  CONVERTED: {img_path.name} -> {out_path.name}")
else:
    print("All embedded images already have light/white backgrounds. No conversion needed.")

print("=" * 70)
