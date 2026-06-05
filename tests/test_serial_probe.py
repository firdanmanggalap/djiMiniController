from dji_xbox.serial_link import probe_port
from dji_xbox.protocol import PACKET_LEN, PING_DATA


class FakeSerial:
    def __init__(self, reply: bytes):
        self._reply = reply
        self.written = b""

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.written += data

    def readline(self):
        return self._reply


def test_probe_true_when_reply_is_full_frame():
    ser = FakeSerial(b"\x00" * PACKET_LEN)
    assert probe_port(ser) is True
    assert ser.written == PING_DATA


def test_probe_false_when_reply_is_short():
    ser = FakeSerial(b"\x00" * 10)
    assert probe_port(ser) is False


def test_probe_false_when_no_reply():
    ser = FakeSerial(b"")
    assert probe_port(ser) is False


class FlakySerial:
    """Returns a sequence of replies across successive readline() calls."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.written = b""

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.written += data

    def readline(self):
        return self._replies.pop(0) if self._replies else b""


def test_probe_true_when_full_frame_arrives_after_partial():
    # First read catches a mid-stream partial frame, then a full one arrives.
    ser = FlakySerial([b"\x00" * 12, b"\x00" * PACKET_LEN])
    assert probe_port(ser) is True


def test_probe_false_when_never_full_within_attempts():
    ser = FlakySerial([b"\x00" * 5] * 3)   # always short, then empty
    assert probe_port(ser) is False
