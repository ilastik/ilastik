#===============================================================================
# Implements a mechanism to keep in sinc the GUI elements with the operators
# for the counting applet
# way round
#===============================================================================


from PyQt4 import QtCore,QtGui
from PyQt4.QtCore import QObject, QRect, QSize, pyqtSignal, QEvent, QPoint
from PyQt4.QtGui import QRubberBand,QBrush,QColor,QMouseEvent
from PyQt4.QtCore import Qt,QTimer,SIGNAL, QPointF
from PyQt4.QtGui import QGraphicsRectItem,QGraphicsItem, QPen,QFont
from PyQt4.QtGui import QApplication


from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.api import Viewer
from volumina.layer import ColortableLayer
from volumina.colortables import jet
from volumina.brushingcontroler import BrushingControler,BrushingInterpreter

import numpy as np
import vigra

from lazyflow.operator import InputSlot
from lazyflow.graph import Operator, OutputSlot, Graph
from lazyflow.operators.generic import OpSubRegion
##add tot hte pos model
from ilastik.widgets.boxListModel import BoxLabel, BoxListModel



#===============================================================================
# Dotting brush interface
#===============================================================================
class DotCrosshairControler(QObject):
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
        
        
        
class DottingInterpreter(BrushingInterpreter):
    
    def __init__( self, navigationControler, brushingControler ):
        super(DottingInterpreter,self).__init__(navigationControler,brushingControler)
        self._brushingModel=self._brushingCtrl._brushingModel
    
    
    
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
                    self._current_state = self.DRAW_MODE
                    self.onEntry_draw( watched, self._lastEvent )
                    #self.onMouseMove_draw( watched, event )
                    
                    self.onExit_draw( watched, event )
                
                    self._current_state = self.DEFAULT_MODE
                    self.onEntry_default( watched, event )

                    return True
                    
                
        return super(DottingInterpreter,self).eventFilter(watched,event)


        
                
                
                
#         elif self._current_state == self.MAYBE_DRAW_MODE:
#             if etype == QEvent.MouseMove:
#                 # navigation interpreter also has to be in
#                 # default mode to avoid inconsistencies
#                 if self._navIntr.state == self._navIntr.DEFAULT_MODE:
#                     ### maybe draw mode -> maybe draw mode
#                     self._current_state = self.DRAW_MODE
#                     self.onEntry_draw( watched, self._lastEvent )
#                     self.onMouseMove_draw( watched, event )
#                     return True
#                 else:
#                     self._navIntr.eventFilter( watched, self._lastEvent )
#                     return self._navIntr.eventFilter( watched, event )
#             elif etype == QEvent.MouseButtonDblClick:
#                 ### maybe draw mode -> default mode
#                 self._current_state = self.DEFAULT_MODE
#                 return self._navIntr.eventFilter( watched, event )
#             elif etype == QEvent.MouseButtonRelease:
#                 self._current_state = self.DRAW_MODE
#                 self.onEntry_draw( watched, self._lastEvent )
#                 self.onExit_draw( watched, event )
#                 self._current_state = self.DEFAULT_MODE
#                 self.onEntry_default( watched, event )
#                 return True
# 
#         elif self._current_state == self.DRAW_MODE:
#             if etype == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
#                 self.onExit_draw( watched, event )
#                 ### draw mode -> default mode
#                 self._current_state = self.DEFAULT_MODE
#                 self.onEntry_default( watched, event )
#                 return True
#             
#             elif etype == QEvent.MouseMove and event.buttons() & Qt.LeftButton:
#                 if self._navIntr.mousePositionValid(watched, event):
#                     self.onMouseMove_draw( watched, event )
#                     return True
#                 else:
#                     self.onExit_draw( watched, event )
#                     ### draw mode -> default mode
#                     self._current_state = self.DEFAULT_MODE
#                     self.onEntry_default( watched, event )
# 
#         # let the navigation interpreter handle common events
#         return self._navIntr.eventFilter( watched, event )
# 
#     def onExit_draw( self, imageview, event ):
#         self._brushingCtrl.endDrawing(imageview.mousePos)
#         if self._temp_erasing:
#             self._brushingCtrl._brushingModel.disableErasing()
#             self._temp_erasing = False
    


class Tool():
    
    Navigation = 0 # Arrow
    Paint      = 1
    Erase      = 2
    Box        = 3

#===============================================================================
# Graphics Classes
#===============================================================================

