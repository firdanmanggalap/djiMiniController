"""App configuration: per-axis calibration + connection prefs, JSON persisted."""

import json
import os
from dataclasses import dataclass, field, asdict

from .mapping import AxisCal

AXIS_NAMES = ["lv", "lh", "rv", "rh", "cam"]


def default_axes() -> dict:
    return {
        "lv": AxisCal(invert=True, deadzone=0.05),
        "lh": AxisCal(invert=False, deadzone=0.05),
        "rv": AxisCal(invert=True, deadzone=0.05),
        "rh": AxisCal(invert=False, deadzone=0.05),
        "cam": AxisCal(invert=False, deadzone=0.02),
    }


@dataclass
class AppConfig:
    port_hint: str | None = None
    output_enabled: bool = True
    log_to_file: bool = False
    cam_low_button: str | None = None    # Xbox button held when dial hits 0%
    cam_high_button: str | None = None   # Xbox button held when dial hits 100%
    axes: dict = field(default_factory=default_axes)


DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)


def load(path=DEFAULT_PATH) -> AppConfig:
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return AppConfig()

    raw_axes = data.get("axes", {})
    axes = {}
    for name in AXIS_NAMES:
        a = raw_axes.get(name, {})
        axes[name] = AxisCal(
            invert=bool(a.get("invert", False)),
            deadzone=float(a.get("deadzone", 0.0)),
            trim=int(a.get("trim", 0)),
            range=float(a.get("range", 1.0)),
        )
    return AppConfig(
        port_hint=data.get("port_hint"),
        output_enabled=bool(data.get("output_enabled", True)),
        log_to_file=bool(data.get("log_to_file", False)),
        cam_low_button=data.get("cam_low_button"),
        cam_high_button=data.get("cam_high_button"),
        axes=axes,
    )


def save(config: AppConfig, path=DEFAULT_PATH) -> None:
    data = {
        "port_hint": config.port_hint,
        "output_enabled": config.output_enabled,
        "log_to_file": config.log_to_file,
        "cam_low_button": config.cam_low_button,
        "cam_high_button": config.cam_high_button,
        "axes": {name: asdict(cal) for name, cal in config.axes.items()},
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
