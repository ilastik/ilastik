import os
from pathlib import PurePath
from typing import Optional, Union

from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QToolButton, QWidget


class FilePathButton(QToolButton):
    """Button that displays a possibly abbreviated filepath."""

    def __init__(self, path: Union[str, os.PathLike], other: str = "", parent: Optional[QWidget] = None):
        """Create a new button with the specified path and (possibly) other text.

        If path is too long, intermediate directories will be replaced by a placeholder.

        The other text, if not empty, is displayed below the path.
        """
        super().__init__(parent)

        path = PurePath(path)
        self._suffix = f"\n{other}" if other else ""

        # Stop table contains widths of abbreviated paths and paths themselves, in decreasing order.
        self._stops = [(self.fontMetrics().horizontalAdvance(str(path)), str(path))]
        for i in range(2, len(path.parts)):
            # U+2026: Horizontal Ellipsis.
            abbrev = str(PurePath(path.parts[0], "\u2026", *path.parts[i:]))
            self._stops.append((self.fontMetrics().horizontalAdvance(abbrev), abbrev))

        self.setMinimumWidth(self._stops[-1][0])
        self.setToolTip(str(path))
        self._update(self.width())

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update(event.size().width())

    def _update(self, width: int) -> None:
        for stop, path in self._stops:
            if stop <= width:
                self.setText(f"{path}{self._suffix}")
                break
