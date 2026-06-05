from dji_xbox.mapping import AxisCal, convert_axis, convert_camera


def test_default_cal_full_positive_maps_to_max():
    # raw=1684 -> vjoy=32768 -> normalized +1
    assert convert_axis(1684, AxisCal()) == 32767


def test_default_cal_full_negative_maps_to_min():
    # raw=364 -> vjoy=0 -> normalized -1
    assert convert_axis(364, AxisCal()) == -32767


def test_neutral_maps_near_zero():
    # raw=1024 -> vjoy≈16384 -> normalized ≈0
    assert abs(convert_axis(1024, AxisCal())) <= 50


def test_invert_flips_sign():
    assert convert_axis(1684, AxisCal(invert=True)) == -32767


def test_deadzone_zeros_small_input():
    assert convert_axis(1024, AxisCal(deadzone=0.2)) == 0


def test_range_and_clamp_never_overflow():
    v = convert_axis(1684, AxisCal(range=1.5))
    assert -32768 <= v <= 32767
    assert v == 32767  # clamped


def test_trim_shifts_neutral_point():
    # raw 1024 is neutral; with trim equal to (1024-CENTER) the neutral moves,
    # so the same raw no longer reads ~0
    assert convert_axis(1024, AxisCal(trim=300)) != 0


def test_convert_camera_maps_to_trigger_range():
    assert convert_camera(1684, AxisCal()) == 255
    assert convert_camera(364, AxisCal()) == 0
