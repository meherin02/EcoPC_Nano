# EcoPC local demonstration

1. Unplug the buzzer. Keep Nano USB connected. Close Serial Monitor and stop serial_test.py.
2. Stop run_simulation.py before uploading firmware (COM3 has one owner).
3. Open arduino/EcoPC/EcoPC.ino in Arduino IDE. Select the same Nano processor/COM3 settings that worked before. Upload. Close Serial Monitor afterward.
4. In a terminal in this folder: .\.venv\Scripts\python.exe run_simulation.py
5. In a SECOND terminal: .\.venv\Scripts\python.exe app.py
6. Open http://127.0.0.1:5000 and hard-refresh once. The page fetches updates without navigation or mouse activity.

PIR needs 60 seconds after reset. Opening COM3 can reset the Nano. A disconnected sensor shows UNKNOWN; a stopped monitor shows stale/offline. Reconnect retries every 3 seconds on the configured COM port.

LED wiring: D9 through a 220-ohm resistor to the green LED anode, D10 through a separate 220-ohm resistor to the red LED anode, and both cathodes to GND. The current firmware uses OUTPUT mode, so each LED needs its own series resistor. Green steady = recent input; green blinking = background CPU activity; red blinking = suspected waste; both off = unknown/host disconnected. Motion alone does not mark the computer active.

Buzzer is disconnected and disabled by default. Its polarity/5V supply test is complete, but current/type is unknown. Safe GPIO drive requires a verified load within Nano limits or a suitable driver. Software cannot substitute for this. Do not set the firmware verification flag until hardware has been checked.

Idle threshold is config.py IDLE_LIMIT_SECONDS (30 s). CPU threshold is 25%. High CPU is only a heuristic; reading/video may occur with low CPU and no input. This project issues suspected-waste warnings and does not shut down the PC. Energy is an 80 W assumption, not actual measured savings. Energy totals reset per monitoring restart; old saved totals remain timestamped until a new session writes.

Stop both terminal processes with Ctrl+C. Run only one monitoring process and one Flask process. Existing database and backups are preserved.

## Sensor contribution
With idle input and low CPU, PIR motion produces IDLE_WITH_MOTION and withholds the waste warning. After PIR goes low, TEMPORARILY_AWAY lasts until GRACE_PERIOD_SECONDS of continuous no-motion; only then can suspected waste be reported. Motion returning clears a waste warning without resetting keyboard/mouse idle or declaring ACTIVE. Missing PIR data with low CPU produces UNKNOWN. Input or CPU activity retain priority. Passersby may postpone warnings; PIR cannot distinguish them from seated users. Both LEDs are off in IDLE_WITH_MOTION, TEMPORARILY_AWAY and UNKNOWN. No Nano re-upload is needed: the new motion-idle state maps to its existing IDLE command.