class ResizeHandle(QGraphicsRectItem):
    
    def __init__(self, shape, constrainAxis):
        size = 3
        super(ResizeHandle, self).__init__(-size/2, -size/2, 2*size, 2*size)
        self.shape=shape
        #self._offset = offset
        self._constrainAxis = constrainAxis
        self._hoverOver = False
        
        self.resetOffset(constrainAxis)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable);
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges ,True)
        self._updateColor()
        
    def resetOffset(self,constrainAxis,newshape=None):
        #self._parent=self.parentItem()
        if newshape!=None:
            self.shape=newshape
        if constrainAxis == 1:
            self._offset = ( self.shape[1], self.shape[0]/2.0 )
        else:
            self._offset = ( self.shape[1]/2.0, self.shape[0] )
        #print "Resetting ",self._offset,self._parent.shape
        self.setPos(QPointF(*self._offset))
        
    def hoverEnterEvent(self, event):
        super(ResizeHandle, self).hoverEnterEvent(event)
        event.setAccepted(True)
        self._hoverOver = True
        self._updateColor();

    def hoverLeaveEvent(self, event):
        super(ResizeHandle, self).hoverLeaveEvent(event)
        self._hoverOver = False
        self._updateColor()
        
    def mouseMoveEvent(self, event):
        #print "[view=%d] mouse move event constrained to %r" % (self.scene().skeletonAxis, self._constrainAxis)
        super(ResizeHandle, self).mouseMoveEvent(event)
    
        axes = [0,1]
        
        if self._constrainAxis == 0:
            newPoint=QPointF(self._offset[0],self.pos().y())
            self.setPos(newPoint)
            self.parentItem().setNewSize(axes[self._constrainAxis],self.pos().y())
        else:
            self.setPos(QPointF(self.pos().x(),self._offset[1]))
            self.parentItem().setNewSize(axes[self._constrainAxis],self.pos().x())
        
        
    def _updateColor(self):
        
        color=Qt.white
        
        if(self._hoverOver):
            self.setBrush(QBrush(color))
            self.setPen(QPen(color))
        else:
            self.setBrush(QBrush(color))
            self.setPen(color)

class QGraphicsResizableRectSignaller(QObject):
    """
     This class is used to emit signals since only QObjects can do it.
     Multiple inheritance is not supported for qt-python classes (Qt 4.10)
    """
    signalHasMoved = pyqtSignal(QPointF) #The resizable rectangle has moved the new position
    signalSelected =  pyqtSignal()
    signalHasResized = pyqtSignal()
    colorHasChanged = pyqtSignal(object)
    def __init__(self,parent=None):
        QObject.__init__(self,parent=parent)


class QGraphicsResizableRect(QGraphicsRectItem):
    hoverColor    = QColor(255, 0, 0) #_hovering and selection color
    

    
    
    def __init__(self,x,y,h,w,scene=None,parent=None):
        """"
        This class implements the resizable rectangle item which is dispalied on the scene
         x y should be the original positions in scene coordinates
         h,w are the height and the width of the rectangle
        """    
    
        QGraphicsRectItem.__init__(self,0,0,w,h,scene=scene,parent=parent)
        self.Signaller=QGraphicsResizableRectSignaller(parent=parent)
    
    
        self._fontColor=QColor(255, 255, 255)
        self._fontSize=12
        self._lineWidth=2
        
        
        
        ##Note: need to do like this because the x,y of the graphics item fix the position 
        # of the zero relative to the scene
        self.moveBy(x,y)
        self.width=w
        self.height=h
        self.shape=(h,w)
        
        #Flags
        self.setFlag(QGraphicsItem.ItemIsMovable,True  )
        self.setFlag(QGraphicsItem.ItemIsSelectable,True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges ,True)
         
        #self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable,True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        
        
        self._resizeHandles=[]
        
        # A bit of flags
        self._hovering=False
        self._normalColor   = QColor(0, 0, 255)
        self.updateColor()
        self._has_moved=False
        self._selected=False
        self._dbg=False
        self._setupTextItem() 
        
        self.resetHandles()
        
        
        
        
    @property
    def fontColor(self):
        return self._fontColor
    
    @fontColor.setter
    def fontColor(self,color):
        self._fontColor=color
        self.textItem.setDefaultTextColor(color)
        self.updateText(self.textItem.toPlainText())
        
    @property
    def fontSize(self):
        return self._fontSize
    
    @fontSize.setter
    def fontSize(self,s):
        self._fontSize=s
        font=QFont()
        font.setPointSize(self._fontSize)
        self.textItem.setFont(font)
        self.updateText(self.textItem.toPlainText())
        
    @property
    def linewWidth(self):
        return self._lineWidth
    
    @linewWidth.setter
    def linewWidth(self,s):
        self._lineWidth=s
        self.updateColor()

    @property
    def color(self):
        return self._normalColor
    
    @color.setter
    def color(self,qcolor):
        self._normalColor=qcolor
        self.updateColor()
    
    
    
    def _setupTextItem(self):
        #Set up the text         
        self.textItem=QtGui.QGraphicsTextItem(QtCore.QString(""),parent=self)
        textItem=self.textItem
        font=QFont()
        font.setPointSize(self._fontSize)
        textItem.setFont(font)
        textItem.setPos(QtCore.QPointF(0,0)) #upper left corner relative to the father        
        
        textItem.setDefaultTextColor(self._fontColor)
        
        if self._dbg:
            #another text item only for debug
            self.textItemBottom=QtGui.QGraphicsTextItem(QtCore.QString(""),parent=self)
            self.textItemBottom.setPos(QtCore.QPointF(self.width,self.height))
            self.textItemBottom.setDefaultTextColor(QColor(255, 255, 255))
        
            self._updateTextBottom("shape " +str(self.shape))
        
    def _updateTextBottom(self,string):
        self.textItemBottom.setPlainText(QtCore.QString(string))   
        
    
    def setNewSize(self, constrainAxis, size):
        

        
        if constrainAxis == 0:
            h,w = size, self.rect().width()
        else:
            h,w = self.rect().height(), size
        
        #FIXME: ensure rect in the scene after resizing
        newrect=QtCore.QRectF(0, 0, w, h)

        self.setRect(newrect)
        self.width=w
        self.height=h
        self.shape=(h,w)
        
        if self._dbg:
            self.textItemBottom.setPos(QtCore.QPointF(self.width,self.height))
        
        for el in self._resizeHandles:
            el.resetOffset(el._constrainAxis,newshape=self.shape)        
         
        self.Signaller.signalHasResized.emit()
        
        
    def hoverEnterEvent(self, event):
        event.setAccepted(True)
        self._hovering = True
        #elf.setCursor(QtCore.Qt.BlankCursor)
        #self.radius = self.radius # modified radius b/c _hovering
        self.updateColor()
        self.setSelected(True)
        self.resetHandles()   
           
        super(QGraphicsResizableRect,self).hoverEnterEvent( event)
  
    def hoverLeaveEvent(self, event):
        event.setAccepted(True)
        self._hovering = False
        self.setSelected(False)
        #self.setCursor(CURSOR)
        #self.radius = self.radius # no longer _hovering
        self.resetHandles()
