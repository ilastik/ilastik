###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################

import colorsys
import csv
import logging
import time
import warnings
from typing import Iterable, TextIO, Tuple

import numpy as np

import vigra
from ilastik.utility.gui import roi2rect
from ilastik.widgets.boxListModel import BoxLabel, BoxListModel
from lazyflow.graph import Graph, Operator, OutputSlot
from lazyflow.operator import InputSlot
from lazyflow.operators.generic import OpSubRegion
from past.utils import old_div
from PyQt5.QtCore import QEvent, QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QRubberBand,
    QStylePainter,
)
from volumina import colortables
from volumina.api import Viewer, createDataSource
from volumina.colortables import jet
from volumina.layer import ColortableLayer

logger = logging.getLogger(__name__)

DELAY = 10  # In millisec,delay in updating the text in the handles, needed because lazy flow cannot stay back the
# user shuffling the boxes


class Tool(object):

    Navigation = 0  # Arrow
    Paint = 1
    Erase = 2
    Threshold = 3
    Box = 4


class ResizeHandle(QGraphicsRectItem):
    def __init__(self, rect, constrainAxis, parent):
        size = 5
        self._rect = rect
        super(ResizeHandle, self).__init__(old_div(-size, 2), old_div(-size, 2), 2 * size, 2 * size, parent)

        self._constrainAxis = constrainAxis
        self._hoverOver = False

        self.resetOffset(constrainAxis, rect)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self._updateColor()

    def resetOffset(self, constrainAxis, rect=None):
        if rect == None:
            rect = self._rect

        if constrainAxis == 0:
            if rect.bottom() > 0:
                self._offset = (old_div((rect.left() + rect.right()), 2.0), rect.bottom())
            else:
                self._offset = (old_div((rect.left() + rect.right()), 2.0), rect.top())

        elif constrainAxis == 1:
            if rect.right() > 0:
                self._offset = (rect.right(), old_div((rect.top() + rect.bottom()), 2.0))
            else:
                self._offset = (rect.left(), old_div((rect.top() + rect.bottom()), 2.0))

        self.setPos(QPointF(*self._offset))
        self._rect = rect

    def hoverEnterEvent(self, event):
        super(ResizeHandle, self).hoverEnterEvent(event)
        event.setAccepted(True)
        self._hoverOver = True
        self._updateColor()
        if hasattr(self.parentItem(), "_editor") and self.parentItem()._editor:
            if isinstance(self.parentItem()._editor.eventSwitch.interpreter, BoxInterpreter):
                if self._constrainAxis == 0:
                    QApplication.setOverrideCursor(Qt.SplitVCursor)
                else:
                    QApplication.setOverrideCursor(Qt.SplitHCursor)

    def hoverLeaveEvent(self, event):
        super(ResizeHandle, self).hoverLeaveEvent(event)
        self._hoverOver = False
        self._updateColor()
        QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, event):
        super(ResizeHandle, self).mouseMoveEvent(event)

        axes = [0, 1]
        rect = self._rect
        flip = False
        if self._constrainAxis == 0:

            if old_div((rect.left() + rect.right()), 2.0) < 0:
                flip = True
            newPoint = QPointF(old_div((rect.left() + rect.right()), 2.0), self.pos().y())
            self.setPos(newPoint)
            self.parentItem().setNewSize(axes[self._constrainAxis], self.pos().y(), flip)
        else:

            if old_div((rect.top() + rect.bottom()), 2.0) < 0:
                flip = True
            self.setPos(QPointF(self.pos().x(), old_div((rect.top() + rect.bottom()), 2.0)))
            self.parentItem().setNewSize(axes[self._constrainAxis], self.pos().x(), flip=flip)

    def _updateColor(self):

        color = Qt.white

        if self._hoverOver:
            self.setBrush(QBrush(color))
            self.setPen(QPen(color))
        else:
            self.setBrush(QBrush(color))
            self.setPen(color)

    def itemChange(self, change, value):
        """
        Enforce that the handle stays in the region of the scene

        """

        if change == QGraphicsRectItem.ItemPositionChange:
            newPos = value  # new position in rectangle coordinates
            nPosScene = self.parentItem().mapToScene(newPos)
            rect = self.parentItem().scene().sceneRect()
            if not rect.contains(nPosScene):
                nPosScene.setX(min(rect.right(), max(nPosScene.x(), rect.left())))
                nPosScene.setY(min(rect.bottom(), max(nPosScene.y(), rect.top())))
                return self.parentItem().mapFromScene(nPosScene)

        return QGraphicsRectItem.itemChange(self, change, value)


