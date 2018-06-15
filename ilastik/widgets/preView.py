from __future__ import division
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
#		   http://ilastik.org/license.html
###############################################################################
from past.utils import old_div
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen, QPalette, QColor
from PyQt5.QtWidgets import QGraphicsView, QVBoxLayout, QLabel, QGraphicsScene
from PyQt5.QtCore import Qt, QRect, QSize, QEvent

#===============================================================================
# PreView
#===============================================================================
class PreView(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)    
        
        self.zoom = 2
        self.scale(self.zoom, self.zoom) 
        self.lastSize = 0
        
        self.setDragMode(QGraphicsView.ScrollHandDrag)
#        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.installEventFilter(self)
                
        self.hudLayout = QVBoxLayout(self)
        self.hudLayout.setContentsMargins(0,0,0,0)
        
        self.ellipseLabel =  QLabel()
        self.ellipseLabel.setMinimumWidth(self.width())
        self.hudLayout.addWidget(self.ellipseLabel)
        self.ellipseLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)  

        
    def setPreviewImage(self, previewImage):
        self.grscene = QGraphicsScene()
        pixmapImage = QPixmap(previewImage)
        self.grscene.addPixmap(pixmapImage)
        self.setScene(self.grscene)
        

    def eventFilter(self, obj, event):
        if(event.type()==QEvent.Resize):
            self.ellipseLabel.setMinimumWidth(self.width())
            self.updateFilledCircle(self.lastSize)
        return False
    
    def sizeHint(self):
        return QSize(200, 200)

    def updateFilledCircle(self, s):
        size = s * self.zoom
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)
        #painter filled ellipse
        p = QPalette()
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        brush = QBrush(p.link().color())
        painter.setBrush(brush)
        painter.setOpacity(0.4)
        painter.drawEllipse(QRect(old_div(self.width(),2) - old_div(size,2), old_div(self.height(),2) - old_div(size,2), size, size))
        painter.end()
        #painter ellipse 2
        painter2 = QPainter()
        painter2.begin(pixmap)
        painter2.setRenderHint(QPainter.Antialiasing)
        pen2 = QPen(Qt.green)
        pen2.setWidth(1)
        painter2.setPen(pen2)
        painter2.drawEllipse(QRect(old_div(self.width(),2) - old_div(size,2), old_div(self.height(),2) - old_div(size,2), size, size))
        painter2.end()
        
        self.ellipseLabel.setPixmap(QPixmap(pixmap))
        self.lastSize = s