#         for h in self._resizeHandles:
#             self.scene().removeItem(h)
#         self._resizeHandles = []
        super(QGraphicsResizableRect,self).hoverLeaveEvent( event)
    
    def resetHandles(self):
        #if len(self._resizeHandles)>0:
        for h in self._resizeHandles:
            self.scene().removeItem(h)
        self._resizeHandles=[]
        if self._hovering or self.isSelected():
            for constrAxes in range(2):
                h = ResizeHandle((self.height,self.width), constrAxes)
                h.setParentItem(self)
                self._resizeHandles.append( h )
                
    
    def setSelected(self, selected):
        QGraphicsRectItem.setSelected(self, selected) 
        if self.isSelected(): self.Signaller.signalSelected.emit()
        if not self.isSelected(): self._hovering=False
        self.updateColor()
        self.resetHandles()
              
    def updateColor(self):
        color = self.hoverColor if (self._hovering or self.isSelected())  else self._normalColor 
        self.setPen(QPen(color,self._lineWidth))
        self.setBrush(QBrush(color, QtCore.Qt.NoBrush))
    
    def dataPos(self):
        dataPos = self.scene().scene2data.map(self.scenePos())
        pos = [dataPos.x(), dataPos.y()]
        return pos 
    
    def mouseMoveEvent(self,event):
        pos=self.dataPos()
        
        #print self.isSelected(),"HSJAHJHSJAHSJH"
        
        modifiers=QApplication.queryKeyboardModifiers()
        if modifiers == Qt.ControlModifier:
            
            self._has_moved=True
            super(QGraphicsResizableRect, self).mouseMoveEvent(event)        
            string=str(self.pos()).split("(")[1][:-1]
            
            #self.QResizableRect.signalIsMoving.emit()
    #         dataPos = self.scene().scene2data.map(self.scenePos())
    #         pos = [dataPos.x(), dataPos.y()]
        
            #self.updateText("("+string+")"+" "+str(pos))
            
    def mouseDoubleClickEvent(self, event):
        print "DOUBLE CLICK ON ITEM"
        #FIXME: Implement me
        event.accept()
    
    def updateText(self,string):
        
        self.textItem.setPlainText(QtCore.QString(string))
    
    
    def mouseReleaseEvent(self, event):
        
        if self._has_moved:
            self.Signaller.signalHasMoved.emit(self.pos())
            #self._has_moved=False
        
            self._has_moved=False
        return QGraphicsRectItem.mouseReleaseEvent(self, event)
    
    def itemChange(self, change,value):
        if change==QGraphicsRectItem.ItemPositionChange:
            newPos=value.toPointF()
            rect = self.scene().sceneRect()

