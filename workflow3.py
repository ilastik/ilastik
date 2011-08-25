#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os, sys

import numpy as np
from PyQt4.QtCore import QObject, QRectF, QTime, Qt, pyqtSignal
from PyQt4.QtGui import QColor, QApplication, QSplitter, QPushButton, \
                        QVBoxLayout, QWidget, QHBoxLayout, QMainWindow

from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow import operators
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
    
    haveData = pyqtSignal()
    dataReadyToView = pyqtSignal()
        
    def __init__(self, useGL, argv):
        QMainWindow.__init__(self)
        self.initUic()
        self.opPredict = None
        self.opTrain = None
        
    def initUic(self):
        
       
       #get the absolute path of the 'ilastik' module
       uic.loadUi("designerElements/MainWindow.ui", self) 
       #connect the window and graph creation to the opening of the file
       self.actionOpen.triggered.connect(self.openFile)
       
       self.haveData.connect(self.initGraph)
       self.dataReadyToView.connect(self.initEditor)

       self.layerstack = LayerStackModel()
       model = LabelListModel()
       self.labelListView.setModel(model)
       self.labelListModel=model
       
       self.labelListView.clicked.connect(self.switchLabel)
       self.labelListView.doubleClicked.connect(self.switchColor)
       
       self.AddLabelButton.clicked.connect(self.addLabel)
       
       self.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
       self.StartClassificationButton.clicked.connect(self.startClassification)
       
       self.g = Graph()
       
 
       
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
        nlabels = self.labelListModel.rowCount()
        if self.opPredict is not None:
            self.opPredict.inputs['LabelsCount'].setValue(nlabels)
            self.updatePredictionLayers()
    
    def startClassification(self):
        if self.opTrain is None:
            #initialize all classification operators
            print "initializing classification..."
            opMultiL = operators.Op5ToMulti(self.g)    
            opMultiL.inputs["Input0"].connect(self.opLabels.outputs["Output"])
            
            self.opTrain = operators.OpTrainRandomForest(self.g)
            self.opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
            self.opTrain.inputs['Images'].connect(self.featureStacker.outputs["Output"])
            self.opTrain.inputs['fixClassifier'].setValue(False)                
            
            opClassifierCache = operators.OpArrayCache(self.g)
            opClassifierCache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])
           
            ################## Prediction
            self.opPredict=operators.OpPredictRandomForest(self.g)
            nclasses = self.labelListModel.rowCount()
            self.opPredict.inputs['LabelsCount'].setValue(nclasses)
            self.opPredict.inputs['Classifier'].connect(opClassifierCache.outputs['Output'])    
            self.opPredict.inputs['Image'].connect(self.featureStacker.outputs['Output'])  
            
            #add prediction results for all classes as separate channels
            self.updatePredictionLayers()
            
    def updatePredictionLayers(self):
            nclasses = self.labelListModel.rowCount()
            #FIXME: remove the layers by name: how else?
            
            predictionlayers = [layer for layer in self.layerstack if "Prediction" in layer.name]
            if (len(predictionlayers)>0):
                print "already have prediction layers:", len(predictionlayers)
                print "don't know what to do now :("
                return 
            
            for icl in range(nclasses):          
                selector=operators.OpSingleChannelSelector(self.g)
                selector.inputs["Input"].connect(self.opPredict.outputs['PMaps'])
                selector.inputs["Index"].setValue(1)
            
                opSelCache = operators.OpArrayCache(self.g)
                opSelCache.inputs["blockShape"].setValue((1,5,5,5,1))
                opSelCache.inputs["Input"].connect(selector.outputs["Output"])                
            
                predictsrc = LazyflowSource(opSelCache.outputs["Output"][0])
            
                layer2 = GrayscaleLayer(predictsrc, normalize = (0.0,1.0) )
                layer2.name = "Prediction for label %d"%icl
                self.layerstack.append( layer2 )
                                    
           
            
    
    def openFile(self):
        #FIXME: only take one file for now, more to come
        #fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Image", os.path.abspath(__file__), "Image Files (*.png *.jpg *.bmp *.tif *.tiff *.gif *.h5)")
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Image", os.path.abspath(__file__), "Numpy files (*.npy)")
        fName, fExt = os.path.splitext(str(fileName))
        self.inputProvider = None
        if fExt=='.npy':
            self.raw = np.load(str(fileName))
            self.inputProvider = operators.OpArrayPiper(self.g)
            self.inputProvider.inputs["Input"].setValue(self.raw)
        else:
            print "not supported yet"
            return
        self.haveData.emit()
       
    def initGraph(self):
        print "going to init the graph"
        
        shape = self.inputProvider.outputs["Output"].shape
        print "data block shape: ", shape
        srcs = []
        #create a layer for each channel of the input:
        nchannels = shape[-1]
        for ich in range(nchannels):
            op1 = OpDataProvider(self.g, self.raw[..., ich:ich+1])
            op2 = OpDelay(self.g, 0.0000)
            op2.inputs["Input"].connect(op1.outputs["Data"])
            layersrc = LazyflowSource(op2.outputs["Output"])
            srcs.append(layersrc)
            
        #FIXME: we shouldn't merge channels automatically, but for now it's prettier
        layer1 = None
        if nchannels == 1:
            layer1 = GrayscaleLayer(srcs[0])
        elif nchannels==2:
            layer1 = RGBALayer(green = srcs[0], red = srcs[1])
        elif nchannels==3:
            layer1 = RGBALayer(green = srcs[0], red = srcs[1], blue = srcs[2])
        else:
            print "only 1,2 or 3 channels supported so far"
            return
        layer1.name = "Input data"
        self.layerstack.append(layer1)
        
