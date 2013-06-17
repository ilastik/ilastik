#===============================================================================
# Implements a mechanism to updte a graphic element from an operator and the other
# way round
#===============================================================================


from PyQt4 import QtCore,QtGui
from PyQt4.QtCore import QObject, QRect, QSize, pyqtSignal, QEvent, QPoint
from PyQt4.QtGui import QRubberBand,QRubberBand,qRed,QPalette,QBrush,QColor,QGraphicsColorizeEffect
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSlot,QTimer,SIGNAL, QPoint,QPointF
from PyQt4.QtGui import QMainWindow,QGraphicsRectItem,QGraphicsItem, QPen
from PyQt4.QtGui import QApplication


from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.api import Viewer
from volumina.layerstack import LayerStackModel
from volumina.layer import GrayscaleLayer,ColortableLayer
from volumina.colortables import jet

import numpy as np
import vigra

from lazyflow.operator import InputSlot
from lazyflow.graph import Operator, OutputSlot, Graph
from lazyflow.operators.generic import OpSubRegion
from ilastik.widgets.labelListModel import LabelListModel


class Tool():
    
    Navigation = 0 # Arrow
    Paint      = 1
    Erase      = 2
    Box        = 3


class MyGraphicsView(QtGui.QGraphicsView):
    #useful class for debug
    def __init__ (self,parent=None):
        super (MyGraphicsView, self).__init__ (parent)


    def mousePressEvent(self,  event):
        super(MyGraphicsView, self).mousePressEvent(event)
        itemUnderMouse = self.itemAt(event.pos())
        print "here",itemUnderMouse

        
def create_qt_default_env():
    #useful for debug
    from PyQt4.QtGui import QGraphicsScene,QGraphicsView,QApplication
    # 1 make the application
    app=QApplication([])
    # 2 then we need a main window to display stuff
    window=QMainWindow()
    # 3 then we a scene that we want to display
    scene=QGraphicsScene(0,0,400,400)
    
    # 4 view on the scene: open a widget on the main window which dispaly the scene
    view=MyGraphicsView(scene)
    window.setCentralWidget(view)
    #window.show()
    
    return app,window,view,scene


class QResizableRect(QObject):
    """
     This is used to send and sincronize signals
     
    """
    signalHasMoved = pyqtSignal(QPointF) #The resizable rectangle has moved the new position
    signalSelected =  pyqtSignal()
    signalHasResized = pyqtSignal()
    #signalIsMoving = pyqtSignal()
    def __init__(self,x,y,w,h,parent=None):
        QObject.__init__(self,parent)
#         self.x=x
#         self.y=y
#         self.pos=(x,y)
#         self.width=w
#         self.height=h
#         self.shape=(h,w)
#     

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
    

    

    

class QGraphicsResizableRect(QGraphicsRectItem):
    hoverColor    = QColor(255, 0, 0) #hovering and selection color
    
    
    
    def __init__(self,x,y,h,w,scene=None,parent=None):
        
        self.resizableRectObject=QResizableRect(x,y,w,h)
        self.normalColor   = QColor(0, 0, 255)
    
        
        ##Note: need to do like this because the x,y of the graphics item fix the position 
        # of the zero relative to the scene
        QGraphicsRectItem.__init__(self,0,0,w,h,scene=scene,parent=parent)
        
        self.moveBy(x,y)
        self.width=w
        self.height=h
        self.shape=(h,w)
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable,True  )
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable,True)
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges ,True)
        #self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable,True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        
        self.hovering=False
        self.updateColor()
        

        self.has_moved=False
        
        self.resizeHandles=[]
        
        self._selected=False
        
        self.dbg=False
        self._setupTextItem() 
    
    
    def _setupTextItem(self):
        #Set up the text         
        self.textItem=QtGui.QGraphicsTextItem(QtCore.QString(""),parent=self)
        textItem=self.textItem
        textItem.setPos(QtCore.QPointF(0,0)) #upper left corner relative to the father        
        textItem.setDefaultTextColor(QColor(255, 255, 255))
        
        if self.dbg:
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
        
        if self.dbg:
            self.textItemBottom.setPos(QtCore.QPointF(self.width,self.height))
        
        for el in self.resizeHandles:
            el.resetOffset(el._constrainAxis,newshape=self.shape)        
         
        self.resizableRectObject.signalHasResized.emit()
        
        
    def hoverEnterEvent(self, event):
        event.setAccepted(True)
        self.hovering = True
        #elf.setCursor(QtCore.Qt.BlankCursor)
        #self.radius = self.radius # modified radius b/c hovering
        self.updateColor()
        self.setSelected(True)
        self.resetHandles()   
           
        super(QGraphicsResizableRect,self).hoverEnterEvent( event)
  
    def hoverLeaveEvent(self, event):
        event.setAccepted(True)
        self.hovering = False
        self.setSelected(False)
        #self.setCursor(CURSOR)
        #self.radius = self.radius # no longer hovering
        self.resetHandles()
