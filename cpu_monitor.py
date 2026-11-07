import time
import psutil


def get_system_usage():
    """Return the current CPU and memory usage percentages."""
    return {
        "cpu_usage": psutil.cpu_percent(interval=None),
        "memory_usage": psutil.virtual_memory().percent
    }


if __name__ == "__main__":
    print("Monitoring CPU and memory usage.")
    print("Press Ctrl+C to stop.")

    # Prepare CPU measurement. The first reading is not useful.
    psutil.cpu_percent(interval=None)

    try:
        while True:
            # Allow one second between CPU measurements.
            time.sleep(1)

            usage = get_system_usage()

            print(
                f"CPU: {usage['cpu_usage']:.1f}% | "
                f"Memory: {usage['memory_usage']:.1f}%"
            )

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

    except Exception as error:
        print(f"CPU/memory monitoring failed: {error}")