#             if not rect.contains(newPos):
#                 newPos.setX(min(rect.right(), max(newPos.x(), rect.left())))
#                 newPos.setY(min(rect.bottom(), max(newPos.y(), rect.top())))
#                 return newPos
#             
            #if not rect.contains(newPos2):
            #    newPos.setX(min(rect.right()-self.width, max(newPos.x()-self.width, rect.left())));
            #    newPos.setY(min(rect.bottom()-self.height, max(newPos.y()-self.height, rect.top())));
            #    return newPos
            if not rect.contains(value.toRectF()) :
                newPos.setX(min(rect.right()-self.width, max(newPos.x(), rect.left())));
                newPos.setY(min(rect.bottom()-self.height, max(newPos.y(), rect.top())));
                return newPos
            
        return QGraphicsRectItem.itemChange(self, change,value)
    
    
    def setOpacity(self,float):
        print "Resetting Opacity",float
        
        self._normalColor.setAlpha(float*255)
        
        self.updateColor()
    

    
        
class RedRubberBand(QRubberBand):
    def __init__(self,*args,**kwargs):
        QRubberBand.__init__(self,*args,**kwargs)

#         palette=QPalette()
#         palette.setBrush(palette.ColorGroup(), palette.foreground(), QBrush( QColor("red") ) );
#         self.setPalette(palette)
        
    def paintEvent(self,pe):
        painter=QtGui.QStylePainter(self)
        pen=QPen(QColor("red"),50)
        painter.setPen(pen)
        painter.drawRect(pe.rect())
        
#===============================================================================
# Functional Classes
#===============================================================================

class CoupledRectangleElement(object):
    def __init__(self,x,y,h,w,inputSlot,scene=None,parent=None,qcolor=QColor(0,0,255)):
        '''
        Couples the functionality of the lazyflow operator OpSubRegion which gets a subregion of interest
        and the functionality of the resizable rectangle Item.
        Keeps the two functionality separated
        
        
        :param x: initial position scene coordinates
        :param y: initial position scene coordinates
        :param h: initial height
        :param w: initial width
        :param inputSlot: Should be the output slot of another operator from which you would like monitor a subregion
        :param scene: the scene where to put the graphics item
        :param parent: the parent object if any
        :param qcolor: initial color of the rectagle
        '''
        
        
        self._rectItem=QGraphicsResizableRect(x,y,h,w,scene,parent)
        self._opsub = OpSubRegion(graph=inputSlot.operator.graph) #sub region correspondig to the rectangle region
        #self.opsum = OpSumAll(graph=inputSlot.operator.graph)
        self._graph=inputSlot.operator.graph
        self._inputSlot=inputSlot #input slot which connect to the sub array
        
        
        self.boxLabel=None #a reference to the label in the labellist model
        self._initConnect()
        
        #self.rectItem.color=qcolor
                
    def _initConnect(self):
        #print "initializing ...", self.getStart(),self.getStop()
        
        #Operator changes
        self._opsub.Input.connect(self._inputSlot)
        self._opsub.Start.setValue(self.getStart())
        self._opsub.Stop.setValue(self.getStop())
