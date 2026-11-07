from config import ASSUMED_PC_POWER_WATTS


def estimate_avoidable_energy_wh(waste_seconds):
    """Estimate energy from time spent in suspected waste."""

    if waste_seconds < 0:
        raise ValueError("Waste duration cannot be negative.")

    waste_hours = waste_seconds / 3600

    return ASSUMED_PC_POWER_WATTS * waste_hours


if __name__ == "__main__":
    # Example durations only, not actual monitoring results.
    example_durations = [0, 60, 3600]

    print(f"Assumed PC power: {ASSUMED_PC_POWER_WATTS} W")
    print("Example calculations:\n")

    for seconds in example_durations:
        energy_wh = estimate_avoidable_energy_wh(seconds)

        print(
            f"{seconds} seconds of suspected waste "
            f"-> {energy_wh:.2f} Wh"
        )