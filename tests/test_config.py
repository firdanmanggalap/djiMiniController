from dji_xbox.config import AppConfig, load, save, AXIS_NAMES
from dji_xbox.mapping import AxisCal


def test_defaults_have_all_five_axes():
    cfg = AppConfig()
    assert set(cfg.axes.keys()) == set(AXIS_NAMES)
    assert cfg.axes["lv"].invert is True   # default matches original main.py
    assert cfg.axes["lh"].invert is False
    assert cfg.output_enabled is True


def test_missing_file_returns_defaults(tmp_path):
    cfg = load(tmp_path / "nope.json")
    assert isinstance(cfg, AppConfig)
    assert cfg.port_hint is None


def test_corrupt_file_returns_defaults(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{ not valid json")
    cfg = load(p)
    assert isinstance(cfg, AppConfig)


def test_save_then_load_round_trips(tmp_path):
    p = tmp_path / "config.json"
    cfg = AppConfig(port_hint="COM3", output_enabled=False)
    cfg.axes["rv"] = AxisCal(invert=False, deadzone=0.12, trim=7, range=1.25)
    save(cfg, p)
    loaded = load(p)
    assert loaded.port_hint == "COM3"
    assert loaded.output_enabled is False
    assert loaded.axes["rv"].deadzone == 0.12
    assert loaded.axes["rv"].trim == 7
    assert loaded.axes["rv"].range == 1.25
