from dji_xbox.widgets.analog_stick import AnalogStick


def test_set_position_clamps_to_unit_range(qapp):
    w = AnalogStick("LEFT")
    w.set_position(5.0, -5.0)
    assert w.x == 1.0
    assert w.y == -1.0


def test_paints_without_error(qapp):
    w = AnalogStick("RIGHT")
    w.resize(140, 140)
    w.set_position(0.3, -0.2)
    w.grab()   # forces a paint pass offscreen; must not raise
