"""
ai/model.py
-----------
Trains a scikit-learn RandomForestRegressor on synthetic telemetry data
to predict a vehicle health score (0-100).

The model is trained on first import (takes ~0.5s) and cached in memory.
Call `predict(telemetry_dict)` to get a health score + recommendation.
"""

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

from .dummy_data import generate_batch, CONDITION_PRESETS
from .telemetry_processor import clean, clean_batch, FEATURE_COLUMNS, extract_warnings

# -------------------------------------------------------
# Model cache path (persists the trained model to disk)
# -------------------------------------------------------
_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(_DIR, "health_model.joblib")
SCALER_PATH = os.path.join(_DIR, "health_scaler.joblib")

_model  = None
_scaler = None


# -------------------------------------------------------
# Score mapping — convert condition preset to target score
# -------------------------------------------------------
CONDITION_SCORES = {
    "excellent": 92,
    "good":      74,
    "fair":      50,
    "poor":      22,
}

# Add natural variance per condition so the model learns a range
CONDITION_VARIANCE = {
    "excellent": 8,
    "good":      10,
    "fair":      12,
    "poor":      10,
}


def _build_training_data(n: int = 400):
    """Generate synthetic training data with labels."""
    import random
    records = []
    labels  = []

    for i in range(n):
        condition = random.choices(
            list(CONDITION_SCORES.keys()),
            weights=[20, 45, 25, 10]
        )[0]

        record = generate_batch(1)[0]
        # Override condition so label matches features
        from .dummy_data import CONDITION_PRESETS
        preset = CONDITION_PRESETS[condition]
        rng = random.Random(i)

        record.update({
            "mileage":         round(rng.uniform(*preset["mileage_range"])),
            "rpm_idle":        round(rng.uniform(*preset["rpm_idle_range"])),
            "rpm_load":        round(rng.uniform(*preset["rpm_load_range"])),
            "oil_life_pct":    round(rng.uniform(*preset["oil_life_range"]), 1),
            "tire_pressure":   round(rng.uniform(*preset["tire_pressure"]), 1),
            "coolant_temp_c":  round(rng.uniform(*preset["coolant_temp"]), 1),
            "battery_voltage": round(rng.uniform(*preset["battery_v"]), 2),
            "brake_pad_pct":   round(rng.uniform(*preset["brake_pad_pct"]), 1),
        })

        base_score = CONDITION_SCORES[condition]
        variance   = CONDITION_VARIANCE[condition]
        label = float(np.clip(base_score + rng.uniform(-variance, variance), 0, 100))

        records.append(record)
        labels.append(label)

    return records, labels


def train_model(force: bool = False):
    """Train and cache the health scoring model."""
    global _model, _scaler

    if not force and os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        _model  = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        return

    print("Training AI health model...")
    records, labels = _build_training_data(n=600)

    X_raw = clean_batch(records)
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X_raw)
    y = np.array(labels)

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)

    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    _model  = model
    _scaler = scaler
    print(f"Model trained. OOB-like score: n/a (RandomForest). Saved to {MODEL_PATH}")


def _ensure_model():
    global _model, _scaler
    if _model is None or _scaler is None:
        train_model()


def _score_to_grade(score: float) -> dict:
    """Convert numeric score to grade, label, and colour."""
    if score >= 85:
        return {"grade": "A", "label": "Excellent",    "color": "#00b894"}
    elif score >= 70:
        return {"grade": "B", "label": "Good",         "color": "#0984e3"}
    elif score >= 50:
        return {"grade": "C", "label": "Fair",         "color": "#fdcb6e"}
    elif score >= 30:
        return {"grade": "D", "label": "Needs Service","color": "#e17055"}
    else:
        return {"grade": "F", "label": "Poor",         "color": "#d63031"}


def predict(telemetry: dict) -> dict:
    """
    Given a dict of raw telemetry values, return:
        {
          "health_score":    float (0-100),
          "grade":           str   ("A"-"F"),
          "label":           str   ("Excellent", "Good", ...),
          "color":           str   (hex color for UI),
          "warnings":        list  of warning strings,
          "recommendation":  str   (overall recommendation sentence)
        }
    """
    _ensure_model()

    X_raw   = clean(telemetry)
    X_scaled = _scaler.transform(X_raw)
    score   = float(np.clip(_model.predict(X_scaled)[0], 0, 100))
    score   = round(score, 1)

    grade_info = _score_to_grade(score)
    warnings   = extract_warnings(telemetry)

    if warnings:
        recommendation = "Action needed: " + "; ".join(warnings[:2]) + "."
    elif score >= 85:
        recommendation = "Vehicle is in excellent condition. No immediate action required."
    elif score >= 70:
        recommendation = "Vehicle is in good health. Maintain regular service schedule."
    elif score >= 50:
        recommendation = "Fair condition. Schedule a service check within the next month."
    else:
        recommendation = "Poor condition. Immediate professional inspection recommended."

    return {
        "health_score":   score,
        "grade":          grade_info["grade"],
        "label":          grade_info["label"],
        "color":          grade_info["color"],
        "warnings":       warnings,
        "recommendation": recommendation,
    }