#        op1 = OpDataProvider(self.g, self.raw[:,:,:,:,0:1]/20)
#        op2 = OpDelay(self.g, 0.00000)
#        op2.inputs["Input"].connect(op1.outputs["Data"])
#        nucleisrc = LazyflowSource(op2.outputs["Output"])
#        
#        op3 = OpDataProvider(self.g, self.raw[:,:,:,:,1:2]/10)
#        op4 = OpDelay(self.g, 0.00000)
#        op4.inputs["Input"].connect(op3.outputs["Data"])
#        membranesrc = LazyflowSource(op4.outputs["Output"])
#        
#        layer1 = RGBALayer( green = membranesrc, red = nucleisrc )
#        layer1.name = "Membranes/Nuclei"
#        self.layerstack.append(layer1)
        
        opImageList = operators.Op5ToMulti(self.g)    
        opImageList.inputs["Input0"].connect(self.inputProvider.outputs["Output"])
        
        #init the features with just the intensity
        opFeatureList = operators.Op5ToMulti(self.g)    
        opFeatureList.inputs["Input0"].connect(opImageList.outputs["Outputs"])

        self.featureStacker=operators.OpMultiArrayStacker(self.g)
        self.featureStacker.inputs["Images"].connect(opFeatureList.outputs["Outputs"])
        self.featureStacker.inputs["AxisFlag"].setValue('c')
        self.featureStacker.inputs["AxisIndex"].setValue(4)
        
        self.initLabels()
        self.dataReadyToView.emit()
        
    def initLabels(self):
        self.opLabels = operators.OpSparseLabelArray(self.g)                                
        self.opLabels.inputs["shape"].setValue(self.raw.shape[:-1] + (1,))
        self.opLabels.inputs["eraser"].setValue(100)                
        self.opLabels.inputs["Input"][0,0,0,0,0] = 1                    
        self.opLabels.inputs["Input"][0,0,0,1,0] = 2                    
        
        self.labelsrc = LazyflowSinkSource(self.opLabels, self.opLabels.outputs["Output"], self.opLabels.inputs["Input"])
        transparent = QColor(0,0,0,0)
        self.labellayer = ColortableLayer(self.labelsrc, colorTable = [transparent.rgba()] )
        self.labellayer.name = "Labels"
        self.layerstack.append(self.labellayer)    
    
    def initEditor(self):
        print "going to init editor"
        useGL = False
        self.editor = VolumeEditor(self.raw.shape, self.layerstack, labelsink=self.labelsrc, useGL=useGL)  
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
        
        
        

