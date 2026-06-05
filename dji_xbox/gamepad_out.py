"""Thin wrapper around vgamepad's virtual Xbox 360 controller (Windows/ViGEmBus)."""

# Xbox button names shown in the UI, mapped lazily to vgamepad enum values.
BUTTON_NAMES = [
    "A", "B", "X", "Y", "LB", "RB", "Back", "Start",
    "LS", "RS", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
]


class GamepadOut:
    def __init__(self, pad=None, button_map=None):
        # pad / button_map can be injected for tests; otherwise built lazily.
        self._pad = pad
        self._opened = pad is not None
        self._button_map = button_map
        self._held = set()

    def open(self) -> None:
        """Create the virtual controller. Raises if ViGEmBus/vgamepad unavailable."""
        if self._pad is None:
            import vgamepad as vg
            self._pad = vg.VX360Gamepad()
        self._opened = True

    def is_open(self) -> bool:
        return self._opened

    def _resolve(self, name):
        """Translate a button name to a vgamepad enum (built lazily, once)."""
        if self._button_map is None:
            import vgamepad as vg
            b = vg.XUSB_BUTTON
            self._button_map = {
                "A": b.XUSB_GAMEPAD_A, "B": b.XUSB_GAMEPAD_B,
                "X": b.XUSB_GAMEPAD_X, "Y": b.XUSB_GAMEPAD_Y,
                "LB": b.XUSB_GAMEPAD_LEFT_SHOULDER,
                "RB": b.XUSB_GAMEPAD_RIGHT_SHOULDER,
                "Back": b.XUSB_GAMEPAD_BACK, "Start": b.XUSB_GAMEPAD_START,
                "LS": b.XUSB_GAMEPAD_LEFT_THUMB, "RS": b.XUSB_GAMEPAD_RIGHT_THUMB,
                "DPAD_UP": b.XUSB_GAMEPAD_DPAD_UP,
                "DPAD_DOWN": b.XUSB_GAMEPAD_DPAD_DOWN,
                "DPAD_LEFT": b.XUSB_GAMEPAD_DPAD_LEFT,
                "DPAD_RIGHT": b.XUSB_GAMEPAD_DPAD_RIGHT,
            }
        return self._button_map[name]

    def send(self, lv: int, lh: int, rv: int, rh: int, trigger: int, buttons=()) -> None:
        self._pad.left_joystick(x_value=lh, y_value=lv)
        self._pad.right_joystick(x_value=rh, y_value=rv)
        self._pad.right_trigger(value=trigger)
        want = set(buttons)
        for name in want - self._held:        # newly pressed
            self._pad.press_button(button=self._resolve(name))
        for name in self._held - want:        # released
            self._pad.release_button(button=self._resolve(name))
        self._held = want
        self._pad.update()

    def neutralize(self) -> None:
        """Center sticks, zero trigger, release all buttons (used when output is off)."""
        if self._pad is not None:
            self.send(0, 0, 0, 0, 0, buttons=())

    def close(self) -> None:
        self._pad = None
        self._opened = False
        self._held = set()
