import pytest

from PySide6.QtCore import QObject, Signal

from dji_xbox.main_window import MainWindow
from dji_xbox.config import AppConfig
from dji_xbox.gamepad_out import GamepadOut


class FakeLink(QObject):
    rawAxes = Signal(object)
    status = Signal(str, str)
    stats = Signal(float, float, int)
    log = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        pass


class FakePad:
    def __init__(self):
        self.calls = []

    def left_joystick(self, x_value, y_value):
        self.calls.append(("left", x_value, y_value))

    def right_joystick(self, x_value, y_value):
        self.calls.append(("right", x_value, y_value))

    def right_trigger(self, value):
        self.calls.append(("trigger", value))

    def update(self):
        self.calls.append(("update",))


def test_raw_axes_updates_sticks_and_sends_to_gamepad(qapp):
    pad = FakePad()
    cfg = AppConfig(output_enabled=True)
    for axis in cfg.axes.values():   # no invert -> display == physical == output
        axis.invert = False
    win = MainWindow(cfg, gamepad=GamepadOut(pad=pad), link=FakeLink())
    win.on_raw_axes({"lv": 1684, "lh": 364, "rv": 1024, "rh": 1684, "cam": 1024})
    # left stick fully up (lv=1684 -> +32767), full left (lh=364 -> -32767)
    assert win.left_stick.y > 0.9
    assert win.left_stick.x < -0.9
    # output forwarded + updated
    assert pad.calls[-1] == ("update",)


def test_output_off_does_not_send(qapp):
    pad = FakePad()
    cfg = AppConfig(output_enabled=False)
    win = MainWindow(cfg, gamepad=GamepadOut(pad=pad), link=FakeLink())
    win.on_raw_axes({"lv": 1024, "lh": 1024, "rv": 1024, "rh": 1024, "cam": 1024})
    assert pad.calls == []


def test_status_updates_pill_text(qapp):
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win.on_status("connected", "COM3")
    assert "COM3" in win.status_label.text()


def test_invert_reflected_in_display(qapp):
    # Toggling Invert must be immediately visible in the dot + H/V label.
    cfg = AppConfig()
    cfg.axes["lv"].invert = False
    win = MainWindow(cfg, gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win.on_raw_axes({"lv": 1684, "lh": 1024, "rv": 1024, "rh": 1024, "cam": 1024})
    assert win.left_stick.y > 0.9
    assert "V +" in win.left_vals.text()

    win.config.axes["lv"].invert = True
    win.on_raw_axes({"lv": 1684, "lh": 1024, "rv": 1024, "rh": 1024, "cam": 1024})
    assert win.left_stick.y < -0.9          # flipped immediately, no save needed
    assert "V -" in win.left_vals.text()


def test_invert_toggle_updates_config_and_saves(qapp, monkeypatch):
    saved = []
    monkeypatch.setattr("dji_xbox.main_window.save", lambda cfg, *a, **k: saved.append(cfg))
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win._invert_boxes["lh"].setChecked(True)
    assert win.config.axes["lh"].invert is True
    assert saved  # _save was triggered by the toggle


def test_deadzone_slider_updates_config(qapp, monkeypatch):
    monkeypatch.setattr("dji_xbox.main_window.save", lambda *a, **k: None)
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win._deadzone_sliders["rv"].setValue(20)
    assert abs(win.config.axes["rv"].deadzone - 0.20) < 1e-9


def test_reset_saves_only_once(qapp, monkeypatch):
    saves = []
    monkeypatch.setattr("dji_xbox.main_window.save", lambda *a, **k: saves.append(1))
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    saves.clear()
    win._reset_calibration()
    assert len(saves) == 1  # blockSignals prevents per-widget save storm


def test_toggle_output_updates_config(qapp, monkeypatch):
    monkeypatch.setattr("dji_xbox.main_window.save", lambda *a, **k: None)
    win = MainWindow(AppConfig(output_enabled=True), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win.output_btn.setChecked(False)
    win._toggle_output()
    assert win.config.output_enabled is False


def test_on_stats_updates_hz_label(qapp):
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win.on_stats(91.0, 11.0, 3)
    assert "91" in win.hz_label.text()


def test_range_slider_updates_config(qapp, monkeypatch):
    monkeypatch.setattr("dji_xbox.main_window.save", lambda *a, **k: None)
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win._range_sliders["lv"].setValue(150)
    assert abs(win.config.axes["lv"].range - 1.5) < 1e-9


def test_camera_bar_reflects_output(qapp):
    cfg = AppConfig()
    cfg.axes["cam"].invert = False
    win = MainWindow(cfg, gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win.on_raw_axes({"lv": 1024, "lh": 1024, "rv": 1024, "rh": 1024, "cam": 1684})
    # camera dial at max -> trigger bar near full
    assert win.cam_bar.value() > 200


def test_reset_resets_range_slider(qapp, monkeypatch):
    monkeypatch.setattr("dji_xbox.main_window.save", lambda *a, **k: None)
    win = MainWindow(AppConfig(), gamepad=GamepadOut(pad=FakePad()), link=FakeLink())
    win._range_sliders["lv"].setValue(150)
    win._reset_calibration()
    assert win._range_sliders["lv"].value() == 100   # back to range 1.0
    assert abs(win.config.axes["lv"].range - 1.0) < 1e-9