#         for h in self.resizeHandles:
#             self.scene().removeItem(h)
#         self.resizeHandles = []
        super(QGraphicsResizableRect,self).hoverLeaveEvent( event)
    
    def resetHandles(self):
        #if len(self.resizeHandles)>0:
        for h in self.resizeHandles:
            self.scene().removeItem(h)
        self.resizeHandles=[]
        if self.hovering or self.isSelected():
            for constrAxes in range(2):
                h = ResizeHandle((self.height,self.width), constrAxes)
                h.setParentItem(self)
                self.resizeHandles.append( h )
                
    
    def setSelected(self, selected):
        QGraphicsRectItem.setSelected(self, selected) 
        if self.isSelected(): self.resizableRectObject.signalSelected.emit()
        if not self.isSelected(): self.hovering=False
        self.updateColor()
        self.resetHandles()
              
    def updateColor(self):
        color = self.hoverColor if (self.hovering or self.isSelected())  else self.normalColor 
        self.setPen(QtGui.QPen(color,2))
        self.setBrush(QtGui.QBrush(color, QtCore.Qt.NoBrush))
    
    def dataPos(self):
        dataPos = self.scene().scene2data.map(self.scenePos())
        pos = [dataPos.x(), dataPos.y()]
        return pos 
    
        
    def mouseMoveEvent(self,event):
        pos=self.dataPos()
        
        #print self.isSelected(),"HSJAHJHSJAHSJH"
        
        modifiers=QApplication.queryKeyboardModifiers()
        if modifiers == Qt.ControlModifier:
            
            self.has_moved=True
            super(QGraphicsResizableRect, self).mouseMoveEvent(event)
            
            string=str(self.pos()).split("(")[1][:-1]
            #self.QResizableRect.signalIsMoving.emit()
    #         dataPos = self.scene().scene2data.map(self.scenePos())
    #         pos = [dataPos.x(), dataPos.y()]
        
            #self.updateText("("+string+")"+" "+str(pos))
            
    def mouseDoubleClickEvent(self, event):
        print "DOUBLE CLICK ON NODE"
        #FIXME: Implement me
        event.accept()
    
    def updateText(self,string):
        self.textItem.setPlainText(QtCore.QString(string))
    
    
    def mouseReleaseEvent(self, event):
        
        if self.has_moved:
            self.resizableRectObject.signalHasMoved.emit(self.pos())
            #self.has_moved=False
        
            self.has_moved=False
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
        
        self.normalColor.setAlpha(float*255)
        
        self.updateColor()
    
    def setColor(self,qcolor):
        self.normalColor=qcolor
        
        self.updateColor()
    


