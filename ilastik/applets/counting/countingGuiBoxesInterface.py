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
#===============================================================================
# Implements a mechanism to keep in sinc the GUI elements with the operators
# for the counting applet
# way round
#===============================================================================


from PyQt4 import QtCore,QtGui
from PyQt4.QtCore import QObject, QRect, QSize, pyqtSignal, QEvent, QPoint, pyqtSlot
from PyQt4.QtGui import QRubberBand,QBrush,QColor,QMouseEvent
from PyQt4.QtCore import Qt,QTimer,SIGNAL, QPointF
from PyQt4.QtGui import QGraphicsRectItem,QGraphicsItem, QPen,QFont
from PyQt4.QtGui import QApplication


from volumina.pixelpipeline.datasources import LazyflowSource
from volumina.api import Viewer
from volumina.layer import ColortableLayer
from volumina.colortables import jet

import numpy as np
import vigra

from lazyflow.operator import InputSlot
from lazyflow.graph import Operator, OutputSlot, Graph
from lazyflow.operators.generic import OpSubRegion
##add tot hte pos model
from ilastik.widgets.boxListModel import BoxLabel, BoxListModel

import warnings
import threading

import time

import logging
logger = logging.getLogger(__name__)

DELAY=10 #In millisec,delay in updating the text in the handles, needed because lazy flow cannot stay back the
         #user shuffling the boxes

class Tool():

    Navigation = 0 # Arrow
    Paint      = 1
    Erase      = 2
    Box        = 3

#===============================================================================
# Graphics Classes
#===============================================================================

