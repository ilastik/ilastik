import os
from pathlib import PurePath
from typing import Optional, Union

from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QPushButton, QWidget

HORIZONTAL_ELLIPSIS = "\u2026"


class FilePathButton(QPushButton):
    """Button that displays a possibly abbreviated filepath."""

    def __init__(self, path: Union[str, os.PathLike], other: str = "", parent: Optional[QWidget] = None):
        """Create a new button with the specified path and (possibly) other text.

        If path is too long, intermediate directories will be replaced by a placeholder.

        The other text, if not empty, is displayed below the path.
        """
        super().__init__(parent)
        self._suffix = f"\n{other}" if other else ""

        path = PurePath(path)
        self._abbrevs = [
            str(path),
            *[str(PurePath(path.parts[0], HORIZONTAL_ELLIPSIS, *path.parts[i:])) for i in range(2, len(path.parts))],
        ]

        self._updateText(self._abbrevs[-1])
        self.setMinimumWidth(self.sizeHint().width())

        self._updateText(self._abbrevs[0])
        self.setToolTip(self._abbrevs[0])

    def resizeEvent(self, event: QResizeEvent) -> None:
        for abbrev in self._abbrevs:
            self._updateText(abbrev)
            if self.sizeHint().width() <= event.size().width():
                break

    def _updateText(self, text: str) -> None:
        self.setText(f"{text}{self._suffix}")
