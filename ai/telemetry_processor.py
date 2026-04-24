"""
ai/telemetry_processor.py
--------------------------
Cleans and preprocesses raw telemetry data using pandas.
Converts raw sensor readings into scaled features for the ML model.
"""

import pandas as pd
import numpy as np


# Feature columns the model expects (must match model.py training order)
FEATURE_COLUMNS = [
    "mileage",
    "rpm_idle",
    "rpm_load",
    "oil_life_pct",
    "tire_pressure",
    "coolant_temp_c",
    "battery_voltage",
    "brake_pad_pct",
]

# Safe operating ranges — values outside these are clipped and flagged
SAFE_RANGES = {
    "mileage":         (0,      250000),
    "rpm_idle":        (500,    1500),
    "rpm_load":        (1000,   8000),
    "oil_life_pct":    (0,      100),
    "tire_pressure":   (20,     40),
    "coolant_temp_c":  (70,     130),
    "battery_voltage": (11.0,   15.0),
    "brake_pad_pct":   (0,      100),
}


def clean(record: dict) -> pd.DataFrame:
    """
    Takes a single telemetry dict, validates and clips outliers,
    and returns a single-row DataFrame ready for model prediction.
    """
    df = pd.DataFrame([record])

    # Keep only known feature columns, fill missing with median-safe defaults
    defaults = {
        "mileage":         30000,
        "rpm_idle":        850,
        "rpm_load":        3000,
        "oil_life_pct":    60,
        "tire_pressure":   32,
        "coolant_temp_c":  92,
        "battery_voltage": 13.8,
        "brake_pad_pct":   65,
    }
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = defaults[col]
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(defaults[col])

    # Clip to safe ranges
    for col, (lo, hi) in SAFE_RANGES.items():
        if col in df.columns:
            df[col] = df[col].clip(lo, hi)

    return df[FEATURE_COLUMNS]


def clean_batch(records: list) -> pd.DataFrame:
    """Clean a list of telemetry dicts and return a multi-row DataFrame."""
    frames = [clean(r) for r in records]
    return pd.concat(frames, ignore_index=True)


def extract_warnings(record: dict) -> list:
    """
    Returns a list of human-readable warning strings based on sensor values.
    Used to populate the recommendation text in the health report.
    """
    warnings = []

    oil = record.get("oil_life_pct", 100)
    if oil < 20:
        warnings.append("Oil life critical — immediate change required")
    elif oil < 40:
        warnings.append("Oil change due soon")

    brake = record.get("brake_pad_pct", 100)
    if brake < 20:
        warnings.append("Brake pads critically worn — replace immediately")
    elif brake < 40:
        warnings.append("Brake pads nearing end of life")

    temp = record.get("coolant_temp_c", 90)
    if temp > 110:
        warnings.append("Engine running hot — check coolant system")

    rpm_idle = record.get("rpm_idle", 800)
    if rpm_idle > 1100:
        warnings.append("High idle RPM — possible fuel or sensor issue")

    battery = record.get("battery_voltage", 13.8)
    if battery < 12.0:
        warnings.append("Battery voltage low — check charging system")

    tire = record.get("tire_pressure", 32)
    if tire < 28:
        warnings.append("Tire pressure low — inspect for leaks")

    return warnings
