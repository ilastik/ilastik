# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys, random
import numpy, qimage2ndarray

class labelButtons(QLabel):
    dock = pyqtSignal()
    undock = pyqtSignal()
    minimize = pyqtSignal()
    maximize = pyqtSignal()
    def __init__(self, backgroundColor=None, foregroundColor=None):
        QLabel.__init__(self)
        self._isDocked = None
        self._isMaximized = None
        
        if not backgroundColor or not foregroundColor:
            self.backgroundColor = QColor("black")
            self.foregroundColor = QColor("white")
        else:
            self.setColors(backgroundColor, foregroundColor)
        
    def setColors(self, backgroundColor, foregroundColor):
        self.backgroundColor = backgroundColor
        self.foregroundColor = foregroundColor
        
    def setUndockIcon(self, backgroundColor=None, foregroundColor=None):
        if backgroundColor and foregroundColor:
            self.setColors(backgroundColor, foregroundColor)
        self._isMaximized = None
        self._isDocked = True
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawLine(70.0, 170.0, 190.0, 60.0)
        painter.drawLine(200.0, 140.0, 200.0, 50.0)
        painter.drawLine(110.0, 50.0, 200.0, 50.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setDockIcon(self, backgroundColor=None, foregroundColor=None):
        if backgroundColor and foregroundColor:
            self.setColors(backgroundColor, foregroundColor)
        self._isMaximized = None
        self._isDocked = False
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawLine(70.0, 170.0, 190.0, 60.0)
        painter.drawLine(60.0, 90.0, 60.0, 180.0)
        painter.drawLine(150.0, 180.0, 60.0, 180.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setMaximizeIcon(self, backgroundColor=None, foregroundColor=None):
        if backgroundColor and foregroundColor:
            self.setColors(backgroundColor, foregroundColor)
        self._isDocked = None
        self._isMaximized = False
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawRect(50.0, 50.0, 150.0, 150.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def setMinimizeIcon(self, backgroundColor=None, foregroundColor=None):
        if backgroundColor and foregroundColor:
            self.setColors(backgroundColor, foregroundColor)
        self._isDocked = None
        self._isMaximized = True
        pixmap = QPixmap(250, 250)
        pixmap.fill(self.backgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.foregroundColor)
        pen.setWidth(30)
        painter.setPen(pen)
        painter.drawRect(50.0, 50.0, 150.0, 150.0)
        painter.drawLine(50.0, 125.0, 200.0, 125.0)
        painter.drawLine(125.0, 200.0, 125.0, 50.0)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pixmap)
        
    def mouseReleaseEvent(self, event):
        if self.underMouse() and self._isDocked == True:
            self.undock.emit()
            self.setDockIcon()
        elif self.underMouse() and self._isDocked == False:
            self.dock.emit()
            self.setUndockIcon()
        elif self.underMouse() and self._isMaximized == True:
            self.minimize.emit()
            self.setMaximizeIcon()
        elif self.underMouse() and self._isMaximized == False:
            self.maximize.emit()
            self.setMinimizeIcon()
            
            
class QuadStatusBar(QHBoxLayout):
    def __init__(self, parent=None ):
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0,4,0,0)
        self.setSpacing(0)   
        
    def createStatusBar(self, xbackgroundColor, xforegroundColor, ybackgroundColor, yforegroundColor, zbackgroundColor, zforegroundColor, graybackgroundColor, grayforegroundColor):             
        
        self.xLabel = QLabel()
        self.xLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.xLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(xbackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(xforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "X")
        brush = QBrush(xforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.xLabel.setPixmap(pixmap)
        self.xSpinBox = QSpinBox()
        self.xSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.xSpinBox.setEnabled(False)
        self.xSpinBox.setAlignment(Qt.AlignCenter)
        self.xSpinBox.setToolTip("xSpinBox")
        self.xSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.xSpinBox.setMaximumHeight(20)
        self.xSpinBox.setMaximum(9999)
        font = self.xSpinBox.font()
        font.setPixelSize(14)
        self.xSpinBox.setFont(font)
        self.xSpinBox.setStyleSheet("QSpinBox { color: " + str(xforegroundColor.name()) + "; font: bold; background-color: " + str(xbackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.xSpinBox)
        
        self.yLabel = QLabel()
        self.yLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.yLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(ybackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(yforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Y")
        brush = QBrush(yforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.yLabel.setPixmap(pixmap)
        self.ySpinBox = QSpinBox()
        self.ySpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.ySpinBox.setEnabled(False)
        self.ySpinBox.setAlignment(Qt.AlignCenter)
        self.ySpinBox.setToolTip("ySpinBox")
        self.ySpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.ySpinBox.setMaximumHeight(20)
        self.ySpinBox.setMaximum(9999)
        font = self.ySpinBox.font()
        font.setPixelSize(14)
        self.ySpinBox.setFont(font)
        self.ySpinBox.setStyleSheet("QSpinBox { color: " + str(yforegroundColor.name()) + "; font: bold; background-color: " + str(ybackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.ySpinBox)
        
        self.zLabel = QLabel()
        self.zLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.zLabel)
        pixmap = QPixmap(25*10, 25*10)
        pixmap.fill(zbackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(zforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Z")
        brush = QBrush(zforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.zLabel.setPixmap(pixmap)
        self.zSpinBox = QSpinBox()
        self.zSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.zSpinBox.setEnabled(False)
        self.zSpinBox.setAlignment(Qt.AlignCenter)
        self.zSpinBox.setToolTip("zSpinBox")
        self.zSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.zSpinBox.setMaximumHeight(20)
        self.zSpinBox.setMaximum(9999)
        font = self.zSpinBox.font()
        font.setPixelSize(14)
        self.zSpinBox.setFont(font)
        self.zSpinBox.setStyleSheet("QSpinBox { color: " + str(zforegroundColor.name()) + "; font: bold; background-color: " + str(zbackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.zSpinBox)
        
        self.addSpacing(4)
        
        self.grayScaleLabel = QLabel()
        self.grayScaleLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.grayScaleLabel)
        pixmap = QPixmap(610, 250)
        pixmap.fill(graybackgroundColor)
        painter = QPainter()
        painter.begin(pixmap)
        pen = QPen(grayforegroundColor)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(25*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, 25*10-50), font, "Gray")
        brush = QBrush(grayforegroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap = pixmap.scaled(QSize(61,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.grayScaleLabel.setPixmap(pixmap)
        self.grayScaleSpinBox = QSpinBox()
        self.grayScaleSpinBox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.grayScaleSpinBox.setEnabled(False)
        self.grayScaleSpinBox.setAlignment(Qt.AlignCenter)
        self.grayScaleSpinBox.setToolTip("grayscaleSpinBox")
        self.grayScaleSpinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.grayScaleSpinBox.setMaximum(255)
        self.grayScaleSpinBox.setMaximumHeight(20)
        self.grayScaleSpinBox.setMaximum(255)
        font = self.grayScaleSpinBox.font()
        font.setPixelSize(14)
        self.grayScaleSpinBox.setFont(font)
        self.grayScaleSpinBox.setStyleSheet("QSpinBox { color: " + str(grayforegroundColor.name()) + "; font: bold; background-color: " + str(graybackgroundColor.name()) + "; border:0;}")
        self.addWidget(self.grayScaleSpinBox)
        
        self.addStretch()
        
        self.channelLabel = QLabel("Channel:")
        self.addWidget(self.channelLabel)
        
        self.channelSpinBox = QSpinBox()
        self.addWidget(self.channelSpinBox)
        self.addSpacing(20)
        
        self.timeLabel = QLabel("Time:")
        self.addWidget(self.timeLabel)
        
        self.timeSpinBox = QSpinBox()
        self.addWidget(self.timeSpinBox)
        self.addSpacing(20)
        
    def setGrayScale(self, gray):
        self.grayScaleSpinBox.setValue(gray)
        
    def setMouseCoords(self, x, y, z):
        self.xSpinBox.setValue(x)
        self.ySpinBox.setValue(y)
        self.zSpinBox.setValue(z)
            
class imageView2DHud(QHBoxLayout):
    spinBoxValueChanged = pyqtSignal(int)
    dock = pyqtSignal()
    undock = pyqtSignal()
    minimize = pyqtSignal()
    maximize = pyqtSignal()
    def __init__(self, parent=None ):
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0,4,0,0)
        self.setSpacing(0)
        
    def createHud(self, axis, value, backgroundColor, foregroundColor):
        self.addSpacing(4)
        self.axisLabel = QLabel()
        self.axisLabel.setToolTip("Axis")
        self.axisLabel.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.addWidget(self.axisLabel)
        
        self.spinBox = QSpinBox()
        self.spinBox.valueChanged.connect(self.spinBoxChanged)
        self.spinBox.setToolTip("Spinbox")
        self.spinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spinBox.setMaximum(10)
        self.spinBox.setAlignment(Qt.AlignRight)
        self.spinBox.setMaximumHeight(20)
        self.spinBox.setSuffix("/10")
        font = self.spinBox.font()
        font.setPixelSize(12)
        self.spinBox.setFont(font)
        self.spinBox.setStyleSheet("QSpinBox { color: " + str(foregroundColor.name()) + "; font: bold; background-color: " + str(backgroundColor.name()) + "; border:0;}")
        self.addSpacing(4)
        self.addWidget(self.spinBox)
      
        width = 25
        height = 25 
        
        pixmap2 = QPixmap(width*10, height*10)
        pixmap2.fill(backgroundColor)
        painter = QPainter()
        painter.begin(pixmap2)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(height*10-30)
        path = QPainterPath()
        path.addText(QPointF(50, height*10-50), font, axis)
        brush = QBrush(foregroundColor)
        painter.setBrush(brush)
        painter.drawPath(path)        
        painter.setFont(font)
        painter.end()
        pixmap2 = pixmap2.scaled(QSize(20,20),Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.axisLabel.setPixmap(pixmap2)        
    
        self.addStretch()
        
        self.dockButton = labelButtons()
        self.dockButton.dock.connect(self.on_dockButton)
        self.dockButton.undock.connect(self.on_undockButton)
        self.dockButton.setUndockIcon(backgroundColor, foregroundColor)
        self.dockButton.setToolTip("Dock/Undock-Button")
        self.addWidget(self.dockButton)
        
        self.addSpacing(4)
        
        self.maxButton = labelButtons()
        self.maxButton.maximize.connect(self.on_maxButton)
        self.maxButton.minimize.connect(self.on_minButton)
        self.maxButton.setMaximizeIcon(backgroundColor, foregroundColor)
        self.maxButton.setToolTip("Max/Minimize-Button")
        self.addWidget(self.maxButton)
        self.addSpacing(4)
    
    def spinBoxChanged(self, value):
        self.spinBoxValueChanged.emit(value)
        
    def on_dockButton(self):
        self.dock.emit()
        self.maxButton.setEnabled(True)
    def on_undockButton(self):
        self.undock.emit()
        self.maxButton.setEnabled(False)
        self.minimize.emit()
        self.maxButton.setMaximizeIcon()
        
    def on_maxButton(self):
        self.maximize.emit()
        
    def on_minButton(self):
        self.minimize.emit()


class imageView2D(QGraphicsView):
    mouseCoordsChanged = pyqtSignal(int, int, int)
    grayScaleChanged = pyqtSignal(int)
    def __init__(self):
        QGraphicsView.__init__(self)
        
        self._isRubberBandZoom = False
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)  
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.viewport().installEventFilter(self)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        
        self.grscene = QGraphicsScene()
        self.grscene.setSceneRect(-50,-50,500,500)
        pixmapImage = QPixmap(qimage2ndarray.array2qimage((numpy.random.rand(400,400)*256).astype(numpy.uint8)))
        self.pixmapImage = self.grscene.addPixmap(pixmapImage)
        self.setScene(self.grscene)
        
    def addHud(self, hud):
        self.hud = hud
        self.hud.spinBoxValueChanged.connect(self.setNewImage)
        self.layout.addLayout(self.hud)
    
    def setNewImage(self, spinBoxValue):
        self.grscene.removeItem(self.pixmapImage)
        pixmapImage = QPixmap(qimage2ndarray.array2qimage((numpy.random.rand(400,400)*256).astype(numpy.uint8)))
        self.pixmapImage = self.grscene.addPixmap(pixmapImage)
    
    
    def keyPressEvent(self, event):
        cursor = QCursor()
        mousePosition = cursor.pos()
        if event.key() == Qt.Key_Left and self.underMouse():
            cursor.setPos(mousePosition.x()-1, mousePosition.y())
        elif event.key() == Qt.Key_Right and self.underMouse():
            cursor.setPos(mousePosition.x()+1, mousePosition.y())
        elif event.key() == Qt.Key_Up and self.underMouse():
            cursor.setPos(mousePosition.x(), mousePosition.y()-1)
        elif event.key() == Qt.Key_Down and self.underMouse():
            cursor.setPos(mousePosition.x(), mousePosition.y()+1)
        #todo testing
        elif event.key() == Qt.Key_S and self.underMouse():
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        elif event.key() == Qt.Key_D and self.underMouse():
            self.centerOn(self.sceneRect().width()/2 + self.sceneRect().x(), self.sceneRect().height()/2 + self.sceneRect().y())
        elif event.key() == Qt.Key_A and self.underMouse(): 
            self.resetTransform()
        elif event.key() == Qt.Key_F and self.underMouse() and event.isAutoRepeat(): 
            self._isRubberBandZoom = True
            
#    def keyReleaseEvent(self, event):
#        if event.key() == Qt.Key_F:
#            self._isRubberBandZoom = False
        
            
    
    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseMove and self.underMouse():
            x = random.randrange(500)
            y = random.randrange(9999)
            z = random.randrange(100)
            gray = random.randrange(255)
            self.mouseCoordsChanged.emit(x, y, z)
            self.grayScaleChanged.emit(gray)
            
        if(event.type()==QEvent.MouseButtonPress):
            if event.button() == Qt.LeftButton and self._isRubberBandZoom:
                self.setDragMode(QGraphicsView.RubberBandDrag)
                self._rubberBandStart = event.pos()
        if(event.type()==QEvent.MouseButtonRelease):
            if event.button() == Qt.LeftButton and self._isRubberBandZoom:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                rect = QRectF(self.mapToScene(self._rubberBandStart), self.mapToScene(event.pos()))
                self.fitInView(rect, Qt.KeepAspectRatio)
                self._isRubberBandZoom = False
        if event.type() == QEvent.MouseMove and self.underMouse():
            x = random.randrange(500)
            y = random.randrange(9999)
            z = random.randrange(100)
            gray = random.randrange(255)
            self.mouseCoordsChanged.emit(x, y, z)
            self.grayScaleChanged.emit(gray)
            
                
        return False

            
class GraphicsViewWindow(QWidget):
    onCloseClick = pyqtSignal()
    def __init__(self):
        QWidget.__init__(self)
        
    def closeEvent(self, event):
        self.onCloseClick.emit()
        event.ignore()

class GroupBoxLayoutForSplitter(QGroupBox):
    onCloseClick = pyqtSignal()
    def __init__(self, graphicsView):
        QGroupBox.__init__(self)
        
        self.graphicsView = graphicsView
        
        self.setContentsMargins(0, 0, 0, 0)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.windowForGraphicsView = GraphicsViewWindow()
        self.windowForGraphicsView.onCloseClick.connect(self.onClose)
        self.windowForGraphicsView.layout = QVBoxLayout()
        self.windowForGraphicsView.layout.setContentsMargins(0, 0, 0, 0)
        self.windowForGraphicsView.setLayout(self.windowForGraphicsView.layout)
        
        self.addGraphicsView()
        
    def onClose(self):
        self.dockView()
        self.onCloseClick.emit()
    def addGraphicsView(self):
        self.layout.addWidget(self.graphicsView)
        
    def removeGraphicsView(self):
        self.layout.removeWidget(self.graphicsView)
        
    def undockView(self):
        self.removeGraphicsView()
        self.windowForGraphicsView.layout.addWidget(self.graphicsView)
        self.windowForGraphicsView.show()
        self.windowForGraphicsView.raise_()
    
    def dockView(self):
        self.windowForGraphicsView.layout.removeWidget(self.graphicsView)
        self.windowForGraphicsView.hide()
        self.addGraphicsView()


class VolumeEditorStyleTest(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        
        self._dummy_graphicsViewList = []
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(0)
        
        self.splitVertical = QSplitter(Qt.Vertical, self)
        self.layout.addWidget(self.splitVertical)
        self.splitHorizontal1 = QSplitter(Qt.Horizontal, self.splitVertical)
        self.splitHorizontal2 = QSplitter(Qt.Horizontal, self.splitVertical)
        
        self.testView1 = imageView2D()
        self.testView1.mouseCoordsChanged.connect(self.setMouseCoordsToQuadStatusBar)
        self.testView1.grayScaleChanged.connect(self.setGrayScaleToQuadStatusBar)
        self.testView1Hud = imageView2DHud()
        self.testView1Hud.createHud("X", 10, QColor("#dc143c"), QColor("white"))
        self.testView1.addHud(self.testView1Hud)
        self.testView1.layout.addStretch()
        
        self.testView2 = imageView2D()
        self.testView2.mouseCoordsChanged.connect(self.setMouseCoordsToQuadStatusBar)
        self.testView2.grayScaleChanged.connect(self.setGrayScaleToQuadStatusBar)
        self.testView2Hud = imageView2DHud()
        self.testView2Hud.createHud("Y", 10, QColor("green"), QColor("white"))
        self.testView2.addHud(self.testView2Hud)
        self.testView2.layout.addStretch()
        
        self.testView3 = imageView2D()
        
        self.testView4 = imageView2D()
        self.testView4.mouseCoordsChanged.connect(self.setMouseCoordsToQuadStatusBar)
        self.testView4.grayScaleChanged.connect(self.setGrayScaleToQuadStatusBar)
        self.testView4Hud = imageView2DHud()
        self.testView4Hud.createHud("Z", 10, QColor("blue"), QColor("white"))
        self.testView4.addHud(self.testView4Hud)
        self.testView4.layout.addStretch()
        
        self.dummy1_ofSplitHorizontal1 = GroupBoxLayoutForSplitter(self.testView1)
        self.dummy1_ofSplitHorizontal1.onCloseClick.connect(lambda arg=self.dummy1_ofSplitHorizontal1 : self.dymmyWindowClosed(arg))
        self._dummy_graphicsViewList.append(self.dummy1_ofSplitHorizontal1)
        self.testView1Hud.dock.connect(lambda arg=self.dummy1_ofSplitHorizontal1 : self.dock(arg))
        self.testView1Hud.undock.connect(lambda arg=self.dummy1_ofSplitHorizontal1 : self.undock(arg))
        self.testView1Hud.maximize.connect(lambda arg=self.dummy1_ofSplitHorizontal1 : self.maximize(arg))
        self.testView1Hud.minimize.connect(lambda arg=self.dummy1_ofSplitHorizontal1 : self.minimize(arg))
        self.splitHorizontal1.addWidget(self.dummy1_ofSplitHorizontal1)
        self.dummy2_ofSplitHorizontal1 = GroupBoxLayoutForSplitter(self.testView2)
        self._dummy_graphicsViewList.append(self.dummy2_ofSplitHorizontal1)
        self.testView2Hud.dock.connect(lambda arg=self.dummy2_ofSplitHorizontal1 : self.dock(arg))
        self.testView2Hud.undock.connect(lambda arg=self.dummy2_ofSplitHorizontal1 : self.undock(arg))
        self.testView2Hud.maximize.connect(lambda arg=self.dummy2_ofSplitHorizontal1 : self.maximize(arg))
        self.testView2Hud.minimize.connect(lambda arg=self.dummy2_ofSplitHorizontal1 : self.minimize(arg))
        self.splitHorizontal1.addWidget(self.dummy2_ofSplitHorizontal1)
        self.dummy1_ofSplitHorizontal2 = GroupBoxLayoutForSplitter(self.testView3)
        self._dummy_graphicsViewList.append(self.dummy1_ofSplitHorizontal2)
        self.splitHorizontal2.addWidget(self.dummy1_ofSplitHorizontal2)
        self.dummy2_ofSplitHorizontal2 = GroupBoxLayoutForSplitter(self.testView4)
        self._dummy_graphicsViewList.append(self.dummy2_ofSplitHorizontal2)
        self.testView4Hud.dock.connect(lambda arg=self.dummy2_ofSplitHorizontal2 : self.dock(arg))
        self.testView4Hud.undock.connect(lambda arg=self.dummy2_ofSplitHorizontal2 : self.undock(arg))
        self.testView4Hud.maximize.connect(lambda arg=self.dummy2_ofSplitHorizontal2 : self.maximize(arg))
        self.testView4Hud.minimize.connect(lambda arg=self.dummy2_ofSplitHorizontal2 : self.minimize(arg))
        self.splitHorizontal2.addWidget(self.dummy2_ofSplitHorizontal2)    
        
        self.quadViewStatusBar = QuadStatusBar()
        self.quadViewStatusBar.createStatusBar(QColor("#dc143c"), QColor("white"), QColor("green"), QColor("white"), QColor("blue"), QColor("white"), QColor("gray"), QColor("white"))
        self.layout.addLayout(self.quadViewStatusBar)
        
    def setGrayScaleToQuadStatusBar(self, gray):
        self.quadViewStatusBar.setGrayScale(gray)
        
    def setMouseCoordsToQuadStatusBar(self, x, y, z):
        self.quadViewStatusBar.setMouseCoords(x, y, z) 
        
        
    def dymmyWindowClosed(self, dummy):
        self.dock(dummy)
        dummy.graphicsView.hud.dockButton.setUndockIcon()
        dummy.graphicsView.hud.maxButton.setEnabled(True)
        
    def dock(self, dummy):
        dummy.dockView()
        
    def undock(self, dummy):
        dummy.undockView()   
    
    def maximize(self, dummy):
        for view in self._dummy_graphicsViewList:
            if not view == dummy:
                view.setVisible(False) 
    
    def minimize(self, dummy):
        for view in self._dummy_graphicsViewList:
            if not view == dummy:
                view.setVisible(True) 
                
        

app = QApplication(sys.argv)
ex = VolumeEditorStyleTest()
ex.show()
ex.raise_()
sys.exit(app.exec_())