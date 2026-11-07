from decision import decide_state
from config import (
    GRACE_PERIOD_SECONDS,
    IDLE_LIMIT_SECONDS,
    CPU_HIGH_THRESHOLD
)


def run_tests():
    # Each test contains:
    # description, presence, CPU, idle time, absence time, expected state
    tests = [
        (
            "User present",
            True, 3.0, 0, 0,
            "ACTIVE"
        ),
        (
            "User recently left",
            False, 3.0, 0, 0,
            "TEMPORARILY_AWAY"
        ),
        (
            "User away with high CPU",
            False, CPU_HIGH_THRESHOLD, IDLE_LIMIT_SECONDS,
            GRACE_PERIOD_SECONDS,
            "BACKGROUND_WORK"
        ),
        (
            "User away, input idle, CPU low",
            False, 0.0, IDLE_LIMIT_SECONDS,
            GRACE_PERIOD_SECONDS,
            "ENERGY_WASTE_SUSPECTED"
        ),
        (
            "User away, input still recent",
            False, 0.0, 0,
            GRACE_PERIOD_SECONDS,
            "IDLE"
        ),
        (
            "Presence unavailable",
            None, 3.0, 60, 60,
            "UNKNOWN"
        ),
        (
            "User returns",
            True, 3.0, 0, 0,
            "ACTIVE"
        ),
        (
            "CPU reading unavailable while away",
            False, None, IDLE_LIMIT_SECONDS,
            GRACE_PERIOD_SECONDS,
            "UNKNOWN"
        )
    ]

    passed = 0

    for description, presence, cpu, idle, absence, expected in tests:
        actual, explanation = decide_state(
            presence=presence,
            cpu_usage=cpu,
            idle_seconds=idle,
            absence_seconds=absence
        )

        if actual == expected:
            print(f"PASS: {description} -> {actual}")
            passed += 1
        else:
            print(f"FAIL: {description}")
            print(f"  Expected: {expected}")
            print(f"  Received: {actual}")
            print(f"  Explanation: {explanation}")

    print(f"\nResults: {passed}/{len(tests)} tests passed.")

    if passed != len(tests):
        raise SystemExit(1)


if __name__ == "__main__":
    run_tests()