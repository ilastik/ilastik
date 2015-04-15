###############################################################################
#   volumina: volume slicing and editing library
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
#Python
from os import path

#PyQt
from PyQt4 import uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QWidget, QButtonGroup

class CropSelectionWidget(QWidget):
    valueChanged = pyqtSignal(str, str, int)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        p = path.split(__file__)[0]
        if not p:
            p = "."

        self.uiPath = p+"/cropSelectionWidget.ui"
        uic.loadUi(self.uiPath, self)
        self.setRange(0,0,0,0,0,0,0,0)

        self._minSliderT.valueChanged.connect(self._onMinSliderTMoved)
        self._maxSliderT.valueChanged.connect(self._onMaxSliderTMoved)
        self._minSpinT.valueChanged.connect(self._onMinSpinTMoved)
        self._maxSpinT.valueChanged.connect(self._onMaxSpinTMoved)

        self._minSliderX.valueChanged.connect(self._onMinSliderXMoved)
        self._maxSliderX.valueChanged.connect(self._onMaxSliderXMoved)
        self._minSpinX.valueChanged.connect(self._onMinSpinXMoved)
        self._maxSpinX.valueChanged.connect(self._onMaxSpinXMoved)

        self._minSliderY.valueChanged.connect(self._onMinSliderYMoved)
        self._maxSliderY.valueChanged.connect(self._onMaxSliderYMoved)
        self._minSpinY.valueChanged.connect(self._onMinSpinYMoved)
        self._maxSpinY.valueChanged.connect(self._onMaxSpinYMoved)

        self._minSliderZ.valueChanged.connect(self._onMinSliderZMoved)
        self._maxSliderZ.valueChanged.connect(self._onMaxSliderZMoved)
        self._minSpinZ.valueChanged.connect(self._onMinSpinZMoved)
        self._maxSpinZ.valueChanged.connect(self._onMaxSpinZMoved)

    # t
    def _onMinSliderTMoved(self, v):
        if v > self._maxSliderT.value():
            self._maxSliderT.setValue(v)
        self.valueChanged.emit('T','min',self._minSliderT.value())
        self._minSpinT.setValue(v)

    def _onMaxSliderTMoved(self, v):
        if v < self._minSliderT.value():
            self._minSliderT.setValue(v)
        self.valueChanged.emit('T','max',self._maxSliderT.value())
        self._maxSpinT.setValue(v)

    def _onMinSpinTMoved(self, v):
        if v > self._maxSpinT.value():
            self._maxSpinT.setValue(v)
        self.valueChanged.emit('T','min',self._minSpinT.value())
        self._minSliderT.setValue(v)

    def _onMaxSpinTMoved(self, v):
        if v < self._minSpinT.value():
            self._minSpinT.setValue(v)
        self.valueChanged.emit('T','max',self._maxSpinT.value())
        self._maxSliderT.setValue(v)

    # x
    def _onMinSliderXMoved(self, v):
        if v > self._maxSliderX.value():
            self._maxSliderX.setValue(v)
        self.valueChanged.emit('X','min',self._minSliderX.value())
        self._minSpinX.setValue(v)

    def _onMaxSliderXMoved(self, v):
        if v < self._minSliderX.value():
            self._minSliderX.setValue(v)
        self.valueChanged.emit('X','max',self._maxSliderX.value())
        self._maxSpinX.setValue(v)

    def _onMinSpinXMoved(self, v):
        if v > self._maxSpinX.value():
            self._maxSpinX.setValue(v)
        self.valueChanged.emit('X','min',self._minSpinX.value())
        self._minSliderX.setValue(v)

    def _onMaxSpinXMoved(self, v):
        if v < self._minSpinX.value():
            self._minSpinX.setValue(v)
        self.valueChanged.emit('X','max',self._maxSpinX.value())
        self._maxSliderX.setValue(v)

    # y
    def _onMinSliderYMoved(self, v):
        if v > self._maxSliderY.value():
            self._maxSliderY.setValue(v)
        self.valueChanged.emit('Y','min',self._minSliderY.value())
        self._minSpinY.setValue(v)

    def _onMaxSliderYMoved(self, v):
        if v < self._minSliderY.value():
            self._minSliderY.setValue(v)
        self.valueChanged.emit('Y','max',self._maxSliderY.value())
        self._maxSpinY.setValue(v)

    def _onMinSpinYMoved(self, v):
        if v > self._maxSpinY.value():
            self._maxSpinY.setValue(v)
        self.valueChanged.emit('Y','min',self._minSpinY.value())
        self._minSliderY.setValue(v)

    def _onMaxSpinYMoved(self, v):
        if v < self._minSpinY.value():
            self._minSpinY.setValue(v)
        self.valueChanged.emit('Y','max',self._maxSpinY.value())
        self._maxSliderY.setValue(v)

    # z
    def _onMinSliderZMoved(self, v):
        if v > self._maxSliderZ.value():
            self._maxSliderZ.setValue(v)
        self.valueChanged.emit('Z','min',self._minSliderZ.value())
        self._minSpinZ.setValue(v)

    def _onMaxSliderZMoved(self, v):
        if v < self._minSliderZ.value():
            self._minSliderZ.setValue(v)
        self.valueChanged.emit('Z','max',self._maxSliderZ.value())
        self._maxSpinZ.setValue(v)

    def _onMinSpinZMoved(self, v):
        if v > self._maxSpinZ.value():
            self._maxSpinZ.setValue(v)
        self.valueChanged.emit('Z','min',self._minSpinZ.value())
        self._minSliderZ.setValue(v)

    def _onMaxSpinZMoved(self, v):
        if v < self._minSpinZ.value():
            self._minSpinZ.setValue(v)
        self.valueChanged.emit('Z','max',self._maxSpinZ.value())
        self._maxSliderZ.setValue(v)


    def setLayername(self, n):
        self._layerLabel.setText("Layer <b>%s</b>" % n)
        
    def setRange(self, minimumT, maximumT, minimumX, maximumX, minimumY, maximumY, minimumZ, maximumZ):

        # t
        self._minSliderT.setRange(minimumT, maximumT)
        self._minSpinT.setRange(minimumT, maximumT)
        self._maxSliderT.setRange(minimumT, maximumT)
        self._maxSpinT.setRange(minimumT, maximumT)
        self._minSpinT.setSuffix("/%d" % maximumT)
        self._maxSpinT.setSuffix("/%d" % maximumT)
        self._minSliderT.setValue(minimumT)
        self._maxSliderT.setValue(maximumT)
        self._minSpinT.setValue(minimumT)
        self._maxSpinT.setValue(maximumT)

        # x
        self._minSliderX.setRange(minimumX, maximumX)
        self._minSpinX.setRange(minimumX, maximumX)
        self._maxSliderX.setRange(minimumX, maximumX)
        self._maxSpinX.setRange(minimumX, maximumX)
        self._minSpinX.setSuffix("/%d" % maximumX)
        self._maxSpinX.setSuffix("/%d" % maximumX)
        self._minSliderX.setValue(minimumX)
        self._maxSliderX.setValue(maximumX)
        self._minSpinX.setValue(minimumX)
        self._maxSpinX.setValue(maximumX)

        # y
        self._minSliderY.setRange(minimumY, maximumY)
        self._minSpinY.setRange(minimumY, maximumY)
        self._maxSliderY.setRange(minimumY, maximumY)
        self._maxSpinY.setRange(minimumY, maximumY)
        self._minSpinY.setSuffix("/%d" % maximumY)
        self._maxSpinY.setSuffix("/%d" % maximumY)
        self._minSliderY.setValue(minimumY)
        self._maxSliderY.setValue(maximumY)
        self._minSpinY.setValue(minimumY)
        self._maxSpinY.setValue(maximumY)

        # Z
        self._minSliderZ.setRange(minimumZ, maximumZ)
        self._minSpinZ.setRange(minimumZ, maximumZ)
        self._maxSliderZ.setRange(minimumZ, maximumZ)
        self._maxSpinZ.setRange(minimumZ, maximumZ)
        self._minSpinZ.setSuffix("/%d" % maximumZ)
        self._maxSpinZ.setSuffix("/%d" % maximumZ)
        self._minSliderZ.setValue(minimumZ)
        self._maxSliderZ.setValue(maximumZ)
        self._minSpinZ.setValue(minimumZ)
        self._maxSpinZ.setValue(maximumZ)

    def setValue(self, minimumT, maximumT, minimumX, maximumX, minimumY, maximumY, minimumZ, maximumZ):

        # t
        self._minSliderT.setValue(minimumT)
        self._maxSliderT.setValue(maximumT)
        self._minSpinT.setValue(minimumT)
        self._maxSpinT.setValue(maximumT)

        # x
        self._minSliderX.setValue(minimumX)
        self._maxSliderX.setValue(maximumX)
        self._minSpinX.setValue(minimumX)
        self._maxSpinX.setValue(maximumX)

        # y
        self._minSliderY.setValue(minimumY)
        self._maxSliderY.setValue(maximumY)
        self._minSpinY.setValue(minimumY)
        self._maxSpinY.setValue(maximumY)

        # z
        self._minSliderZ.setValue(minimumZ)
        self._maxSliderZ.setValue(maximumZ)
        self._minSpinZ.setValue(minimumZ)
        self._maxSpinZ.setValue(maximumZ)

    def getValues(self):

        return (self._minSliderT.value(),
                self._maxSliderT.value(),
                self._minSliderX.value(),
                self._maxSliderX.value(),
                self._minSliderY.value(),
                self._maxSliderY.value(),
                self._minSliderZ.value(),
                self._maxSliderZ.value())