#         self.opsum.Input.connect(self._opsub.Output)
        self._inputSlot.notifyDirty(self._updateTextWhenChanges)
        
        
        #Signalling when the ractangle is moved 
        self._rectItem.Signaller.signalHasMoved.connect(self._updateTextWhenChanges)
        self._rectItem.Signaller.signalHasResized.connect(self._updateTextWhenChanges)
        self._updateTextWhenChanges()
        
    def _updateTextWhenChanges(self,*args,**kwargs):
        '''
        Do the actual job of displaying a new number when the region gets notified dirty
        or the rectangle is moved or resized
        '''
        
        subarray=self.getSubRegion()

        #self.current_sum= self.opsum.outputs["Output"][:].wait()[0]
        value=np.sum(subarray)
        
        #print "Resetting to a new value ",value,self.boxLabel
        
        self._rectItem.updateText("%.1f"%(value))
        
        if self.boxLabel!=None:
            from PyQt4.QtCore import QString
            self.boxLabel.density=QString("%.1f"%value)
        
    def getOpsub(self):
        return self._opsub
    
    def getRectItem(self):
        return self._rectItem

    def disconnectInput(self):
        self._inputSlot.unregisterDirty(self._updateTextWhenChanges)
        self._opsub.Input.disconnect()
    
    def getStart(self):
        '''
         5D coordinates of the start position of the subregion
        '''
        rect=self._rectItem
        newstart=self._rectItem.dataPos()
    
        start=(0,newstart[0],newstart[1],0,0)
        return start
    
    def getStop(self):
        '''
         5D coordinates of the start position of the subregion
        '''
        
        rect=self._rectItem
        newstart=self._rectItem.dataPos()
    
        stop=(1,newstart[0]+rect.width,newstart[1]+rect.height,1,1)
        return stop
    
    
    def getSubRegion(self):
        '''
        Gets the sub region of interest in the array input Slot
        
        '''
        oldstart=self.getStart()
        oldstop=self.getStop()
        start=[]
        stop=[]
        for s1,s2 in zip(oldstart,oldstop):
            start.append(int(np.minimum(s1,s2)))
            stop.append(int(np.maximum(s1,s2)))
        
        self._opsub.Stop.disconnect()
        self._opsub.Start.disconnect()
        self._opsub.Start.setValue(tuple(start))
        self._opsub.Stop.setValue(tuple(stop))
        
        return self._opsub.outputs["Output"][:].wait()
    
    @property
    def color(self):
        return self._rectItem.color
         
    def setColor(self,qcolor):
        self._rectItem.color=qcolor
    
    @property
    def fontSize(self):
        return self._rectItem.fontSize
         
    def setFontSize(self,size):
        self._rectItem.fontSize=size
    
    @property
    def fontColor(self):
        return self._rectItem.fontSize
         
    def setFontColor(self,color):
        self._rectItem.fontColor=color
    
    @property
    def lineWidth(self):
        return self._rectItem.linewWidth
    
    def setLineWidth(self,w):
        self._rectItem.linewWidth=w    
               
    def setVisible(self,bool):
        return self._rectItem.setVisible(bool)
    
    def setOpacity(self,float):
        return self._rectItem.setOpacity(float)

    def setZValue(self,val):
        return self._rectItem.setZValue(val)
    
    def release(self):
        self.disconnectInput()
        self._rectItem.scene().removeItem(self._rectItem)
        
        self.boxLabel.isFixed=False
        self.boxLabel.isFixedChanged.emit(True)
        
        del self
        

# class OpSumAll(Operator):
#     name = "SumRegion"
#     description = ""
# 
#     #Inputs
#     Input = InputSlot() 
#    
#     #Outputs
#     Output = OutputSlot()
#     
#     
#     def setupOutputs(self):
#         inputSlot = self.inputs["Input"]
#         self.Output.meta.shape = (1,)
#         self.Output.meta.dtype = np.float
#         self.Output.meta.axistags = None
# 
# 
#     def execute(self, slot, subindex, roi, result):
#         #key = roi.toSlice()
#         arr = self.inputs["Input"][:].wait()
#         result[:]=np.sum(arr)
#         return result
# 
#     def propagateDirty(self, slot, subindex, roi):
#         key = roi.toSlice()
#         # Check for proper name because subclasses may define extra inputs.
#         # (but decline to override notifyDirty)
#         if slot.name == 'Input':
#             self.outputs["Output"].setDirty(slice(None))
#         else:
#             # If some input we don't know about is dirty (i.e. we are subclassed by an operator with extra inputs),
#             # then mark the entire output dirty.  This is the correct behavior for e.g. 'sigma' inputs.
#             self.outputs["Output"].setDirty(slice(None))
    
            



#===============================================================================
# Controlling of the boxes
#===============================================================================


