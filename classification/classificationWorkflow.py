#make the program quit on Ctrl+C
import signal
from lazyflow.operators.obsolete.vigraOperators import OpH5WriterBigDataset
from lazyflow.operators.ioOperators import OpH5Writer
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os, sys, numpy, copy

import h5py

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL
from PyQt4.QtGui import QColor, QMainWindow, QApplication, QFileDialog, \
                        QMessageBox, qApp, QItemSelectionModel, QIcon, QTransform, QDialog
from PyQt4 import uic

from igms.stackloader import OpStackChainBuilder,StackLoader

from lazyflow.graph import Graph
from lazyflow.operators import Op5ToMulti, OpArrayCache, OpBlockedArrayCache, \
                               OpArrayPiper, OpPredictRandomForest, \
                               OpSingleChannelSelector, OpSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForest, OpPixelFeatures, \
                               OpMultiArraySlicer2,OpH5Reader, OpBlockedSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForestBlocked, OpPixelFeatures, \
                               OpH5ReaderBigDataset, OpSlicedBlockedArrayCache, OpPixelFeaturesPresmoothed

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
    AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource
from volumina.adaptors import Op5ifyer
from igms.labelListView import Label
from igms.labelListModel import LabelListModel

from igms.featureTableWidget import FeatureEntry
from igms.featureDlg import FeatureDlg
from exportDlg import ExportDialog
from loadFileDlg import LoadFileDialog

import vigra

from pixel_classification_lazyflow import PixelClassificationLazyflow