class CoupledRectangleElement(object):
    def __init__(self,x,y,h,w,inputSlot,scene=None,parent=None,qcolor=QColor(0,0,255)):
        #couple the functionality of the array and the functionality of the
        #resizable rectangel
        #input slot should be a output slot array of another operator
        
        self.rectItem=QGraphicsResizableRect(x,y,h,w,scene,parent)
        self.opsub = OpSubRegion(graph=inputSlot.operator.graph) #sub region correspondig to the rectangle region
        #self.opsum = OpSumAll(graph=inputSlot.operator.graph)
        self._graph=inputSlot.operator.graph
        self._inputSlot=inputSlot #input slot which connect to the sub array
        
        
        self.boxLabel=None
        self._initConnect()
        
        self.color=qcolor
        self.setNormalColor(qcolor)
        
        self.isActive=False
        
        #FIXME: Test
        
    def _initConnect(self):
        print "initializing ...", self.getStart(),self.getStop()
        
        self.opsub.Input.connect(self._inputSlot)
        self.opsub.Start.setValue(self.getStart())
        self.opsub.Stop.setValue(self.getStop())
#         self.opsum.Input.connect(self.opsub.Output)
        self._inputSlot.notifyDirty(self.updateTextWhenChanges)
        
        self.rectItem.resizableRectObject.signalHasMoved.connect(self.updateTextWhenChanges)
        self.rectItem.resizableRectObject.signalHasResized.connect(self.updateTextWhenChanges)
        
        self.updateTextWhenChanges()
        
        
#     def get_opsum(self):
#         return self.opsum
    
    def get_opsub(self):
        return self.opsub


    def disconnectInput(self):
        self._inputSlot.unregisterDirty(self.updateTextWhenChanges)
        self.opsub.Input.disconnect()
    
    def getStart(self):
        rect=self.rectItem
        newstart=self.rectItem.dataPos()
    
        start=(0,newstart[0],newstart[1],0,0)
        return start
    
    def getStop(self):
        rect=self.rectItem
        newstart=self.rectItem.dataPos()
    
        stop=(1,newstart[0]+rect.width,newstart[1]+rect.height,1,1)
        return stop
    
    
    def getSubRegion(self):
        #get the sub region of interest in the array
        oldstart=self.getStart()
        oldstop=self.getStop()
        start=[]
        stop=[]
        for s1,s2 in zip(oldstart,oldstop):
            start.append(int(np.minimum(s1,s2)))
            stop.append(int(np.maximum(s1,s2)))
        
        self.opsub.Stop.disconnect()
        self.opsub.Start.disconnect()
        self.opsub.Start.setValue(tuple(start))
        self.opsub.Stop.setValue(tuple(stop))
        
        return self.opsub.outputs["Output"][:].wait()
        
    def updateTextWhenChanges(self,*args,**kwargs):
        subarray=self.getSubRegion()

        #self.current_sum= self.opsum.outputs["Output"][:].wait()[0]
        value=np.sum(subarray)/255.0
        
        print "Resetting to a new value ",value,self.boxLabel
        
        self.rectItem.updateText("%.1f"%(value))
        
        if self.boxLabel!=None:
            print "SHould redraw"
            from PyQt4.QtCore import QString
            self.boxLabel.density=QString("%.1f"%value)
        
    def setNormalColor(self,qcolor):
        self.rectItem.normalColor=qcolor
        self.rectItem.updateColor()
       
    def setVisible(self,bool):
        return self.rectItem.setVisible(bool)
    
    def setOpacity(self,float):
        return self.rectItem.setOpacity(float)

    

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



class BoxInterpreter(QObject):
    rightClickReceived = pyqtSignal(object, QPoint) # list of indexes, global window coordinate of click
    leftClickReceived = pyqtSignal(object, QPoint)  # ditto
    leftClickReleased = pyqtSignal(object, object)
    #boxAdded= pyqtSignal(object, object)
    focusObjectChages= pyqtSignal(object, QPoint)
    cursorPositionChanged  = pyqtSignal(object)
    deleteItemsSignal= pyqtSignal() #send the signal that we want to delete the currently selected item
    
    def __init__(self, navigationInterpreter, positionModel, BoxContr, widget):
        QObject.__init__(self)
        
        
        self.baseInterpret = navigationInterpreter
        self.posModel      = positionModel
        self.rubberBand = RedRubberBand(QRubberBand.Rectangle, widget)
        
        self.boxController=BoxContr
        
        self.leftClickReleased.connect(BoxContr.addNewBox)
        self.rightClickReceived.connect(BoxContr.onChangedPos)
        self.deleteItemsSignal.connect(BoxContr.deleteSelectItems)
        
        
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
            print event.key()==Qt.Key_N 
            
            if event.key()==Qt.Key_N :
                #assert items[0].hovering
                #items[0].setZValue(1)
                for el in items:
                    print el.zValue()
                
                if len(items)>1:
                    items[-1].setZValue(items[0].zValue()+1)
                    items[0].setSelected(False)
                    items[-1].setSelected(True)
                    #items[0].setZero()
            if event.key()==Qt.Key_Delete:
                self.deleteItemsSignal.emit()
            
        
            
            
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