class BoxInterpreter(QObject):
    rightClickReceived = pyqtSignal(object, QPoint) # list of indexes, global window coordinate of click
    leftClickReceived = pyqtSignal(object, QPoint)  
    leftClickReleased = pyqtSignal(object, object)
    #boxAdded= pyqtSignal(object, object)
    #focusObjectChages= pyqtSignal(object, QPoint)
    cursorPositionChanged  = pyqtSignal(object)
    deleteSelectedItemsSignal= pyqtSignal() #send the signal that we want to delete the currently selected item
    
    def __init__(self, navigationInterpreter, positionModel, BoxContr, widget):
        '''
        Class which interacts directly with the image scene
        
        :param navigationInterpreter:
        :param positionModel:
        :param BoxContr:
        :param widget: The main widget
        
        '''
        
        
        QObject.__init__(self)
        
        
        self.baseInterpret = navigationInterpreter
        self.posModel      = positionModel
        self.rubberBand = RedRubberBand(QRubberBand.Rectangle, widget)
        
        self.boxController=BoxContr
        
        self.leftClickReleased.connect(BoxContr.addNewBox)
        self.rightClickReceived.connect(BoxContr.onChangedPos)
        self.deleteSelectedItemsSignal.connect(BoxContr.deleteSelectedItems)
        
        
        self.origin = QPoint()
        self.originpos = object()

    def start( self ):
        self.baseInterpret.start()

    def stop( self ):
        self.baseInterpret.stop()

    def eventFilter( self, watched, event ):
        pos = [int(i) for i in self.posModel.cursorPos]
        pos = [self.posModel.time] + pos + [self.posModel.channel]
        
        #Rectangles under the current point
        items=watched.scene().items(QPointF(*pos[1:3]))
        items=filter(lambda el: isinstance(el, QGraphicsResizableRect),items)
        
        
        #Keyboard interaction
        if event.type()==QEvent.KeyPress:      
            #Switch selection
            if event.key()==Qt.Key_N :
                #assert items[0]._hovering
                #items[0].setZValue(1)
                for el in items:
                    print el.zValue()
                
                if len(items)>1:
                    items[-1].setZValue(items[0].zValue()+1)
                    items[0].setSelected(False)
                    items[-1].setSelected(True)
                    #items[0].setZero()
            
            #Delete element
            if event.key()==Qt.Key_Delete:
                self.deleteSelectedItemsSignal.emit()
            
        
            
            
        #Pressing mouse and menaging rubber band
        if event.type() == QEvent.MouseButtonPress: 
            if event.button() == Qt.LeftButton:
                self.origin = QPoint(event.pos())
                self.originpos = pos
                self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                
                itemsall=watched.scene().items(QPointF(*pos[1:3]))
                itemsall =filter(lambda el: isinstance(el, ResizeHandle), itemsall)
                 
#                 if len(itemsall)==0: #show rubber band only if there is no rubbber band
#                     self.rubberBand.show()              

                modifiers=QApplication.keyboardModifiers() 
                if modifiers != Qt.ControlModifier and modifiers != Qt.ShiftModifier and len(itemsall)==0: #show rubber band if Ctrl is not pressed
                    self.rubberBand.show()
            

                gPos = watched.mapToGlobal( event.pos() )
                self.leftClickReceived.emit( pos, gPos )
                
            if event.button() == Qt.RightButton:
                gPos = watched.mapToGlobal( event.pos() )
                self.rightClickReceived.emit( pos, gPos )                
        
        if event.type() == QEvent.MouseMove:
            self.cursorPositionChanged.emit(event.pos())
            if not self.origin.isNull():
                self.rubberBand.setGeometry(QRect(self.origin,
                                                  event.pos()).normalized())
        #Relasing the button
        if event.type() == QEvent.MouseButtonRelease:
            pos = [int(i) for i in self.posModel.cursorPos]
            pos = [self.posModel.time] + pos + [self.posModel.channel]
            if event.button() == Qt.LeftButton:
                self.rubberBand.hide()
                self.leftClickReleased.emit( self.originpos,pos )                

        # Event is always forwarded to the navigation interpreter.
        return self.baseInterpret.eventFilter(watched, event)


class BoxController(QObject):
    
    fixedBoxesChanged = pyqtSignal(list)

    def __init__(self,scene,connectionInput,boxListModel):
        '''
        Class which controls all boxes on the scene
        
        :param scene:
        :param connectionInput: The imput slot to which connect all the new boxes
        :param boxListModel:
 
        '''
        QObject.__init__(self,parent=scene.parent())
        self._setUpRandomColors()
        self.scene=scene
        self.connectionInput=connectionInput
        self._currentBoxesList=[]
        #self._currentActiveItem=[]
        #self.counter=1000
        self.currentColor=self._getNextBoxColor()
        self.boxListModel=boxListModel
        self.scene.selectionChanged.connect(self.handleSelectionChange)
        
        
        boxListModel.boxRemoved.connect(self.deleteItem)
        
    def getCurrentActiveBox(self):
        pass
        
        
    def addNewBox(self,pos5Dstart,pos5Dstop):
        modifiers=QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier: #add stuff
            return

        for el  in self.scene.selectedItems(): #retun if there is an handle on the scene at that position
            if isinstance(el, ResizeHandle): return      

#             
#         print "Start = ",pos5Dstart,
#         print "Stop =", pos5Dstop
        oldstart=pos5Dstart[1:3]
        oldstop=pos5Dstop[1:3]
        start=[]
        stop=[]
        for s1,s2 in zip(oldstart,oldstop):
            start.append(np.minimum(s1,s2))
            stop.append(np.maximum(s1,s2))
        
        
        