class QGraphicsResizableRectSignaller(QObject):
    """
     This class is used to emit signals since only QObjects can do it.
     Multiple inheritance is not supported for qt-python classes (Qt 4.10)
    """

    signalHasMoved = pyqtSignal(QPointF)  # The resizable rectangle has moved the new position
    signalSelected = pyqtSignal()
    signalHasResized = pyqtSignal()
    colorHasChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        QObject.__init__(self, parent=parent)


class QGraphicsResizableRect(QGraphicsRectItem):
    hoverColor = QColor(255, 0, 0)  # _hovering and selection color

    def __init__(self, x, y, h, w, scene=None, parent=None, editor=None):
        """"
        This class implements the resizable rectangle item which is dispalied on the scene
         x y should be the original positions in scene coordinates
         h,w are the height and the width of the rectangle
        """

        self._editor = editor

        QGraphicsRectItem.__init__(self, 0, 0, w, h, parent=parent)
        self.Signaller = QGraphicsResizableRectSignaller(parent=parent)

        scene.addItem(self)

        # Default Appearence Properties
        self._fontColor = QColor(255, 255, 255)
        self._fontSize = 10
        self._lineWidth = 1

        ##Note: need to do like this because the x,y of the graphics item fix the position
        # of the zero relative to the scene
        self.moveBy(x, y)

        # Flags
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

        self._resizeHandles = []

        # A bit of flags
        self._hovering = False
        self._normalColor = QColor(0, 0, 255)
        self.updateColor()
        self._has_moved = False
        self._selected = False
        self._dbg = False
        self._setupTextItem()
        self._isFixed = False

        self.initHandles()
        self.hideHandles()

        self.setToolTip("Hold CTRL to drag the box")

    @property
    def fontColor(self):
        return self._fontColor

    @pyqtSlot(int)
    def setFontColor(self, color):
        self._fontColor = color
        self.textItem.setDefaultTextColor(color)
        self.updateText(self.textItem.toPlainText())

    @property
    def fontSize(self):
        return self._fontSize

    @pyqtSlot(int)
    def setFontSize(self, s):
        self._fontSize = s
        font = QFont()
        font.setPointSize(self._fontSize)
        self.textItem.setFont(font)
        self.updateText(self.textItem.toPlainText())

    @property
    def lineWidth(self):
        return self._lineWidth

    @pyqtSlot(int)
    def setLineWidth(self, s):
        self._lineWidth = s
        self.updateColor()

    @property
    def color(self):
        return self._normalColor

    @pyqtSlot(int)
    def setColor(self, qcolor):
        self._normalColor = qcolor
        self.updateColor()

    @pyqtSlot()
    def _setupTextItem(self):
        # Set up the text
        self.textItem = QGraphicsTextItem("", parent=self)
        textItem = self.textItem
        font = QFont()
        font.setPointSize(self._fontSize)
        textItem.setFont(font)
        textItem.setPos(QPointF(0, 0))  # upper left corner relative to the father

        textItem.setDefaultTextColor(self._fontColor)

        if self._dbg:
            # another text item only for debug
            self.textItemBottom = QGraphicsTextItem("", parent=self)
            self.textItemBottom.setPos(QPointF(self.width, self.height))
            self.textItemBottom.setDefaultTextColor(QColor(255, 255, 255))

            self._updateTextBottom("shape " + str(self.shape))

    @pyqtSlot(str)
    def _updateTextBottom(self, string):
        self.textItemBottom.setPlainText(string)

    def setNewSize(self, constrainAxis, size, flip=False):

        if constrainAxis == 0:
            h, w = size, self.rect().width()

        else:
            h, w = self.rect().height(), size

        if flip and constrainAxis == 0:
            w = -w
        if flip and constrainAxis == 1:
            h = -h
        newrect = QRectF(0, 0, w, h).normalized()
        self.setRect(newrect)
        self.width = self.rect().width()
        self.height = self.rect().height()
        self.shape = (self.height, self.width)

        # Ensures that the text is in the upper left corner
        a = 0
        b = 0
        if w <= 0:
            a = w
        if h <= 0:
            b = h
        self.textItem.setPos(QPointF(a, b))

        if self._dbg:
            self.textItemBottom.setPos(QPointF(self.width, self.height))

        for el in self._resizeHandles:
            el.resetOffset(el._constrainAxis, rect=newrect)

        self.Signaller.signalHasResized.emit()

    def hoverEnterEvent(self, event):
        event.setAccepted(True)
        self._hovering = True
        self.updateColor()
        self.setSelected(True)
        self.showHandles()

        super(QGraphicsResizableRect, self).hoverEnterEvent(event)
        self._editor.imageViews[2].setFocus()

    def hoverLeaveEvent(self, event):
        event.setAccepted(True)
        self._hovering = False
        self.setSelected(False)
        self.hideHandles()
        super(QGraphicsResizableRect, self).hoverLeaveEvent(event)

    def initHandles(self):
        for constrAxes in range(2):
            h = ResizeHandle(self.rect(), constrAxes, self)
            self._resizeHandles.append(h)

    def moveHandles(self):
        for h, constrAxes in zip(self._resizeHandles, list(range(2))):
            h.resetOffset(constrAxes, self.rect())

    def hideHandles(self):
        for h in self._resizeHandles:
            h.hide()

    def showHandles(self):
        for h in self._resizeHandles:
            h.show()

    @pyqtSlot(int)
    def setSelected(self, selected):
        QGraphicsRectItem.setSelected(self, selected)
        if self.isSelected():
            self.Signaller.signalSelected.emit()
        if not self.isSelected():
            self._hovering = False
        self.updateColor()

    @pyqtSlot()
    def updateColor(self):
        color = self.hoverColor if (self._hovering or self.isSelected()) else self._normalColor
        self.setPen(QPen(color, self._lineWidth))
        self.setBrush(QBrush(color, Qt.NoBrush))

    def dataPos(self):
        dataPos = self.scenePos()
        pos = [int(dataPos.x()), int(dataPos.y())]

        return pos

    def topLeftDataPos(self):
        dataPos = self.rect().topLeft() + self.scene().scene2data.map(self.scenePos())
        pos = [int(dataPos.x()), int(dataPos.y())]

        return pos

    def bottomRightDataPos(self):
        dataPos = self.rect().bottomRight() + self.scene().scene2data.map(self.scenePos())
        pos = [int(dataPos.x()), int(dataPos.y())]
        return pos

    def mousePressEvent(self, event):
        modifiers = QApplication.queryKeyboardModifiers()
        if modifiers == Qt.ControlModifier:
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = self.dataPos()

        modifiers = QApplication.queryKeyboardModifiers()
        if modifiers == Qt.ControlModifier:

            self._has_moved = True
            super(QGraphicsResizableRect, self).mouseMoveEvent(event)
            string = str(self.pos()).split("(")[1][:-1]

    def mouseDoubleClickEvent(self, event):
        logger.debug("DOUBLE CLICK ON ITEM")
        # FIXME: Implement me
        event.accept()

    @pyqtSlot(str)
    def updateText(self, string):

        self.textItem.setPlainText(string)

    def mouseReleaseEvent(self, event):

        if self._has_moved:
            self.Signaller.signalHasMoved.emit(self.pos())

            self._has_moved = False
        QApplication.restoreOverrideCursor()
        return QGraphicsRectItem.mouseReleaseEvent(self, event)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            newPos = value  # new position in scene coordinates
            rect = self.scene().sceneRect()
            topLeftRectCoords = self.rect().topLeft()
            bottomRightRectCoords = self.rect().bottomRight()

            ntl = topLeftRectCoords + newPos
            nbr = bottomRightRectCoords + newPos

            if not rect.contains(ntl) or not rect.contains(nbr):
                ntl.setX(min(rect.right() - self.rect().width(), max(ntl.x(), rect.left())))
                ntl.setY(min(rect.bottom() - self.rect().height(), max(ntl.y(), rect.top())))
                return ntl - topLeftRectCoords

        return QGraphicsRectItem.itemChange(self, change, value)

    def setOpacity(self, float):
        logger.debug("Resetting Opacity {}".format(float))

        self._normalColor.setAlpha(float * 255)

        self.updateColor()

    def fixSelf(self, isFixed):
        self._isFixed = isFixed
        self.setFlag(QGraphicsItem.ItemIsMovable, not isFixed)


