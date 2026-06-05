from dji_xbox.lag_detector import LagDetector


def test_first_record_returns_none_and_no_hz():
    d = LagDetector()
    assert d.record(0.0) is None


def test_steady_stream_reports_no_lag_and_correct_hz():
    d = LagDetector(expected_interval=0.011, lag_floor_ms=50)
    t = 0.0
    events = []
    for _ in range(30):
        t += 0.011
        e = d.record(t)
        if e:
            events.append(e)
    assert events == []
    assert 80 < d.hz < 110   # ~91 Hz


def test_big_gap_is_flagged_as_lag_with_drop_estimate():
    d = LagDetector(expected_interval=0.011, lag_floor_ms=50)
    d.record(0.000)
    d.record(0.011)
    e = d.record(0.011 + 0.25)   # 250 ms gap
    assert e is not None
    assert e.kind == "lag"
    assert e.drops >= 1
    assert d.total_drops >= 1