#         itemsall1=self.scene.items(QPointF(*pos5Dstart[1:3]))
#         itemsall1 =filter(lambda el: isinstance(el, ResizeHandle), itemsall1)
#         itemsall2=self.scene.items(QPointF(*pos5Dstop[1:3]))
#         itemsall2 =filter(lambda el: isinstance(el, ResizeHandle), itemsall2)
#         itemsall=itemsall1+itemsall2
#         print itemsall
        
         

        h=stop[1]-start[1]
        w=stop[0]-start[0]
        if h*w<9: return #too small
        
        rect=CoupledRectangleElement(start[0],start[1],h,w,self.connectionInput,scene=self.scene,parent=self.scene.parent())
        rect.setZValue(len(self._currentBoxesList))
        rect.setColor(self.currentColor)
        #self.counter-=1
        self._currentBoxesList.append(rect)
        

        
        newRow=self.boxListModel.rowCount()
        box = BoxLabel( "Box%d"%newRow, self.currentColor)
        
        box.colorChanged.connect(rect.setColor)
        box.lineWidthChanged.connect(rect.setLineWidth)
        box.fontColorChanged.connect(rect.setFontColor)
        box.fontSizeChanged.connect(rect.setFontSize)
        box.isFixedChanged.connect(self._fixedBoxesChanged)
        
        
        
        
        self.boxListModel.insertRow( newRow, box )
        rect.boxLabel=box
        rect._updateTextWhenChanges()
        
        self.currentColor=self._getNextBoxColor()
        
    def _fixedBoxesChanged(self, *args):
        boxes = []
        for box, rect in zip(self.boxListModel._elements, self._currentBoxesList):
            if box.isFixed:
                boxes.append([rect.getStart(), rect.getStop(), box._fixvalue])

        self.fixedBoxesChanged.emit(boxes)
         


    def itemsAtPos(self,pos5D):
        pos5D=pos5D[1:3]
        items=self.scene.items(QPointF(*pos5D))
        items=filter(lambda el: isinstance(el, ResizeHandle),items)
        return items
    
    def onChangedPos(self,pos,gpos):
        pos=pos[1:3]
        items=self.scene.items(QPointF(*pos))
        print items
        items=filter(lambda el: isinstance(el, QGraphicsResizableRect),items)
        
        self.itemsAtpos=items
    
    def deleteSelectedItems(self):
        tmp=[]
        for k,el in enumerate(self._currentBoxesList):
            if el._rectItem.isSelected():
                el.release()
                
                super(type(self.boxListModel),self.boxListModel).removeRow(k)
            else:
                tmp.append(el)
        self._currentBoxesList=tmp
    
    def deleteItem(self,index):
        el=self._currentBoxesList.pop(index)
        #super(type(self.boxListModel),self.boxListModel).removeRow(index)
        el.release()
        
        
    def selectBoxItem(self,index):
        [el._rectItem.setSelected(False) for el in self._currentBoxesList] #deselect the others
        self._currentBoxesList[index]._rectItem.setSelected(True)
        
    def handleSelectionChange(self):
        for row,el in enumerate(self._currentBoxesList):
            if el._rectItem.isSelected():
                self.boxListModel.blockSignals(True)
                self.boxListModel.select(row)
                self.boxListModel.blockSignals(False)
                break
    
    def changeBoxesVisibility(self,bool):
        for item in self._currentBoxesList:
            item.setVisible(bool)
    
    def changeBoxesOpacity(self,float):
        for item in self._currentBoxesList:
            item.setOpacity(float)
    
    
    def _setUpRandomColors(self):
        seed=42
        self._RandomColorGenerator=RandomColorGenerator(seed)

        self._RandomColorGenerator.next() #discard black red and green
        self._RandomColorGenerator.next()
        self._RandomColorGenerator.next()
    
    def _getNextBoxColor(self):
        color=self._RandomColorGenerator.next()
        return color

#===============================================================================
# Random colors
#===============================================================================

import numpy as np
import colorsys

def _get_colors(num_colors,seed=42):
    golden_ratio_conjugate = 0.618033988749895
    np.random.seed(seed)
    colors=[]
    hue=np.random.rand()*360
    for i in np.arange(0., 360., 360. / num_colors):
        hue += golden_ratio_conjugate
        lightness = (50 + 1 * 10)/100.
        saturation = (90 + 1 * 10)/100.
        
        colors.append(colorsys.hsv_to_rgb(hue, 0.99,0.99))
    return colors


