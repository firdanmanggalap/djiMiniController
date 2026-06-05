"""Thin wrapper around vgamepad's virtual Xbox 360 controller (Windows/ViGEmBus)."""


class GamepadOut:
    def __init__(self, pad=None):
        # pad can be injected for tests; otherwise created lazily in open()
        self._pad = pad
        self._opened = pad is not None

    def open(self) -> None:
        """Create the virtual controller. Raises if ViGEmBus/vgamepad unavailable."""
        if self._pad is None:
            import vgamepad as vg
            self._pad = vg.VX360Gamepad()
        self._opened = True

    def is_open(self) -> bool:
        return self._opened

    def send(self, lv: int, lh: int, rv: int, rh: int, trigger: int) -> None:
        self._pad.left_joystick(x_value=lh, y_value=lv)
        self._pad.right_joystick(x_value=rh, y_value=rv)
        self._pad.right_trigger(value=trigger)
        self._pad.update()

    def close(self) -> None:
        self._pad = None
        self._opened = False
