"""Find which packet byte(s) the remote's PHOTO / RECORD buttons use.

The main app only decodes the 4 sticks + camera dial. The physical buttons are
digital bits somewhere else in the 38-byte frame (if they're sent at all) — this
tool tries to locate them.

Run it from the project root (CLOSE the main app first — only one program can use
the COM port at a time):

    .venv\\Scripts\\python tools\\capture_buttons.py            (auto-detect)
    .venv\\Scripts\\python tools\\capture_buttons.py --port COM6
    .venv\\Scripts\\python tools\\capture_buttons.py --raw 5     (raw hex fallback)

Follow the prompts, then copy whatever it prints and send it back.
"""

import argparse
import os
import sys
import time

# make `import dji_xbox` work no matter how this file is launched
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial
from serial.tools import list_ports

from dji_xbox.protocol import PING_DATA, PACKET_LEN, AXIS_OFFSETS

BAUD = 115200

# Bytes used by the sticks + dial — skipped, since they move with the sticks.
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


def open_port(args):
    if args.port:
        try:
            return serial.Serial(args.port, BAUD, timeout=0.3), args.port
        except Exception as e:
            print(f"Could not open {args.port}: {e}")
            print("If the main app is open, CLOSE it first — only one program can "
                  "use the port at a time.")
            return None, None
    s, dev = find_port()
    if s is None:
        print("Remote not found by auto-scan.")
        print("Most likely the main app is still running and holding the port —")
        print("close it, then re-run. Or point the tool at the port directly:")
        print("   .venv\\Scripts\\python tools\\capture_buttons.py --port COM6")
    return s, dev


def capture_value_sets(s, seconds):
    """For every byte, collect each value it takes during `seconds`."""
    sets = {i: set() for i in range(PACKET_LEN)}
    end = time.time() + seconds
    frames = 0
    while time.time() < end:
        s.write(PING_DATA)
        d = s.readline()
        if len(d) != PACKET_LEN:
            continue
        frames += 1
        for i in sets:
            sets[i].add(d[i])
    return sets, frames


def probe_button(label, candidates, s):
    input(f"\n>> When you press Enter, PRESS the {label} button repeatedly for ~4s "
          f"(DON'T touch the sticks)... ")
    held, frames = capture_value_sets(s, 4.0)
    hits = []
    for i, base_vals in candidates.items():
        new_vals = held[i] - base_vals
        if new_vals:
            hits.append((i, base_vals, new_vals))
    if hits:
        for i, base_vals, new_vals in hits:
            b = min(base_vals)
            nv = " ".join(f"{v:#04x}" for v in sorted(new_vals))
            masks = " ".join(f"{(b ^ v):#04x}" for v in sorted(new_vals))
            tag = "  (axis byte — could be stick noise)" if i in AXIS_BYTES else ""
            print(f"   {label}: byte[{i}]  base {b:#04x}  ->  new {nv}  "
                  f"(mask {masks})   [{frames} frames]{tag}")
    else:
        print(f"   {label}: no new byte value seen while pressing. [{frames} frames]")
    return hits


def raw_dump(s, seconds):
    print(f"\nStreaming raw frames for {seconds}s at ~6/s — press PHOTO then RECORD "
          f"while this runs:\n")
    end = time.time() + seconds
    nxt = 0.0
    while time.time() < end:
        s.write(PING_DATA)
        d = s.readline()
        if len(d) != PACKET_LEN:
            continue
        now = time.time()
        if now >= nxt:
            print(d.hex())
            nxt = now + 1 / 6
    print("\n(Copy all the hex lines above and send them back.)")


def main():
    ap = argparse.ArgumentParser(description="Locate the PHOTO/RECORD button bits.")
    ap.add_argument("-p", "--port", help="Serial port (e.g. COM6). Omit to auto-detect.")
    ap.add_argument("--raw", type=float, metavar="SECONDS",
                    help="Just stream raw hex frames for N seconds (fallback).")
    args = ap.parse_args()

    s, dev = open_port(args)
    if s is None:
        return
    print(f"Connected on {dev}.")

    try:
        if args.raw:
            raw_dump(s, args.raw)
            return

        input("\n>> Release ALL buttons, keep sticks centered, then press Enter... ")
        base, frames = capture_value_sets(s, 2.5)
        # "candidate" = near-constant byte (a digital button bit lives here;
        # counters/checksums take many values and are excluded).
        candidates = {i: vals for i, vals in base.items() if len(vals) <= 3}
        print(f"   baseline captured ({frames} frames, "
              f"{len(candidates)} near-constant bytes to watch)")

        any_hit = False
        any_hit |= bool(probe_button("PHOTO (shutter)", candidates, s))
        any_hit |= bool(probe_button("RECORD (video)", candidates, s))

        if not any_hit:
            print("\nNo button bits found in the serial frame. These buttons are")
            print("probably NOT sent over this USB serial stream (DJI may handle")
            print("photo/record only over the RF link). If you want, re-run with")
            print("   --raw 6   and send the hex so I can double-check by hand.")
    except KeyboardInterrupt:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
