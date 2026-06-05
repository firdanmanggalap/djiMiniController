"""Custom QWidget: a round stick pad with crosshair and a live dot."""

import math

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF


class AnalogStick(QWidget):
    def __init__(self, label: str = ""):
        super().__init__()
        self.label = label
        self.x = 0.0   # -1..1
        self.y = 0.0   # -1..1 (up = positive)
        self.setMinimumSize(140, 140)

    def set_position(self, x: float, y: float) -> None:
        self.x = max(-1.0, min(1.0, x))
        self.y = max(-1.0, min(1.0, y))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = (min(w, h) - 8) / 2
        cx, cy = w / 2, h / 2

        p.setPen(QPen(QColor("#313846"), 2))
        p.setBrush(QColor("#171a21"))
        p.drawEllipse(QPointF(cx, cy), r, r)

        p.setPen(QPen(QColor("#2c333f"), 1))
        p.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))
        p.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))

        # Constrain the dot to the circular pad (not the square bounding box),
        # and keep the whole dot inside the ring.
        dot_r = 10
        track = r - dot_r
        x, y = self.x, self.y
        mag = math.hypot(x, y)
        if mag > 1.0:
            x, y = x / mag, y / mag
        dx = cx + x * track
        dy = cy - y * track   # screen y is inverted
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4ade80"))
        p.drawEllipse(QPointF(dx, dy), dot_r, dot_r)
        p.end()