class RedRubberBand(QRubberBand):
    def __init__(self, *args, **kwargs):
        QRubberBand.__init__(self, *args, **kwargs)

    def paintEvent(self, pe):
        painter = QStylePainter(self)
        pen = QPen(QColor("red"), 4)
        painter.setPen(pen)
        painter.drawRect(pe.rect())


class CoupledRectangleElement(object):
    def __init__(self, pos: QRect, inputSlot, editor=None, scene=None, parent=None, qcolor=QColor(0, 0, 255)):
        """
        Couples the functionality of the lazyflow operator OpSubRegion which gets a subregion of interest
        and the functionality of the resizable rectangle Item.
        Keeps the two functionality separated


        :param pos: initial position
        :param inputSlot: Should be the output slot of another operator from which you would like monitor a subregion
        :param scene: the scene where to put the graphics item
        :param parent: the parent object if any
        :param qcolor: initial color of the rectangle
        """
        assert inputSlot.meta.getTaggedShape()["c"] == 1

        assert parent is None, "FIXME: QT structure does not seem to be implemented thoroughly. parent is always None!"
        self._rectItem = QGraphicsResizableRect(pos.x(), pos.y(), pos.height(), pos.width(), scene, parent, editor)
        # self._rectItem.color=qcolor  # FIXME: color can't be set

        # sub region corresponding to the rectangle region
        self._opsub = OpSubRegion(graph=inputSlot.operator.graph, parent=inputSlot.operator.parent)

        self._inputSlot = inputSlot  # input slot which connect to the sub array

        self.boxLabel = None  # a reference to the label in the labellist model
        self._initConnect()

    def _initConnect(self):
        # Operator changes
        self._opsub.Input.connect(self._inputSlot)
        self._opsub.Roi.setValue([self.getStart(), self.getStop()])
        self._inputSlot.notifyDirty(self._updateTextWhenChanges)

        # Signaling when the rectangle is moved
        self._rectItem.Signaller.signalHasMoved.connect(self._updateTextWhenChanges)
        self._rectItem.Signaller.signalHasResized.connect(self._updateTextWhenChanges)
        self._updateTextWhenChanges()

    @pyqtSlot()
    def _updateTextWhenChanges(self, *args, **kwargs):
        """
            Do the actual job of displaying a new number when the region gets
            notified dirty or the rectangle is moved or resized
        """
        time.sleep(DELAY * 0.001)

        # FIXME: Workaround: when the array is resized over the border of the image scene the
        # region get a wrong size
        # try:
        try:
            subarray = self.getSubRegion()
            value = 0
            if subarray is not None:
                value = subarray.sum()

            self._rectItem.updateText(f"{value:.1f}")

            if self.boxLabel is not None:
                self.boxLabel.density = f"{value:.1f}"

        except Exception as e:
            warnings.warn(f"Warning: invalid subregion. {e}", RuntimeWarning)

    def getOpsub(self):
        return self._opsub

    def getRectItem(self):
        return self._rectItem

    def disconnectInput(self):
        self._inputSlot.unregisterDirty(self._updateTextWhenChanges)
        self._opsub.Input.disconnect()

    def getStart(self):
        """ 5D coordinates of the start position of the subregion """
        rect_start = self._rectItem.topLeftDataPos()

        start = [0] * 5
        start[self._inputSlot.meta.getAxisKeys().index("x")] = rect_start[0]
        start[self._inputSlot.meta.getAxisKeys().index("y")] = rect_start[1]

        return tuple(start)

    def getStop(self):
        """ 5D coordinates of the stop position of the subregion """
        rect_stop = self._rectItem.bottomRightDataPos()

        stop = [1] * 5
        stop[self._inputSlot.meta.getAxisKeys().index("x")] = rect_stop[0]
        stop[self._inputSlot.meta.getAxisKeys().index("y")] = rect_stop[1]

        return tuple(stop)

    def getSubRegion(self):
        """ Gets the sub region of interest in the array input Slot """
        start = self.getStart()
        stop = self.getStop()

        for sta, sto in zip(start, stop):
            assert sto >= sta

        self._opsub.Roi.setValue([start, stop])
        return self._opsub.Output[:].wait()

    @property
    def color(self):
        return self._rectItem.color

    def setColor(self, qcolor):
        self._rectItem.setColor(qcolor)

    @property
    def fontSize(self):
        return self._rectItem.fontSize

    def setFontSize(self, size):
        self._rectItem.setFontSize(size)

    @property
    def fontColor(self):
        return self._rectItem.fontSize

    def setFontColor(self, color):
        self._rectItem.setFontColor(color)

    @property
    def lineWidth(self):
        return self._rectItem.lineWidth

    def setLineWidth(self, w):
        self._rectItem.setLineWidth(w)

    def setVisible(self, bool):
        return self._rectItem.setVisible(bool)

    def setOpacity(self, float):
        return self._rectItem.setOpacity(float)

    def setZValue(self, val):
        return self._rectItem.setZValue(val)

    def release(self):
        self.disconnectInput()
        self._rectItem.scene().removeItem(self._rectItem)

        self.boxLabel.isFixed = False
        self.boxLabel.isFixedChanged.emit(True)
        self.boxLabel.existenceChanged.emit()
        # FIXME: maybe dangerous to do del explicitely here
        del self


