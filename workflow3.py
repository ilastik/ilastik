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

from featureDlg import *

import  numpy


class Main(QMainWindow):
     def __init__(self, useGL, argv):
         QMainWindow.__init__(self)
         self.initUic()
         
     def initUic(self):
         
        self.g=g=Graph() 
         
        #get the absolute path of the 'ilastik' module
        uic.loadUi("designerElements/MainWindow.ui", self) 
        
        self.layerstack = LayerStackModel()
        
        fn = os.path.split(os.path.abspath(__file__))[0] +"/5d.npy"
        raw = np.load(fn)
        
        op1 = OpDataProvider(g, raw[:,:,:,:,0:1]/20)
        op2 = OpDelay(g, 0.00000)
        op2.inputs["Input"].connect(op1.outputs["Data"])
        nucleisrc = LazyflowSource(op2.outputs["Output"])
        op3 = OpDataProvider(g, raw[:,:,:,:,1:2]/10)
        op4 = OpDelay(g, 0.00000)
        op4.inputs["Input"].connect(op3.outputs["Data"])
        membranesrc = LazyflowSource(op4.outputs["Output"])
        
        tint = np.zeros(shape=raw.shape, dtype=np.uint8)
        tint[:] = 255
        tintsrc = ArraySource(tint)
        
        #new shit
        from lazyflow import operators
        opLabels = operators.OpSparseLabelArray(g)                                
        opLabels.inputs["shape"].setValue(raw.shape[:-1] + (1,))
        opLabels.inputs["eraser"].setValue(100)                
        opLabels.inputs["Input"][0,0,0,0,0] = 1                    
        opLabels.inputs["Input"][0,0,0,1,0] = 2                    
        
        labelsrc = LazyflowSinkSource(opLabels, opLabels.outputs["Output"], opLabels.inputs["Input"])
        
        layer1 = RGBALayer( green = membranesrc, red = nucleisrc )
        layer1.name = "Membranes/Nuclei"
        
        
        self.layerstack.append(layer1)
        
        
        opImage  = operators.OpArrayPiper(g)
        opImage.inputs["Input"].setValue(raw[:,:,:,:,0:1]/20)
        opImage2  = operators.OpArrayPiper(g)
        opImage2.inputs["Input"].setValue(raw[:,:,:,:,1:2]/10)
        
        opImageList = operators.Op5ToMulti(g)    
        opImageList.inputs["Input0"].connect(opImage.outputs["Output"])
        opImageList.inputs["Input1"].connect(opImage2.outputs["Output"])
        
        
        opFeatureList = operators.Op5ToMulti(g)    
        opFeatureList.inputs["Input0"].connect(opImageList.outputs["Outputs"])
        
        #                
        stacker=operators.OpMultiArrayStacker(g)
        #                
        #                opMulti = operators.Op20ToMulti(g)    
        #                opMulti.inputs["Input00"].connect(opG.outputs["Output"])
        stacker.inputs["Images"].connect(opFeatureList.outputs["Outputs"])
        stacker.inputs["AxisFlag"].setValue('c')
        stacker.inputs["AxisIndex"].setValue(4)
        
        ################## Training
        opMultiL = operators.Op5ToMulti(g)    
        
        opMultiL.inputs["Input0"].connect(opLabels.outputs["Output"])
        
        opTrain = operators.OpTrainRandomForest(g)
        opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
        opTrain.inputs['Images'].connect(stacker.outputs["Output"])
        opTrain.inputs['fixClassifier'].setValue(False)                
        
        opClassifierCache = operators.OpArrayCache(g)
        opClassifierCache.inputs["Input"].connect(opTrain.outputs['Classifier'])
        
        ################## Prediction
        opPredict=operators.OpPredictRandomForest(g)
        opPredict.inputs['LabelsCount'].setValue(2)
        opPredict.inputs['Classifier'].connect(opClassifierCache.outputs['Output'])    
        opPredict.inputs['Image'].connect(stacker.outputs['Output'])            
        
        
        
        selector=operators.OpSingleChannelSelector(g)
        selector.inputs["Input"].connect(opPredict.outputs['PMaps'])
        selector.inputs["Index"].setValue(1)
        
        opSelCache = operators.OpArrayCache(g)
        opSelCache.inputs["blockShape"].setValue((1,5,5,5,1))
        opSelCache.inputs["Input"].connect(selector.outputs["Output"])                
        
        predictsrc = LazyflowSource(opSelCache.outputs["Output"][0])
        
        layer2 = GrayscaleLayer( predictsrc, normalize = (0.0,1.0) )
        layer2.name = "Prediction"
        self.layerstack.append( layer2 )
                      
        source = nucleisrc        
        
        
        
        
        
        

        
        useGL=False
        
        model = LabelListModel()
        self.labelListView.setModel(model)
        self.labelListModel=model
        
        shape = raw.shape
        
        transparent = QColor(0,0,0,0)
        self.labellayer = ColortableLayer(labelsrc, colorTable = [transparent.rgba()] )
        self.labellayer.name = "Labels"
        self.layerstack.append(self.labellayer)        
        
        self.labelListView.clicked.connect(self.switchLabel)
        self.labelListView.doubleClicked.connect(self.switchColor)
        
        self.editor = VolumeEditor(shape, self.layerstack, labelsink=labelsrc, useGL=useGL)  
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
        
        
        #connections
        self.AddLabelButton.clicked.connect(self.addLabel)
        
        self.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
        
     def onFeatureButtonClicked(self):
         ex2 = FeatureDlg()
         ex2.createFeatureTable({"Color": [SimpleObject("Banananananaana")], "Edge": [SimpleObject("Mango"), SimpleObject("Cherry")]}, [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
         ex2.setWindowTitle("ex2")
         ex2.setImageToPreView((numpy.random.rand(100,100)*256).astype(numpy.uint8))
         
         
         self.featureDlg=ex2
         ex2.show()     
     def switchLabel(self, modelIndex):
         self.editor.brushingModel.setDrawnNumber(modelIndex.row()+1)
         
     def switchColor(self, modelIndex):
         if modelIndex.column()>0:
             return
         #FIXME: we shouldn't pass the role like that, some object should know it
         newcolor = self.labelListView.model().data(modelIndex, Qt.EditRole)
         # +1 because the first entry of the color table is transparent
         self.labellayer.colorTable[modelIndex.row()+1]=newcolor.rgba()
         self.editor.invalidateAllSlices()
     
     def addLabel(self):
         color = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
         self.labellayer.colorTable.append(color.rgba())
         self.labelListModel.insertRow(self.labelListModel.rowCount(), Label("Label %d" % (self.labelListModel.rowCount() + 1), color))
        
     def createLabelSource(self, shape):
         pass
         from lazyflow import operators
               
         
         
         
         
         labelsrc = LazyflowSinkSource(opLabels, opLabels.outputs["Output"], opLabels.inputs["Input"])
         return labelsrc
     
     def startClassification():
       self.g

app = QApplication(sys.argv)        
t = Main(False, [])
t.show()

app.exec_()




