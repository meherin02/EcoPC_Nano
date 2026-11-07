# EcoPC

EcoPC helps a lab user decide when an idle Windows PC can go to sleep. It combines keyboard and mouse idle time, CPU load, and motion from an Arduino-connected PIR sensor. A local dashboard explains the decision, and a blinking red LED and short PC speaker beep draw attention to suspected waste.

## What makes it different

A timer tells you how long it has been since the last input. EcoPC adds context before recommending sleep. An unattended machine may still be running a demanding task. Someone may also be near an idle machine without touching its controls.

For example, leave the keyboard and mouse untouched until a warning appears. Then wave near the PIR sensor. EcoPC changes from **Energy waste suspected** to **Idle with motion** and clears the red warning while the input idle counter keeps rising. Touching the mouse is what brings the state back to **Active**. This makes the sensor's effect visible and explainable.

## What the dashboard does

- Shows the current state and its reason, PIR motion, input idle time, CPU and memory usage, and recent state changes.
- Sends the decision to the Nano over USB. Green is steady for active use and blinks during background work. Red blinks during suspected waste.
- Plays a short alert through the Windows PC speakers approximately every five seconds during a warning.
- Offers **Sleep now** with confirmation, plus **Keep awake** and **Resume warnings**. Keep awake pauses EcoPC warnings for 15 minutes. Windows manages its own sleep timer.
- Estimates energy during warning periods using an assumed power draw. Includes an illustrative lab cost example and marks readings stale when monitoring stops.

## How it works

**HC-SR501 PIR → Arduino Nano → USB serial → Python monitor → SQLite → Flask dashboard**

The Python monitor combines PIR readings with input idle time and CPU load, then sends its decision back to the Nano for LED control. Flask serves the dashboard on the same PC and reads the stored results.

| Condition | Decision |
| --- | --- |
| Recent keyboard or mouse input | **ACTIVE** |
| Input idle and CPU at or above the threshold | **BACKGROUND_WORK** |
| Input idle, CPU below the threshold, and PIR detects movement | **IDLE_WITH_MOTION** |
| Input idle and CPU low, but the no-motion window is still running | **TEMPORARILY_AWAY** |
| Input idle, CPU low, and continuous no motion for the configured window | **ENERGY_WASTE_SUSPECTED** |
| Required readings unavailable | **UNKNOWN** |

The demo settings in `config.py` are **20 seconds** of input idle, **10 seconds** of continuous no motion, and a **70% CPU threshold**. Changes between background work and suspected waste require a sustained CPU change for 10 seconds. Recent input takes priority.

## Hardware

You need a Windows PC, a Classic Arduino Nano, a data-capable USB cable, an HC-SR501 PIR, a breadboard, jumpers, one green LED, one red LED, and two 220 Ω resistors.

| Connection | Wiring |
| --- | --- |
| PIR power and signal | VCC → Nano 5V, GND → Nano GND, OUT → D2. Follow the sensor's pin labels. |
| Green LED | D9 → 220 Ω resistor → LED anode. Cathode → GND. |
| Red LED | D10 → separate 220 Ω resistor → LED anode. Cathode → GND. |

The current sketch configures D9 and D10 as outputs. Use one series resistor per LED and a common ground. The PC speaker provides the audible alert.

## Run it on Windows

1. Open [EcoPC.ino](arduino/EcoPC/EcoPC.ino) in Arduino IDE. Select **Arduino Nano**, the processor setting that matches your board, and the Nano's COM port. Upload the sketch. Close Serial Monitor when done so Python can open the port.
2. Open PowerShell in the project folder. Set `SERIAL_PORT` in `config.py` to your Nano's port. The demo uses `COM3` at `9600` baud.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run_simulation.py
```

3. In a second terminal in the same folder, start Flask.

```powershell
.\.venv\Scripts\python.exe app.py
```

4. Open [the local dashboard](http://127.0.0.1:5000/). Allow about 60 seconds for PIR warmup after the Nano resets.

Stop the processes with **Ctrl+C** in their terminals. Stop monitoring before uploading a new sketch. To try the decision flow without the Nano, set `SIMULATION_MODE = True`, restart both processes, and use `p`, `a`, or `u` in the monitoring terminal to simulate motion, no motion, or unknown. Sleep now is disabled in simulation mode.

## Try the demo

1. Move the mouse to show **Active** and the steady green LED.
2. Leave the PC and the sensor field still. When input idle, CPU, and no-motion conditions are met, show the warning, red blink, and speaker beep.
3. Wave near the PIR without touching the computer. Show **Idle with motion** and the warning clearing. Use **Recent events** to review the transitions.

## Reading the energy estimate

EcoPC multiplies suspected-waste time by an assumed **80 W** draw. For example, 30 minutes in warning corresponds to **40 Wh of estimated energy during that interval**. To quantify actual savings, measure the same equipment in idle and sleep and record how much idle time was replaced with sleep.

PIR detects movement and can miss a person sitting still. A passerby can delay a warning, and low CPU use can occur while someone reads or watches a video. The dashboard presents a recommendation, with sleep triggered by the user's confirmation.

## Project layout

| File | Purpose |
| --- | --- |
| [`arduino/EcoPC/EcoPC.ino`](arduino/EcoPC/EcoPC.ino) | PIR readings and LED outputs |
| `run_simulation.py`, `arduino_presence.py` | Monitoring loop and USB serial communication |
| `monitor.py`, `cpu_monitor.py`, `decision.py` | Input and workload monitoring and state decisions |
| `energy_tracker.py`, `database.py` | Session estimates and SQLite storage |
| `app.py`, `windows_sleep.py`, `templates/`, `static/` | Local dashboard and user-confirmed power controls |

