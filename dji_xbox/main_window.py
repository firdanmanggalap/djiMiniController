"""Main window: header, live sticks, calibration grid, log panel — wires it all."""

import time

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QGridLayout, QCheckBox, QSlider, QPlainTextEdit, QProgressBar,
)
from PySide6.QtCore import Qt

from .widgets.analog_stick import AnalogStick
from .mapping import convert_axis, convert_camera
from .config import save, AXIS_NAMES, default_axes
from .gamepad_out import GamepadOut
from .serial_link import SerialLink
from .logger import LogBuffer

AXIS_LABELS = {"lv": "L-Vert", "lh": "L-Horz", "rv": "R-Vert",
               "rh": "R-Horz", "cam": "Camera"}

_LOG_FILE = "session.log"


def _undo_invert(v: int, cal) -> int:
    """Undo output inversion so the display shows the physical stick direction."""
    return -v if cal.invert else v


class MainWindow(QMainWindow):
    def __init__(self, config, gamepad=None, link=None, autostart=True):
        super().__init__()
        self.config = config
        self.gamepad = gamepad or GamepadOut()
        self.logbuf = LogBuffer(file_path=(_LOG_FILE if config.log_to_file else None))
        self.setWindowTitle("DJI Mini -> Xbox Controller")

        self._build_ui()

        self._gamepad_ready = False
        try:
            self.gamepad.open()
            self._gamepad_ready = True
        except Exception as e:  # vgamepad/ViGEmBus missing
            self._log("err", f"ViGEmBus belum siap: {e}")

        self.link = link or SerialLink(port_hint=config.port_hint)
        self.link.rawAxes.connect(self.on_raw_axes)
        self.link.status.connect(self.on_status)
        self.link.stats.connect(self.on_stats)
        self.link.log.connect(self._log)
        if autostart:
            self.link.start()

    # ---------- UI construction ----------
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        # header
        header = QHBoxLayout()
        title = QLabel("🛩️ DJI Mini → Xbox Controller")
        title.setStyleSheet("font-weight:700;font-size:14px")
        self.hz_label = QLabel("⟳ 0 Hz")
        self.status_label = QLabel("Mencari remote…")
        self.output_btn = QPushButton("Output: ON" if self.config.output_enabled
                                      else "Output: OFF")
        self.output_btn.setCheckable(True)
        self.output_btn.setChecked(self.config.output_enabled)
        self.output_btn.clicked.connect(self._toggle_output)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.hz_label)
        header.addWidget(self.status_label)
        header.addWidget(self.output_btn)
        root.addLayout(header)

        # body: live + calibration
        body = QHBoxLayout()

        live = QVBoxLayout()
        sticks = QHBoxLayout()
        self.left_stick = AnalogStick("LEFT")
        self.right_stick = AnalogStick("RIGHT")
        left_col = QVBoxLayout()
        left_col.addWidget(self.left_stick)
        self.left_vals = QLabel("H 0  V 0")
        left_col.addWidget(QLabel("LEFT · Thr/Yaw"))
        left_col.addWidget(self.left_vals)
        right_col = QVBoxLayout()
        right_col.addWidget(self.right_stick)
        self.right_vals = QLabel("H 0  V 0")
        right_col.addWidget(QLabel("RIGHT · Pitch/Roll"))
        right_col.addWidget(self.right_vals)
        sticks.addLayout(left_col)
        sticks.addLayout(right_col)
        live.addLayout(sticks)
        live.addWidget(QLabel("Dial Kamera → Right Trigger"))
        self.cam_bar = QProgressBar()
        self.cam_bar.setRange(0, 255)
        live.addWidget(self.cam_bar)
        body.addLayout(live, 3)

        # calibration grid
        cal = QGridLayout()
        cal.addWidget(QLabel("Axis"), 0, 0)
        cal.addWidget(QLabel("Invert"), 0, 1)
        cal.addWidget(QLabel("Deadzone"), 0, 2)
        cal.addWidget(QLabel("Trim"), 0, 3)
        self._invert_boxes = {}
        self._deadzone_sliders = {}
        self._trim_sliders = {}
        for row, name in enumerate(AXIS_NAMES, start=1):
            c = self.config.axes[name]
            cal.addWidget(QLabel(AXIS_LABELS[name]), row, 0)

            box = QCheckBox()
            box.setChecked(c.invert)
            box.toggled.connect(lambda v, n=name: self._set_invert(n, v))
            cal.addWidget(box, row, 1)
            self._invert_boxes[name] = box

            dz = QSlider(Qt.Horizontal)
            dz.setRange(0, 30)                 # 0.00 .. 0.30
            dz.setValue(int(c.deadzone * 100))
            dz.valueChanged.connect(lambda v, n=name: self._set_deadzone(n, v))
            cal.addWidget(dz, row, 2)
            self._deadzone_sliders[name] = dz

            tr = QSlider(Qt.Horizontal)
            tr.setRange(-200, 200)             # raw-unit trim
            tr.setValue(c.trim)
            tr.valueChanged.connect(lambda v, n=name: self._set_trim(n, v))
            cal.addWidget(tr, row, 3)
            self._trim_sliders[name] = tr

        reset = QPushButton("↺ Reset")
        reset.clicked.connect(self._reset_calibration)
        cal.addWidget(reset, len(AXIS_NAMES) + 1, 0, 1, 4)

        cal_widget = QWidget()
        cal_widget.setLayout(cal)
        body.addWidget(cal_widget, 2)
        root.addLayout(body)

        # log panel
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Log live (deteksi lag)"))
        log_header.addStretch()
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setCheckable(True)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_log)
        save_log_btn = QPushButton("💾 Simpan ke file")
        save_log_btn.clicked.connect(self._enable_log_file)
        log_header.addWidget(self.pause_btn)
        log_header.addWidget(clear_btn)
        log_header.addWidget(save_log_btn)
        root.addLayout(log_header)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(1000)
        root.addWidget(self.log_view)

        self.setCentralWidget(central)

    # ---------- slots ----------
    def on_raw_axes(self, axes: dict):
        vals = {n: convert_axis(axes[n], self.config.axes[n])
                for n in ("lv", "lh", "rv", "rh")}
        trig = convert_camera(axes["cam"], self.config.axes["cam"])

        # Display the PHYSICAL stick position; invert only affects gamepad output.
        phys = {n: _undo_invert(vals[n], self.config.axes[n])
                for n in ("lv", "lh", "rv", "rh")}

        self.left_stick.set_position(phys["lh"] / 32767, phys["lv"] / 32767)
        self.right_stick.set_position(phys["rh"] / 32767, phys["rv"] / 32767)
        self.left_vals.setText(f"H {phys['lh']:+d}  V {phys['lv']:+d}")
        self.right_vals.setText(f"H {phys['rh']:+d}  V {phys['rv']:+d}")
        self.cam_bar.setValue(trig)

        if self.config.output_enabled and self._gamepad_ready:
            self.gamepad.send(vals["lv"], vals["lh"], vals["rv"], vals["rh"], trig)

    def on_status(self, state: str, port: str):
        text = {"searching": "Mencari remote…",
                "connected": f"● Connected — {port}",
                "disconnected": f"Terputus ({port}), reconnect…"}.get(state, state)
        self.status_label.setText(text)

    def on_stats(self, hz: float, interval_ms: float, drops: int):
        self.hz_label.setText(f"⟳ {hz:.0f} Hz · {interval_ms:.1f}ms · drop {drops}")

    def _log(self, level: str, message: str):
        ts = time.strftime("%H:%M:%S")
        self.logbuf.add(level, message, ts)
        if not self.pause_btn.isChecked():
            self.log_view.appendPlainText(f"{ts}  [{level}]  {message}")

    # ---------- calibration handlers (auto-save) ----------
    def _set_invert(self, name, value):
        self.config.axes[name].invert = bool(value)
        self._save()

    def _set_deadzone(self, name, value):
        self.config.axes[name].deadzone = value / 100.0
        self._save()

    def _set_trim(self, name, value):
        self.config.axes[name].trim = int(value)
        self._save()

    def _reset_calibration(self):
        self.config.axes = default_axes()
        for name in AXIS_NAMES:
            c = self.config.axes[name]
            widgets = (self._invert_boxes[name], self._deadzone_sliders[name],
                       self._trim_sliders[name])
            for w in widgets:
                w.blockSignals(True)
            self._invert_boxes[name].setChecked(c.invert)
            self._deadzone_sliders[name].setValue(int(c.deadzone * 100))
            self._trim_sliders[name].setValue(c.trim)
            for w in widgets:
                w.blockSignals(False)
        self._save()

    def _toggle_output(self):
        self.config.output_enabled = self.output_btn.isChecked()
        self.output_btn.setText("Output: ON" if self.config.output_enabled
                                else "Output: OFF")
        self._save()

    def _clear_log(self):
        self.logbuf.clear()
        self.log_view.clear()

    def _enable_log_file(self):
        self.config.log_to_file = True
        self.logbuf.set_file(_LOG_FILE)
        self._save()
        self._log("info", "Log disimpan ke session.log")

    def _save(self):
        save(self.config)

    def closeEvent(self, event):
        try:
            self.link.stop()
            self.link.wait(1000)
        except Exception:
            pass
        super().closeEvent(event)
