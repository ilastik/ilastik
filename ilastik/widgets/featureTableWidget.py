###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2018, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import enum
from qtpy.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap, QPolygon, QKeyEvent
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QItemDelegate,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTableWidgetSelectionRange,
)
from qtpy.QtCore import QPoint, QRect, QSize, Qt

from ilastik.utility.gui import is_qt_dark_mode


class FeatureEntry(object):
    def __init__(self, name, minimum_scale=0.7):
        self.name = name
        self.minimum_scale = minimum_scale


# ==============================================================================
# FeatureTableWidgetV2dHeader
# ==============================================================================
class FeatureTableWidgetV2dHeader(QTableWidgetItem):
    isExpanded = False
    children = []

    def __init__(self, text="Compute in 2D/3D"):
        QTableWidgetItem.__init__(self)
        self.setText(text)


# ==============================================================================
# FeatureTableWidgetVSigmaHeader
# ==============================================================================
class FeatureTableWidgetVSigmaHeader(QTableWidgetItem):
    isExpanded = False
    children = []

    def __init__(self, text="Sigma"):
        QTableWidgetItem.__init__(self)
        self.setText(text)


class _FeatureSelectionColors:
    """
    Class that holds some color "constants". Colors change according to
    used system theme (on windows and MacOS).
    """

    @staticmethod
    def foreground():
        return QApplication.palette().windowText().color()

    @staticmethod
    def green():
        if is_qt_dark_mode():
            # dark mode
            return QColor("#00ad6b")
        else:
            # light mode
            return QColor("#00fa9a")

    @staticmethod
    def light_gray():
        if is_qt_dark_mode():
            # dark mode
            return QColor("#4d4d4d")
        else:
            # light mode
            return QColor("#dcdcdc")

    @staticmethod
    def dark_gray():
        if is_qt_dark_mode():
            # dark mode
            return QColor("#dcdcdc")
        else:
            # light mode
            return QColor("#4d4d4d")


# ==============================================================================
# FeatureTableWidgetVHeader
# ==============================================================================
class FeatureTableWidgetVHeader(QTableWidgetItem):
    def __init__(self):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.isExpanded = True
        self.isRootNode = False
        self.feature = None
        self.vHeaderName = None
        self.children = []
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))

    def setExpanded(self):
        self.isExpanded = True
        self._drawIcon()

    def setCollapsed(self):
        self.isExpanded = False
        self._drawIcon()

    def setIconAndText(self):
        self._drawIcon()

    def setFeatureVHeader(self, feature):
        self.feature = feature
        self.vHeaderName = feature.name
        self.setText(self.vHeaderName)

        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        self.setIcon(QIcon(pixmap))

    def setGroupVHeader(self, name):
        self.vHeaderName = name
        self.setText(self.vHeaderName)
        self.isRootNode = True

    def _drawIcon(self):

        if self.isRootNode:
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            pen = QPen(_FeatureSelectionColors.foreground())
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(QBrush(_FeatureSelectionColors.foreground(), Qt.SolidPattern))
            painter.setRenderHint(QPainter.Antialiasing)
            if not self.isExpanded:
                arrowRightPolygon = [QPoint(6, 6), QPoint(6, 14), QPoint(14, 10)]
                painter.drawPolygon(QPolygon(arrowRightPolygon))
            else:
                arrowDownPolygon = [QPoint(6, 6), QPoint(15, 6), QPoint(10, 14)]
                painter.drawPolygon(QPolygon(arrowDownPolygon))
            painter.end()
            self.setIcon(QIcon(pixmap))


