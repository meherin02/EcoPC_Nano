import time
import serial
from config import SERIAL_PORT, BAUD_RATE
from simulation_mode import SimulatedPresence

class ArduinoPresence(SimulatedPresence):
    def __init__(self):
        super().__init__()
        self.connection = None
        self.buffer = ''
        self.last_reading = None
        self.retry_at = 0
        self.last_command = 0
        self._connect()

    def _disconnect(self):
        if self.connection is not None:
            self.connection.close()
        self.connection = None
        self.buffer = ''
        self.last_reading = None
        self.set_presence(None)
        self.retry_at = time.monotonic() + 3

    def _connect(self):
        try:
            self.connection = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0, write_timeout=0.2)
        except (serial.SerialException, OSError):
            self._disconnect()

    def update(self):
        if self.connection is None:
            if time.monotonic() >= self.retry_at:
                self._connect()
            return
        try:
            size = self.connection.in_waiting
            if size > 16384:
                self.connection.reset_input_buffer()
                self.buffer = ''
                self.last_reading = None
            elif size:
                self.buffer += self.connection.read(size).decode('utf-8', errors='replace')
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    message = line.strip()
                    if message in ('Motion detected', 'No motion', 'MOTION:1', 'MOTION:0'):
                        self.set_presence(message in ('Motion detected', 'MOTION:1'))
                        self.last_reading = time.monotonic()
                if len(self.buffer) > 1024:
                    self.buffer = ''
            if self.last_reading is None or time.monotonic() - self.last_reading > 3:
                self.set_presence(None)
        except (serial.SerialException, OSError):
            self._disconnect()

    def get_presence(self):
        self.update()
        return super().get_presence()

    def get_absence_seconds(self):
        return super().get_absence_seconds()

    def send_state(self, state):
        if self.connection is None or time.monotonic() - self.last_command < 0.5:
            return
        try:
            # Current Nano firmware already accepts IDLE (both LEDs off).
            wire_state = 'IDLE' if state in ('IDLE_WITH_MOTION', 'KEEP_AWAKE') else state
            self.connection.write(('STATE:' + wire_state + '\n').encode('ascii'))
            self.last_command = time.monotonic()
        except (serial.SerialException, OSError):
            self._disconnect()

    def close(self):
        if self.connection is not None:
            try:
                self.connection.write(b'STATE:UNKNOWN\n')
            except (serial.SerialException, OSError):
                pass
        self._disconnect()