class BoxInterpreter(QObject):
    leftClickReleased = pyqtSignal(QRect)

    def __init__(self, navigationInterpreter, positionModel, BoxContr, widget):
        """
        Class which interacts directly with the image scene

        :param navigationInterpreter:
        :param positionModel:
        :param BoxContr:
        :param widget: The main widget

        """

        QObject.__init__(self)

        self.baseInterpret = navigationInterpreter
        self._posModel = positionModel
        self.rubberBand = RedRubberBand(QRubberBand.Rectangle, widget)

        self.boxController = BoxContr

        self.leftClickReleased.connect(BoxContr.addNewBox)

        self.origin = QPoint()
        self.originpos = None

    def start(self):
        self.baseInterpret.start()

    def stop(self):
        self.baseInterpret.stop()

    def eventFilter(self, watched, event):
        pos = tuple(map(int, self._posModel.cursorPos[:2]))

        # Rectangles under the current point
        items = watched.scene().items(QPointF(*pos))
        items = [el for el in items if isinstance(el, QGraphicsResizableRect)]

        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space:
            # Switch selection
            if len(items) > 1:
                items[-1].setZValue(items[0].zValue() + 1)
                items[0].setSelected(False)
                items[-1].setSelected(True)

        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Control:
            QApplication.setOverrideCursor(Qt.OpenHandCursor)

        elif event.type() == QEvent.KeyRelease and event.key() == Qt.Key_Control:
            QApplication.restoreOverrideCursor()

        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # Pressing mouse and menaging rubber band

            self.origin = QPoint(event.pos())
            self.originpos = pos
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))

            itemsall = watched.scene().items(QPointF(*pos))
            itemsall = [el for el in itemsall if isinstance(el, ResizeHandle)]

            modifiers = QApplication.keyboardModifiers()
            if modifiers != Qt.ControlModifier and modifiers != Qt.ShiftModifier and len(itemsall) == 0:  # show rubber band if Ctrl is not pressed
                self.rubberBand.show()

        elif event.type() == QEvent.MouseMove:
            if not self.origin.isNull():
                self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if self.rubberBand.isVisible():
                self.rubberBand.hide()
                self.leftClickReleased.emit(roi2rect(self.originpos, pos))
                self.originpos = None

        # Event is always forwarded to the navigation interpreter.
        return self.baseInterpret.eventFilter(watched, event)


