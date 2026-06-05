"""Find which packet byte(s) the remote's PHOTO / RECORD buttons use.

The main app only decodes the 4 sticks + camera dial. The physical buttons are
digital bits somewhere else in the 38-byte frame — this tool locates them so we
can wire them up.

Run it from the project root:

    .venv\\Scripts\\python tools\\capture_buttons.py        (Windows)
    .venv/bin/python tools/capture_buttons.py              (Linux/macOS)

Then follow the prompts. Copy the "byte[..]" lines it prints and send them back.
"""

import os
import sys
import time

# make `import dji_xbox` work no matter how this file is launched
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial
from serial.tools import list_ports

from dji_xbox.protocol import PING_DATA, PACKET_LEN, AXIS_OFFSETS

BAUD = 115200

# Bytes used by the sticks + dial — ignored, since they change as you move them.
AXIS_BYTES = set()
for _a, _b in AXIS_OFFSETS.values():
    AXIS_BYTES.update(range(_a, _b))


def find_port():
    """Auto-detect the DJI remote by probing every serial port."""
    for p in list_ports.comports():
        try:
            s = serial.Serial(p.device, BAUD, timeout=0.3)
        except Exception:
            continue
        try:
            for _ in range(8):
                s.reset_input_buffer()
                s.write(PING_DATA)
                if len(s.readline()) == PACKET_LEN:
                    return s, p.device
        except Exception:
            pass
        try:
            s.close()
        except Exception:
            pass
    return None, None


def capture_stable(s, seconds=2.0):
    """Read frames for a while; return {byte_index: value} for bytes that stayed
    constant the whole time (ignoring the stick/dial bytes). Constantly-changing
    bytes like counters/checksums are dropped automatically."""
    seen = {}
    end = time.time() + seconds
    frames = 0
    while time.time() < end:
        s.write(PING_DATA)
        d = s.readline()
        if len(d) != PACKET_LEN:
            continue
        frames += 1
        for i, val in enumerate(d):
            if i in AXIS_BYTES:
                continue
            seen.setdefault(i, set()).add(val)
    stable = {i: next(iter(v)) for i, v in seen.items() if len(v) == 1}
    return stable, frames


def probe_button(label, base, s):
    input(f"\n>> HOLD the {label} button, keep holding, then press Enter... ")
    held, frames = capture_stable(s)
    changes = [(i, base[i], held[i])
               for i in held if i in base and base[i] != held[i]]
    if changes:
        for i, b, h in changes:
            print(f"   {label}: byte[{i}]  {b:#04x} -> {h:#04x}  "
                  f"(bit mask {b ^ h:#04x})   [{frames} frames]")
    else:
        print(f"   {label}: no stable change found — hold the button firmly and "
              f"re-run. [{frames} frames]")
    return changes


def main():
    s, dev = find_port()
    if s is None:
        print("Remote not found. Plug it in (and power it on) and try again.")
        return
    print(f"Connected on {dev}.")
    input("\n>> Release ALL buttons, keep sticks centered, then press Enter... ")
    base, frames = capture_stable(s)
    print(f"   baseline captured ({frames} frames, "
          f"{len(base)} stable non-stick bytes)")

    try:
        probe_button("PHOTO (shutter)", base, s)
        probe_button("RECORD (video)", base, s)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass
    print("\nDone — copy the byte[..] lines above and send them back.")


if __name__ == "__main__":
    main()
