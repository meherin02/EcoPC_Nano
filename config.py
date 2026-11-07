# Start with simulated presence. No Arduino is needed.
SIMULATION_MODE = False

# Arduino connection settings — used later.
SERIAL_PORT = "COM3"
BAUD_RATE = 9600

# Demo timings, measured in seconds.
GRACE_PERIOD_SECONDS = 10
IDLE_LIMIT_SECONDS = 20

# CPU usage at or above this percentage suggests background work.
CPU_HIGH_THRESHOLD = 70.0

# How often the program checks activity and saves monitoring logs.
MONITOR_INTERVAL_SECONDS = 1
DATABASE_LOG_INTERVAL_SECONDS = 1 

# Assumed PC power for estimating avoidable energy.
# This is an estimate, not a measured electricity reading.
ASSUMED_PC_POWER_WATTS = 80.0