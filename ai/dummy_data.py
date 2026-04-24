"""
ai/dummy_data.py
----------------
Generates realistic dummy telemetry data for supercar health simulation.
Used for testing and demo purposes when real OBD/IoT data isn't available.
"""

import random


# Presets for different car conditions
CONDITION_PRESETS = {
    "excellent": {
        "mileage_range":    (0, 15000),
        "rpm_idle_range":   (750, 850),
        "rpm_load_range":   (2000, 3500),
        "oil_life_range":   (80, 100),
        "tire_pressure":    (32, 35),
        "coolant_temp":     (85, 95),
        "battery_v":        (13.8, 14.4),
        "brake_pad_pct":    (75, 100),
    },
    "good": {
        "mileage_range":    (15000, 40000),
        "rpm_idle_range":   (800, 950),
        "rpm_load_range":   (2500, 4500),
        "oil_life_range":   (50, 80),
        "tire_pressure":    (30, 34),
        "coolant_temp":     (90, 100),
        "battery_v":        (13.2, 14.0),
        "brake_pad_pct":    (50, 75),
    },
    "fair": {
        "mileage_range":    (40000, 80000),
        "rpm_idle_range":   (900, 1100),
        "rpm_load_range":   (3000, 5500),
        "oil_life_range":   (25, 50),
        "tire_pressure":    (28, 32),
        "coolant_temp":     (95, 108),
        "battery_v":        (12.6, 13.4),
        "brake_pad_pct":    (25, 50),
    },
    "poor": {
        "mileage_range":    (80000, 200000),
        "rpm_idle_range":   (1000, 1400),
        "rpm_load_range":   (4000, 7000),
        "oil_life_range":   (0, 25),
        "tire_pressure":    (24, 30),
        "coolant_temp":     (105, 120),
        "battery_v":        (11.5, 12.8),
        "brake_pad_pct":    (0, 25),
    }
}


def generate_telemetry(car_id: int, condition: str = None) -> dict:
    """
    Generate a single snapshot of telemetry data for a car.

    Args:
        car_id:    The car's database ID (used as seed for consistency).
        condition: Force a condition preset ('excellent','good','fair','poor').
                   If None, picks randomly weighted toward 'good'.

    Returns:
        dict of telemetry readings.
    """
    if condition is None:
        condition = random.choices(
            ["excellent", "good", "fair", "poor"],
            weights=[20, 45, 25, 10]
        )[0]

    preset = CONDITION_PRESETS.get(condition, CONDITION_PRESETS["good"])

    # Use car_id as part of seed so same car always gets similar results
    rng = random.Random(car_id * 7 + 42)

    def rnd(lo, hi):
        return round(rng.uniform(lo, hi), 2)

    return {
        "car_id":         car_id,
        "condition_hint": condition,
        "mileage":        round(rng.uniform(*preset["mileage_range"])),
        "rpm_idle":       round(rng.uniform(*preset["rpm_idle_range"])),
        "rpm_load":       round(rng.uniform(*preset["rpm_load_range"])),
        "oil_life_pct":   rnd(*preset["oil_life_range"]),
        "tire_pressure":  rnd(*preset["tire_pressure"]),
        "coolant_temp_c": rnd(*preset["coolant_temp"]),
        "battery_voltage":rnd(*preset["battery_v"]),
        "brake_pad_pct":  rnd(*preset["brake_pad_pct"]),
    }


def generate_batch(n: int = 200) -> list:
    """Generate a batch of telemetry records for training the model."""
    records = []
    for i in range(n):
        condition = random.choices(
            ["excellent", "good", "fair", "poor"],
            weights=[20, 45, 25, 10]
        )[0]
        record = generate_telemetry(car_id=i + 1, condition=condition)
        records.append(record)
    return records
