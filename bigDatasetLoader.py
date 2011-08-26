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
from volumeeditor._testing.from_lazyflow import OpThorbenHack 


from labelListView import LabelListView, Label
from labelListModel import LabelListModel

from PyQt4 import QtCore, QtGui, uic

from featureDlg import *

import  numpy

from lazyflow import operators as op

class Main(QMainWindow):
     def __init__(self, useGL, argv):
         QMainWindow.__init__(self)
         self.initUic()
         
     def initUic(self):
         
        self.g=g=Graph(8,softMaxMem = 15000*1024**2) 
         
        #get the absolute path of the 'ilastik' module
        uic.loadUi("designerElements/MainWindow.ui", self) 
        
        self.layerstack = LayerStackModel()
        
        
        Reader=op.OpH5Reader(g)
        
        Reader.inputs["Filename"].setValue("scripts/Knott_compressed_oldshape.h5")
        Reader.inputs["hdf5Path"].setValue("volume/data")
        
        
        opFeatureCache = op.OpArrayCache(g)
        opFeatureCache.inputs["blockShape"].setValue((1,128,128,128,1))
        opFeatureCache.inputs["Input"].connect(Reader.outputs["Image"]) 
        
        """
        import h5py
        f=h5py.File("Knott_compressed.h5",'r')
        d=f["volume/data"].value
        
        #Try
        opImage  = op.OpArrayPiper(g)
        opImage.inputs["Input"].setValue(d)
        """
      
        #datasrc = LazyflowSource(opFeatureCache.outputs["Output"])
        datasrc = LazyflowSource(Reader.outputs["Image"])
        
        
        #datasrc = LazyflowSource(opImage.outputs["Output"])
        
        layer1 = GrayscaleLayer( datasrc,normalize = (0.0,255.0) )
        layer1.name = "Big Data"
        
        
        self.layerstack.append(layer1)
        
        
        

        
        useGL=False
        
        
        shape=Reader.outputs["Image"].shape
        print shape
        self.editor = VolumeEditor(shape, self.layerstack,useGL=useGL,showDebugTiles=True)  
        self.editor.setDrawingEnabled(True)
        
        self.volumeEditorWidget.init(self.editor)
        model = self.editor.layerStack
        self.layerWidget.init(model)
        
        self.UpButton.clicked.connect(model.moveSelectedUp)
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        self.DeleteButton.clicked.connect(model.deleteSelected)
        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)        
        
        
        
        
     
app = QApplication(sys.argv)        
t = Main(False, [])
t.show()

app.exec_()