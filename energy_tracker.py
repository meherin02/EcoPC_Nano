import time

from energy import estimate_avoidable_energy_wh
from config import MONITOR_INTERVAL_SECONDS


class EnergyTracker:
    def __init__(self):
        self.waste_seconds = 0.0
        self.previous_time = time.monotonic()
        self.previous_state = None

    def update(self, state):
        now = time.monotonic()
        elapsed = now - self.previous_time

        # Skip long gaps, such as PC sleep or a paused program.
        maximum_gap = max(5.0, MONITOR_INTERVAL_SECONDS * 5)

        if (
            self.previous_state == "ENERGY_WASTE_SUSPECTED"
            and 0 <= elapsed <= maximum_gap
        ):
            self.waste_seconds += elapsed

        self.previous_time = now
        self.previous_state = state

    def get_estimated_energy_wh(self):
        return estimate_avoidable_energy_wh(
            self.waste_seconds
        )