class Main(QMainWindow):    
    haveData        = pyqtSignal()
    dataReadyToView = pyqtSignal()
        
    def __init__(self, argv):
        QMainWindow.__init__(self)
        
        #Normalize the data if true
        self._normalize_data=True
        
        if 'notnormalize' in sys.argv:
            print sys.argv
            self._normalize_data=False
            sys.argv.remove('notnormalize')
        if len(sys.argv)==2:
            def loadCommandlineFile():
                self._openFile(sys.argv[1:])
            QTimer.singleShot(0, loadCommandlineFile)

        self._colorTable16 = self._createDefault16ColorColorTable()
        
        self.g = Graph()
        self.workflow = None
        self.fixableOperators = []
        
        self.featureDlg=None

        
        #The old ilastik provided the following scale names:
        #['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        #The corresponding scales are:
        self.featScalesList=[0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        
        self.initUic()
        
        #if the filename was specified on command line, load it
        def loadFile():
            self._openFile(sys.argv[1:])
        if len(sys.argv) > 2:
            QTimer.singleShot(0, loadFile)
        
    def setIconToViewMenu(self):
            self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))
        
    def initUic(self):
        try:
            p = os.path.split(__file__)[0]+'/'
        except:
            p = '.'
        if p == "/": p = "."+p
        uic.loadUi(p+"/classificationWorkflow.ui", self) 
        #connect the window and graph creation to the opening of the file
        self.actionOpenFile.triggered.connect(self._load)
        self.actionOpenStack.triggered.connect(self.openImageStack)
        self.actionQuit.triggered.connect(qApp.quit)
        self.actionSaveAs.triggered.connect(self._save)
        
        def toggleDebugPatches(show):
            self.editor.showDebugPatches = show
        def fitToScreen():
            shape = self.editor.posModel.shape
            for i, v in enumerate(self.editor.imageViews):
                s = list(copy.copy(shape))
                del s[i]
                v.changeViewPort(v.scene().data2scene.mapRect(QRectF(0,0,*s)))  
                
        def fitImage():
            if hasattr(self.editor, '_lastImageViewFocus'):
                self.editor.imageViews[self.editor._lastImageViewFocus].fitImage()
                
        def restoreImageToOriginalSize():
            if hasattr(self.editor, '_lastImageViewFocus'):
                self.editor.imageViews[self.editor._lastImageViewFocus].doScaleTo()
                    
        def rubberBandZoom():
            if hasattr(self.editor, '_lastImageViewFocus'):
                if not self.editor.imageViews[self.editor._lastImageViewFocus]._isRubberBandZoom:
                    self.editor.imageViews[self.editor._lastImageViewFocus]._isRubberBandZoom = True
                    self.editor.imageViews[self.editor._lastImageViewFocus]._cursorBackup = self.editor.imageViews[self.editor._lastImageViewFocus].cursor()
                    self.editor.imageViews[self.editor._lastImageViewFocus].setCursor(Qt.CrossCursor)
                else:
                    self.editor.imageViews[self.editor._lastImageViewFocus]._isRubberBandZoom = False
                    self.editor.imageViews[self.editor._lastImageViewFocus].setCursor(self.editor.imageViews[self.editor._lastImageViewFocus]._cursorBackup)
                
        
        def hideHud():
            if self.editor.imageViews[0]._hud.isVisible():
                hide = False
            else:
                hide = True
            for i, v in enumerate(self.editor.imageViews):
                v.hideHud(hide)
                
        def toggleSelectedHud():
            if hasattr(self.editor, '_lastImageViewFocus'):
                self.editor.imageViews[self.editor._lastImageViewFocus].toggleHud()
                
        def centerAllImages():
            for i, v in enumerate(self.editor.imageViews):
                v.centerImage()
                
        def centerImage():
            if hasattr(self.editor, '_lastImageViewFocus'):
                self.editor.imageViews[self.editor._lastImageViewFocus].centerImage()
                self.actionOnly_for_current_view.setEnabled(True)
        
        self.actionCenterAllImages.triggered.connect(centerAllImages)
        self.actionCenterImage.triggered.connect(centerImage)
        self.actionToggleAllHuds.triggered.connect(hideHud)
        self.actionToggleSelectedHud.triggered.connect(toggleSelectedHud)
        self.actionShowDebugPatches.toggled.connect(toggleDebugPatches)
        self.actionFitToScreen.triggered.connect(fitToScreen)
        self.actionFitImage.triggered.connect(fitImage)
        self.actionReset_zoom.triggered.connect(restoreImageToOriginalSize)
        self.actionRubberBandZoom.triggered.connect(rubberBandZoom)
        
        self.haveData.connect(self.initGraph)
        self.dataReadyToView.connect(self.initEditor)
        
        self.layerstack = LayerStackModel()
        
        model = LabelListModel()
        self.labelListView.setModel(model)
        self.labelListModel=model
        
        self.labelListModel.rowsAboutToBeRemoved.connect(self.onLabelAboutToBeRemoved)
        self.labelListModel.labelSelected.connect(self.switchLabel)
        
        def onDataChanged(topLeft, bottomRight):
            firstRow = topLeft.row()
            lastRow  = bottomRight.row()
        
            firstCol = topLeft.column()
            lastCol  = bottomRight.column()
            
            if lastCol == firstCol == 0:
                assert(firstRow == lastRow) #only one data item changes at a time

                #in this case, the actual data (for example color) has changed
                self.switchColor(firstRow+1, self.labelListModel[firstRow].color)
                self.editor.scheduleSlicesRedraw()
            else:
                #this column is used for the 'delete' buttons, we don't care
                #about data changed here
                pass
            
        self.labelListModel.dataChanged.connect(onDataChanged)
        
        self.AddLabelButton.clicked.connect(self.addLabel)
        
        self.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)

        self.checkInteractive.setEnabled(False)
        self.checkInteractive.toggled.connect(self.toggleInteractive)   

        self.interactionComboBox.currentIndexChanged.connect(self.changeInteractionMode)
        self.interactionComboBox.setEnabled(False)

        self._initFeatureDlg()
        
    def toggleInteractive(self, checked):
        print "toggling interactive mode to '%r'" % checked
        
        #Check if the number of labels in the layer stack is equals to the number of Painted labels
        if checked==True:
            labels =numpy.unique(numpy.asarray(self.workflow.labels.outputs["nonzeroValues"][:].allocate().wait()[0]))           
            nPaintedLabels=labels.shape[0]
            nLabelsLayers = self.labelListModel.rowCount()
            selectedFeatures = numpy.asarray(self.featureDlg.featureTableWidget.createSelectedFeaturesBoolMatrix())
            
            if nPaintedLabels!=nLabelsLayers:
                self.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("Did you forget to paint some labels?")
                mexBox.setInformativeText("Painted Labels %d \nNumber Active Labels Layers %d"%(nPaintedLabels,self.labelListModel.rowCount()))
                mexBox.exec_()
                return
            if (selectedFeatures==0).all():
                self.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("The are no features selected ")
                mexBox.exec_()
                return
        else:
            self.g.stopGraph()
            self.g.resumeGraph()
                
        self.AddLabelButton.setEnabled(not checked)
        self.SelectFeaturesButton.setEnabled(not checked)
        for o in self.fixableOperators:
            o.inputs["fixAtCurrent"].setValue(not checked)
        self.labelListModel.allowRemove(not checked)
        
        self.editor.scheduleSlicesRedraw()

    def changeInteractionMode( self, index ):
        modes = {0: "navigation", 1: "brushing"}
        self.editor.setInteractionMode( modes[index] )
        self.interactionComboBox.setCurrentIndex(index)
        print "interaction mode switched to", modes[index]

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
        if self.workflow is not None:
            print "Label added, changing predictions"
            #re-train the forest now that we have more labels
            self.workflow.predict.inputs['LabelsCount'].setValue(nlabels)
            self.addPredictionLayer(nlabels-1, self.labelListModel._labels[nlabels-1])
        
        #make the new label selected
        index = self.labelListModel.index(nlabels-1, 1)
        self.labelListModel._selectionModel.select(index, QItemSelectionModel.ClearAndSelect)
        
        #FIXME: this should watch for model changes   
        #drawing will be enabled when the first label is added  
        self.changeInteractionMode( 1 )
        self.interactionComboBox.setEnabled(True)
    
    def onLabelAboutToBeRemoved(self, parent, start, end):
        #the user deleted a label, reshape prediction and remove the layer
        #the interface only allows to remove one label at a time?
        
        nout = start-end+1
        ncurrent = self.labelListModel.rowCount()
        print "removing", nout, "out of ", ncurrent
        
        if self.workflow is not None:
            self.workflow.predict.inputs['LabelsCount'].setValue(ncurrent-nout)
        for il in range(start, end+1):
            labelvalue = self.labelListModel._labels[il]
            self.removePredictionLayer(labelvalue)
            self.workflow.labels.inputs["deleteLabel"].setValue(il+1)
            self.editor.scheduleSlicesRedraw()
            
    def startClassification(self):
        nclasses = self.labelListModel.rowCount()
        self.workflow.predict.inputs['LabelsCount'].setValue(nclasses)

        #add prediction results for all classes as separate channels
        for icl in range(nclasses):
            self.addPredictionLayer(icl, self.labelListModel._labels[icl])
        self.checkInteractive.setEnabled(True)
                                    
    def addPredictionLayer(self, icl, ref_label):
        
        selector=OpSingleChannelSelector(self.g)
        selector.inputs["Input"].connect(self.workflow.prediction_cache.outputs['Output'])
        selector.inputs["Index"].setValue(icl)
                
        self.workflow.prediction_cache.inputs["fixAtCurrent"].setValue(not self.checkInteractive.isChecked())
        
        predictsrc = LazyflowSource(selector.outputs["Output"][0])
        def srcName(newName):
            predictsrc.setObjectName("Prediction for %s" % ref_label.name)
        srcName("")
        
        predictLayer = AlphaModulatedLayer(predictsrc, tintColor=ref_label.color, normalize = None )
        predictLayer.nameChanged.connect(srcName)
        
        def setLayerColor(c):
            print "as the color of label '%s' has changed, setting layer's '%s' tint color to %r" % (ref_label.name, predictLayer.name, c)
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
        self.fixableOperators.append(self.workflow.prediction_cache)
               
    def removePredictionLayer(self, ref_label):
        for il, layer in enumerate(self.layerstack):
            if layer.ref_object==ref_label:
                print "found the prediction", layer.ref_object, ref_label
                self.layerstack.removeRows(il, 1)
                break
    
    def openImageStack(self):
        self.stackLoader = StackLoader()
        self.stackLoader.show()
        self.stackLoader.loadButton.clicked.connect(self._stackLoad)

    def openFile(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Open Image", os.path.abspath(__file__))
        if fileNames.count() == 0:
            return
        #self._openFile(fileNames)
        self._load()
        
    def _save(self):
        exportDlg = ExportDialog()
        exportDlg.setInput(self.workflow.images.outputs["Outputs"][0], self.g)
        exportDlg.exec_()
        #print self.workflow.prediction_cache.outputs["Output"][0].shape
        #print self.workflow.prediction_cache.outputs["Output"][0].dtype
        #print self.workflow.prediction_cache.outputs["Output"][0].axistags
        #print type(self.workflow.prediction_cache.outputs["Output"][0])

    def _load(self):
        
        loadDlg = LoadFileDialog()
        filename = str(loadDlg.exec_())
        hdf5Path = 'volume/data'
        f = h5py.File(filename, 'r')
        self.inputProvider = OpArrayPiper(self.g)
        self.raw = f[hdf5Path][:]
        self.raw = self.raw.view(vigra.VigraArray)
        self.min, self.max = numpy.min(self.raw), numpy.max(self.raw)
        self.raw.axistags =  vigra.AxisTags(
                vigra.AxisInfo('t',vigra.AxisType.Time),
                vigra.AxisInfo('x',vigra.AxisType.Space),
                vigra.AxisInfo('y',vigra.AxisType.Space),
                vigra.AxisInfo('z',vigra.AxisType.Space),
                vigra.AxisInfo('c',vigra.AxisType.Channels))
        self.inputProvider.inputs["Input"].setValue(self.raw)
        self.haveData.emit()
        
        

    def _stackLoad(self):
        self.inputProvider = OpArrayPiper(self.g)
        op5ifyer = Op5ifyer(self.g)
        op5ifyer.inputs["Input"].connect(self.stackLoader.ChainBuilder.outputs["output"])
        self.raw = op5ifyer.outputs["Output"][:].allocate().wait()
        self.raw = self.raw.view(vigra.VigraArray)
        self.min, self.max = numpy.min(self.raw), numpy.max(self.raw)
        self.raw.axistags =  vigra.AxisTags(
                vigra.AxisInfo('t',vigra.AxisType.Time),
                vigra.AxisInfo('x',vigra.AxisType.Space),
                vigra.AxisInfo('y',vigra.AxisType.Space),
                vigra.AxisInfo('z',vigra.AxisType.Space),
                vigra.AxisInfo('c',vigra.AxisType.Channels))
        self.inputProvider.inputs["Input"].setValue(self.raw)
        self.haveData.emit()
        self.stackLoader.close()
        
    def _openFile(self, fileNames):
        self.inputProvider = None
        fName, fExt = os.path.splitext(str(fileNames[0]))
        print "Opening Files %r" % fileNames
        if fExt=='.npy':
            fileName = fileNames[0]
            if len(fileNames)>1:
                print "WARNING: only the first file will be read, multiple file prediction not supported yet"
            fName, fExt = os.path.splitext(str(fileName))
            self.raw = numpy.load(str(fileName))
            self.min, self.max = numpy.min(self.raw), numpy.max(self.raw)
            self.inputProvider = OpArrayPiper(self.g)
            self.raw = self.raw.view(vigra.VigraArray)
            self.raw.axistags =  vigra.AxisTags(
                vigra.AxisInfo('t',vigra.AxisType.Time),
                vigra.AxisInfo('x',vigra.AxisType.Space),
                vigra.AxisInfo('y',vigra.AxisType.Space),
                vigra.AxisInfo('z',vigra.AxisType.Space),
                vigra.AxisInfo('c',vigra.AxisType.Channels))
            self.inputProvider.inputs["Input"].setValue(self.raw)
        elif fExt=='.h5':
            readerNew=OpH5ReaderBigDataset(self.g)
            
            
            readerNew.inputs["Filenames"].setValue(fileNames)
            readerNew.inputs["hdf5Path"].setValue("volume/data")

            readerCache =  OpSlicedBlockedArrayCache(self.g)
            readerCache.inputs["fixAtCurrent"].setValue(False)
            readerCache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
            readerCache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
            readerCache.inputs["Input"].connect(readerNew.outputs["Output"])

            self.inputProvider = OpArrayPiper(self.g)
            self.inputProvider.inputs["Input"].connect(readerCache.outputs["Output"])
        else:
            raise RuntimeError("opening filenames=%r not supported yet" % fileNames)
        
        self.haveData.emit()
       
    def initGraph(self):
        shape = self.inputProvider.outputs["Output"].shape
        srcs    = []
        minMax = []
        
        print "* Data has shape=%r" % (shape,)
        
        #create a layer for each channel of the input:
        slicer=OpMultiArraySlicer2(self.g)
        slicer.inputs["Input"].connect(self.inputProvider.outputs["Output"])
        
        slicer.inputs["AxisFlag"].setValue('c')
       
        nchannels = shape[-1]
        for ich in xrange(nchannels):
            if self._normalize_data:
                data=slicer.outputs['Slices'][ich][:].allocate().wait()
                #find the minimum and maximum value for normalization
                mm = (numpy.min(data), numpy.max(data))
                print "  - channel %d: min=%r, max=%r" % (ich, mm[0], mm[1])
                minMax.append(mm)
            else:
                minMax.append(None)
            layersrc = LazyflowSource(slicer.outputs['Slices'][ich], priority = 100)
            layersrc.setObjectName("raw data channel=%d" % ich)
            srcs.append(layersrc)
            
        #FIXME: we shouldn't merge channels automatically, but for now it's prettier
        layer1 = None
        if nchannels == 1:
            layer1 = GrayscaleLayer(srcs[0], normalize=minMax[0])
            layer1.set_range(0,minMax[0])
            print "  - showing raw data as grayscale"
        elif nchannels==2:
            layer1 = RGBALayer(red  = srcs[0], normalizeR=minMax[0],
                               green = srcs[1], normalizeG=minMax[1])
            layer1.set_range(0, minMax[0])
            layer1.set_range(1, minMax[1])
            print "  - showing channel 1 as red, channel 2 as green"
        elif nchannels==3:
            layer1 = RGBALayer(red   = srcs[0], normalizeR=minMax[0],
                               green = srcs[1], normalizeG=minMax[1],
                               blue  = srcs[2], normalizeB=minMax[2])
            layer1.set_range(0, minMax[0])
            layer1.set_range(1, minMax[1])
            layer1.set_range(2, minMax[2])
            print "  - showing channel 1 as red, channel 2 as green, channel 3 as blue"
        else:
            print "only 1,2 or 3 channels supported so far"
            return
        print
        
        layer1.name = "Input data"
        layer1.ref_object = None
        self.layerstack.append(layer1)
 
        self.workflow = PixelClassificationLazyflow( self.g, self.featScalesList, self.inputProvider.outputs["Output"])

        self.initLabels()
        self.startClassification()
        self.dataReadyToView.emit()
        
    def initLabels(self):
        #Add the layer to draw the labels, but don't add any labels
        self.labelsrc = LazyflowSinkSource(self.workflow.labels, self.workflow.labels.outputs["Output"], self.workflow.labels.inputs["Input"])
        self.labelsrc.setObjectName("labels")
        
        transparent = QColor(0,0,0,0)
        self.labellayer = ColortableLayer(self.labelsrc, colorTable = [transparent.rgba()] )
        self.labellayer.name = "Labels"
        self.labellayer.ref_object = None
        self.layerstack.append(self.labellayer)    
    
    def initEditor(self):
        shape=self.inputProvider.outputs["Output"].shape
        
        self.editor = VolumeEditor(self.layerstack, labelsink=self.labelsrc)

        self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        #drawing will be enabled when the first label is added  
        self.editor.setInteractionMode( 'navigation' )
        self.volumeEditorWidget.init(self.editor)
        model = self.editor.layerStack
        self.layerWidget.init(model)
        self.UpButton.clicked.connect(model.moveSelectedUp)
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        self.DeleteButton.clicked.connect(model.deleteSelected)
        model.canDeleteSelected.connect(self.DeleteButton.setEnabled)     
        
        self.workflow.labels.inputs["eraser"].setValue(self.editor.brushingModel.erasingNumber)      
        
        #finally, setup the editor to have the correct shape
        #doing this last ensures that all connections are setup already
        self.editor.dataShape = shape
    
    def _createDefault16ColorColorTable(self):
        c = []
        c.append(QColor(0, 0, 255))
        c.append(QColor(255, 255, 0))
        c.append(QColor(255, 0, 0))
        c.append(QColor(0, 255, 0))
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
        c.append(QColor(69, 69, 69))    # dark grey
        return c
    
    
    def onFeatureButtonClicked(self):
        self.featureDlg.show()
    
    def _onFeaturesChosen(self):
        selectedFeatures = self.featureDlg.featureTableWidget.createSelectedFeaturesBoolMatrix()
        print "new feature set:", selectedFeatures
        self.workflow.features.inputs['Matrix'].setValue(numpy.asarray(selectedFeatures))
    
    def _initFeatureDlg(self):
        dlg = self.featureDlg = FeatureDlg()
        
        dlg.setWindowTitle("Features")
        dlg.createFeatureTable({"Features": [FeatureEntry("Gaussian smoothing"), \
                                             FeatureEntry("Laplacian of Gaussian"), \
                                             FeatureEntry("Structure Tensor Eigenvalues"), \
                                             FeatureEntry("Hessian of Gaussian EV"),  \
                                             FeatureEntry("Gaussian Gradient Magnitude"), \
                                             FeatureEntry("Difference Of Gaussian")]}, \
                               self.featScalesList)
        dlg.setImageToPreView(None)
        m = [[1,0,0,0,0,0,0],[1,0,0,0,0,0,0],[0,0,0,0,0,0,0],[1,0,0,0,0,0,0],[1,0,0,0,0,0,0],[1,0,0,0,0,0,0]]
        dlg.featureTableWidget.setSelectedFeatureBoolMatrix(m)
        dlg.accepted.connect(self._onFeaturesChosen)
    
app = QApplication(sys.argv)        
t = Main(sys.argv)
t.show()

app.exec_()
        
        
        

