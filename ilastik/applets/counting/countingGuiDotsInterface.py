from __future__ import absolute_import

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
# ===============================================================================
# Implements a mechanism to keep in sync the Dot Graphic Items
# with ilastik's operators
# Idea: 1) Several graphics items are under the control of a single controller class
#       2) An interpreter class takes care of redirection user actions to the controller
#       3) Dots are coupled with actual brush strokes
# Note: brushing contro"ll"er is actually called brushingcontro"l"er (sic in volumina)
# ===============================================================================


from qtpy.QtGui import QBrush, QColor, QMouseEvent, QPen, QBrush
from qtpy.QtCore import Qt, QObject, Signal, QEvent
from qtpy.QtWidgets import QApplication, QGraphicsEllipseItem


from volumina.api import createDataSource
from volumina.api import Viewer
from volumina.layer import ColortableLayer
from volumina.colortables import jet
from volumina.brushingcontroller import BrushingController, BrushingInterpreter

import numpy as np
import vigra

import logging

logger = logging.getLogger(__name__)


# ===============================================================================
# ITEMS CLASSES
# ===============================================================================
class DotCrosshairController(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._brushingModel = brushingModel
        self._imageViews = imageViews
        self._brushingModel.brushSizeChanged.connect(self._setBrushSize)
        self._brushingModel.brushColorChanged.connect(self._setBrushColor)
        self._brushingModel.drawnNumberChanged.connect(self._setBrushSize)
        self._sigma = 2.5

    def setSigma(self, s):
        self._sigma = s
        self._setBrushSize(None)

    def _setBrushSize(self, size):
        if self._brushingModel.drawnNumber == 1:
            size = self._sigma * 4
        else:
            size = self._brushingModel.brushSize

        for v in self._imageViews:
            v._crossHairCursor.setBrushSize(size)

    def _setBrushColor(self, color):
        for v in self._imageViews:
            v._crossHairCursor.setColor(color)


class DotSignaller(QObject):
    """
    This class handles the signals of the graphics items
    """

    createdSignal = Signal(float, float, object)
    deletedSignal = Signal(object)


class QDot(QGraphicsEllipseItem):
    hoverColor = QColor(255, 255, 255)

    def __init__(self, pos, radius, Signaller=DotSignaller(), normalColor=QColor(255, 0, 0)):
        y, x = pos
        x = x + 0.5
        y = y + 0.5
        size = radius * 2
        super(QDot, self).__init__(y - radius, x - radius, size, size)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.RightButton)
        self.x = x
        self.y = y
        self._radius = radius
        self.hovering = False
        self._normalColor = normalColor
        self._normalColor.setAlphaF(0.7)
        self.updateColor()
        self.Signaller = Signaller

    def hoverEnterEvent(self, event):
        event.setAccepted(True)
        self.hovering = True
        self.setCursor(Qt.BlankCursor)
        self.radius = self.radius  # modified radius b/c hovering
        self.updateColor()

    def hoverLeaveEvent(self, event):
        event.setAccepted(True)
        self.hovering = False
        # self.setCursor(CURSOR)
        self.radius = self.radius  # no longer hovering
        self.updateColor()

    def mousePressEvent(self, event):
        if Qt.RightButton == event.button():
            event.setAccepted(True)
            self.Signaller.deletedSignal.emit(self)

    def setColor(self, normalColor):
        self._normalColor = normalColor
        self.updateColor()

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, val):
        self._radius = val
        radius = self.radius
        if self.hovering:
            radius *= 1.25
        size = radius * 2
        self.setRect(self.y - radius, self.x - radius, size, size)

    def updateColor(self):
        color = self.hoverColor if self.hovering else self._normalColor
        self.setPen(QPen(color))
        self.setBrush(QBrush(color, Qt.SolidPattern))

    def pos(self):
        return (self.y - 0.5, self.x - 0.5)

    def __str__(self, *args, **kwargs):
        return "Dot %s" % (self.pos(),)


# ===============================================================================
# CONTROL CLASSES
# ===============================================================================


