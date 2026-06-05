"""Custom QWidget: a round stick pad with crosshair and a live dot."""

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

        dx = cx + self.x * r
        dy = cy - self.y * r   # screen y is inverted
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4ade80"))
        p.drawEllipse(QPointF(dx, dy), 10, 10)
        p.end()
