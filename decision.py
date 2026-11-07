from config import IDLE_LIMIT_SECONDS, CPU_HIGH_THRESHOLD, GRACE_PERIOD_SECONDS


def decide_state(presence, cpu_usage, idle_seconds, absence_seconds):
    """Fuse input, CPU activity, and sustained absence of PIR motion."""
    if idle_seconds is None:
        return 'UNKNOWN', 'Keyboard/mouse activity is unavailable.'
    if idle_seconds < IDLE_LIMIT_SECONDS:
        return 'ACTIVE', 'Recent keyboard or mouse activity detected.'
    if cpu_usage is None:
        return 'UNKNOWN', 'CPU usage is unavailable.'
    if cpu_usage >= CPU_HIGH_THRESHOLD:
        return 'BACKGROUND_WORK', 'Input is inactive, but CPU activity is high.'
    if presence is None:
        return 'UNKNOWN', 'Input is inactive and CPU is low; PIR data unavailable. Waste warning withheld.'
    if presence:
        return (
            'IDLE_WITH_MOTION',
            'Input is inactive and CPU is low, but nearby motion was detected. '
            'Waste warning withheld; motion does not prove PC use.'
        )
    if absence_seconds is None:
        return 'UNKNOWN', 'No-motion duration is unavailable. Waste warning withheld.'
    if absence_seconds < GRACE_PERIOD_SECONDS:
        return (
            'TEMPORARILY_AWAY',
            f'No motion for {absence_seconds:.1f}s; waiting for '
            f'{GRACE_PERIOD_SECONDS}s of continuous no-motion before considering a warning.'
        )
    return (
        'ENERGY_WASTE_SUSPECTED',
        f'Input idle for at least {IDLE_LIMIT_SECONDS}s, CPU below '
        f'{CPU_HIGH_THRESHOLD}%, and no PIR motion for at least '
        f'{GRACE_PERIOD_SECONDS}s. Possible waste; static reading/video can be missed.'
    )


class StateStabilizer:
    """Require sustained CPU evidence before switching idle classifications."""

    def __init__(self, hold_seconds=10):
        self.hold_seconds = hold_seconds
        self.state = None
        self.explanation = ''
        self.candidate = None
        self.since = 0.0

    def update(self, proposed, explanation, now=None, motion=None):
        import time
        if now is None:
            now = time.monotonic()
        # Never retain a waste warning when motion returns or is unavailable.
        if self.state == 'ENERGY_WASTE_SUSPECTED' and motion is not False:
            self.state = None
        cpu_states = {'BACKGROUND_WORK', 'ENERGY_WASTE_SUSPECTED'}
        if proposed not in cpu_states or self.state not in cpu_states:
            self.state, self.explanation = proposed, explanation
            self.candidate = None
        elif proposed == self.state:
            self.explanation = explanation
            self.candidate = None
        else:
            if self.candidate != proposed:
                self.candidate, self.since = proposed, now
            if now - self.since >= self.hold_seconds:
                self.state, self.explanation = proposed, explanation
                self.candidate = None
            else:
                return self.state, (
                    f'Keeping {self.state}: confirming sustained CPU change '
                    f'for {self.hold_seconds} seconds. '
                    'Energy totals follow this stabilized classification.'
                )
        return self.state, self.explanation
