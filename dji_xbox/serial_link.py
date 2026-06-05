"""Background serial reader: scan, probe, connect, parse, auto-reconnect."""

import time

import serial
from serial.tools import list_ports
from PySide6.QtCore import QThread, Signal

from .protocol import PING_DATA, PACKET_LEN, parse_packet
from .lag_detector import LagDetector

BAUD = 115200


def probe_port(ser, ping: bytes = PING_DATA) -> bool:
    """Write the ping and return True if the device replies with a full frame."""
    ser.reset_input_buffer()
    ser.write(ping)
    data = ser.readline()
    return len(data) == PACKET_LEN


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
        for dev in self._candidate_ports():
            if not self._running:
                break
            try:
                ser = serial.Serial(port=dev, baudrate=BAUD, timeout=0.3)
            except (serial.SerialException, OSError):
                continue
            claimed = False
            try:
                if probe_port(ser):
                    self.log.emit("ok", f"{dev} balas paket 38-byte -> remote DJI")
                    self._serial = ser
                    claimed = True
                    return dev
            except (serial.SerialException, OSError):
                pass
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
                        self.log.emit("warn", f"paket {len(data)} byte di-skip")
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
            self.log.emit("err", f"{port} hilang: {e} - reconnect...")
        finally:
            try:
                ser.close()
            except (serial.SerialException, OSError):
                pass
            self.status.emit("disconnected", port)