# ==============================================================================
# FeatureTableWidgetHHeader
# ==============================================================================
class FeatureTableWidgetHHeader(QTableWidgetItem):
    sub_trans = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    def __init__(self, column, sigma=None, window_size=3.5):
        QTableWidgetItem.__init__(self)
        # init
        # ------------------------------------------------
        self.column = column
        self.sigma = sigma
        self.window_size = window_size
        self.pixmapSize = QSize(61, 61)
        self.setNameAndBrush(self.sigma)

    @property
    def brushSize(self):
        if self.sigma is None:
            return 0
        else:
            return int(3.0 * self.sigma + 0.5) + 1

    def setNameAndBrush(self, sigma):
        self.sigma = sigma
        self.setText(f"σ{self.column}".translate(self.sub_trans))
        if self.sigma is not None:
            total_window = 1 + 2 * int(self.sigma * self.window_size + 0.5)
            self.setToolTip(f"sigma = {sigma:.1f} pixels, window diameter = {total_window:.1f}")
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        pixmap = QPixmap(self.pixmapSize)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        brush = QBrush(_FeatureSelectionColors.foreground(), Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawEllipse(
            QRect(
                self.pixmapSize.width() // 2 - self.brushSize // 2,
                self.pixmapSize.height() // 2 - self.brushSize // 2,
                self.brushSize,
                self.brushSize,
            )
        )
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setTextAlignment(Qt.AlignVCenter)

    def setIconAndText(self):
        self.setNameAndBrush(self.sigma)


# ==============================================================================
# ItemDelegate
# ==============================================================================
class ItemDelegate(QItemDelegate):
    """
    This class responsible for drawing checkboxes and 2d / 3d toggle
    """

    @enum.unique
    class Role(enum.Enum):
        CHECKED = "checked"
        UNCHECKED = "unchecked"
        PARTIAL = "partial"
        DISABLED = "disabled"
        MODE_2D = "2d"
        MODE_3D = "3d"

    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)
        self._pixmapCache = {}

    def getPixmap(self, role: Role, size: QSize) -> QPixmap:
        key = role, size.width(), size.height()
        if key not in self._pixmapCache:
            pixmap = self._drawPixmap(role, size)
            self._pixmapCache[key] = pixmap

        return self._pixmapCache[key]

    def _drawPixmap(self, role: Role, size: QSize) -> None:
        pixmap = QPixmap(size)
        width, height = pixmap.width(), pixmap.height()
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if role == self.Role.CHECKED:
            self.drawPixmapForChecked(painter, width, height)
        elif role == self.Role.UNCHECKED:
            self.drawPixmapForUnchecked(painter, width, height)
        elif role == self.Role.PARTIAL:
            self.drawPixmapForPartiallyChecked(painter, width, height)
        elif role == self.Role.MODE_3D:
            self.drawPixmapFor3d(painter, width, height)
        elif role == self.Role.MODE_2D:
            self.drawPixmapFor2d(painter, width, height)
        elif role == self.Role.DISABLED:
            pixmap.fill(Qt.transparent)
        else:
            raise NotImplementedError(f"{role}")

        return pixmap

    def drawPixmapFor2d(self, painter: QPainter, width: int, height: int) -> None:
        pen = QPen(_FeatureSelectionColors.foreground())
        pen.setWidth(4)
        painter.setPen(pen)
        font = QFont()
        font.setPixelSize(height - 10)
        painter.setFont(font)
        painter.drawRect(QRect(5, 5, width - 15, height - 10))
        painter.fillRect(QRect(5, 5, width - 15, height - 10), _FeatureSelectionColors.green())

        painter.drawText(QRect(5, 4, width - 15, height - 10), Qt.AlignCenter, "2D")
        painter.end()

    def drawPixmapFor3d(self, painter: QPainter, width: int, height: int) -> None:
        font = QFont()
        font.setPixelSize(height - 10)
        pen = QPen(_FeatureSelectionColors.foreground())
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(_FeatureSelectionColors.light_gray()))
        top = [
            QPoint(5, 5),
            QPoint(width - 10, 5),
            QPoint(width - 5, 0),
            QPoint(10, 0),
            QPoint(5, 5),
        ]
        painter.drawConvexPolygon(*top)
        left = [
            QPoint(width - 10, 5),
            QPoint(width - 10, height - 5),
            QPoint(width - 5, height - 10),
            QPoint(width - 5, 0),
            QPoint(width - 10, 5),
        ]
        painter.drawConvexPolygon(*left)
        painter.setBrush(QBrush())
        painter.setFont(font)
        painter.drawRect(QRect(5, 5, width - 15, height - 10))
        painter.drawText(QRect(5, 4, width - 15, height - 10), Qt.AlignCenter, "3D")
        painter.end()

    def drawPixmapForUnchecked(self, painter: QPainter, width: int, height: int) -> None:
        pen = QPen(_FeatureSelectionColors.foreground())
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, width - 10, height - 10))
        painter.end()

    def drawPixmapForChecked(self, painter: QPainter, width: int, height: int) -> None:
        pen = QPen(_FeatureSelectionColors.foreground())
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, width - 10, height - 10))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(width // 2 - 5, height // 2, width // 2, height - 10)
        painter.drawLine(width // 2, height - 10, width // 2 + 10, 2)
        painter.end()

    def drawPixmapForPartiallyChecked(self, painter: QPainter, width: int, height: int) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(_FeatureSelectionColors.foreground())
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, width - 10, height - 10))
        pen.setWidth(4)
        pen.setColor(_FeatureSelectionColors.dark_gray())
        painter.setPen(pen)
        painter.drawLine(width // 2 - 5, height // 2, width // 2, height - 10)
        painter.drawLine(width // 2, height - 10, width // 2 + 10, 2)
        painter.end()

    def paint(self, painter, option, index):
        tableWidgetCell = self.parent().item(index.row(), index.column())
        if index.row() == 1:
            # paint sigma row
            painter.setRenderHint(QPainter.Antialiasing, True)
            if isinstance(tableWidgetCell.sigma, str):
                sigma_str = tableWidgetCell.sigma
            else:
                sigma_str = f"{tableWidgetCell.sigma:.2f}"
            painter.drawText(option.rect, Qt.AlignCenter, sigma_str)
        elif index.column() + 1 == self.parent().columnCount():
            # last column is always empty (exists only for adding another sigma). Except for sigma row (entry 'add')
            return
        elif index.row() == 0:
            # paint 'compute in 2d' row
            flags = tableWidgetCell.flags()
            if not (flags & Qt.ItemIsEnabled):
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.DISABLED, option.rect.size()))
            elif tableWidgetCell.featureState == Qt.Unchecked:
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.MODE_3D, option.rect.size()))
                option.state = QStyle.State_Off
            else:
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.MODE_2D, option.rect.size()))
        else:
            flags = tableWidgetCell.flags()
            if not (flags & Qt.ItemIsEnabled):
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.DISABLED, option.rect.size()))
            elif tableWidgetCell.featureState == Qt.Unchecked:
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.UNCHECKED, option.rect.size()))
                option.state = QStyle.State_Off
            elif tableWidgetCell.featureState == Qt.PartiallyChecked:
                painter.fillRect(option.rect.adjusted(5, 5, -5, -5), _FeatureSelectionColors.light_gray())
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.PARTIAL, option.rect.size()))
            else:
                painter.fillRect(option.rect.adjusted(5, 5, -5, -5), _FeatureSelectionColors.green())
                painter.drawPixmap(option.rect, self.getPixmap(self.Role.CHECKED, option.rect.size()))


