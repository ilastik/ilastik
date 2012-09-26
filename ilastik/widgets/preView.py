from PyQt4.QtGui import QGraphicsView, QVBoxLayout, QLabel, QGraphicsScene, QPixmap, QPainter, QBrush, QPen, QPalette, QColor
from PyQt4.QtCore import Qt, QRect, QSize, QEvent

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


    def setFilledBrsuh(self, size):
        self.updateFilledCircle(size)
        
    def updateCircle(self, s):
        size = s * self.zoom
        pixmap = QPixmap(self.width(), self.height())
        pixmap.fill(Qt.transparent)
        #painter ellipse 1
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.red)
        pen.setWidth(3)
        painter.setPen(pen)
        brush = QBrush(Qt.green)
        painter.setBrush(brush)
        painter.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter.end()
        #painter ellipse 2
        painter2 = QPainter()
        painter2.begin(pixmap)
        painter2.setRenderHint(QPainter.Antialiasing)
        pen2 = QPen(Qt.green)
        pen2.setStyle(Qt.DotLine)
        pen2.setWidth(3)
        painter2.setPen(pen2)
        painter2.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter2.end()
        
        self.ellipseLabel.setPixmap(QPixmap(pixmap))
        self.lastSize = s
        
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
        painter.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter.end()
        #painter ellipse 2
        painter2 = QPainter()
        painter2.begin(pixmap)
        painter2.setRenderHint(QPainter.Antialiasing)
        pen2 = QPen(Qt.green)
        pen2.setWidth(1)
        painter2.setPen(pen2)
        painter2.drawEllipse(QRect(self.width()/2 - size/2, self.height()/2 - size/2, size, size))
        painter2.end()
        
        self.ellipseLabel.setPixmap(QPixmap(pixmap))
        self.lastSize = s

