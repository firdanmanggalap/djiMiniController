"""Pure conversion from raw DJI axis values to Xbox int16, with calibration."""

from dataclasses import dataclass

from .protocol import CENTER, SCALE_NUM, SCALE_DEN

XBOX_MAX = 32767
XBOX_MIN = -32768


@dataclass
class AxisCal:
    invert: bool = False
    deadzone: float = 0.0   # fraction 0..0.30
    trim: int = 0           # raw-unit offset that shifts the neutral point
    range: float = 1.0      # sensitivity multiplier 0.5..1.5


def _apply_deadzone(n: float, dz: float) -> float:
    if dz <= 0:
        return n
    if abs(n) < dz:
        return 0.0
    sign = 1.0 if n > 0 else -1.0
    return sign * (abs(n) - dz) / (1.0 - dz)


def convert_axis(raw: int, cal: AxisCal) -> int:
    """raw DJI int -> trim -> normalize -> deadzone -> range -> invert -> Xbox int16."""
    vjoy = (raw - CENTER - cal.trim) * SCALE_NUM // SCALE_DEN   # ~0..32768
    n = vjoy / 32768.0 * 2.0 - 1.0                              # ~[-1, 1], neutral 0
    n = _apply_deadzone(n, cal.deadzone)
    n *= cal.range
    if cal.invert:
        n = -n
    value = int(round(n * XBOX_MAX))
    return max(XBOX_MIN, min(XBOX_MAX, value))


def convert_camera(raw: int, cal: AxisCal) -> int:
    """Map a calibrated axis value to the 0..255 trigger range."""
    v = convert_axis(raw, cal)
    trig = int(round(((v + 32768) / 65535.0) * 255))
    return max(0, min(255, trig))
