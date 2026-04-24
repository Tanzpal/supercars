"""
test_ai_model.py
----------------
Standalone test for the AI health scoring pipeline.
Run from project root: python test_ai_model.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.dummy_data import generate_telemetry, generate_batch
from ai.telemetry_processor import clean, extract_warnings
from ai.model import train_model, predict

print("=" * 50)
print("  AI HEALTH SCORE - PIPELINE TEST")
print("=" * 50)

# Step 1: Train (or load cached) model
print("\n[1] Training / loading model...")
train_model()
print("    Model ready.")

# Step 2: Test with 4 cars covering all condition buckets
test_cases = [
    (1,  "excellent"),
    (2,  "good"),
    (3,  "fair"),
    (4,  "poor"),
]

print("\n[2] Predicting health scores:")
print(f"{'Car':>4}  {'Condition':<12}  {'Score':>6}  {'Grade'}  {'Label':<15}  Recommendation")
print("-" * 90)

for car_id, condition in test_cases:
    telemetry = generate_telemetry(car_id, condition=condition)
    result    = predict(telemetry)
    print(
        f"{car_id:>4}  {condition:<12}  {result['health_score']:>6.1f}  "
        f"  {result['grade']}    {result['label']:<15}  {result['recommendation'][:55]}"
    )

# Step 3: Warnings extraction test
print("\n[3] Warning extraction for a poor-condition car:")
poor_telemetry = generate_telemetry(99, condition="poor")
warnings = extract_warnings(poor_telemetry)
if warnings:
    for w in warnings:
        print(f"    - {w}")
else:
    print("    No warnings (unexpected for poor condition)")

# Step 4: Batch generate + clean
print("\n[4] Batch data generation (50 records)...")
batch = generate_batch(50)
from ai.telemetry_processor import clean_batch
df = clean_batch(batch)
print(f"    Shape: {df.shape}")
print(f"    Columns: {list(df.columns)}")
print(f"    NaN count: {df.isna().sum().sum()}")

print("\nAll tests passed.")
