import time
from pynput import keyboard, mouse


class InputMonitor:
    """Track time since the last keyboard or mouse action."""

    def __init__(self):
        # Start counting from when this monitor is created.
        self.last_input_time = time.monotonic()

        self.keyboard_listener = keyboard.Listener(
            on_press=self.record_activity
        )

        self.mouse_listener = mouse.Listener(
            on_move=self.record_activity,
            on_click=self.record_activity,
            on_scroll=self.record_activity
        )

    def record_activity(self, *args):
        # Different input events provide different arguments.
        # We only need to know that activity happened.
        self.last_input_time = time.monotonic()

    def start(self):
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def get_idle_seconds(self):
        return time.monotonic() - self.last_input_time

    def stop(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()


# Run this demonstration only when this file is run directly.
if __name__ == "__main__":
    monitor = InputMonitor()

    try:
        monitor.start()
        print("Monitoring keyboard and mouse activity.")
        print("Leave both untouched to watch idle time increase.")
        print("Press Ctrl+C in this terminal to stop.")

        while True:
            print(f"Input idle time: {monitor.get_idle_seconds():.1f} seconds")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

    except Exception as error:
        print(f"Monitoring failed: {error}")

    finally:
        monitor.stop()