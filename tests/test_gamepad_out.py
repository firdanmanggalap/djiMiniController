from dji_xbox.gamepad_out import GamepadOut


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


def test_open_with_injected_pad_does_not_import_vgamepad():
    pad = FakePad()
    out = GamepadOut(pad=pad)
    out.open()   # must not raise even though vgamepad is absent
    assert out.is_open() is True


def test_send_forwards_axes_and_trigger_then_updates():
    pad = FakePad()
    out = GamepadOut(pad=pad)
    out.open()
    out.send(lv=100, lh=-200, rv=300, rh=-400, trigger=128)
    assert ("left", -200, 100) in pad.calls     # x=lh, y=lv
    assert ("right", -400, 300) in pad.calls     # x=rh, y=rv
    assert ("trigger", 128) in pad.calls
    assert pad.calls[-1] == ("update",)
