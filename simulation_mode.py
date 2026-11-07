import time

class SimulatedPresence:
    """Provide fake presence data and track absence duration."""

    def __init__(self):
        self.presence = None
        self.away_since = None

    def set_presence(self, presence):
        if presence is False:
            # Start timing only when changing to away.
            if self.presence is not False:
                self.away_since = time.monotonic()
        else:
            # Present or unknown: clear the absence timer.
            self.away_since = None

        self.presence = presence

    def get_presence(self):
        return self.presence

    def get_absence_seconds(self):
        if self.presence is None:
            return None

        if self.presence is True:
            return 0.0

        return time.monotonic() - self.away_since


if __name__ == "__main__":
    sensor = SimulatedPresence()

    print("EcoPC presence simulation")
    print("1 = User present")
    print("0 = User away")
    print("u = Sensor unavailable")
    print("q = Quit")

    try:
        while True:
            choice = input("\nEnter your choice: ").strip().lower()

            if choice == "q":
                print("Simulation stopped.")
                break

            elif choice == "1":
                sensor.set_presence(True)

            elif choice == "0":
                sensor.set_presence(False)

            elif choice == "u":
                sensor.set_presence(None)

            else:
                print("Invalid choice. Enter 1, 0, u, or q.")
                continue

            presence = sensor.get_presence()
            absence = sensor.get_absence_seconds()

            if absence is None:
                print("Away duration: UNKNOWN")
            else:
                print(f"Away duration: {absence:.1f} seconds")

            if presence is True:
                print("Presence: PRESENT")

            elif presence is False:
                print("Presence: AWAY")

            else:
                print("Presence: UNKNOWN")

    except (KeyboardInterrupt, EOFError):
        print("\nSimulation stopped.")