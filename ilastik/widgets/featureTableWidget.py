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
from past.utils import old_div
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QImage, QPainter, QPen, QPixmap, QPolygon
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QItemDelegate, QStyle, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QPoint, QRect, QSize, Qt


class FeatureEntry(object):
    def __init__(self, name, minimum_scale=.7):
        self.name = name
        self.minimum_scale = minimum_scale


# ==============================================================================
# FeatureTableWidgetV2dHeader
# ==============================================================================
class FeatureTableWidgetV2dHeader(QTableWidgetItem):
    isExpanded = False
    children = []

    def __init__(self, text='Compute in 2D/3D'):
        QTableWidgetItem.__init__(self)
        self.setText(text)


# ==============================================================================
# FeatureTableWidgetVSigmaHeader
# ==============================================================================
class FeatureTableWidgetVSigmaHeader(QTableWidgetItem):
    isExpanded = False
    children = []

    def __init__(self, text='Sigma'):
        QTableWidgetItem.__init__(self)
        self.setText(text)


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

    def setIconAndTextColor(self, color):
        self._drawIcon(color)

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

    def _drawIcon(self, color=Qt.black):
        self.setForeground(QBrush(color))

        if self.isRootNode:
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(color)
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
    sub_trans = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')

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

    def setNameAndBrush(self, sigma, color=Qt.black):
        self.sigma = sigma
        self.setText(f'σ{self.column}'.translate(self.sub_trans))
        if self.sigma is not None:
            total_window = (1 + 2 * int(self.sigma * self.window_size + 0.5))
            self.setToolTip(f'sigma = {sigma:.1f} pixels, window diameter = {total_window:.1f}')
        font = QFont()
        font.setPointSize(10)
        # font.setBold(True)
        self.setFont(font)
        self.setForeground(color)

        pixmap = QPixmap(self.pixmapSize)
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(color)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.drawEllipse(QRect(old_div(self.pixmapSize.width(), 2) - old_div(self.brushSize, 2),
                                  old_div(self.pixmapSize.height(), 2) - old_div(self.brushSize, 2),
                                  self.brushSize, self.brushSize))
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setTextAlignment(Qt.AlignVCenter)

    def setIconAndTextColor(self, color):
        self.setNameAndBrush(self.sigma, color)


