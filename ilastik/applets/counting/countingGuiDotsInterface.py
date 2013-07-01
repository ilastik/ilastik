#===============================================================================
# Implements a mechanism to keep in sync the Dot Graphic Items
# with ilastik's operators 
# Idea: 1) Several graphics items are under the control of a single controller class
#       2) An interpreter class takes care of redirection user actions to the controller
#       3) Dots are coupled with actual brush strokes
# Note: brushing contro"ll"er is actually called brushingcontro"l"er (sic in volumina)
#===============================================================================


from PyQt4 import QtCore,QtGui
from PyQt4.QtCore import QObject, pyqtSignal, QEvent
from PyQt4.QtGui import QBrush,QColor,QMouseEvent
from PyQt4.QtCore import Qt,QTimer,SIGNAL, QPointF
from PyQt4.QtGui import QPen
from PyQt4.QtGui import QApplication


from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.api import Viewer
from volumina.layer import ColortableLayer
from volumina.colortables import jet
from volumina.brushingcontroler import BrushingControler,BrushingInterpreter

import numpy as np
import vigra

from countingGuiBoxesInterface import OpArrayPiper2




#===============================================================================
# ITEMS CLASSES
#===============================================================================
class DotCrosshairController(QObject):
    def __init__(self, brushingModel, imageViews):
        QObject.__init__(self, parent=None)
        self._brushingModel = brushingModel
        self._imageViews = imageViews
        self._brushingModel.brushSizeChanged.connect(self._setBrushSize)
        self._brushingModel.brushColorChanged.connect(self._setBrushColor)
        self._brushingModel.drawnNumberChanged.connect(self._setBrushSize)
        self._sigma=2.5
    
    def setSigma(self,s):
        self._sigma=s
    
    def _setBrushSize(self, size):
        if self._brushingModel.drawnNumber==1:
            size=self._sigma*4
        else:
            size=self._brushingModel.brushSize
                        
        for v in self._imageViews:
            v._crossHairCursor.setBrushSize(size)

    def _setBrushColor(self, color):
        for v in self._imageViews:
            v._crossHairCursor.setColor(color)
        
class DotSignaller(QObject):
    '''
    This class handles the signals of the graphics items
    '''
    createdSignal = pyqtSignal(float,float,object)
    deletedSignal = pyqtSignal(object)
    

class QDot(QtGui.QGraphicsEllipseItem):
    hoverColor    = QtGui.QColor(255, 255, 255)

    def __init__(self, pos, radius,Signaller=DotSignaller(),normalColor=QtGui.QColor(255, 0, 0)):
        y, x = pos
        x = x + 0.5
        y = y + 0.5
        size = radius * 2
        super(QDot, self).__init__(y - radius, x - radius, size, size)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(QtCore.Qt.RightButton)
        self.x = x
        self.y = y
        self._radius = radius
        self.hovering = False
        self._normalColor=normalColor
        self._normalColor.setAlphaF(0.7)
        self.updateColor()
        self.Signaller=Signaller
        
    def hoverEnterEvent(self, event):
        event.setAccepted(True)
        self.hovering = True
        self.setCursor(QtCore.Qt.BlankCursor)
        self.radius = self.radius # modified radius b/c hovering
        self.updateColor()

    def hoverLeaveEvent(self, event):
        event.setAccepted(True)
        self.hovering = False
        #self.setCursor(CURSOR)
        self.radius = self.radius # no longer hovering
        self.updateColor()

    def mousePressEvent(self, event):
        if QtCore.Qt.RightButton == event.button():
            event.setAccepted(True)
            self.Signaller.deletedSignal.emit(self)

    def setColor(self,normalColor):
        self._normalColor=normalColor
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
        self.setPen(QtGui.QPen(color))
        self.setBrush(QtGui.QBrush(color, QtCore.Qt.SolidPattern))

    def pos(self):
        return (self.y-0.5,self.x-0.5)
    
    def __str__(self, *args, **kwargs):
        return "Dot %s"%(self.pos(),)

        

#===============================================================================
# CONTROL CLASSES
#===============================================================================

