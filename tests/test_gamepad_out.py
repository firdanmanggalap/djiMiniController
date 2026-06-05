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

    def press_button(self, button):
        self.calls.append(("press", button))

    def release_button(self, button):
        self.calls.append(("release", button))

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


def test_held_button_pressed_once_then_released():
    pad = FakePad()
    out = GamepadOut(pad=pad, button_map={"RB": "RB"})
    out.open()
    out.send(0, 0, 0, 0, 0, buttons=["RB"])
    assert ("press", "RB") in pad.calls
    out.send(0, 0, 0, 0, 0, buttons=["RB"])      # still held -> not pressed again
    assert pad.calls.count(("press", "RB")) == 1
    out.send(0, 0, 0, 0, 0, buttons=[])          # left the zone -> released
    assert ("release", "RB") in pad.calls


def test_neutralize_releases_held_buttons():
    pad = FakePad()
    out = GamepadOut(pad=pad, button_map={"A": "A"})
    out.open()
    out.send(0, 0, 0, 0, 0, buttons=["A"])
    out.neutralize()
    assert ("release", "A") in pad.calls