class BoxController(QObject):
    fixedBoxesChanged = pyqtSignal(dict)
    viewBoxesChanged = pyqtSignal(dict)

    def __init__(self, editor, connectionInput, boxListModel):
        """
        Class which controls all boxes on the scene

        :param scene:
        :param connectionInput: The imput slot to which connect all the new boxes
        :param boxListModel:

        """

        scene = editor.imageScenes[2]
        self._editor = editor

        QObject.__init__(self, parent=scene.parent())
        self._setUpRandomColors()
        self.scene = scene
        self.connectionInput = connectionInput
        self._currentBoxesList = []
        self.currentColor = self._getNextBoxColor()
        self.boxListModel = boxListModel
        self.scene.selectionChanged.connect(self.handleSelectionChange)

        boxListModel.boxRemoved.connect(self.deleteItem)

    def addNewBox(self, pos: QRect) -> None:
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            return

        if any(isinstance(elem, ResizeHandle) for elem in self.scene.selectedItems()):
            return

        if pos.isEmpty():
            return

        rect = CoupledRectangleElement(
            pos, self.connectionInput, editor=self._editor, scene=self.scene, parent=self.scene.parent()
        )
        rect.setZValue(len(self._currentBoxesList))
        rect.setColor(self.currentColor)
        self._currentBoxesList.append(rect)

        newRow = self.boxListModel.rowCount()
        box = BoxLabel(f"Box{newRow}", self.currentColor)

        box.colorChanged.connect(rect.setColor)
        box.lineWidthChanged.connect(rect.setLineWidth)
        box.fontColorChanged.connect(rect.setFontColor)
        box.fontSizeChanged.connect(rect.setFontSize)
        box.isFixedChanged.connect(self._fixedBoxesChanged)
        box.existenceChanged.connect(self._viewBoxesChanged)

        self.boxListModel.insertRow(newRow, box)
        box.existenceChanged.emit()
        rect.boxLabel = box
        box.isFixedChanged.connect(rect._rectItem.fixSelf)
        rect._updateTextWhenChanges()

        self.currentColor = self._getNextBoxColor()

    def _fixedBoxesChanged(self, *args):
        boxes = {"rois": [], "values": []}
        for box, rect in zip(self.boxListModel._elements, self._currentBoxesList):
            if rect._rectItem.scene() and box.isFixed:
                boxes["rois"].append([rect.getStart(), rect.getStop()])
                boxes["values"].append(float(box._fixvalue))

        self.fixedBoxesChanged.emit(boxes)

        self._viewBoxesChanged()

    def _viewBoxesChanged(self, *args):
        boxes = {"rois": []}
        for box, rect in zip(self.boxListModel._elements, self._currentBoxesList):
            if rect._rectItem.scene() and not box.isFixed:
                boxes["rois"].append([rect.getStart(), rect.getStop()])

        self.viewBoxesChanged.emit(boxes)

    def deleteSelectedItems(self):
        tmp = []
        for k, el in enumerate(self._currentBoxesList):
            if el._rectItem.isSelected():
                el.release()

                super(type(self.boxListModel), self.boxListModel).removeRow(k)
            else:
                tmp.append(el)
        self._currentBoxesList = tmp

    def deleteItem(self, index):
        el = self._currentBoxesList.pop(index)
        # super(type(self.boxListModel),self.boxListModel).removeRow(index)
        el.release()

    def deleteAll(self) -> None:
        """Delete all boxes."""
        for i in reversed(range(len(self._currentBoxesList))):
            self.deleteItem(i)

    def rois(self) -> Iterable[Tuple[int, int, int, int]]:
        """Start X, start Y, end X and end Y box coordinates (start inclusive, end exclusive)."""
        for box in self._currentBoxesList:
            item = box.getRectItem()
            left, top = item.topLeftDataPos()
            right, bottom = item.bottomRightDataPos()
            yield left, top, right, bottom

    def selectBoxItem(self, index):
        [el._rectItem.setSelected(False) for el in self._currentBoxesList]  # deselect the others
        self._currentBoxesList[index]._rectItem.setSelected(True)

    def handleSelectionChange(self):
        for row, el in enumerate(self._currentBoxesList):
            if el._rectItem.isSelected():
                self.boxListModel.blockSignals(True)
                self.boxListModel.select(row)
                self.boxListModel.blockSignals(False)
                break

    def changeBoxesVisibility(self, bool):
        for item in self._currentBoxesList:
            item.setVisible(bool)

    def changeBoxesOpacity(self, float):
        for item in self._currentBoxesList:
            item.setOpacity(float)

    def _setUpRandomColors(self):
        seed = 42
        self._RandomColorGenerator = RandomColorGenerator(seed)

        next(self._RandomColorGenerator)  # discard black red and green
        next(self._RandomColorGenerator)
        next(self._RandomColorGenerator)

    def _getNextBoxColor(self):
        color = next(self._RandomColorGenerator)
        return color

    def csvRead(self, src: TextIO) -> None:
        """Read box coordinates from CSV.

        The first row should contain columns' names.

        Required columns:

        - StartX
        - StartY
        - StopX
        - StopY

        Raises:
            ValueError: Required column is missing or has an invalid format.
        """
        names = "StartX", "StartY", "StopX", "StopY"
        boxes = []

        # The first line is consumed by DictReader.
        for line, row in enumerate(csv.DictReader(src), 2):
            cols = []

            for name in names:
                try:
                    cols.append(int(row[name]))

                except KeyError:
                    names_repr = ", ".join(map(repr, names))
                    raise ValueError(f"Line {line}: missing column {name!r} (required columns: {names_repr})")

                except ValueError:
                    raise ValueError(f"Line {line}: column {name!r} is not an integer")

            boxes.append(roi2rect(cols[:2], cols[2:]))

        for box in boxes:
            self.addNewBox(box)

    def csvWrite(self, dest: TextIO) -> None:
        """Write box coordinates and statistics to CSV.

        Columns:

        - StartX
        - StartY
        - StopX
        - StopY
        - Count
        - AverageDensity
        - StdDensity
        """
        names = "StartX", "StartY", "StopX", "StopY", "Count", "AverageDensity", "StdDensity"
        writer = csv.DictWriter(dest, fieldnames=names, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for box in self._currentBoxesList:
            rect = box.getRectItem()
            startX, startY = rect.topLeftDataPos()
            stopX, stopY = rect.bottomRightDataPos()
            region = box.getSubRegion()
            row = {
                "StartX": format(startX, "d"),
                "StartY": format(startY, "d"),
                "StopX": format(stopX, "d"),
                "StopY": format(stopY, "d"),
                "Count": format(np.sum(region), "f"),
                "AverageDensity": format(np.mean(region), "f"),
                "StdDensity": format(np.std(region), "f"),
            }
            writer.writerow(row)


def RandomColorGenerator(seed=42):
    np.random.seed(seed)
    default = colortables.default16_new

    i = -1
    while 1:
        i += 1
        if i < 16:
            yield QColor(default[i])
        else:
            hue = np.random.rand() * 360

            color = colorsys.hsv_to_rgb(hue, 0.99, 0.99)
            color = [c * 255.0 for c in color]
            yield QColor(*color)