# ==============================================================================
# FeatureTableWidget2d
# ==============================================================================
class FeatureTableWidget2d(QTableWidgetItem):
    def __init__(self, enabled=None, featureState=Qt.Unchecked):
        QTableWidgetItem.__init__(self)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        if enabled is not None:
            self.setEnabled(enabled)

        self.isRootNode = False
        self.children = []
        self.featureState = featureState

    def __hash__(self):
        return hash((self.row(), self.column()))

    def setEnabled(self, enabled):
        flags = self.flags()
        if enabled:
            flags |= Qt.ItemIsEnabled
        else:
            flags &= ~Qt.ItemIsEnabled
        self.setFlags(flags)

    def setFeatureState(self, state):
        self.featureState = state

    def toggleState(self):
        if self.featureState == Qt.Unchecked:
            self.featureState = Qt.Checked
        else:
            self.featureState = Qt.Unchecked


# ==============================================================================
# FeatureTableWidgetSigma
# ==============================================================================
class FeatureTableWidgetSigma(QTableWidgetItem):
    def __init__(self, sigma):
        QTableWidgetItem.__init__(self)
        self.sigma = sigma
        flags = self.flags()
        flags |= Qt.ItemIsEditable
        flags &= ~Qt.ItemIsSelectable
        self.setFlags(flags)