class ResizeHandle(QGraphicsRectItem):

    def __init__(self, rect, constrainAxis, parent):
        size = 5
        self._rect=rect
        super(ResizeHandle, self).__init__(-size/2, -size/2, 2*size, 2*size, parent)

        #self._offset = offset
        self._constrainAxis = constrainAxis
        self._hoverOver = False

        self.resetOffset(constrainAxis,rect)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable);
        self.setFlag(QtGui.QGraphicsItem.ItemSendsGeometryChanges ,True)
        self._updateColor()

    def resetOffset(self,constrainAxis,rect=None):
        #self._parent=self.parentItem()
        if rect==None:
            rect=self._rect


        if constrainAxis == 0:
            if  rect.bottom()>0:
                self._offset = ((rect.left()+rect.right())/2.0, rect.bottom() )
            else:
                self._offset = ((rect.left()+rect.right())/2.0, rect.top() )

        elif constrainAxis == 1:
            if rect.right()>0:
                self._offset = (rect.right(),(rect.top()+rect.bottom())/2.0 )
            else:
                self._offset = (rect.left(),(rect.top()+rect.bottom())/2.0 )


            #self._offset = ( sel, self.shape[0] )
        #print "Resetting ",self._offset
        self.setPos(QPointF(*self._offset))
        self._rect=rect


    def hoverEnterEvent(self, event):
        super(ResizeHandle, self).hoverEnterEvent(event)
        event.setAccepted(True)
        self._hoverOver = True
        self._updateColor()
        if hasattr(self.parentItem(), "_editor") and \
            self.parentItem()._editor:
            if hasattr(self.parentItem()._editor.eventSwitch.interpreter, "acceptBoxManipulation"):
                if self._constrainAxis == 0:
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.SplitVCursor)
                else:
                    QtGui.QApplication.setOverrideCursor(QtCore.Qt.SplitHCursor)
                

            

    def hoverLeaveEvent(self, event):
        super(ResizeHandle, self).hoverLeaveEvent(event)
        self._hoverOver = False
        self._updateColor()
        QtGui.QApplication.restoreOverrideCursor()


    def mouseMoveEvent(self, event):
        #print "[view=%d] mouse move event constrained to %r" % (self.scene().skeletonAxis, self._constrainAxis)
        super(ResizeHandle, self).mouseMoveEvent(event)

        axes = [0,1]
        rect=self._rect
        flip=False
        if self._constrainAxis == 0:


            if (rect.left()+rect.right())/2.0<0:
                flip=True
            newPoint=QPointF((rect.left()+rect.right())/2.0,self.pos().y())
            self.setPos(newPoint)
            self.parentItem().setNewSize(axes[self._constrainAxis],self.pos().y(),flip)
        else:

            if (rect.top()+rect.bottom())/2.0<0:
                flip=True
            self.setPos(QPointF(self.pos().x(),(rect.top()+rect.bottom())/2.0))
            self.parentItem().setNewSize(axes[self._constrainAxis],self.pos().x(),flip=flip)

    def _updateColor(self):

        color=Qt.white

        if(self._hoverOver):
            self.setBrush(QBrush(color))
            self.setPen(QPen(color))
        else:
            self.setBrush(QBrush(color))
            self.setPen(color)

    def itemChange(self, change,value):
        """
        Enforce that the hadle stays in the region of the scene

        """

        if change==QGraphicsRectItem.ItemPositionChange:
            newPos=value.toPointF() #new position in rectangle coordinates
            nPosScene=self.parentItem().mapToScene(newPos)
            rect=self.parentItem().scene().sceneRect()
            if not rect.contains(nPosScene):
                nPosScene.setX(min(rect.right(), max(nPosScene.x(),rect.left())))
                nPosScene.setY(min(rect.bottom(), max(nPosScene.y(), rect.top())))
                return self.parentItem().mapFromScene(nPosScene)

        return QGraphicsRectItem.itemChange(self, change,value)




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

    def __init__(self,x,y,h,w, scene=None,parent=None, editor=None):
        """"
        This class implements the resizable rectangle item which is dispalied on the scene
         x y should be the original positions in scene coordinates
         h,w are the height and the width of the rectangle
        """
        
        self._editor = editor

        QGraphicsRectItem.__init__(self,0,0,w,h,scene=scene,parent=parent)
        self.Signaller=QGraphicsResizableRectSignaller(parent=parent)


        #Default Appearence Properties
        self._fontColor=QColor(255, 255, 255)
        self._fontSize=10
        self._lineWidth=1

        ##Note: need to do like this because the x,y of the graphics item fix the position
        # of the zero relative to the scene
        self.moveBy(x,y)

        #Flags
        self.setFlag(QGraphicsItem.ItemIsMovable,True  )
        self.setFlag(QGraphicsItem.ItemIsSelectable,True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges ,True)

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
        self._isFixed = False

        self.initHandles()
        self.hideHandles()


        self.setToolTip("Hold CTRL to drag the box")

    @property
    def fontColor(self):
        return self._fontColor

    @pyqtSlot(int)
    def setFontColor(self,color):
        self._fontColor=color
        self.textItem.setDefaultTextColor(color)
        self.updateText(self.textItem.toPlainText())

    @property
    def fontSize(self):
        return self._fontSize

    @pyqtSlot(int)
    def setFontSize(self,s):
        self._fontSize=s
        font=QFont()
        font.setPointSize(self._fontSize)
        self.textItem.setFont(font)
        self.updateText(self.textItem.toPlainText())

    @property
    def lineWidth(self):
        return self._lineWidth

    @pyqtSlot(int)
    def setLineWidth(self,s):
        self._lineWidth=s
        self.updateColor()

    @property
    def color(self):
        return self._normalColor

    @pyqtSlot(int)
    def setColor(self,qcolor):
        self._normalColor=qcolor
        self.updateColor()


    @pyqtSlot()
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

    @pyqtSlot(str)
    def _updateTextBottom(self,string):
        self.textItemBottom.setPlainText(QtCore.QString(string))

    def setNewSize(self, constrainAxis, size, flip=False):

        if constrainAxis == 0:
            h,w = size, self.rect().width()

        else:
            h,w = self.rect().height(), size


        if flip and constrainAxis ==0:
            w=-w
        if flip and constrainAxis ==1:
            h=-h
        newrect=QtCore.QRectF(0, 0, w, h).normalized()
        self.setRect(newrect)
        self.width=self.rect().width()
        self.height=self.rect().height()
        self.shape=(self.height,self.width)

        #Ensures that the text is in the upper left corner
        a=0
        b=0
        if w<=0: a=w
        if h<=0: b=h
        self.textItem.setPos(QtCore.QPointF(a,b))

        if self._dbg:
            self.textItemBottom.setPos(QtCore.QPointF(self.width,self.height))

        for el in self._resizeHandles:
            #print "shape = %s , left = %s , right = %s , top = %s , bottm , %s "%(self.shape,self.rect().left(),self.rect().right(),self.rect().top(),self.rect().bottom())
            el.resetOffset(el._constrainAxis,rect=newrect)


        self.Signaller.signalHasResized.emit()


    def hoverEnterEvent(self, event):
        event.setAccepted(True)
        self._hovering = True
        #elf.setCursor(QtCore.Qt.BlankCursor)
        #self.radius = self.radius # modified radius b/c _hovering
        self.updateColor()
        self.setSelected(True)
        self.showHandles()

        super(QGraphicsResizableRect,self).hoverEnterEvent( event)
        self._editor.imageViews[2].setFocus()

    def hoverLeaveEvent(self, event):
        event.setAccepted(True)
        self._hovering = False
        self.setSelected(False)
        #self.setCursor(CURSOR)
        #self.radius = self.radius # no longer _hovering
        self.hideHandles()
        super(QGraphicsResizableRect,self).hoverLeaveEvent( event)



    def initHandles(self):
        for constrAxes in range(2):
            h = ResizeHandle(self.rect(), constrAxes, self)
            self._resizeHandles.append( h )

    def moveHandles(self):
        for h, constrAxes in zip(self._resizeHandles, range(2)):
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
        if self.isSelected(): self.Signaller.signalSelected.emit()
        if not self.isSelected(): self._hovering=False
        self.updateColor()
        #self.resetHandles()

    @pyqtSlot()
    def updateColor(self):
        color = self.hoverColor if (self._hovering or self.isSelected())  else self._normalColor
        self.setPen(QPen(color,self._lineWidth))
        self.setBrush(QBrush(color, QtCore.Qt.NoBrush))

    def dataPos(self):
        dataPos = self.scenePos()
        pos = [int(dataPos.x()), int(dataPos.y())]

        return pos

    def topLeftDataPos(self):
        dataPos = self.rect().topLeft()+self.scene().scene2data.map(self.scenePos())
        pos = [int(dataPos.x()), int(dataPos.y())]

        return pos

    def bottomRightDataPos(self):
        dataPos = self.rect().bottomRight()+self.scene().scene2data.map(self.scenePos())
        pos = [int(dataPos.x()), int(dataPos.y())]
        return pos

    def mousePressEvent(self,event):
        modifiers=QApplication.queryKeyboardModifiers()
        if modifiers == Qt.ControlModifier:
            QApplication.setOverrideCursor(QtCore.Qt.ClosedHandCursor)

    def mouseMoveEvent(self,event):
        pos=self.dataPos()

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
        logger.debug("DOUBLE CLICK ON ITEM")
        #FIXME: Implement me
        event.accept()

    @pyqtSlot(str)
    def updateText(self,string):

        self.textItem.setPlainText(QtCore.QString(string))


    def mouseReleaseEvent(self, event):

        if self._has_moved:
            self.Signaller.signalHasMoved.emit(self.pos())
            #self._has_moved=False

            self._has_moved=False
        QApplication.restoreOverrideCursor()
        return QGraphicsRectItem.mouseReleaseEvent(self, event)

    
    def itemChange(self, change,value):
        if change==QGraphicsRectItem.ItemPositionChange:
            newPos=value.toPointF() #new position in scene coordinates
            rect=self.scene().sceneRect()
            topLeftRectCoords=self.rect().topLeft()
            bottomRightRectCoords=self.rect().bottomRight()

            ntl=topLeftRectCoords+newPos
            nbr=bottomRightRectCoords+newPos



            if not rect.contains(ntl) or not rect.contains(nbr):
                ntl.setX(min(rect.right()-self.rect().width(), max(ntl.x(),rect.left())))
                ntl.setY(min(rect.bottom()-self.rect().height(), max(ntl.y(), rect.top())));
                return ntl-topLeftRectCoords




        return QGraphicsRectItem.itemChange(self, change,value)


    def setOpacity(self,float):
        logger.debug("Resetting Opacity {}".format(float))

        self._normalColor.setAlpha(float*255)

        self.updateColor()


    def fixSelf(self, isFixed):
        self._isFixed = isFixed
        self.setFlag(QGraphicsItem.ItemIsMovable,not isFixed)
        #self.setFlag(QGraphicsItem.ItemIsSelectable,True)
        #self.setFlag(QGraphicsItem.ItemSendsGeometryChanges ,True)




