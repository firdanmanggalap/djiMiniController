"""DJI Mavic Mini RC serial protocol: constants + pure packet parsing."""

# Ping the RC sends to request a frame (from the original main.py)
PING_DATA = bytes.fromhex("550d04330a0e0300400601f44a")

# A valid analog frame is exactly this many bytes
PACKET_LEN = 38

# Raw-value center and scale (from the original main.py conversion)
CENTER = 364
SCALE_NUM = 4096
SCALE_DEN = 165

# byte offset (start, end) of each axis inside a PACKET_LEN frame
AXIS_OFFSETS = {
    "rh": (7, 9),
    "rv": (10, 12),
    "lv": (13, 15),
    "lh": (16, 18),
    "cam": (19, 21),
}


def raw_value(two_bytes: bytes) -> int:
    """Little-endian unsigned int from a 2-byte slice."""
    return int.from_bytes(two_bytes, byteorder="little")


def parse_packet(data: bytes):
    """Return {axis_name: raw_int} for a 38-byte frame, or None if malformed."""
    if len(data) != PACKET_LEN:
        return None
    return {name: raw_value(data[a:b]) for name, (a, b) in AXIS_OFFSETS.items()}
