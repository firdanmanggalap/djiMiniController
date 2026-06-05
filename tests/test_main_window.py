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