class DotInterpreter(BrushingInterpreter):
    
    def __init__( self, navigationControler, brushingControler,dotsController ):
        '''
        This class inherit for the brushing interpreter because
        when putting a dot we place a graphic item on top of an actual 
        brushing label of one pixel size which is needed to create an object density
        
        
        :param navigationControler: A standard navigation controller handling mouse move
        :param brushingControler: A standard brushing controller to handle serialization of the brush
        :param dotsController: A dots controller to rout user produced signal to Graphics Items
        '''
        
        
        super(DotInterpreter,self).__init__(navigationControler,brushingControler)
        self._posModel=navigationControler._model
        self._brushingModel=self._brushingCtrl._brushingModel
        self._dotsController=dotsController
        

    def getColor(self):
        return self._brushingModel.drawnNumber
    
    def eventFilter( self, watched, event ):
        etype = event.type()
        
        if self._current_state == self.DEFAULT_MODE:
            if etype == QEvent.MouseButtonPress \
                and event.button() == Qt.LeftButton \
                and event.modifiers() == Qt.NoModifier \
                and self._navIntr.mousePositionValid(watched, event):
                
                ### default mode -> maybe draw mode
                self._current_state = self.MAYBE_DRAW_MODE
                # event will not be valid to use after this function exits,
                # so we must make a copy of it instead of just saving the pointer
                self._lastEvent = QMouseEvent( event.type(), event.pos(), event.globalPos(), event.button(), event.buttons(), event.modifiers() )
                
                if self.getColor()==1:
                    assert self._brushingModel.brushSize==1,"Wrong brush size %d"%self._brushingModel.brushSize
                    self._current_state = self.DRAW_MODE
                    self.onEntry_draw( watched, self._lastEvent )
                    #self.onMouseMove_draw( watched, event )
                    
                    self.onExit_draw( watched, event )
                
                    self._current_state = self.DEFAULT_MODE
                    self.onEntry_default( watched, event )
                    
                    pos = [int(i) for i in self._posModel.cursorPos]
                    pos = [self._posModel.time] + pos + [self._posModel.channel]
                    self._dotsController.addNewDot(pos)
                    
                    return True   
        
        return super(DotInterpreter,self).eventFilter(watched,event)

    def onMouseMove_draw( self, imageview, event ):
        self._navIntr.onMouseMove_default( imageview, event )

        o = imageview.scene().data2scene.map(QPointF(imageview.oldX,imageview.oldY))
        n = imageview.scene().data2scene.map(QPointF(imageview.x,imageview.y))
        
        # Draw temporary line for the brush stroke so the user gets feedback before the data is really updated.
        pen = QPen( QBrush(self._brushingCtrl._brushingModel.drawColor), self._brushingCtrl._brushingModel.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        line = imageview.scene().addLine(o.x(), o.y(), n.x(), n.y(), pen)
        
        #if line collide with a dot delete the dot
        items=imageview.scene().collidingItems(line)
        items=filter(lambda el: isinstance(el, QDot),items)
        
        for dot in items:
            eraseN=self._brushingModel.erasingNumber
            mask=np.ones((3,3),np.uint8)*eraseN
            self._brushingCtrl._writeIntoSink(QPointF(dot.y-1.5,dot.x-1.5),mask)
            self._dotsController.deleteDot(dot)
            
            
        self._lineItems.append(line)
        self._brushingCtrl._brushingModel.moveTo(imageview.mousePos)




    
class DotController(QObject):
    signalDotAdded =   pyqtSignal()
    signalDotDeleted = pyqtSignal()
    signalColorChanged=pyqtSignal(QColor)
    signalRadiusChanged=pyqtSignal(float)
    

    def __init__(self,scene,brushingController=None,radius=30,color=QColor(255,0,0)):
        '''
        Class which controls all dots of the scene
        
        :param scene: the scene under control, this is restricted to 2D only !
        :param brushingController: not needed, old interface 
        
        '''
        QObject.__init__(self,parent=scene.parent())
        self.scene=scene
        self._currentDotsHash=dict()
        self._radius=radius
        self._color=color
        #self._brushingModel=brushingController._brushingModel
        #self._brushingController=brushingController       
        
        #self._currentActiveItem=[]
        #self.counter=1000
#         self.scene.selectionChanged.connect(self.handleSelectionChange)
        
        self.Signaller=DotSignaller()
        self.Signaller.deletedSignal.connect(self.deleteDot)
                
    def addNewDot(self,pos5D):
        pos=tuple(pos5D[1:3])
        if self._currentDotsHash.has_key(pos): 
            print "Dot is already there %s",self._currentDotsHash[pos]
            return
        
        newdot=QDot(pos,self._radius,self.Signaller)
        assert newdot.pos()==pos
        self._currentDotsHash[pos]=newdot
        
        self.scene.addItem(newdot)
                
        self.signalDotAdded.emit()
    
    def deleteDot(self,dot):
        
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
    
    def setDotsRadius(self,radius):
        self._radius=radius
        self.signalRadiusChanged.emit(self._radius)
        for _,v in self._currentDotsHash.items():
            v.radius=radius
    
    def setDotsColor(self,qcolor):
        self._color=qcolor
        for _,v in self._currentDotsHash.items():
            v.setColor(qcolor)
        self.signalColorChanged.emit(qcolor)
    
    def sedDotsVisibility(self,boolval):
        for _,v in self._currentDotsHash.items():
            v.setVisible(boolval)
    
    

if __name__=="__main__":

    #===========================================================================
    # Example: of how the dotting interface works
    # we generate a random signal a certain position every 200 milliseconds
    # in order to simulate a signal of update from the graph.
    #===========================================================================
    from ilastik.widgets.labelListModel import LabelListModel,Label
    from ilastik.widgets.labelListView import LabelListView
    from lazyflow.graph import Graph
    app = QApplication([])
    
    labelListModel=LabelListModel()
    
    
    
    
    
    LV=LabelListView()
    LV.setModel(labelListModel)
    LV._table.setShowGrid(True)
    g = Graph()
        
    cron = QTimer()
    cron.start(500*3)
    
    op = OpArrayPiper2(graph=g) #Generate random noise
    shape=(1,500,500,1,1)
    
    array = np.random.randint(0,255,500*500).reshape(shape).astype(np.uint8)
    op.Input.setValue(array)
    
    
    
    def do():
        #Generate 
        #array[:] = np.random.randint(0,255,500*500).reshape(shape).astype(np.uint8)
        a = np.zeros(500*500).reshape(500,500).astype(np.uint8)
        ii=np.random.randint(0,500,1)
        jj=np.random.randint(0,500,1)
        a[ii,jj]=1
        a=vigra.filters.discDilation(a,radius=20)
        array[:]=a.reshape(shape).view(np.ndarray)*255
        op.Input.setDirty()
    
    do()
    
    cron.connect(cron, SIGNAL('timeout()'), do)
    ds = LazyflowSource( op.Output )
    layer = ColortableLayer(ds,jet())
     
    mainwin=Viewer()
    
    
    def _addNewLabel():
        """
        Add a new label to the label list GUI control.
        Return the new number of labels in the control.
        """
        erase=Label( "Dummy",QColor(255,255,255))
        label = Label( "Foreground",QColor(255,0,0))
        back = Label( "Background",QColor(0,255,0))
        
        newRow = labelListModel.rowCount()
        labelListModel.insertRow( newRow, erase )

        newRow = labelListModel.rowCount()
        labelListModel.insertRow( newRow, label )
        newRow = labelListModel.rowCount()
        labelListModel.insertRow( newRow, back )
        labelListModel.makeRowPermanent(0)
        labelListModel.makeRowPermanent(1)
        labelListModel.makeRowPermanent(2)
        
        

    _addNewLabel()
    mainwin.editor.brushingModel.erasingNumber=0
    
    
    
    def _handleSelection(int):
        if int==0:
            mainwin.editor.brushingModel.setErasing()
        else:
            #mainwin.editor.brushingModel.disableErasing()
            mainwin.editor.brushingModel.setDrawnNumber(int)
            if int==1:
                mainwin.editor.brushingModel.setBrushColor(QColor(255,0,0))
                mainwin.editor.brushingModel.setBrushSize(1)
            else:
                mainwin.editor.brushingModel.setBrushSize(20)
                mainwin.editor.brushingModel.setBrushColor(QColor(0,255,0))
    
    labelListModel.elementSelected.connect(_handleSelection)
    
    
    mainwin.layerstack.append(layer)
    mainwin.dataShape=(1,500,500,1,1)
    print mainwin.centralWidget()    
     
     
    BoxContr=DotController(mainwin.editor.imageScenes[2],mainwin.editor.brushingControler)
    BoxInt=DotInterpreter(mainwin.editor.navCtrl,mainwin.editor.brushingControler,BoxContr)
    
    

    mainwin.editor.setNavigationInterpreter(BoxInt)
    labelListModel.select(1)
    LV.show()
    mainwin.show()
     
    app.exec_()

    