def _createDefault16ColorColorTable():
    from PyQt4.QtGui import QColor
    from PyQt4.QtCore import Qt
    colors = []
    # Transparent for the zero label
    colors.append(QColor(0,0,0,0))
    # ilastik v0.5 colors
    colors.append( QColor( Qt.red ) )
    colors.append( QColor( Qt.green ) )
    colors.append( QColor( Qt.yellow ) )
    colors.append( QColor( Qt.blue ) )
    colors.append( QColor( Qt.magenta ) )
    colors.append( QColor( Qt.darkYellow ) )
    colors.append( QColor( Qt.lightGray ) )
    # Additional colors
    colors.append( QColor(255, 105, 180) ) #hot pink
    colors.append( QColor(102, 205, 170) ) #dark aquamarine
    colors.append( QColor(165,  42,  42) ) #brown
    colors.append( QColor(0, 0, 128) )     #navy
    colors.append( QColor(255, 165, 0) )   #orange
    colors.append( QColor(173, 255,  47) ) #green-yellow
    colors.append( QColor(128,0, 128) )    #purple
    colors.append( QColor(240, 230, 140) ) #khaki
    return colors

def RandomColorGenerator(seed=42):
    np.random.seed(seed)    
    default=_createDefault16ColorColorTable()
    print default
    i=-1
    while 1:
        i+=1
        if i<16:
            yield default[i]
        else:        
            hue=np.random.rand()*360
            lightness = (50 + 1 * 10)/100.
            saturation = (90 + 1 * 10)/100.
            
            color=colorsys.hsv_to_rgb(hue, 0.99,0.99)
            color=[c*255.0 for c in color]
            yield QColor(*color)        


#===============================================================================
# FOR DEBUG PURPOSES ---------
#===============================================================================

# class MyGraphicsView(QtGui.QGraphicsView):
#     #useful class for debug
#     def __init__ (self,parent=None):
#         super (MyGraphicsView, self).__init__ (parent)
# 
# 
#     def mousePressEvent(self,  event):
#         super(MyGraphicsView, self).mousePressEvent(event)
#         itemUnderMouse = self.itemAt(event.pos())
#         print "here",itemUnderMouse
# 
#         
# def create_qt_default_env():
#     #useful for debug
#     from PyQt4.QtGui import QGraphicsScene,QGraphicsView,QApplication
#     # 1 make the application
#     app=QApplication([])
#     # 2 then we need a main window to display stuff
#     window=QMainWindow()
#     # 3 then we a scene that we want to display
#     scene=QGraphicsScene(0,0,400,400)
#     
#     # 4 view on the scene: open a widget on the main window which dispaly the scene
#     view=MyGraphicsView(scene)
#     window.setCentralWidget(view)
#     #window.show()
#     
#     return app,window,view,scene

        
class OpArrayPiper2(Operator):
    name = "ArrayPiper"
    description = "simple piping operator"

    #Inputs
    Input = InputSlot() 
   
    #Outputs
    Output = OutputSlot()

    def setupOutputs(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"].meta.assignFrom(inputSlot.meta)

        self.Output.meta.axistags = vigra.AxisTags([vigra.AxisInfo("t"), vigra.AxisInfo("x"), vigra.AxisInfo("y"), vigra.AxisInfo("z"), vigra.AxisInfo("c")])

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        req = self.inputs["Input"][key].writeInto(result)
        req.wait()
        return result

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        # Check for proper name because subclasses may define extra inputs.
        # (but decline to override notifyDirty)
        if slot.name == 'Input':
            self.outputs["Output"].setDirty(key)
        else:
            # If some input we don't know about is dirty (i.e. we are subclassed by an operator with extra inputs),
            # then mark the entire output dirty.  This is the correct behavior for e.g. 'sigma' inputs.
            self.outputs["Output"].setDirty(slice(None))

    def setInSlot(self, slot, subindex, roi, value):
        # Forward to output
        assert subindex == ()
        assert slot == self.Input
        key = roi.toSlice()
        self.outputs["Output"][key] = value
    


 
import sys
if __name__=="__main__":

    #===========================================================================
    # Example of how to do the thing
    # we generate a dot at random position every 200 milliseconds
    # when the dot happen to be in the centre of the movable squere in the
    # image then we show a one on the top left corner
    #===========================================================================
    from ilastik.widgets.boxListView import BoxListView
    from PyQt4.QtGui import QWidget
    app = QApplication([])
    
    boxListModel=BoxListModel()
    
    
    
    
    
    LV=BoxListView()
    LV.setModel(boxListModel)
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
    
    mainwin.layerstack.append(layer)
    mainwin.dataShape=(1,500,500,1,1)
    print mainwin.centralWidget()    
     
     
    BoxContr=BoxController(mainwin.editor.imageScenes[2],op.Output,boxListModel)
    BoxInt=BoxInterpreter(mainwin.editor.navInterpret,mainwin.editor.posModel,BoxContr,mainwin.centralWidget())
    

    mainwin.editor.setNavigationInterpreter(BoxInt)
#     boxListModel.boxRemoved.connect(BoxContr.deleteItem)
    LV.show()
    mainwin.show()
     
    app.exec_()

    
    



