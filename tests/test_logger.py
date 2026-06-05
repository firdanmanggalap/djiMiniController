from dji_xbox.logger import LogBuffer


def test_add_and_read_lines():
    buf = LogBuffer()
    buf.add("info", "hello", "12:00:00.000")
    buf.add("err", "boom", "12:00:01.000")
    lines = buf.lines()
    assert len(lines) == 2
    assert lines[0] == ("12:00:00.000", "info", "hello")
    assert lines[1] == ("12:00:01.000", "err", "boom")


def test_buffer_caps_at_max_lines():
    buf = LogBuffer(max_lines=3)
    for i in range(5):
        buf.add("info", f"line {i}", "t")
    lines = buf.lines()
    assert len(lines) == 3
    assert lines[0][2] == "line 2"   # oldest two dropped


def test_clear_empties_buffer():
    buf = LogBuffer()
    buf.add("info", "x", "t")
    buf.clear()
    assert buf.lines() == []


def test_writes_to_file_when_enabled(tmp_path):
    p = tmp_path / "session.log"
    buf = LogBuffer(file_path=p)
    buf.add("warn", "lag here", "12:00:00.000")
    content = p.read_text()
    assert "lag here" in content
    assert "warn" in content
