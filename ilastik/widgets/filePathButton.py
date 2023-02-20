import os
from pathlib import PurePath
from typing import Iterable, Optional, Union

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
        styleSheet: str = "",
        parent: Optional[QWidget] = None,
    ):
        """Create a new button with the specified path, subtext, and icon.

        If the path is too long, intermediate directories will be replaced by a placeholder.

        The subtext, if not empty, is displayed below the path.
        """
        super().__init__(parent)
        # Setting stylesheet early is necessary for correct size calculation on all platforms
        # platforms (linux and windows would otherwise result in sizes which were too small).
        if styleSheet:
            self.setStyleSheet(styleSheet)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._path = PurePath(path)
        self._subtext = subtext
        if icon is not None:
            super().setIcon(icon)
        self._abbrevs = [(PurePath(), 0)]
        self._update()

    def sizeHint(self) -> QSize:
        return QSize(self._abbrevs[0][1], super().sizeHint().height())

    def minimumSizeHint(self) -> QSize:
        return QSize(self._abbrevs[-1][1], super().sizeHint().height())

    def setText(self, text: str) -> None:
        self._path = PurePath(text)
        self.setToolTip(str(self._path))
        self._update()

    def setSubtext(self, subtext: str) -> None:
        self._subtext = subtext
        self._update()

    def setIcon(self, icon: QIcon) -> None:
        super().setIcon(icon)
        self._update()

    def setIconSize(self, size: QSize) -> None:
        super().setIconSize(size)
        self._update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._update(update_abbrevs=False)

    def _update(self, update_abbrevs: bool = True) -> None:
        """Update widget text.

        If abbreviations and their corresponding widths don't need to be recomputed,
        set ``update_abbrevs`` to ``False``.
        """
        if update_abbrevs:
            self._abbrevs.clear()
            for abbrev in abbreviated_paths(self._path):
                # super().sizeHint() computes the proper size of the button
                # for this abbreviation.
                self._set_path(abbrev)
                self._abbrevs.append((abbrev, super().sizeHint().width()))
        self._set_path(next((p for p, w in self._abbrevs if w <= self.width()), self._abbrevs[-1][0]))

    def _set_path(self, path: PurePath) -> None:
        """Set the current text as the specified path and (possibly) subtext on a new line."""
        super().setText(f"{path}\n{self._subtext}" if self._subtext else str(path))


def abbreviated_paths(path: PurePath, placeholder: str = HORIZONTAL_ELLIPSIS) -> Iterable[PurePath]:
    """Yield the original path, and then it's consecutive abbreviations.

    In an abbreviated path, one or more intermediate directories in that path
    are replaced by a placeholder.

    Directories are abbreviated starting from root, but the root itself
    and the final path component are never abbreviated.
    """
    yield path
    yield from (PurePath(path.parts[0], placeholder, *path.parts[i:]) for i in range(2, len(path.parts)))
