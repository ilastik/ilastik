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
from volumina.pixelpipeline.datasources import LazyflowSource, ConstantSource
from volumina.pixelpipeline._testing import OpDataProvider
from volumina._testing.from_lazyflow import OpDataProvider5D, OpDelay
from volumina.layer import GrayscaleLayer, RGBALayer, ColortableLayer
from volumina.layerwidget.layerwidget import LayerWidget
from volumina.layerstack import LayerStackModel
from volumina.volumeEditor import VolumeEditor
from volumina.volumeEditorWidget import VolumeEditorWidget
from volumina.pixelpipeline.datasources import ArraySource, LazyflowSinkSource

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
        
        self.opPredict = None
        self.opTrain = None
        self.g = Graph()
        
        
        self.featureDlg=None
        self.featScalesList=[.1,.2,1,2]
         #The scales at which features are computed
        
        
        
        self.initUic()
        
        if "5d.npy" in argv:
            self.raw = np.load("5d.npy")
            self.inputProvider = operators.OpArrayPiper(self.g)
            self.inputProvider.inputs["Input"].setValue(self.raw)
            self.haveData.emit()
        
        
        
        
    def initUic(self):
       #Init the graphical elements of the workflow 
       
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
       
       self.labelListModel.rowsAboutToBeRemoved.connect(self.onLabelAboutToBeRemoved)
       self.labelListView.clicked.connect(self.switchLabel)
       self.labelListView.doubleClicked.connect(self.switchColor)
       
       self.AddLabelButton.clicked.connect(self.addLabel)
       
       self.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
       self.StartClassificationButton.clicked.connect(self.startClassification)
       
       self.initTheFeatureDlg()
       
    
    def initTheFeatureDlg(self):
        dlg = FeatureDlg()
        self.featureDlg=dlg
        dlg.setWindowTitle("Features")
        dlg.accepted.connect(self.choosenDifferrentFeatSet)
        
        
        
          
    def onFeatureButtonClicked(self):
        
        dlg=self.featureDlg
        dlg.createFeatureTable({"Features": [SimpleObject("Gaussian smoothing"), SimpleObject("Laplacian of Gaussian"), SimpleObject("Hessian of Gaussian"), SimpleObject("Hessian of Gaussian EV")]}, self.featScalesList)
        dlg.setImageToPreView((numpy.random.rand(100,100)*256).astype(numpy.uint8))
        dlg.show()
    
    
    def choosenDifferrentFeatSet(self):
        dlg=self.featureDlg
        selectedFeatures = dlg.featureTableWidget.createSelectedFeaturesBoolMatrix()
        print "******", selectedFeatures
        
        for i in range(100):
            print "!HAPPY2", 
        
        print self.OpPF.outputs["Output"].shape
        
        self.OpPF.inputs['Matrix'].setValue(numpy.asarray(selectedFeatures))
 
         
         
        
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
            print "Label added, changing predictions"
            #re-train the forest now that we have more labels
            self.opTrain.notifyDirty(None, None)
            self.opPredict.inputs['LabelsCount'].setValue(nlabels)
            self.addPredictionLayer(nlabels-1, self.labelListModel._labels[nlabels-1])
    
    def onLabelAboutToBeRemoved(self, parent, start, end):
        #the user deleted a label, reshape prediction and remove the layer
        #the interface only allows to remove one label at a time?
        
        nout = start-end+1
        ncurrent = self.labelListModel.rowCount()
        print "removing", nout, "out of ", ncurrent
        self.opPredict.inputs['LabelsCount'].setValue(ncurrent-nout)
        for il in range(start, end+1):
            labelvalue = self.labelListModel._labels[il]
            self.removePredictionLayer(labelvalue)
    
    def startClassification(self):
        
        if not self.OpPF.inputs["Matrix"].connected():
            print "Please Before Select Some Features"
            return
        
        if self.opTrain is None:
            #initialize all classification operators
            print "initializing classification..."
            opMultiL = operators.Op5ToMulti(self.g)    
            opMultiL.inputs["Input0"].connect(self.opLabels.outputs["Output"])
            
            self.opTrain = operators.OpTrainRandomForest(self.g)
            self.opTrain.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
            self.opTrain.inputs['Images'].connect(self.OpFeatureCache.outputs["Output"])
            self.opTrain.inputs['fixClassifier'].setValue(False)                
            
            opClassifierCache = operators.OpArrayCache(self.g)
            opClassifierCache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])
           
            ################## Prediction
            self.opPredict=operators.OpPredictRandomForest(self.g)
            nclasses = self.labelListModel.rowCount()
            self.opPredict.inputs['LabelsCount'].setValue(nclasses)
            self.opPredict.inputs['Classifier'].connect(opClassifierCache.outputs['Output']) 
            #self.opPredict.inputs['Classifier'].connect(self.opTrain.outputs['Classifier'])       
            self.opPredict.inputs['Image'].connect(self.OpFeatureCache.outputs["Output"])  
            
            #add prediction results for all classes as separate channels
            for icl in range(nclasses):
                self.addPredictionLayer(icl, self.labelListModel._labels[icl])
                
            #self.updatePredictionLayers()
            
                                    
    def addPredictionLayer(self, icl, ref_label):
        
        selector=operators.OpSingleChannelSelector(self.g)
        selector.inputs["Input"].connect(self.opPredict.outputs['PMaps'])
        selector.inputs["Index"].setValue(icl)
        
        #opSelCache = operators.OpArrayFixableCache(self.g)
        opSelCache = operators.OpArrayCache(self.g)
        opSelCache.inputs["blockShape"].setValue((1,5,5,5,1))
        #opSelCache.inputs["fixAtCurrent"].setValue(False)
        opSelCache.inputs["Input"].connect(selector.outputs["Output"])                
        
        predictsrc = LazyflowSource(opSelCache.outputs["Output"][0])
        
        layer2 = GrayscaleLayer(predictsrc, normalize = (0.0,1.0) )
        layer2.name = "Prediction for " + ref_label.name
        layer2.ref_object = ref_label
        self.layerstack.append( layer2 )
               
    def removePredictionLayer(self, ref_label):
        for il, layer in enumerate(self.layerstack):
            if layer.ref_object==ref_label:
                print "found the prediction", layer.ref_object, ref_label
                self.layerstack.removeRows(il, 1)
                break
    
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
        
        g=self.g
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
        layer1.ref_object = None
        self.layerstack.append(layer1)
        

        
        opImageList = operators.Op5ToMulti(self.g)    
        opImageList.inputs["Input0"].connect(self.inputProvider.outputs["Output"])
        
        
        #Operator of the pixel features
        OpPF = operators.OpPixelFeatures2(g)
        
        print "HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH"
        print self.inputProvider.outputs["Output"].shape
        OpPF.inputs["Input"].setValue(self.inputProvider.outputs["Output"])
        OpPF.inputs["Scales"].setValue(self.featScalesList)
        #OpPF.inputs["Input"].setValue(numpy.random.rand(60,60,60,10,10).astype(numpy.float32))
        #OpPF.inputs["Matrix"].setValue([[1,0,0,0],[1,0,0,0],[1,0,0,0],[1,0,0,0]])
        
        self.OpPF=OpPF
        
        
        #init the features with just the intensity
        opFeatureList = operators.Op5ToMulti(g)    
        opFeatureList.inputs["Input0"].connect(OpPF.outputs["Output"])
        
        #Caching the computed Features
        opFeatureCache = operators.OpArrayCache(g)
        opFeatureCache.inputs["blockShape"].setValue((1,64,64,64,1))
        opFeatureCache.inputs["Input"].connect(opFeatureList.outputs["Outputs"])  
        self.OpFeatureCache=opFeatureCache
        
                
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
        self.labellayer.ref_object = None
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
t = Main(False, sys.argv[1:])
t.show()

app.exec_()
        
        
        