# ==============================================================================
# FeatureTableWidgetItem
# ==============================================================================
class FeatureTableWidgetItem(QTableWidgetItem):
    def __init__(self, enabled=None, featureState=Qt.Unchecked):
        QTableWidgetItem.__init__(self)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        if enabled is not None:
            self.setEnabled(enabled)

        self.isRootNode = False
        self.children = []
        self.featureState = featureState

    def __hash__(self):
        return hash((self.row(), self.column()))

    def setEnabled(self, enabled):
        flags = self.flags()
        if enabled:
            flags |= Qt.ItemIsEnabled
        else:
            flags &= ~Qt.ItemIsEnabled
        self.setFlags(flags)

    def setFeatureState(self, state):
        self.featureState = state

    def toggleState(self):
        if self.featureState == Qt.Unchecked:
            self.featureState = Qt.Checked
        else:
            self.featureState = Qt.Unchecked


# ==============================================================================
# FeatureTableWidget
# ==============================================================================
class FeatureTableWidget(QTableWidget):
    def __init__(self, parent=None, featureGroups=[], sigmas=[], computeIn2d=[], window_size=3.5):
        """
        Args:
            featureGroups: A list with schema: [ (groupName1, [entry, entry...]),
                                                 (groupName2, [entry, entry...]), ... ]
            sigmas: List of sigmas (applies to all features)
            computeIn2d: List of booleans to indicate which sigma column should be computed in 2d (rather than 3d)
        """
        QTableWidget.__init__(self, parent)

        self.setCornerButtonEnabled(False)
        self.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setShowGrid(False)
        self.setMouseTracking(1)

        self.verticalHeader().setHighlightSections(False)
        self.verticalHeader().setSectionsClickable(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().sectionPressed.disconnect()
        self.verticalHeader().sectionClicked.connect(self._expandOrCollapseVHeader)

        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionsClickable(False)
        # self.horizontalHeader().installEventFilter(self)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.itemSelectionChanged.connect(self._itemSelectionChanged)
        self.cellChanged.connect(self._cellChanged)
        if featureGroups or sigmas or computeIn2d:
            self.setup(featureGroups, sigmas, computeIn2d, window_size)

    def setup(self, featureGroups: list, sigmas: list, computeIn2d: list, window_size=3.5):
        self.window_size = window_size
        assert featureGroups, "featureGroups may not be empty"
        assert isinstance(featureGroups, (list, tuple)), featureGroups
        assert isinstance(featureGroups[0], (list, tuple))
        assert isinstance(featureGroups[0][0], str)
        assert isinstance(featureGroups[0][1], list)
        assert all([fg[1] for fg in featureGroups]), "all featureGroups must have entries"
        if computeIn2d:
            assert len(sigmas) == len(computeIn2d), (sigmas, computeIn2d)
        elif sigmas:
            computeIn2d = [False] * len(sigmas)

        self.setSigmas(sigmas, computeIn2d)
        self.setFeatureGroups(featureGroups)
        self._setFixedSizeToHeaders()
        self._setSizeHintToTableWidgetItems()
        self.itemDelegate = ItemDelegate(self)
        self.setItemDelegate(self.itemDelegate)
        self._updateRootItems()

        self._collapsAllRows()  # Hide fine-grain control by default
        self._resetSelection()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._resetSelection()

    def _selectAllFeatures(self):
        """
        Selects all features without modifying the 2d/3d switches
        """
        # top (1st row 2d/3d, 2nd row sigma value), left, bottom, right
        selection_range = QTableWidgetSelectionRange(2, 0, self.rowCount() - 1, self.columnCount() - 2)
        self.setRangeSelected(selection_range, True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Overrides default select all shortcut to avoid toggling 2d/3d state
        is_select_all_shortcut = event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A
        if is_select_all_shortcut:
            self._selectAllFeatures()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, e):
        super().keyReleaseEvent(e)
        if e.key() == Qt.Key_Shift:
            self.preSelectionState = {}
            self.clearSelection()
            self._resetSelection()
        elif e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            self.preSelectionState = {}
            self.clearSelection()
            self._resetSelection()

    @property
    def computeIn2d(self):
        return [self.item(0, col).featureState == Qt.Checked for col in range(self.columnCount() - 1)]

    @property
    def sigmas(self):
        return self._sigmas

    def setSigmas(self, sigmas, computeIn2d=[]):
        assert isinstance(sigmas, list), type(sigmas)
        assert sigmas, "sigmas cannot be empty"
        if computeIn2d:
            assert len(sigmas) == len(computeIn2d)
            self._computeIn2d = computeIn2d
        elif len(sigmas) == len(self.computeIn2d):
            self._computeIn2d = self.computeIn2d  # use old computeIn2d flags
        else:
            self._computeIn2d = [False] * len(sigmas)

        self._sigmas = sigmas
        self.setColumnCount(len(sigmas) + 1)
        for column, s in enumerate(sigmas):
            self.setHorizontalHeaderItem(column, FeatureTableWidgetHHeader(column, s, window_size=self.window_size))

        column += 1
        self.setHorizontalHeaderItem(column, FeatureTableWidgetHHeader(column))
        self._fillTabelWithItems()

    def setFeatureGroups(self, featureGroups):
        self.setRowCount(2)
        self.setVerticalHeaderItem(0, FeatureTableWidgetV2dHeader())
        self.setVerticalHeaderItem(1, FeatureTableWidgetVSigmaHeader())
        self.minimum_scale_for_row = [None] * 2
        row = 2
        for group, features in featureGroups:
            self.insertRow(row)
            self.minimum_scale_for_row.append(None)
            vGroupHeader = FeatureTableWidgetVHeader()
            vGroupHeader.setGroupVHeader(group)
            self.setVerticalHeaderItem(row, vGroupHeader)
            row += 1
            for feature in features:
                self.insertRow(row)
                self.minimum_scale_for_row.append(feature.minimum_scale)
                vFeatureHeader = FeatureTableWidgetVHeader()
                vFeatureHeader.setFeatureVHeader(feature)
                self.setVerticalHeaderItem(row, vFeatureHeader)
                vGroupHeader.children.append(row)
                row += 1

        self._fillTabelWithItems()

    def row_valid_for_sigma(self, row, sigma):
        return sigma >= self.minimum_scale_for_row[row]

    @property
    def featureMatrix(self):
        matrix = []
        for row in range(2, self.rowCount()):
            if not self.verticalHeaderItem(row).isRootNode:
                matrix.append(
                    [
                        self.item(row, col).featureState == Qt.Checked
                        and bool(self.item(row, col).flags() & Qt.ItemIsEnabled)
                        for col in range(self.columnCount() - 1)
                    ]
                )

        return matrix

    def setFeatureMatrix(self, featureMatrix):
        feautre_row = 0
        for row in range(2, self.rowCount()):
            if not self.verticalHeaderItem(row).isRootNode:
                for column in range(self.columnCount() - 1):
                    if featureMatrix[feautre_row][column]:
                        self.item(row, column).setFeatureState(Qt.Checked)
                    else:
                        self.item(row, column).setFeatureState(Qt.Unchecked)

                feautre_row += 1

        self._updateRootItems()

    def focusCell(self, row, column):
        self._resetSelection()
        self.setCurrentCell(row, column)
        self.clearSelection()

    def _tableEntries(self):
        for row in range(self.rowCount()):
            for column in range(self.columnCount() - 1):
                yield row, column

    def sizeHint(self):
        height = super().sizeHint().height()
        width = (
            self.horizontalHeader().sizeHint().width() * self.columnCount()
            + self.verticalHeader().sizeHint().width()
            + 22
        )
        return QSize(width, height)

    def _setSizeHintToTableWidgetItems(self):
        width = self.horizontalHeader().sizeHint().width()
        height = self.verticalHeader().sizeHint().height()
        for r, c in self._tableEntries():
            self.item(r, c).setSizeHint(QSize(width + 5, height + 5))

    def _setFixedSizeToHeaders(self):
        hHeaderSize = self.horizontalHeader().sizeHint()
        vHeaderSize = self.verticalHeader().sizeHint()
        for i in range(self.columnCount() - 1):
            self.horizontalHeaderItem(i).setSizeHint(hHeaderSize)
        for j in range(self.rowCount()):
            self.verticalHeaderItem(j).setSizeHint(vHeaderSize)

    def _fillTabelWithItems(self):
        for column in range(self.columnCount() - 1):
            in2d = Qt.Checked if self._computeIn2d[column] else Qt.Unchecked
            self.setItem(0, column, FeatureTableWidget2d(enabled=True, featureState=in2d))
            sigma = self.sigmas[column]
            self.setItem(1, column, FeatureTableWidgetSigma(sigma))
            for row in range(2, self.rowCount()):
                item = FeatureTableWidgetItem()
                if self.verticalHeaderItem(row).isRootNode:
                    item.isRootNode = True
                    parent = item
                else:
                    item.setEnabled(self.row_valid_for_sigma(row, sigma))
                    parent.children.append(item)

                self.setItem(row, column, item)

        column += 1
        self.setItem(0, column, FeatureTableWidget2d(enabled=False))
        self.setItem(1, column, FeatureTableWidgetSigma("add"))
        for row in range(2, self.rowCount()):
            self.setItem(row, column, FeatureTableWidgetItem(enabled=False))

        self.focusCell(2, 0)
        self._setSizeHintToTableWidgetItems()

    def _expandOrCollapseVHeader(self, row):
        self._resetSelection()
        vHeader = self.verticalHeaderItem(row)
        if vHeader.children:
            if vHeader.isExpanded:
                for subRow in vHeader.children:
                    self.hideRow(subRow)
                    vHeader.setCollapsed()
            else:
                vHeader.setExpanded()
                for subRow in vHeader.children:
                    self.showRow(subRow)

    def _collapsAllRows(self):
        for i in range(2, self.rowCount()):
            if not self.verticalHeaderItem(i).isRootNode:
                self.hideRow(i)
            else:
                self.verticalHeaderItem(i).setCollapsed()

    def _cellChanged(self, row, column):
        if row == 1:
            item = self.item(row, column)
            try:
                sigma = float(item.text())
            except ValueError:
                sigma = -1
            if sigma == 0:
                # remove column
                in2d = self.computeIn2d
                in2d = in2d[:column] + in2d[column + 1 :]
                matrix = [r[:column] + r[column + 1 :] for r in self.featureMatrix]
                self.setSigmas(self.sigmas[:column] + self.sigmas[column + 1 :], in2d)
                self.setFeatureMatrix(matrix)
                self.focusCell(2, 0)
            elif sigma >= min([s for s in self.minimum_scale_for_row if s is not None]):
                if column + 1 == self.columnCount():
                    # add new column
                    matrix = [r + [Qt.Unchecked] for r in self.featureMatrix]
                    try:
                        lastIn2d = self.computeIn2d[-1]
                    except IndexError:
                        lastIn2d = False
                    self.setSigmas(self.sigmas + [sigma], self.computeIn2d + [lastIn2d])
                    self.setFeatureMatrix(matrix)
                else:
                    # change existing sigma
                    matrix = self.featureMatrix
                    newSigmas = self.sigmas
                    newSigmas[column] = sigma
                    self.setSigmas(newSigmas, self.computeIn2d)
                    self.setFeatureMatrix(matrix)

                self.focusCell(2, column)

    def _resetSelection(self):
        self.preSelectionState = {}
        self.lastSelectedItems = []
        self.clearSelection()

    def _set_new_state(self, selectedItems):
        firstItem = selectedItems[0]
        if firstItem.featureState == Qt.Checked:
            self.newState = Qt.Unchecked
        else:
            self.newState = Qt.Checked

    def _itemSelectionChanged(self):
        # ignore sigma row and last column (empty for new sigma)
        selectedItems = [
            item for item in self.selectedItems() if item.row() != 1 and item.column() + 1 < self.columnCount()
        ]

        if self.lastSelectedItems:
            # some items were already selected before
            if len(selectedItems) == 1:
                self._set_new_state(selectedItems)

            # continue selection => only process difference to previous selection
            if all([item.isRootNode for item in selectedItems]):
                # all items are root nodes => select all their children instead
                selectInstead = []
                for item in selectedItems:
                    for child in item.children:
                        selectInstead.append(child)

                selectedItems = selectInstead
            else:
                # mixed selection => ignore root items
                selectedItems = [item for item in selectedItems if not item.isRootNode]

            selected = [item for item in selectedItems if item not in self.lastSelectedItems]
            unselected = [item for item in self.lastSelectedItems if item not in selectedItems]

        elif selectedItems:
            # Start a new selection
            self._set_new_state(selectedItems)
            selectInstead = []
            for item in selectedItems:
                if item.isRootNode:
                    selectInstead += [child for child in item.children]
                else:
                    selectInstead.append(item)

            selectedItems = selectInstead
            selected = selectedItems
            unselected = []
        else:
            # no change in (relevant) selection
            selected = []
            unselected = []

        for item in selected:
            # save item state
            self.preSelectionState[item] = item.featureState
            item.setFeatureState(self.newState)

        for item in unselected:
            try:
                # restore item state
                item.setFeatureState(self.preSelectionState[item])
            except Exception:
                pass  # selection was reset

        self.lastSelectedItems = selectedItems
        self._updateRootItems()

    def _updateRootItems(self):
        for row in range(2, self.rowCount()):
            for column in range(self.columnCount() - 1):
                item = self.item(row, column)
                if item.isRootNode:
                    flags = item.flags()
                    enabled_children = [child for child in item.children if child.flags() & Qt.ItemIsEnabled]
                    if enabled_children:
                        flags |= Qt.ItemIsEnabled
                        children = [child.featureState == Qt.Checked for child in enabled_children]
                        if any(children):
                            if all(children):
                                item.featureState = Qt.Checked
                            else:
                                item.featureState = Qt.PartiallyChecked
                        else:
                            item.featureState = Qt.Unchecked
                    else:
                        flags &= ~Qt.ItemIsEnabled

                    item.setFlags(flags)

            self.viewport().update()


if __name__ == "__main__":
    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    t = FeatureTableWidget(
        None,
        (
            ("Color", [FeatureEntry("Banana", minimum_scale=0.3)]),
            ("Edge", [FeatureEntry("Mango"), FeatureEntry("Cherry")]),
        ),
        [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0],
    )
    t.show()
    t.raise_()
    app.exec_()
