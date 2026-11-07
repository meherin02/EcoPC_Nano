import time
import msvcrt
import sqlite3
import winsound
from energy_tracker import EnergyTracker

from database import initialize_database, save_log, save_event, save_energy_summary, get_warning_pause_until
from config import (
    SIMULATION_MODE,
    MONITOR_INTERVAL_SECONDS,
    DATABASE_LOG_INTERVAL_SECONDS,
)
from arduino_presence import ArduinoPresence
from monitor import InputMonitor
from cpu_monitor import get_system_usage
from simulation_mode import SimulatedPresence
from decision import decide_state, StateStabilizer


def run_simulation():
    input_monitor = InputMonitor()
    presence_source = None
    energy_tracker = EnergyTracker()
    state_stabilizer = StateStabilizer(hold_seconds=10)

    try:
        if SIMULATION_MODE:
            presence_source = SimulatedPresence()
            print("EcoPC simulation mode")
            print("p = Present | a = Away | u = Unknown | q = Quit")
        else:
            presence_source = ArduinoPresence()
            print("EcoPC Arduino mode")
            print("Sensor ready hote 60 seconds lagte pare.")
            print("q = Quit")

        print("Control key use korte terminal selected rakho.\n")

        input_monitor.start()

        # Prepare CPU measurement.
        get_system_usage()
        time.sleep(MONITOR_INTERVAL_SECONDS)

        previous_state = None
        last_log_time = None
        next_warning_beep = 0.0

        try:
            initialize_database()
            save_energy_summary(0.0, 0.0)
        except sqlite3.Error as error:
            print(f"Database setup failed: {error}")
            print("Monitoring will continue; logging may fail.")

        while True:
            if msvcrt.kbhit():
                choice = msvcrt.getwch().lower()

                if choice == "q":
                    break
                elif SIMULATION_MODE and choice == "p":
                    presence_source.set_presence(True)
                elif SIMULATION_MODE and choice == "a":
                    presence_source.set_presence(False)
                elif SIMULATION_MODE and choice == "u":
                    presence_source.set_presence(None)

            presence = presence_source.get_presence()
            absence = presence_source.get_absence_seconds()
            idle = input_monitor.get_idle_seconds()
            usage = get_system_usage()

            state, explanation = decide_state(
                presence=presence,
                cpu_usage=usage["cpu_usage"],
                idle_seconds=idle,
                absence_seconds=absence,
            )
            state, explanation = state_stabilizer.update(state, explanation, motion=presence)
            if state == 'ENERGY_WASTE_SUSPECTED':
                try:
                    pause_remaining = get_warning_pause_until() - time.time()
                except sqlite3.Error as error:
                    print(f'Could not read warning pause: {error}')
                else:
                    if pause_remaining > 0:
                        state = 'KEEP_AWAKE'
                        explanation = f'EcoPC warning paused for {pause_remaining:.0f} more seconds.' 
            if isinstance(presence_source, ArduinoPresence):
                presence_source.send_state(state)
            energy_tracker.update(state)

            # Use the PC speaker for a short audible warning every five seconds.
            if state != 'ENERGY_WASTE_SUSPECTED':
                next_warning_beep = 0.0
            elif time.monotonic() >= next_warning_beep:
                next_warning_beep = time.monotonic() + 5.0
                try:
                    winsound.Beep(1050, 150)
                except RuntimeError as error:
                    print(f'Windows speaker alert unavailable: {error}')

            print(
                f"Suspected waste: "
                f"{energy_tracker.waste_seconds:.1f}s | "
                f"Estimated energy: "
                f"{energy_tracker.get_estimated_energy_wh():.3f} Wh"
            )

            # Save an event when the state changes.
            if state != previous_state:
                message = (
                    f"{previous_state or 'START'} -> {state}: "
                    f"{explanation}"
                )

                try:
                    save_event("STATE_CHANGE", message)
                    print(f"Event saved: {message}")
                except sqlite3.Error as error:
                    print(f"Could not save event: {error}")

                previous_state = state

            # Save monitoring readings periodically.
            now = time.monotonic()

            if (
                last_log_time is None
                or now - last_log_time >= DATABASE_LOG_INTERVAL_SECONDS
            ):
                try:
                    save_log(
                        presence=presence,
                        cpu_usage=usage["cpu_usage"],
                        memory_usage=usage["memory_usage"],
                        idle_seconds=idle,
                        absence_seconds=absence,
                        state=state,
                        decision=explanation,
                    )
                    save_energy_summary(
                        energy_tracker.waste_seconds,
                        energy_tracker.get_estimated_energy_wh(),
                    )
                    print("Monitoring reading saved.")
                except sqlite3.Error as error:
                    print(f"Could not save reading: {error}")

                last_log_time = now

            away_text = (
                "unknown"
                if absence is None
                else f"{absence:.0f}s"
            )

            print(
                f"CPU: {usage['cpu_usage']:.1f}% | "
                f"Idle: {idle:.0f}s | "
                f"Away: {away_text} | "
                f"State: {state}"
            )
            print(f"  {explanation}")

            time.sleep(MONITOR_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStop requested.")

    except Exception as error:
        print(f"\nMonitoring failed: {error}")

    finally:
        try:
            input_monitor.stop()
        finally:
            if isinstance(presence_source, ArduinoPresence):
                presence_source.close()

        print("Monitoring stopped.")


if __name__ == "__main__":
    run_simulation()