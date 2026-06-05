from dji_xbox.protocol import parse_packet, PACKET_LEN, PING_DATA


def test_ping_data_is_known_bytes():
    assert PING_DATA == bytes.fromhex("550d04330a0e0300400601f44a")


def test_parse_packet_wrong_length_returns_none():
    assert parse_packet(b"\x00" * 10) is None
    assert parse_packet(b"") is None


def test_parse_packet_extracts_all_axes_little_endian():
    data = bytearray(PACKET_LEN)
    data[7:9] = (111).to_bytes(2, "little")    # rh
    data[10:12] = (222).to_bytes(2, "little")  # rv
    data[13:15] = (333).to_bytes(2, "little")  # lv
    data[16:18] = (444).to_bytes(2, "little")  # lh
    data[19:21] = (555).to_bytes(2, "little")  # cam
    parsed = parse_packet(bytes(data))
    assert parsed == {"rh": 111, "rv": 222, "lv": 333, "lh": 444, "cam": 555}