class BoxController(object):
    def __init__(self,scene,connectionInput,boxListModel):
        self.scene=scene
        self.connectionInput=connectionInput
        self._currentBoxesList=[]
        #self._currentActiveItem=[]
        #self.counter=1000
        self.currentColor=QColor(0,0,255)    
        self.boxListModel=boxListModel
        self.scene.selectionChanged.connect(self.handleSelectionChange)
        
    def getCurrentActiveBox(self):
        pass
        
        
    def addNewBox(self,pos5Dstart,pos5Dstop):
            
        print "Start = ",pos5Dstart,
        print "Stop =", pos5Dstop
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
        
        modifiers=QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier: #add stuff
            return
         
        for el  in self.scene.selectedItems(): #retun if there is an handle
            if isinstance(el, ResizeHandle): return      

        h=stop[1]-start[1]
        w=stop[0]-start[0]
        if h*w<9: return #too small
        
        rect=CoupledRectangleElement(start[0],start[1],h,w,self.connectionInput,scene=self.scene)
        rect.rectItem.setZValue(len(self._currentBoxesList))
        rect.setNormalColor(self.currentColor)
        #self.counter-=1
        self._currentBoxesList.append(rect)
        
        ##add tot hte pos model
        from ilastik.widgets.boxListModel import *
        
        newRow=self.boxListModel.rowCount()
        box = BoxLabel( "Box%d"%newRow, self.currentColor,
                       pmapColor=None,
                   )
        
        box.pmapColorChanged.connect(rect.setNormalColor)
        
        self.boxListModel.insertRow( newRow, box )
        rect.boxLabel=box
        rect.updateTextWhenChanges()
        
        
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
        
        print "here = ",pos
        self.itemsAtpos=items
    
    def deleteSelectItems(self):
        tmp=[]
        for k,el in enumerate(self._currentBoxesList):
            if el.rectItem.isSelected():
                el.disconnectInput()
                el.rectItem.scene().removeItem( el.rectItem)
                del el
                super(type(self.boxListModel),self.boxListModel).removeRow(k)
            else:
                tmp.append(el)
        self._currentBoxesList=tmp
    
    def deleteItem(self,index):
        el=self._currentBoxesList.pop(index)
        el.disconnectInput()
        el.rectItem.scene().removeItem(el.rectItem)
        del el
        
        
    def selectBoxItem(self,index):
        [el.rectItem.setSelected(False) for el in self._currentBoxesList] #deselct the others
        self._currentBoxesList[index].rectItem.setSelected(True)
        
    def handleSelectionChange(self):
        for row,el in enumerate(self._currentBoxesList):
            if el.rectItem.isSelected():
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
    
        
    
import sys
if __name__=="__main__":

    #===========================================================================
    # Example of how to do the thing
    # we generate a dot at random position every 200 milliseconds
    # when the dot happen to be in the centre of the movable squere in the
    # image then we show a one on the top left corner
    #===========================================================================
        
        
    g = Graph()
        
    app = QApplication([])
    cron = QTimer()
    cron.start(500)
    
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
     
     
    BoxContr=BoxController(mainwin.editor.imageScenes[2],op.Output)
    BoxInt=BoxInterpreter(mainwin.editor.navInterpret,mainwin.editor.posModel,BoxContr,mainwin.centralWidget())
    

    mainwin.editor.setNavigationInterpreter(BoxInt)
    
    mainwin.show()
     
    app.exec_()

    
    



