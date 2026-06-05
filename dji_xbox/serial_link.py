"""Background serial reader: scan, probe, connect, parse, auto-reconnect."""

import time

import serial
from serial.tools import list_ports
from PySide6.QtCore import QThread, Signal

from .protocol import PING_DATA, PACKET_LEN, parse_packet
from .lag_detector import LagDetector

BAUD = 115200


def probe_port(ser, ping: bytes = PING_DATA, attempts: int = 8) -> bool:
    """Ping a few times; return True if the device replies with a full 38-byte frame.

    The remote may need several pings before it answers, and the first read after
    opening often catches a partial (mid-stream) frame, so we retry instead of
    giving up on a single read.
    """
    ser.reset_input_buffer()
    for _ in range(attempts):
        ser.write(ping)
        data = ser.readline()
        if len(data) == PACKET_LEN:
            return True
    return False


class SerialLink(QThread):
    rawAxes = Signal(object)            # dict {axis: raw_int}
    status = Signal(str, str)           # (state, port): searching/connected/disconnected
    stats = Signal(float, float, int)   # (hz, interval_ms, total_drops)
    log = Signal(str, str)              # (level, message)

    def __init__(self, port_hint=None):
        super().__init__()
        self._running = True
        self._port_hint = port_hint
        self._serial = None
        self._last_stats_emit = 0.0
        self._last_candidates = None

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            port = self._find_port()
            if port is None:
                self.status.emit("searching", "")
                self.msleep(1000)
                continue
            self._stream(port)

    def _candidate_ports(self):
        ports = [p.device for p in list_ports.comports()]
        if self._port_hint and self._port_hint in ports:
            ports.remove(self._port_hint)
            ports.insert(0, self._port_hint)
        return ports

    def _find_port(self):
        candidates = self._candidate_ports()
        # Only log scan details when the set of ports changes, so a failing
        # 1s scan loop doesn't flood the log.
        verbose = candidates != self._last_candidates
        self._last_candidates = candidates
        if verbose:
            self.log.emit("info",
                          f"Scanning ports: {', '.join(candidates)}" if candidates
                          else "No COM ports detected")
        for dev in candidates:
            if not self._running:
                break
            try:
                ser = serial.Serial(port=dev, baudrate=BAUD, timeout=0.3)
            except (serial.SerialException, OSError) as e:
                if verbose:
                    self.log.emit("warn", f"{dev}: failed to open ({e})")
                continue
            claimed = False
            try:
                if verbose:
                    self.log.emit("info", f"{dev}: checking for DJI remote…")
                if probe_port(ser):
                    self.log.emit("ok", f"{dev} replied with a 38-byte frame -> DJI remote")
                    self._serial = ser
                    claimed = True
                    return dev
                if verbose:
                    self.log.emit("info", f"{dev}: not the DJI remote, skipping")
            except (serial.SerialException, OSError) as e:
                if verbose:
                    self.log.emit("warn", f"{dev}: probe error ({e})")
            finally:
                if not claimed:
                    try:
                        ser.close()
                    except (serial.SerialException, OSError):
                        pass
        return None

    def _stream(self, port):
        ser = self._serial
        self.status.emit("connected", port)
        self._port_hint = port
        detector = LagDetector()
        try:
            while self._running:
                ser.write(PING_DATA)
                data = ser.readline()
                t = time.monotonic()
                if len(data) != PACKET_LEN:
                    if data:
                        self.log.emit("warn", f"skipped {len(data)}-byte packet")
                    continue
                self.rawAxes.emit(parse_packet(data))
                ev = detector.record(t)
                if t - self._last_stats_emit > 0.25:   # throttle ~4 Hz
                    self.stats.emit(detector.hz, detector.interval_ms,
                                    detector.total_drops)
                    self._last_stats_emit = t
                if ev is not None:
                    self.log.emit("warn", ev.message)
        except (serial.SerialException, OSError) as e:
            self.log.emit("err", f"{port} lost: {e} - reconnecting...")
        finally:
            try:
                ser.close()
            except (serial.SerialException, OSError):
                pass
            self.status.emit("disconnected", port)
