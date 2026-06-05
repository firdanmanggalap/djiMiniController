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
