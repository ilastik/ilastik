#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os, sys

import numpy as np
from PyQt4.QtCore import QObject, QRectF, QTime, Qt
from PyQt4.QtGui import QColor, QApplication, QSplitter, QPushButton, \
                        QVBoxLayout, QWidget, QHBoxLayout, QMainWindow

from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from volumeeditor.pixelpipeline.datasources import LazyflowSource, ConstantSource
from volumeeditor.pixelpipeline._testing import OpDataProvider
from volumeeditor._testing.from_lazyflow import OpDataProvider5D, OpDelay
from volumeeditor.layer import GrayscaleLayer, RGBALayer, ColortableLayer
from volumeeditor.layerwidget.layerwidget import LayerWidget
from volumeeditor.layerstack import LayerStackModel
from volumeeditor.volumeEditor import VolumeEditor
from volumeeditor.volumeEditorWidget import VolumeEditorWidget
from volumeeditor.pixelpipeline.datasources import ArraySource, LazyflowSinkSource

from labelListView import LabelListView, Label
from labelListModel import LabelListModel

from PyQt4 import QtCore, QtGui, uic


class Main(QMainWindow):
     def __init__(self, useGL, argv):
         QMainWindow.__init__(self)
         self.initUic()
         
     def initUic(self):
        #get the absolute path of the 'ilastik' module
        
        uic.loadUi("designerElements/MainWindow.ui", self) 
        fn = os.path.split(os.path.abspath(__file__))[0] +"/5d.npy"
        raw = np.load(fn)

        self.layerstack = LayerStackModel()
        useGL=False
        nucleisrc = ArraySource(raw[...,0:1]/20)
        membranesrc = ArraySource(raw[...,0:1]/20)
        
        layer1 = GrayscaleLayer( membranesrc )
        layer1.name = "Membranes"
        self.layerstack.append(layer1)
        
        layer2 = RGBALayer( red = nucleisrc )
        layer2.name = "Nuclei"
        layer2.opacity = 0.5
        
     
        
        self.layerstack.append(layer2)
        
        shape = raw.shape
        labelsrc = self.createLabelSource(shape)
        red   = QColor(255,0,0)
        green = QColor(0,255,0)
        black = QColor(0,0,0,0)
        
        self.labellayer = ColortableLayer(labelsrc, colorTable = [black.rgba(), red.rgba(), green.rgba()] )
        self.labellayer.name = "Labels"
        self.layerstack.append(self.labellayer)        
        
        
        
        self.editor = VolumeEditor(shape, self.layerstack, labelsink=labelsrc, useGL=useGL)  
        self.editor.setDrawingEnabled(True)
        
        self.volumeEditorWidget.init(self.editor)
        model = self.editor.layerStack
        self.layerWidget.init(model)        
     
     def switchLabel(self, modelIndex):
         self.editor.brushingModel.setDrawnNumber(modelIndex.row()+1)
         
     def switchColor(self, modelIndex):
         if modelIndex.column()>0:
             return
         #FIXME: we shouldn't pass the role like that, some object should know it
         newcolor = self.labelList.model().data(modelIndex, Qt.EditRole)
         self.labellayer.colorTable[modelIndex.row()+1]=newcolor.rgba()

     
     def createLabelSource(self, shape):
         from lazyflow import operators
         g = Graph()
         self.g=g
         opLabels = operators.OpSparseLabelArray(g)                                
         opLabels.inputs["shape"].setValue(shape[:-1] + (1,))
         opLabels.inputs["eraser"].setValue(100)                
         #opLabels.inputs["Input"][0,0,0,0,0] = 1                    
         #opLabels.inputs["Input"][0,0,0,1,0] = 2                    
         
         labelsrc = LazyflowSinkSource(opLabels, opLabels.outputs["Output"], opLabels.inputs["Input"])
         return labelsrc
     
     def startClassification():
       self.g

app = QApplication(sys.argv)        
t = Main(False, [])
t.show()

app.exec_()




