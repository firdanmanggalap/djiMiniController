"""Entry point: launch the DJI Mini -> Xbox controller app."""

import sys

from PySide6.QtWidgets import QApplication

from dji_xbox.config import load
from dji_xbox.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    config = load()
    window = MainWindow(config)
    window.resize(820, 620)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