class RedRubberBand(QRubberBand):
    def __init__(self,*args,**kwargs):
        QRubberBand.__init__(self,*args,**kwargs)

#         palette=QPalette()
#         palette.setBrush(palette.ColorGroup(), palette.foreground(), QBrush( QColor("red") ) );
#         self.setPalette(palette)

    def paintEvent(self,pe):
        painter=QtGui.QStylePainter(self)
        pen=QPen(QColor("red"),4)
        painter.setPen(pen)
        painter.drawRect(pe.rect())

#===============================================================================
# Functional Classes
#===============================================================================

class CoupledRectangleElement(object):
    def __init__(self,x,y,h,w,inputSlot,editor = None, scene=None,parent=None,qcolor=QColor(0,0,255)):
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
        :param qcolor: initial color of the rectangle
        '''


        self._rectItem=QGraphicsResizableRect(x,y,h,w,scene,parent,editor)
        self._opsub = OpSubRegion(graph=inputSlot.operator.graph, parent = inputSlot.operator.parent) #sub region correspondig to the rectangle region
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
        self._opsub.Roi.setValue( [self.getStart(), self.getStop()] )
        self._inputSlot.notifyDirty(self._updateTextWhenChanges)


        #Signalling when the ractangle is moved
        self._rectItem.Signaller.signalHasMoved.connect(self._updateTextWhenChanges)
        self._rectItem.Signaller.signalHasResized.connect(self._updateTextWhenChanges)
        self._updateTextWhenChanges()

    #@mainthreadonly
    @pyqtSlot()
    def _updateTextWhenChanges(self, *args, **kwargs):
        '''
        Do the actual job of displaying a new number when the region gets notified dirty
        or the rectangle is moved or resized
        '''

        time.sleep(DELAY*0.001)


        #FIXME: Workaround: when the array is resized over the border of the image scene the
        # region get a wrong size
        try:
            subarray=self.getSubRegion()

            #self.current_sum= self.opsum.outputs["Output"][:].wait()[0]
            value=0
            if subarray!=None:
                value=np.sum(subarray)

            #print "Resetting to a new value ",value,self.boxLabel

            self._rectItem.updateText("%.1f"%(value))

            if self.boxLabel!=None:
                from PyQt4.QtCore import QString
                self.boxLabel.density=QString("%.1f"%value)
        except Exception,e:
            import warnings
            warnings.warn("Warning: invalid subregion", RuntimeWarning)



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
        newstart=self._rectItem.topLeftDataPos()

        start=(0,newstart[0],newstart[1],0,0)
        return start

    def getStop(self):
        '''
         5D coordinates of the stop position of the subregion
        '''
        rect=self._rectItem
        newstop=self._rectItem.bottomRightDataPos()
        stop=(1,newstop[0],newstop[1],1,1)
        return stop

    def getSubRegion(self):
        '''
        Gets the sub region of interest in the array input Slot

        '''
        oldstart=self.getStart()
        oldstop=self.getStop()

        # print "Start = %s , Stop = %s"%(oldstart,oldstop)

        start=[]
        stop=[]
        for s1,s2 in zip(oldstart,oldstop):
            if (s1-s2) == 0: #means that the region is squeezed to zero
                           # thus return None
                return None
            start.append(int(np.minimum(s1,s2)))
            stop.append(int(np.maximum(s1,s2)))

        self._opsub.Roi.disconnect()
        self._opsub.Roi.setValue([ tuple(start), tuple(stop)] )


        return self._opsub.outputs["Output"][:].wait()

    @property
    def color(self):
        return self._rectItem.color

    def setColor(self,qcolor):
        self._rectItem.setColor(qcolor)

    @property
    def fontSize(self):
        return self._rectItem.fontSize

    def setFontSize(self,size):
        self._rectItem.setFontSize(size)

    @property
    def fontColor(self):
        return self._rectItem.fontSize

    def setFontColor(self,color):
        self._rectItem.setFontColor(color)

    @property
    def lineWidth(self):
        return self._rectItem.lineWidth

    def setLineWidth(self,w):
        self._rectItem.setLineWidth(w)

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
        self.boxLabel.existenceChanged.emit()
        #FIXME: maybe dangerous to do del explicitely here
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

    acceptBoxManipulation = True

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
        self._posModel      = positionModel
        self.rubberBand = RedRubberBand(QRubberBand.Rectangle, widget)

        self.boxController=BoxContr

        self.leftClickReleased.connect(BoxContr.addNewBox)
        self.rightClickReceived.connect(BoxContr.onChangedPos)
        #self.deleteSelectedItemsSignal.connect(BoxContr.deleteSelectedItems)


        self.origin = QPoint()
        self.originpos = object()

    def start( self ):
        self.baseInterpret.start()

    def stop( self ):
        self.baseInterpret.stop()

    def eventFilter( self, watched, event ):
        pos = [int(i) for i in self._posModel.cursorPos]
        pos = [self._posModel.time] + pos + [self._posModel.channel]

        #Rectangles under the current point
        items=watched.scene().items(QPointF(*pos[1:3]))
        items=filter(lambda el: isinstance(el, QGraphicsResizableRect),items)


        #Keyboard interaction
        if event.type()==QEvent.KeyPress:
            #Switch selection
            if event.key()==Qt.Key_Space :
                #assert items[0]._hovering
                #items[0].setZValue(1)
                #for el in items:
                #    print el.zValue()

                if len(items)>1:
                    items[-1].setZValue(items[0].zValue()+1)
                    items[0].setSelected(False)
                    items[-1].setSelected(True)
                    #items[0].setZero()

            if event.key()==Qt.Key_Control :
                QApplication.setOverrideCursor(QtCore.Qt.OpenHandCursor)

            # #Delete element
            # if event.key()==Qt.Key_Delete:
            #     self.deleteSelectedItemsSignal.emit()
        if event.type()==QEvent.KeyRelease:
            if event.key()==Qt.Key_Control :
                QApplication.restoreOverrideCursor()


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
            pos = [int(i) for i in self._posModel.cursorPos]
            pos = [self._posModel.time] + pos + [self._posModel.channel]
            if self.rubberBand.isVisible():
                if event.button() == Qt.LeftButton:
                    self.rubberBand.hide()
                    self.leftClickReleased.emit( self.originpos,pos )

        # Event is always forwarded to the navigation interpreter.
        return self.baseInterpret.eventFilter(watched, event)


class BoxController(QObject):

    fixedBoxesChanged = pyqtSignal(dict)
    viewBoxesChanged = pyqtSignal(dict)


    def __init__(self,editor,connectionInput,boxListModel):
        '''
        Class which controls all boxes on the scene

        :param scene:
        :param connectionInput: The imput slot to which connect all the new boxes
        :param boxListModel:

        '''

        scene = editor.imageScenes[2]
        self._editor = editor
        
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
        boxListModel.signalSaveAllBoxesToCSV.connect(self.saveBoxesToCSV)



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

        rect=CoupledRectangleElement(start[0],start[1],h,w,self.connectionInput,editor = self._editor, scene=self.scene,parent=self.scene.parent())
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
        box.existenceChanged.connect(self._viewBoxesChanged)


        self.boxListModel.insertRow( newRow, box )
        box.existenceChanged.emit()
        rect.boxLabel=box
        box.isFixedChanged.connect(rect._rectItem.fixSelf)
        rect._updateTextWhenChanges()

        self.currentColor=self._getNextBoxColor()

    def _fixedBoxesChanged(self, *args):
        boxes = {"rois" : [], "values" : []}
        for box, rect in zip(self.boxListModel._elements, self._currentBoxesList):
            if rect._rectItem.scene() and box.isFixed:
                boxes["rois"].append([rect.getStart(), rect.getStop()])
                boxes["values"].append(float(box._fixvalue.toDouble()[0]))

        self.fixedBoxesChanged.emit(boxes)

        self._viewBoxesChanged()
    
    def _viewBoxesChanged(self, *args):
        boxes = {"rois" : []}
        for box, rect in zip(self.boxListModel._elements, self._currentBoxesList):
            if rect._rectItem.scene() and not box.isFixed:
                boxes["rois"].append([rect.getStart(), rect.getStop()])

        self.viewBoxesChanged.emit(boxes)



    def itemsAtPos(self,pos5D):
        pos5D=pos5D[1:3]
        items=self.scene.items(QPointF(*pos5D))
        items=filter(lambda el: isinstance(el, ResizeHandle),items)
        return items

    def onChangedPos(self,pos,gpos):
        pos=pos[1:3]
        items=self.scene.items(QPointF(*pos))
        #print items
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


    def saveBoxesToCSV(self,filename):
        import os,csv
        b,ext=os.path.splitext(str(filename))
        assert ext ==".txt","wrong filename or extension %s"%str(filename)
        try:
            with open(filename,'wb') as fh:



                header = ["ID","StartX","StartY","StopX","StopY","Count","Average density","Std density"]

                fh.write(" , ".join(header) +"\n")


                for k,box in enumerate(self._currentBoxesList):
                    start=box.getStart()
                    stop=box.getStop()
                    region = box.getSubRegion()
                    count = np.sum(region)
                    averagedens = np.mean(region)
                    stddensity = np.std(region)


                    line=["%5.5d"%k, "%5.5d"%start[1], "%5.5d"%start[2], "%5.5d"%stop[1],\
                    "%5.5d"%stop[2],"%5.2f"%count,"%5.2f"%averagedens, "%5.2f"%stddensity]
                    logger.debug( "line " + ",".join(line) )
                    fh.write(",".join(line)+"\n")



        except IOError,e:
            logger.error( e )
            raise IOError

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


    h,w=(500,500)


    LV=BoxListView()
    LV.setModel(boxListModel)
    LV._table.setShowGrid(True)
    g = Graph()

    cron = QTimer()
    cron.start(500*100)

    op = OpArrayPiper2(graph=g) #Generate random noise
    shape=(1,w,h,1,1)

    #array = np.random.randint(0,255,500*500).reshape(shape).astype(np.uint8)
    import scipy
    array=scipy.misc.lena().astype(np.uint8)
    array=vigra.sampling.resize(array.astype(np.float32),(h,w)).reshape(shape).astype(np.uint8)
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
    mainwin.dataShape=(1,h,w,1,1)
    print mainwin.centralWidget()


    BoxContr=BoxController(mainwin.editor,op.Output,boxListModel)
    BoxInt=BoxInterpreter(mainwin.editor.navInterpret,mainwin.editor.posModel,BoxContr,mainwin.centralWidget())


    mainwin.editor.setNavigationInterpreter(BoxInt)
#     boxListModel.boxRemoved.connect(BoxContr.deleteItem)
    LV.show()
    mainwin.show()

    app.exec_()






