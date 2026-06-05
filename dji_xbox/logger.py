"""In-memory ring buffer of log lines, with optional append-to-file."""

from collections import deque


class LogBuffer:
    def __init__(self, max_lines: int = 1000, file_path=None):
        self._lines = deque(maxlen=max_lines)
        self.file_path = file_path

    def add(self, level: str, message: str, timestamp_str: str) -> None:
        self._lines.append((timestamp_str, level, message))
        if self.file_path:
            try:
                with open(self.file_path, "a") as f:
                    f.write(f"{timestamp_str}\t{level}\t{message}\n")
            except OSError:
                pass

    def lines(self):
        return list(self._lines)

    def clear(self) -> None:
        self._lines.clear()

    def set_file(self, file_path) -> None:
        self.file_path = file_path
