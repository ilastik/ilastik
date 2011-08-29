#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os, sys, numpy

from PyQt4.QtCore import pyqtSignal, QTimer, QString
from PyQt4.QtGui import QColor, QMainWindow, QApplication, QFileDialog, \
                        QMessageBox, qApp, QItemSelectionModel
from PyQt4 import uic

from lazyflow.graph import Graph
from lazyflow.operators import Op5ToMulti, OpArrayCache, OpArrayFixableCache, \
                               OpArrayPiper, OpPredictRandomForest, \
                               OpSingleChannelSelector, OpSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForest

from lazyflow import operators

from volumeeditor.pixelpipeline.datasources import LazyflowSource
from volumeeditor.pixelpipeline._testing import OpDataProvider
from volumeeditor.layer import GrayscaleLayer, RGBALayer, ColortableLayer, \
                               AlphaModulatedLayer
from volumeeditor.layerstack import LayerStackModel
from volumeeditor.volumeEditor import VolumeEditor
from volumeeditor.volumeEditorWidget import VolumeEditorWidget
from volumeeditor.pixelpipeline.datasources import LazyflowSinkSource

from labelListView import Label
from labelListModel import LabelListModel

from featureDlg import FeatureDlg, FeatureEntry

class Main(QMainWindow):    
    haveData        = pyqtSignal()
    dataReadyToView = pyqtSignal()
        
    def __init__(self, argv):
        QMainWindow.__init__(self)
        
        self.opPredict = None
        self.opTrain = None
        self._colorTable16 = self._createDefault16ColorColorTable()
        
        self.g = Graph()
        self.fixableOperators = []
        self.predictionSources = []
        
        self.initUic()
        
        #
        # if the filename was specified on command line, load it
        #
        if len(sys.argv) == 2:
            def loadFile():
                self._openFile(sys.argv[1])
            QTimer.singleShot(0, loadFile)
        
    def initUic(self):
        #get the absolute path of the 'ilastik' module
        uic.loadUi("designerElements/MainWindow_multifile.ui", self) 
        #connect the window and graph creation to the opening of the file
        self.actionOpen.triggered.connect(self.openFile)
        self.actionQuit.triggered.connect(qApp.quit)
        def toggleDebugPatches(show):
            self.editor.showDebugPatches = show
        self.actionShowDebugPatches.toggled.connect(toggleDebugPatches)
        
        self.haveData.connect(self.initGraph)
        self.haveData.connect(self.fillFileList)
        self.dataReadyToView.connect(self.initEditor)
        
        self.fileListWidget.itemSelectionChanged.connect(self.switchImage)
        
        self.layerstack = LayerStackModel()
        
        model = LabelListModel()
        self.labelListView.setModel(model)
        self.labelListModel=model
        
        self.labelListModel.rowsAboutToBeRemoved.connect(self.onLabelAboutToBeRemoved)
        self.labelListModel.labelSelected.connect(self.switchLabel)
        
        def onDataChanged(topLeft, bottomRight):
            firstRow = topLeft.row()
            lastRow  = bottomRight.row()
            assert firstRow == lastRow
            firstCol = topLeft.column()
            lastCol  = bottomRight.column()
            if 0 in range(firstCol, lastCol+1):
                self.switchColor(firstRow+1, self.labelListModel[firstRow].color)
                self.editor.scheduleSlicesRedraw()
            #self.onColorChanged()
            
            
        self.labelListModel.dataChanged.connect(onDataChanged)
        
        self.AddLabelButton.clicked.connect(self.addLabel)
        
        self.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
        self.StartClassificationButton.clicked.connect(self.initClassification)
        
        self.checkInteractive.toggled.connect(self.toggleInteractive)   
 
    def toggleInteractive(self, checked):
        print "checked = ", checked
        
        #Check if the number of labels in the layer stack is equals to the number of Painted labels
        if checked==True:
            nPaintedLabels = 0
            for opl in self.opLabelList:
                labels =numpy.unique(numpy.asarray(opl.outputs["nonzeroValues"][:].allocate().wait()[0]))
                nPaintedLabels = labels.shape[0] if labels.shape[0]>nPaintedLabels else nPaintedLabels
            #nPaintedLabels=labels.shape[0]
            nLabelsLayers = self.labelListModel.rowCount()
            if nPaintedLabels!=nLabelsLayers:
                self.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("Did you forget to paint some labels?")
                mexBox.setInformativeText("Painted Labels %d \nNumber Active Labels Layers %d"%(nPaintedLabels,self.labelListModel.rowCount()))
                mexBox.exec_()
                #print "Painted Labels: ", labels
                #print "nPainted Labels: " , nPaintedLabels
                #print "nLabelsLayers", self.labelListModel.rowCount()
                return
        
        if checked==True:
            self.AddLabelButton.setEnabled(False)
            self.SelectFeaturesButton.setEnabled(False)
            for o in self.fixableOperators:
                o.inputs["fixAtCurrent"].setValue(False)
        else:
            self.AddLabelButton.setEnabled(True)
            self.SelectFeaturesButton.setEnabled(True)
            for o in self.fixableOperators:
                o.inputs["fixAtCurrent"].setValue(True)
       
    def onFeatureButtonClicked(self):
        ex2 = FeatureDlg()
        ex2.createFeatureTable({"Color": [FeatureEntry("Banananananaana")], "Edge": [FeatureEntry("Mango"), FeatureEntry("Cherry")]}, [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
        ex2.setWindowTitle("ex2")
        ex2.setImageToPreView((numpy.random.rand(100,100)*256).astype(numpy.uint8))
        self.featureDlg=ex2
        ex2.show()     
        
    def switchLabel(self, row):
        print "switching to label=%r" % (self.labelListModel[row])
        #+1 because first is transparent
        
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        self.editor.brushingModel.setBrushColor(self.labelListModel[row].color)
        
    def switchColor(self, row, color):
        print "label=%d changes color to %r" % (row, color)
        self.labellayer.colorTable[row]=color.rgba()
        self.editor.brushingModel.setBrushColor(color)
        self.editor.scheduleSlicesRedraw()
    
    def addLabel(self):
        color = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
        numLabels = len(self.labelListModel)
        if numLabels < len(self._colorTable16):
            color = self._colorTable16[numLabels]
        self.labellayer.colorTable.append(color.rgba())
        
        self.labelListModel.insertRow(self.labelListModel.rowCount(), Label("Label %d" % (self.labelListModel.rowCount() + 1), color))
        nlabels = self.labelListModel.rowCount()
        if self.opPredict is not None:
            print "Label added, changing predictions"
            #re-train the forest now that we have more labels
            #self.opTrain.notifyDirty(None, None)
            self.opPredict.inputs['LabelsCount'].setValue(nlabels)
            self.addPredictionLayer(nlabels-1, self.labelListModel._labels[nlabels-1])
        
        #make the new label selected
        index = self.labelListModel.index(nlabels-1, 1)
        self.labelListModel._selectionModel.select(index, QItemSelectionModel.ClearAndSelect)
        
        
        #FIXME: this should watch for model changes   
        #drawing will be enabled when the first label is added  
        self.editor.setDrawingEnabled(True)
    
    def onLabelAboutToBeRemoved(self, parent, start, end):
        #the user deleted a label, reshape prediction and remove the layer
        #the interface only allows to remove one label at a time?
        
        nout = start-end+1
        ncurrent = self.labelListModel.rowCount()
        print "removing", nout, "out of ", ncurrent
        
        if self.opPredict is not None:
            self.opPredict.inputs['LabelsCount'].setValue(ncurrent-nout)
        for il in range(start, end+1):
            labelvalue = self.labelListModel._labels[il]
            self.removePredictionLayer(labelvalue)
            self.opLabels.inputs["deleteLabel"].setValue(il+1)
            self.editor.scheduleSlicesRedraw()
            
    
    def initClassification(self):
        if self.opTrain is None:
            #initialize all classification operators
            print "initializing classification..."
            #opMultiL = Op5ToMulti(self.g)    
            #opMultiL.inputs["Input0"].connect(self.opLabels.outputs["Output"])
            
            self.opTrain = OpTrainRandomForest(self.g)
            self.opTrain.inputs['Labels'].connect(self.opMultiL.outputs["Outputs"])
            self.opTrain.inputs['Images'].connect(self.featureStacker.outputs["Output"])
            self.opTrain.inputs['fixClassifier'].setValue(False)                
            
            opClassifierCache = OpArrayCache(self.g)
            opClassifierCache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])
           
            ################## Prediction
            self.opPredict=OpPredictRandomForest(self.g)
            nclasses = self.labelListModel.rowCount()
            self.opPredict.inputs['LabelsCount'].setValue(nclasses)
            self.opPredict.inputs['Classifier'].connect(opClassifierCache.outputs['Output']) 
            self.opPredict.inputs['Image'].connect(self.featureStacker.outputs['Output'])  
            
            #add prediction results for all classes as separate channels
            for icl in range(nclasses):
                self.addPredictionSourceOperators(icl)
                self.addPredictionLayer(self.currentInputProviderIndex, icl, self.labelListModel._labels[icl])
    
    def addPredictionSourceOperators(self, icl):
        #init the operators for displaying the prediction results
        
        selector=OpSingleChannelSelector(self.g)
        selector.inputs["Input"].connect(self.opPredict.outputs['PMaps'])
        selector.inputs["Index"].setValue(icl)
        
        opSelCache = OpArrayFixableCache(self.g)
        #opSelCache = OpArrayCache(self.g)
        opSelCache.inputs["blockShape"].setValue((1,128,128,128,1))
        opSelCache.inputs["Input"].connect(selector.outputs["Output"])  
        if self.checkInteractive.isChecked():
            opSelCache.inputs["fixAtCurrent"].setValue(False)
        else:
            opSelCache.inputs["fixAtCurrent"].setValue(True)
        
        self.predictionSources.append(opSelCache)
        self.fixableOperators.append(opSelCache)
    
    def addPredictionLayer(self, inputSourceIndex, icl, ref_label):
        
        predictsrc = LazyflowSource(self.predictionSources[icl].outputs["Output"][inputSourceIndex])
        
        predictLayer = AlphaModulatedLayer(predictsrc, tintColor=ref_label.color, normalize = (0.0,1.0) )
        
        def setLayerColor(c):
            print "as the color of label '%s'  has changed, setting layer's '%s' tint color to %r" % (ref_label.name, predictLayer.name, c)
            predictLayer.tintColor = c
        ref_label.colorChanged.connect(setLayerColor)
        def setLayerName(n):
            newName = "Prediction for %s" % ref_label.name
            print "as the name of label '%s' has changed, setting layer's '%s' name to '%s'" % (ref_label.name, predictLayer.name, newName)
            predictLayer.name = newName
        setLayerName(ref_label.name)
        ref_label.nameChanged.connect(setLayerName)
        
        predictLayer.ref_object = ref_label
        #make sure that labels (index = 0) stay on top!
        self.layerstack.insert(1, predictLayer )
        #self.fixableOperators.append(opSelCache)
               
    def removePredictionLayer(self, ref_label):
        for il, layer in enumerate(self.layerstack):
            if layer.ref_object==ref_label:
                print "found the prediction", layer.ref_object, ref_label
                self.layerstack.removeRows(il, 1)
                break
    
    def openFile(self):
        
        fileNames = QFileDialog.getOpenFileNames(self, "Open Image", os.path.abspath(__file__), "Numpy files (*.npy)")
        print "files selected:", fileNames
        self._openFile(fileNames)
        
    def _openFile(self, fileNames):
        self.totalInputProvider = None        
        self.inputProviders = []
        self.fileList = []
        self.currentInputProviderIndex = 0
        for fname in fileNames: 
            fName, fExt = os.path.splitext(str(fname))
            if fExt=='.npy':
                self.raw = numpy.load(str(fname))
                self.min, self.max = numpy.min(self.raw), numpy.max(self.raw)
                if self.totalInputProvider is None:
                    self.totalInputProvider = operators.OpMultiArrayPiper(self.g)
                    self.totalInputProvider.inputs["MultiInput"].resize(len(fileNames))
                ip = OpArrayPiper(self.g)
                ip.inputs["Input"].setValue(self.raw)
                self.inputProviders.append(ip)
                self.totalInputProvider.inputs["MultiInput"].connect(ip.outputs["Output"])
                self.currentInputProviderIndex = 0     
                self.fileList.append(str(fname))               
                #self.inputProvider = OpArrayPiper(self.g)
                #self.inputProvider.inputs["Input"].setValue(self.raw)
            else:
                print "not supported yet"
                return
        self.haveData.emit()
       
    def initGraph(self):
        print "going to init the graph"
        

        
        #opImageList = Op5ToMulti(self.g)    
        #opImageList.inputs["Input0"].connect(self.inputProvider.outputs["Output"])
        
        #init the features with just the intensity
        opFeatureList = Op5ToMulti(self.g)    
        opFeatureList.inputs["Input0"].connect(self.totalInputProvider.outputs["MultiOutput"])

        self.featureStacker=OpMultiArrayStacker(self.g)
        self.featureStacker.inputs["Images"].connect(opFeatureList.outputs["Outputs"])
        self.featureStacker.inputs["AxisFlag"].setValue('c')
        self.featureStacker.inputs["AxisIndex"].setValue(4)
        
        self.initDataLayers(0)
        self.initLabels()
        self.dataReadyToView.emit()
    
    def initDataLayers(self, inputSourceIndex):
        #init the layers to display the input data for the source number inputSourceIndex
        
        shape = self.inputProviders[inputSourceIndex].outputs["Output"].shape
        print "data block shape: ", shape
        srcs    = []
        minMax = []
        
        #create a layer for each channel of the input:
        nchannels = shape[-1]
        #DANGERDANGER: allocate the whole thing until something better comes up
        self.raw = self.inputProviders[inputSourceIndex].outputs["Output"][:].allocate().wait()
        
        for ich in range(nchannels):
            op1 = OpDataProvider(self.g, self.raw[..., ich:ich+1])

            #find the minimum and maximum value for normalization
            #FIXME: this reads the whole data in memory. OK for 5d.npy, not ok in general
            mm = (numpy.min(self.raw[..., ich:ich+1]), numpy.max(self.raw[..., ich:ich+1]))
            print "  - channel %d: min=%r, max=%r" % (ich, mm[0], mm[1])
            if mm == (0.0, 255.0):
                #do not normalize in this case
                mm = None
            minMax.append(mm)
            layersrc = LazyflowSource(op1.outputs["Data"])
            srcs.append(layersrc)
            
        #FIXME: we shouldn't merge channels automatically, but for now it's prettier
        layer1 = None
        if nchannels == 1:
            layer1 = GrayscaleLayer(srcs[0], normalize=minMax[0])
            layer1.rangeRed   = minMax[0]
            print "  - showing raw data as grayscale"
        elif nchannels==2:
            layer1 = RGBALayer(red  = srcs[0], normalizeR=minMax[0],
                               green = srcs[1], normalizeG=minMax[1])
            layer1.rangeRed   = minMax[0]
            layer1.rangeGreen = minMax[1]
            print "  - showing channel 1 as red, channel 2 as green"
        elif nchannels==3:
            layer1 = RGBALayer(red   = srcs[0], normalizeR=minMax[0],
                               green = srcs[1], normalizeG=minMax[1],
                               blue  = srcs[2], normalizeB=minMax[2])
            layer1.rangeRed   = minMax[0]
            layer1.rangeGreen = minMax[1]
            layer1.rangeBlue  = minMax[2]
            print "  - showing channel 1 as red, channel 2 as green, channel 3 as blue"
        else:
            print "only 1,2 or 3 channels supported so far"
            return
        
        layer1.name = "Input data"
        layer1.ref_object = None
        self.layerstack.append(layer1)
        
    def initLabels(self):
        #Add the layer to draw the labels, but don't add any labels
        self.opLabelList = []
        #FIXME: limited to 10 images for now
        self.opMultiL = operators.Op10ToMulti(self.g)
        nsources = len(self.inputProviders)
        for nip, ip in enumerate(self.inputProviders):
            opl = operators.OpSparseLabelArray(self.g)
            opl.inputs["shape"].setValue(ip.outputs["Output"].shape[:-1] + (1,))
            opl.inputs["eraser"].setValue(100)
            #ugly-ugly-ugly
            ipname = "Input"+str(nip)
            self.opMultiL.inputs[ipname].connect(opl.outputs["Output"])
            self.opLabelList.append(opl)     
        self.initLabelLayer(0)
    
    def initLabelLayer(self, inputSourceIndex):
        self.labelsrc = LazyflowSinkSource(self.opLabelList[inputSourceIndex], \
                                           self.opLabelList[inputSourceIndex].outputs["Output"], \
                                           self.opLabelList[inputSourceIndex].inputs["Input"])
        transparent = QColor(0,0,0,0)
        self.labellayer = ColortableLayer(self.labelsrc, colorTable = [transparent.rgba()] )
        self.labellayer.name = "Labels"
        self.labellayer.ref_object = None
        self.layerstack.append(self.labellayer)
    
    def initEditor(self):
        print "going to init editor"
        print "raw shape:", self.raw.shape
        print "layer stack: ", len(self.layerstack)
        
        self.editor = VolumeEditor(self.raw.shape, self.layerstack, labelsink=self.labelsrc)
        #drawing will be enabled when the first label is added  
        self.editor.setDrawingEnabled(False)
        
        self.volumeEditorWidget.init(self.editor)
        model = self.editor.layerStack
        self.layerWidget.init(model)
        self.UpButton.clicked.connect(model.moveSelectedUp)
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        self.DeleteButton.clicked.connect(model.deleteSelected)
        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)           
    
    def fillFileList(self):
        for f in self.fileList:
            self.fileListWidget.addItem(QString(f))
        self.fileListWidget.setCurrentRow(self.currentInputProviderIndex)
        
    def switchImage(self):
        print
        print "switching image..."
        self.layerstack = LayerStackModel()
        newindex = self.fileListWidget.currentRow()
        self.currentInputProviderIndex = newindex
        self.initDataLayers(newindex)
        self.initLabelLayer(newindex)
        nclasses = self.labelListModel.rowCount()
        for icl in range(nclasses):
            self.addPredictionLayer(self.currentInputProviderIndex, icl, self.labelListModel._labels[icl])
        self.initEditor()
    
    def _createDefault16ColorColorTable(self):
        c = []
        c.append(QColor(255, 0, 0))
        c.append(QColor(0, 255, 0))
        c.append(QColor(0, 0, 255))
        c.append(QColor(255, 255, 0))
        c.append(QColor(0, 255, 255))
        c.append(QColor(255, 0, 255))
        c.append(QColor(255, 105, 180)) #hot pink
        c.append(QColor(102, 205, 170)) #dark aquamarine
        c.append(QColor(165,  42,  42)) #brown        
        c.append(QColor(0, 0, 128))     #navy
        c.append(QColor(255, 165, 0))   #orange
        c.append(QColor(173, 255,  47)) #green-yellow
        c.append(QColor(128,0, 128))    #purple
        c.append(QColor(192, 192, 192)) #silver
        c.append(QColor(240, 230, 140)) #khaki
        c.append(QColor(69, 69, 69))    #dark grey
        return c
    
app = QApplication(sys.argv)        
t = Main(sys.argv)
t.show()

app.exec_()
        
        
        

