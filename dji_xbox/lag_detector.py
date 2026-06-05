"""Pure rolling packet-rate + lag detector. Caller supplies monotonic times."""

from dataclasses import dataclass


@dataclass
class LagEvent:
    kind: str          # "lag"
    message: str
    hz: float
    interval_ms: float
    drops: int


class LagDetector:
    def __init__(self, expected_interval=0.011, lag_factor=3.0,
                 lag_floor_ms=50.0, window=30):
        self.expected_interval = expected_interval
        self.lag_factor = lag_factor
        self.lag_floor = lag_floor_ms / 1000.0
        self.window = window
        self._last = None
        self._intervals = []
        self.hz = 0.0
        self.interval_ms = 0.0
        self.total_drops = 0

    def record(self, t: float):
        """Record a packet arrival time. Return a LagEvent on a lag spike, else None."""
        if self._last is None:
            self._last = t
            return None
        interval = t - self._last
        self._last = t
        self.interval_ms = interval * 1000.0

        self._intervals.append(interval)
        if len(self._intervals) > self.window:
            self._intervals.pop(0)
        avg = sum(self._intervals) / len(self._intervals)
        self.hz = (1.0 / avg) if avg > 0 else 0.0

        threshold = max(self.lag_floor, self.expected_interval * self.lag_factor)
        if interval > threshold:
            drops = max(1, round(interval / self.expected_interval) - 1)
            self.total_drops += drops
            return LagEvent(
                kind="lag",
                message=(f"LAG: gap {self.interval_ms:.0f}ms "
                         f"(normal ~{self.expected_interval*1000:.0f}ms), drop {drops}"),
                hz=self.hz,
                interval_ms=self.interval_ms,
                drops=drops,
            )
        return None
