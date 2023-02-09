import os
from pathlib import PurePath
from typing import Optional, Tuple, Union

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QResizeEvent
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QWidget

HORIZONTAL_ELLIPSIS = "\u2026"


class FilePathButton(QPushButton):
    """Button that displays a possibly abbreviated filepath."""

    def __init__(
        self,
        path: Union[str, os.PathLike],
        subtext: str = "",
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None,
    ):
        """Create a new button with the specified path, other text, and icon.

        If the path is too long, intermediate directories will be replaced by a placeholder.

        The other text, if not empty, is displayed below the path.
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._path = PurePath(path)
        self.setToolTip(str(self._path))

        self._suffix = f"\n{subtext}" if subtext else ""

        # Icon should be set before the text in order to be accounted for in the size hint.
        if icon is not None:
            super().setIcon(icon)

        self._abbrevs = [(PurePath(), 0)]
        self._update_abbrevs()

    def minimumSizeHint(self) -> QSize:
        return QSize(self._abbrevs[-1][1], super().sizeHint().height())

    def sizeHint(self) -> QSize:
        return QSize(self._abbrevs[0][1], super().sizeHint().height())

    def setText(self, text: str) -> None:
        self._path = PurePath(text)
        self.setToolTip(str(self._path))
        self._update_abbrevs()

    def setIcon(self, icon: QIcon) -> None:
        super().setIcon(icon)
        self._update_abbrevs()

    def setIconSize(self, size: QSize) -> None:
        super().setIconSize(size)
        self._update_abbrevs()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update_current_text()

    def _update_abbrevs(self) -> None:
        """Update abbreviations for the current widget state, then update the current text."""
        self._abbrevs = [self._set_path(self._path)]
        for i in range(2, len(self._path.parts)):
            path = PurePath(self._path.parts[0], HORIZONTAL_ELLIPSIS, *self._path.parts[i:])
            self._abbrevs.append(self._set_path(path))
        self._update_current_text()

    def _update_current_text(self) -> None:
        """Update the current text to the shortest possible one that fits into the button."""
        path = next((abbrev for abbrev, width in self._abbrevs if width <= self.width()), self._abbrevs[-1][0])
        self._set_path(path)

    def _set_path(self, path: PurePath) -> Tuple[str, int]:
        """Set button text from path; return the path's text, and the ideal width of this widget."""
        text = str(path)
        super().setText(f"{text}{self._suffix}")
        return text, super().sizeHint().width()