# ==============================================================================
# ItemDelegate
# ==============================================================================
class ItemDelegate(QItemDelegate):
    """"
     TODO: DOKU
    """

    def __init__(self, parent, width, height):
        QItemDelegate.__init__(self, parent)

        self.itemWidth = width
        self.itemHeight = height
        self.icon2d = None
        self.icon3d = None
        self.checkedIcon = None
        self.partiallyCheckedIcon = None
        self.uncheckedIcon = None
        self.pixmap2d = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapFor2d()
        self.pixmap3d = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapFor3d()
        self.pixmapUnckecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForUnckecked()
        self.pixmapCkecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForCkecked()
        self.pixmapPartiallyChecked = QPixmap(self.itemWidth, self.itemHeight)
        self.drawPixmapForPartiallyChecked()
        self.drawPixmapForDisabled()

        # self.itemEditorFactory().setDefaultFactory(QDoubleSpinBox)

    def drawPixmapForDisabled(self):
        self.pixmapDisabled = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapDisabled.fill(Qt.white)

    def drawPixmapFor2d(self):
        self.pixmap2d = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmap2d.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmap2d)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, self.itemWidth - 10, self.itemHeight - 10))
        painter.fillRect(QRect(5, 5, self.itemWidth - 10, self.itemHeight - 10), QColor(0, 250, 154))

        painter.drawText(QRect(5, 5, self.itemWidth - 10, self.itemHeight - 10), Qt.AlignCenter, '2D')
        painter.end()

    def drawPixmapFor3d(self):
        self.pixmap3d = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmap3d.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmap3d)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        top = [QPoint(5, 10),
               QPoint(self.itemWidth - 10, 10),
               QPoint(self.itemWidth - 5, 5),
               QPoint(10, 5),
               QPoint(5, 10)]
        painter.drawConvexPolygon(*top)
        left = [QPoint(self.itemWidth - 10, 10),
                QPoint(self.itemWidth - 10, self.itemHeight - 5),
                QPoint(self.itemWidth - 5, self.itemHeight - 10),
                QPoint(self.itemWidth - 5, 5),
                QPoint(self.itemWidth - 10, 10)]
        painter.drawConvexPolygon(*left)
        painter.setBrush(QBrush())
        painter.drawRect(QRect(5, 10, self.itemWidth - 15, self.itemHeight - 15))
        painter.drawText(QRect(5, 10, self.itemWidth - 15, self.itemHeight - 15), Qt.AlignCenter, '3D')
        painter.end()

    def drawPixmapForUnckecked(self):
        self.pixmapUnckecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapUnckecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapUnckecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, self.itemWidth - 10, self.itemHeight - 10))
        painter.end()

    def drawPixmapForCkecked(self):
        self.pixmapCkecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapCkecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapCkecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, self.itemWidth - 10, self.itemHeight - 10))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawLine(old_div(self.itemWidth, 2) - 5, old_div(self.itemHeight, 2),
                         old_div(self.itemWidth, 2), self.itemHeight - 9)
        painter.drawLine(old_div(self.itemWidth, 2), self.itemHeight - 9, old_div(self.itemWidth, 2) + 10, 2)
        painter.end()

    def drawPixmapForPartiallyChecked(self):
        self.pixmapPartiallyChecked = QPixmap(self.itemWidth, self.itemHeight)
        self.pixmapPartiallyChecked.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(self.pixmapPartiallyChecked)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen()
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(QRect(5, 5, self.itemWidth - 10, self.itemHeight - 10))
        pen.setWidth(4)
        pen.setColor(QColor(139, 137, 137))
        painter.setPen(pen)
        painter.drawLine(old_div(self.itemWidth, 2) - 5, old_div(self.itemHeight, 2),
                         old_div(self.itemWidth, 2), self.itemHeight - 9)
        painter.drawLine(old_div(self.itemWidth, 2), self.itemHeight - 9, old_div(self.itemWidth, 2) + 10, 2)
        painter.end()

    def paint(self, painter, option, index):
        tableWidgetCell = self.parent().item(index.row(), index.column())
        if index.row() == 1:
            # paint sigma row
            painter.setRenderHint(QPainter.Antialiasing, True)
            if isinstance(tableWidgetCell.sigma, str):
                sigma_str = tableWidgetCell.sigma
            else:
                sigma_str = f'{tableWidgetCell.sigma:.2f}'
            painter.drawText(option.rect, Qt.AlignCenter, sigma_str)
        elif index.column() + 1 == self.parent().columnCount():
            # last column is always empty (exists only for adding another sigma). Except for sigma row (entry 'add')
            return
        elif index.row() == 0:
            # paint 'compute in 2d' row
            flags = tableWidgetCell.flags()
            if not (flags & Qt.ItemIsEnabled):
                painter.drawPixmap(option.rect, self.pixmapDisabled)
            elif tableWidgetCell.featureState == Qt.Unchecked:
                if self.icon3d is not None:
                    painter.drawImage(self.adjustRectForImage(option), self.icon3d)
                else:
                    painter.drawPixmap(option.rect, self.pixmap3d)
                    option.state = QStyle.State_Off
            else:
                if self.icon2d is not None:
                    painter.drawImage(self.adjustRectForImage(option), self.icon2d)
                else:
                    painter.drawPixmap(option.rect, self.pixmap2d)
        else:
            flags = tableWidgetCell.flags()
            if not (flags & Qt.ItemIsEnabled):
                painter.drawPixmap(option.rect, self.pixmapDisabled)
            elif tableWidgetCell.featureState == Qt.Unchecked:
                if self.uncheckedIcon is not None:
                    painter.drawImage(self.adjustRectForImage(option), self.uncheckedIcon)
                else:
                    painter.drawPixmap(option.rect, self.pixmapUnckecked)
                    option.state = QStyle.State_Off
            elif tableWidgetCell.featureState == Qt.PartiallyChecked:
                if self.partiallyCheckedIcon is not None:
                    painter.drawImage(self.adjustRectForImage(option), self.partiallyCheckedIcon)
                else:
                    painter.fillRect(option.rect.adjusted(3, 3, -3, -3), QColor(220, 220, 220))
                    painter.drawPixmap(option.rect, self.pixmapPartiallyChecked)
            else:
                if self.checkedIcon is not None:
                    painter.drawImage(self.adjustRectForImage(option), self.checkedIcon)
                else:
                    painter.fillRect(option.rect.adjusted(3, 3, -3, -3), QColor(0, 250, 154))
                    painter.drawPixmap(option.rect, self.pixmapCkecked)

            # Be careful with this! It may call itself recursively.
            # self.parent().update()

    def setCheckBoxIcons(self, checked=None, partiallyChecked=None, unchecked=None, icon2d=None, icon3d=None):
        if checked is not None:
            self.checkedIcon = QImage(checked)
        if partiallyChecked is not None:
            self.partiallyCheckedIcon = QImage(partiallyChecked)
        if unchecked is not None:
            self.uncheckedIcon = QImage(unchecked)
        if icon2d is not None:
            self.icon2d = QImage(icon2d)
        if icon3d is not None:
            self.icon3d = QImage(icon3d)

    def adjustRectForImage(self, option):
        if self.itemWidth > self.itemHeight:
            return option.rect.adjusted(old_div((self.itemWidth - self.itemHeight), 2) + 5, 5,
                                        -(old_div((self.itemWidth - self.itemHeight), 2)) - 5, -5)
        else:
            return option.rect.adjusted(5, old_div((self.itemHeight - self.itemWidth), 2) + 5,
                                        -(old_div((self.itemHeight - self.itemWidth), 2)) - 5, -5)


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
        assert featureGroups, 'featureGroups may not be empty'
        assert isinstance(featureGroups, (list, tuple)), featureGroups
        assert isinstance(featureGroups[0], (list, tuple))
        assert isinstance(featureGroups[0][0], str)
        assert isinstance(featureGroups[0][1], list)
        assert all([fg[1] for fg in featureGroups]), 'all featureGroups must have entries'
        if computeIn2d:
            assert len(sigmas) == len(computeIn2d), (sigmas, computeIn2d)
        elif sigmas:
            computeIn2d = [False] * len(sigmas)

        self.setSigmas(sigmas, computeIn2d)
        self.setFeatureGroups(featureGroups)
        self._setFixedSizeToHeaders()
        self._setSizeHintToTableWidgetItems()
        self.itemDelegate = ItemDelegate(self, self.horizontalHeader().sizeHint().width(),
                                         self.verticalHeader().sizeHint().height())
        self.setItemDelegate(self.itemDelegate)
        self._updateRootItems()

        self._collapsAllRows()  # Hide fine-grain control by default
        self._resetSelection()

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self._resetSelection()

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
        assert sigmas, 'sigmas cannot be empty'
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
                matrix.append([self.item(row, col).featureState == Qt.Checked and
                               bool(self.item(row, col).flags() & Qt.ItemIsEnabled)
                               for col in range(self.columnCount() - 1)])

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
        width = self.horizontalHeader().sizeHint().width() * self.columnCount() + \
            self.verticalHeader().sizeHint().width() + 22
        return QSize(width, height)

    def _setSizeHintToTableWidgetItems(self):
        width = self.horizontalHeader().sizeHint().width()
        height = self.verticalHeader().sizeHint().height()
        for r, c in self._tableEntries():
            self.item(r, c).setSizeHint(QSize(width, height))

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
        self.setItem(1, column, FeatureTableWidgetSigma('add'))
        for row in range(2, self.rowCount()):
            self.setItem(row, column, FeatureTableWidgetItem(enabled=False))

        self.focusCell(2, 0)

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
                in2d = in2d[:column] + in2d[column + 1:]
                matrix = [r[:column] + r[column + 1:] for r in self.featureMatrix]
                self.setSigmas(self.sigmas[:column] + self.sigmas[column + 1:], in2d)
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
        selectedItems = [item
                         for item in self.selectedItems()
                         if item.row() != 1 and item.column() + 1 < self.columnCount()]

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


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    t = FeatureTableWidget(None,
        (("Color", [FeatureEntry("Banana", minimum_scale=.3)]),
         ("Edge", [FeatureEntry("Mango"), FeatureEntry("Cherry")])),
        [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
    t.show()
    t.raise_()
    app.exec_()
