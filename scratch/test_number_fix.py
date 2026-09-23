import pptx, re

NUMERICAL_REPLACEMENTS = [
    # Multi-word / specific expressions
    ("Stage 21 Spatial Architecture & Multi Seed Scorecard", "Stage 2.1 Spatial Architecture & Multi-Seed Scorecard"),
    ("Stage 21 Spatial Architecture", "Stage 2.1 Spatial Architecture"),
    ("Stage 22 predictive world model", "Stage 2.2 predictive world model"),
    ("Stage 22", "Stage 2.2"),
    
    # Slide 22
    ("01–05 m/s", "0.1–0.5 m/s"),
    ("01-05 m/s", "0.1–0.5 m/s"),
    ("02–15 rad/s", "0.2–1.5 rad/s"),
    ("02-15 rad/s", "0.2–1.5 rad/s"),
    
    # Slide 23
    ("μ = 035", "μ = 0.35"),
    ("u = 035", "μ = 0.35"),
    
    # Slide 24
    ("μ ∈ [005, 10]", "μ ∈ [0.05, 1.0]"),
    ("u ∈ [005, 10]", "μ ∈ [0.05, 1.0]"),
    ("μ = 005–025", "μ = 0.05–0.25"),
    ("μ = 005-025", "μ = 0.05–0.25"),
    ("slip σ reaches 982%", "slip σ reaches 98.2%"),
    ("slip reaches 982%", "slip reaches 98.2%"),
    ("μ = 050–10", "μ = 0.50–1.0"),
    ("μ = 050-10", "μ = 0.50–1.0"),
    ("stabilizes at 241%", "stabilizes at 24.1%"),
    
    # Slide 26
    ("drift = 00650 m", "drift = 0.0650 m"),
    ("within 022 m", "within 0.22 m"),
    ("drift = 00570 m", "drift = 0.0570 m"),
    ("(022 m gate)", "(within 0.22 m target gate)"),
    
    # Slide 27
    ("homing error = 0065 m", "homing error = 0.065 m"),
    ("homing error = 0071 m", "homing error = 0.071 m"),
    ("homing error = 0062 m", "homing error = 0.062 m"),
    ("homing error = 0059 m", "homing error = 0.059 m"),
    ("homing error = 0057 m", "homing error = 0.057 m"),
    ("Target < 022 m", "Target < 0.22 m"),
    ("drift < 002 rad/s", "drift < 0.02 rad/s"),
    
    # Slide 28 Table Cells
    ("≥ 090", "≥ 0.90"),
    ("R² = 09613", "R² = 0.9613"),
    ("≥ 080", "≥ 0.80"),
    ("R² = 08466", "R² = 0.8466"),
    ("≥ 050", "≥ 0.50"),
    ("R² = 05377", "R² = 0.5377"),
    ("ROC AUC = 0995", "ROC-AUC = 0.995"),
    ("ROC AUC", "ROC-AUC"),
    ("< 150%", "< 15.0%"),
    ("Drift = 818%", "Drift = 8.18%"),
    ("> 035", "> 0.35"),
    ("Δ = 0442", "Δ = 0.442"),
    ("≤ 100 ms", "≤ 10.0 ms"),
    ("≤ 100 ", "≤ 10.0 "),
    ("212 ms", "2.12 ms"),
    ("212 ", "2.12 "),
    
    # Slide 29
    ("Δ ≥ +030 m", "Δ ≥ +0.30 m"),
    ("R² ≥ 050", "R² ≥ 0.50"),
    ("mean R² = 0772", "mean R² = 0.772"),
]

def fix_text(txt):
    for bad, good in NUMERICAL_REPLACEMENTS:
        if bad in txt:
            txt = txt.replace(bad, good)
    return txt

prs = pptx.Presentation('D:/ebca/310_Stage3_Updated_Final.pptx')

# Check Slide 28 specifically
s28 = prs.slides[27]
for sh in s28.shapes:
    if sh.has_table and len(sh.table.rows) == 8:
        tbl = sh.table
        gate_data = [
            ("Gate 1: Body Proprioception", "Forward Velocity (v) R²", "≥ 0.90", "R² = 0.9613", "PASS"),
            ("Gate 2: Angular Gyroscope", "Rotational Velocity (ω) R²", "≥ 0.80", "R² = 0.8466", "PASS"),
            ("Gate 3: Dynamic Sonar Range", "Virtual Rays Range R²", "≥ 0.50", "R² = 0.5377", "PASS"),
            ("Gate 4: Collision Prediction", "Imminent Contact ROC-AUC", "≥ 0.90", "ROC-AUC = 0.995", "PASS"),
            ("Gate 5: Multi-Step Stability", "5-Step Rollout Drift", "< 15.0%", "Drift = 8.18%", "PASS"),
            ("Gate 6: Causal Sensitivity", "Action Intervention Δ", "> 0.35", "Δ = 0.442", "PASS"),
            ("Gate 7: Compute Latency", "Inference Cycle Time", "≤ 10.0 ms", "2.12 ms", "PASS"),
        ]
        for r_idx, row in enumerate(gate_data):
            for c_idx, val in enumerate(row):
                cell = tbl.cell(r_idx + 1, c_idx)
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        r.text = val
                        break

# Process all shapes
for s_idx, s in enumerate(prs.slides):
    for sh in s.shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.text = fix_text(r.text)
        elif sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    for p in cell.text_frame.paragraphs:
                        for r in p.runs:
                            r.text = fix_text(r.text)

prs.save('d:/ebca/scratch/test_fixed_numbers.pptx')
print("Saved test_fixed_numbers.pptx!")