class DotInterpreter(BrushingInterpreter):
    def __init__(self, navigationController, brushingController):
        """
        This class inherit for the brushing interpreter because
        when putting a dot we place a graphic item on top of an actual
        brushing label of one pixel size which is needed to create an object density


        :param navigationController: A standard navigation controller handling mouse move
        :param brushingController: A standard brushing controller to handle serialization of the brush
        :param dotsController: A dots controller to rout user produced signal to Graphics Items
        """

        super(DotInterpreter, self).__init__(navigationController, brushingController)
        self._posModel = navigationController._model
        self._brushingModel = self._brushingCtrl._brushingModel
        # self._dotsController=dotsController

    def getColor(self):
        return self._brushingModel.drawnNumber

    def eventFilter(self, watched, event):
        etype = event.type()

        if self._current_state == self.DEFAULT_MODE:

            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Control:
                    QApplication.setOverrideCursor(Qt.OpenHandCursor)

            if event.type() == QEvent.KeyRelease:
                if event.key() == Qt.Key_Control:
                    QApplication.restoreOverrideCursor()

            if (
                etype == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton
                and event.modifiers() == Qt.NoModifier
                and self._navIntr.mousePositionValid(watched, event)
            ):

                ### default mode -> maybe draw mode
                self._current_state = self.MAYBE_DRAW_MODE
                # event will not be valid to use after this function exits,
                # so we must make a copy of it instead of just saving the pointer
                self._lastEvent = QMouseEvent(
                    event.type(), event.pos(), event.globalPos(), event.button(), event.buttons(), event.modifiers()
                )

                if self.getColor() == 1:
                    assert self._brushingModel.brushSize == 1, "Wrong brush size %d" % self._brushingModel.brushSize
                    self._current_state = self.DRAW_MODE
                    self.onEntry_draw(watched, self._lastEvent)
                    # self.onMouseMove_draw( watched, event )

                    self.onExit_draw(watched, event)

                    self._current_state = self.DEFAULT_MODE
                    self.onEntry_default(watched, event)

                    pos = [int(i) for i in self._posModel.cursorPos]
                    pos = [self._posModel.time] + pos + [self._posModel.channel]
                    # self._dotsController.addNewDot(pos)

                    return True

        return super(DotInterpreter, self).eventFilter(watched, event)


class DotController(QObject):
    signalDotAdded = Signal()
    signalDotDeleted = Signal()
    signalColorChanged = Signal(QColor)
    signalRadiusChanged = Signal(float)

    def __init__(self, scene, brushingController=None, radius=30, color=QColor(255, 0, 0)):
        """
        Class which controls all dots of the scene

        :param scene: the scene under control, this is restricted to 2D only !
        :param brushingController: not needed, old interface

        """
        QObject.__init__(self, parent=scene.parent())
        self.scene = scene
        self._currentDotsHash = dict()
        self._radius = radius
        self._color = color
        # self._brushingModel=brushingController._brushingModel
        # self._brushingController=brushingController

        # self._currentActiveItem=[]
        # self.counter=1000
        #         self.scene.selectionChanged.connect(self.handleSelectionChange)

        self.Signaller = DotSignaller()
        self.Signaller.deletedSignal.connect(self.deleteDot)

    def addNewDot(self, pos5D):
        pos = tuple(pos5D[1:3])
        if pos in self._currentDotsHash:
            logger.debug("Dot is already there %s", self._currentDotsHash[pos])
            return

        newdot = QDot(pos, self._radius, self.Signaller)
        assert newdot.pos() == pos
        self._currentDotsHash[pos] = newdot

        self.scene.addItem(newdot)

        self.signalDotAdded.emit()

    def deleteDot(self, dot):

        del self._currentDotsHash[dot.pos()]
        self.scene.removeItem(dot)

        #         eraseN=self._brushingModel.erasingNumber
        #         mask=np.ones((3,3),np.uint8)*eraseN
        #         self._brushingController._writeIntoSink(QPointF(dot.y-1.5,dot.x-1.5),mask)
        self.signalDotDeleted.emit()

    #     def itemsAtPos(self,pos5D):
    #         pos5D=pos5D[1:3]
    #         items=self.scene.items(QPointF(*pos5D))
    #         items=filter(lambda el: isinstance(el, QDot),items)
    #         return items

    def setDotsRadius(self, radius):
        self._radius = radius
        self.signalRadiusChanged.emit(self._radius)
        for _, v in list(self._currentDotsHash.items()):
            v.radius = radius

    def setDotsColor(self, qcolor):
        self._color = qcolor
        for _, v in list(self._currentDotsHash.items()):
            v.setColor(qcolor)
        self.signalColorChanged.emit(qcolor)

    def sedDotsVisibility(self, boolval):
        for _, v in list(self._currentDotsHash.items()):
            v.setVisible(boolval)
