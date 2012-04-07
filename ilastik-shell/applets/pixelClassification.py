from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

import os, sys, numpy, copy

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *

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
from labelListView import Label
from labelListModel import LabelListModel

from featureTableWidget import FeatureEntry
from featureDlg import FeatureDlg

from ilastikshell.applet import Applet

import vigra

class PixelClassificationGui(QMainWindow):        
    def __init__(self, pipeline = None, graph = None ):
        QMainWindow.__init__(self)
        
        self.pipeline = pipeline
        
        #Normalize the data if true
        self._normalize_data=True
        
        if 'notnormalize' in sys.argv:
            print sys.argv
            self._normalize_data=False
            sys.argv.remove('notnormalize')

        self._colorTable16 = self._createDefault16ColorColorTable()
        
        self.g = graph if graph else Graph()
        self.fixableOperators = []
        
        self.featureDlg=None
        
        self.pipeline.inputDataChangedSignal.connect(self.handleGraphInputChanged)

        
        #The old ilastik provided the following scale names:
        #['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        #The corresponding scales are:
        self.featScalesList=[0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        
        self.initCentralUic()
        self.initAppletBarUic()
        
        #if the filename was specified on command line, load it
        def loadFile():
            self._openFile(sys.argv[1:])
        if len(sys.argv) > 1:
            QTimer.singleShot(0, loadFile)
        
    def setIconToViewMenu(self):
            self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))
        
    def initCentralUic(self):
        # We don't know where the user is running this script from,
        #  so locate the .ui file relative to this .py file's path
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        uic.loadUi(p+"/classificationWorkflow.ui", self) 
        #connect the window and graph creation to the opening of the file
        self.actionOpenFile.triggered.connect(self.openFile)
        self.actionOpenStack.triggered.connect(self.openImageStack)
        
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
                
        self.layerstack = LayerStackModel()
                            
        self.interactionComboBox.currentIndexChanged.connect(self.changeInteractionMode)
        self.interactionComboBox.setEnabled(False)

        self._initFeatureDlg()
        
    def getAppletBarUi(self):
        return self._appletBarUi
    
    def initAppletBarUic(self):
        # We don't know where the user is running this script from,
        #  so locate the .ui file relative to this .py file's path
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        _appletBarUi = uic.loadUi(p+"/pixelClassificationAppletBar.ui") # Don't pass self: applet ui is separate from the main ui

        # We own the applet bar ui
        self._appletBarUi = _appletBarUi

        # Initialize the label list model
        model = LabelListModel()
        _appletBarUi.labelListView.setModel(model)
        _appletBarUi.labelListModel=model
        _appletBarUi.labelListModel.rowsAboutToBeRemoved.connect(self.onLabelAboutToBeRemoved)
        _appletBarUi.labelListModel.labelSelected.connect(self.switchLabel)
        
        def onDataChanged(topLeft, bottomRight):
            """Handle changes to the label list selections."""
            firstRow = topLeft.row()
            lastRow  = bottomRight.row()
        
            firstCol = topLeft.column()
            lastCol  = bottomRight.column()
            
            if lastCol == firstCol == 0:
                assert(firstRow == lastRow) #only one data item changes at a time

                #in this case, the actual data (for example color) has changed
                self.switchColor(firstRow+1, _appletBarUi.labelListModel[firstRow].color)
                self.editor.scheduleSlicesRedraw()
            else:
                #this column is used for the 'delete' buttons, we don't care
                #about data changed here
                pass

        # Connect Applet GUI to our event handlers
        _appletBarUi.AddLabelButton.clicked.connect(self.addLabel)
        _appletBarUi.checkInteractive.setEnabled(False)
        _appletBarUi.checkInteractive.toggled.connect(self.toggleInteractive)
        _appletBarUi.labelListModel.dataChanged.connect(onDataChanged)
        _appletBarUi.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)

        
    def toggleInteractive(self, checked):
        print "toggling interactive mode to '%r'" % checked
        
        #Check if the number of labels in the layer stack is equals to the number of Painted labels
        if checked==True:
            labels =numpy.unique(numpy.asarray(self.pipeline.labels.outputs["nonzeroValues"][:].allocate().wait()[0]))           
            nPaintedLabels=labels.shape[0]
            nLabelsLayers = self._appletBarUi.labelListModel.rowCount()
            selectedFeatures = numpy.asarray(self.featureDlg.featureTableWidget.createSelectedFeaturesBoolMatrix())
            
            if nPaintedLabels!=nLabelsLayers:
                self._appletBarUi.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("Did you forget to paint some labels?")
                mexBox.setInformativeText("Painted Labels %d \nNumber Active Labels Layers %d"%(nPaintedLabels,self._appletBarUi.labelListModel.rowCount()))
                mexBox.exec_()
                return
            if (selectedFeatures==0).all():
                self._appletBarUi.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("The are no features selected ")
                mexBox.exec_()
                return
        else:
            self.g.stopGraph()
            self.g.resumeGraph()
                
        self._appletBarUi.AddLabelButton.setEnabled(not checked)
        self._appletBarUi.SelectFeaturesButton.setEnabled(not checked)
        for o in self.fixableOperators:
            o.inputs["fixAtCurrent"].setValue(not checked)
        self._appletBarUi.labelListModel.allowRemove(not checked)
        
        self.editor.scheduleSlicesRedraw()

    def changeInteractionMode( self, index ):
        modes = {0: "navigation", 1: "brushing"}
        self.editor.setInteractionMode( modes[index] )
        self.interactionComboBox.setCurrentIndex(index)
        print "interaction mode switched to", modes[index]

    def switchLabel(self, row):
        print "switching to label=%r" % (self._appletBarUi.labelListModel[row])
        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        self.editor.brushingModel.setBrushColor(self._appletBarUi.labelListModel[row].color)
        
    def switchColor(self, row, color):
        print "label=%d changes color to %r" % (row, color)
        self.labellayer.colorTable[row]=color.rgba()
        self.editor.brushingModel.setBrushColor(color)
        self.editor.scheduleSlicesRedraw()
    
    def addLabel(self):
        color = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
        numLabels = len(self._appletBarUi.labelListModel)
        if numLabels < len(self._colorTable16):
            color = self._colorTable16[numLabels]
        self.labellayer.colorTable.append(color.rgba())
        
        self._appletBarUi.labelListModel.insertRow(self._appletBarUi.labelListModel.rowCount(), Label("Label %d" % (self._appletBarUi.labelListModel.rowCount() + 1), color))
        nlabels = self._appletBarUi.labelListModel.rowCount()
        if self.pipeline is not None:
            print "Label added, changing predictions"
            #re-train the forest now that we have more labels
            self.pipeline.predict.inputs['LabelsCount'].setValue(nlabels)
            self.addPredictionLayer(nlabels-1, self._appletBarUi.labelListModel._labels[nlabels-1])
        
        #make the new label selected
        index = self._appletBarUi.labelListModel.index(nlabels-1, 1)
        self._appletBarUi.labelListModel._selectionModel.select(index, QItemSelectionModel.ClearAndSelect)
        
        #FIXME: this should watch for model changes   
        #drawing will be enabled when the first label is added  
        self.changeInteractionMode( 1 )
        self.interactionComboBox.setEnabled(True)
    
    def onLabelAboutToBeRemoved(self, parent, start, end):
        #the user deleted a label, reshape prediction and remove the layer
        #the interface only allows to remove one label at a time?
        
        nout = start-end+1
        ncurrent = self._appletBarUi.labelListModel.rowCount()
        print "removing", nout, "out of ", ncurrent
        
        if self.pipeline is not None:
            self.pipeline.predict.inputs['LabelsCount'].setValue(ncurrent-nout)
        for il in range(start, end+1):
            labelvalue = self._appletBarUi.labelListModel._labels[il]
            self.removePredictionLayer(labelvalue)
            self.pipeline.labels.inputs["deleteLabel"].setValue(il+1)
            self.editor.scheduleSlicesRedraw()
            
    def startClassification(self):
        nclasses = self._appletBarUi.labelListModel.rowCount()
        self.pipeline.predict.inputs['LabelsCount'].setValue(nclasses)

        #add prediction results for all classes as separate channels
        for icl in range(nclasses):
            self.addPredictionLayer(icl, self._appletBarUi.labelListModel._labels[icl])
        self._appletBarUi.checkInteractive.setEnabled(True)
                                    
    def addPredictionLayer(self, icl, ref_label):
        
        selector=OpSingleChannelSelector(self.g)
        selector.inputs["Input"].connect(self.pipeline.prediction_cache.outputs['Output'])
        selector.inputs["Index"].setValue(icl)
                
        self.pipeline.prediction_cache.inputs["fixAtCurrent"].setValue(not self._appletBarUi.checkInteractive.isChecked())
        
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
        self.fixableOperators.append(self.pipeline.prediction_cache)
               
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
        fileNames = QFileDialog.getOpenFileNames(self, "Open Image", os.path.abspath(__file__), "Numpy and h5 files (*.npy *.h5)")
        if fileNames.count() == 0:
            return
        self._openFile(fileNames)
    
    def _stackLoad(self):
        inputProvider = OpArrayPiper(self.g)
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
        inputProvider.inputs["Input"].setValue(self.raw)
        self.pipeline.setInputData(inputProvider)
        self.stackLoader.close()
            
    def _openFile(self, fileNames):
        """Open the given image file(s) and load them into our pipeline."""
        inputProvider = None
        fName, fExt = os.path.splitext(str(fileNames[0]))
        print "Opening Files %r" % fileNames
        if fExt=='.npy':
            inputProvider = self.createArrayPiperFromNpyFile(fileNames)
        elif fExt=='.h5':
            inputProvider = createArrayPiperFromHdf5File(fileNames)
        else:
            raise RuntimeError("opening filenames=%r not supported yet" % fileNames)

        self.pipeline.setInputData(inputProvider)
    
    def createArrayPiperFromNpyFile(self, fileNames):
        """Open given .npy file(s) and produce an array piper operator with the data."""
        fileName = fileNames[0]
        if len(fileNames)>1:
            print "WARNING: only the first file will be read, multiple file prediction not supported yet"
        fName, fExt = os.path.splitext(str(fileName))
        self.raw = numpy.load(str(fileName))
        self.min, self.max = numpy.min(self.raw), numpy.max(self.raw)
        inputProvider = OpArrayPiper(self.g)
        self.raw = self.raw.view(vigra.VigraArray)
        self.raw.axistags =  vigra.AxisTags(
            vigra.AxisInfo('t',vigra.AxisType.Time),
            vigra.AxisInfo('x',vigra.AxisType.Space),
            vigra.AxisInfo('y',vigra.AxisType.Space),
            vigra.AxisInfo('z',vigra.AxisType.Space),
            vigra.AxisInfo('c',vigra.AxisType.Channels))
        inputProvider.inputs["Input"].setValue(self.raw)
        
        return inputProvider

    def createArrayPiperFromHdf5File(self, fileNames):
        """Open given .h5 file(s) and produce an array piper operator with the data."""
        readerNew=OpH5ReaderBigDataset(self.g)
        
        readerNew.inputs["Filenames"].setValue(fileNames)
        readerNew.inputs["hdf5Path"].setValue("volume/data")

        readerCache =  OpSlicedBlockedArrayCache(self.g)
        readerCache.inputs["fixAtCurrent"].setValue(False)
        readerCache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        readerCache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        readerCache.inputs["Input"].connect(readerNew.outputs["Output"])

        inputProvider = OpArrayPiper(self.g)
        inputProvider.inputs["Input"].connect(readerCache.outputs["Output"])
        return inputProvider
    
    def handleGraphInputChanged(self, newInputProvider):
        """Update our view of the data with the new dataset, as provided in the newInputProvider operator.""" 
        shape = newInputProvider.outputs["Output"].shape
        srcs    = []
        minMax = []
        
        print "* Data has shape=%r" % (shape,)
        
        #create a layer for each channel of the input:
        slicer=OpMultiArraySlicer2(self.g)
        slicer.inputs["Input"].connect(newInputProvider.outputs["Output"])
        
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
 
        self.initLabels()
        self.startClassification()
        self.initEditor(newInputProvider)
        
    def initLabels(self):
        #Add the layer to draw the labels, but don't add any labels
        self.labelsrc = LazyflowSinkSource(self.pipeline.labels, self.pipeline.labels.outputs["Output"], self.pipeline.labels.inputs["Input"])
        self.labelsrc.setObjectName("labels")
        
        transparent = QColor(0,0,0,0)
        self.labellayer = ColortableLayer(self.labelsrc, colorTable = [transparent.rgba()] )
        self.labellayer.name = "Labels"
        self.labellayer.ref_object = None
        self.layerstack.append(self.labellayer)    
    
    def initEditor(self, newInputProvider):
        shape = newInputProvider.outputs["Output"].shape
        
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
        
        self.pipeline.labels.inputs["eraser"].setValue(self.editor.brushingModel.erasingNumber)      
        
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
        # Refresh the feature matrix in case it has changed since the last time we were opened
        # (e.g. if the user loaded a project from disk)
        pipelineFeatures = self.pipeline.features.inputs['Matrix'].value
        if pipelineFeatures is not None:
            self.featureDlg.selectedFeatureBoolMatrix = pipelineFeatures
        
        # Now open the feature selection dialog
        self.featureDlg.show()
    
    def _onNewFeaturesFromFeatureDlg(self):
        selectedFeatures = self.featureDlg.getSelectedFeatureMatrix()
        print "new feature set:", selectedFeatures
        self.pipeline.features.inputs['Matrix'].setValue(numpy.asarray(selectedFeatures))
    
    def _initFeatureDlg(self):
        self.featureDlg = FeatureDlg()
        
        self.featureDlg.setWindowTitle("Features")
        self.featureDlg.createFeatureTable({"Features":
                                                [FeatureEntry("Gaussian smoothing"), \
                                                 FeatureEntry("Laplacian of Gaussian"), \
                                                 FeatureEntry("Structure Tensor Eigenvalues"), \
                                                 FeatureEntry("Hessian of Gaussian EV"),  \
                                                 FeatureEntry("Gaussian Gradient Magnitude"), \
                                                 FeatureEntry("Difference Of Gaussian")]}, \
                                           self.featScalesList)
        self.featureDlg.setImageToPreView(None)
        m = [[1,0,0,0,0,0,0],[1,0,0,0,0,0,0],[0,0,0,0,0,0,0],[1,0,0,0,0,0,0],[1,0,0,0,0,0,0],[1,0,0,0,0,0,0]]
        self.featureDlg.selectedFeatureBoolMatrix = numpy.asarray(m)
        self.featureDlg.accepted.connect(self._onNewFeaturesFromFeatureDlg)


class PixelClassificationPipeline( QObject ):
    """Represents the pipeline of pixel classification operations.  
       Inherits from QObject because it provides signals."""

    inputDataChangedSignal = pyqtSignal(object)
    
    def __init__( self, graph ):
        QObject.__init__(self)
        #The old ilastik provided the following scale names:
        #['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        #The corresponding scales are:
        feature_scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]

        ##
        # IO
        ##
        self.images = Op5ToMulti( graph )
        self.features = OpPixelFeaturesPresmoothed( graph )
        self.features_cache = OpBlockedArrayCache( graph )
        self.labels = OpBlockedSparseLabelArray( graph )                                

        self.features.inputs["Input"].connect(self.images.outputs["Outputs"])
        self.features.inputs["Scales"].setValue( feature_scales )        

        self.features_cache.inputs["Input"].connect(self.features.outputs["Output"])
        self.features_cache.inputs["innerBlockShape"].setValue((1,32,32,32,16))
        self.features_cache.inputs["outerBlockShape"].setValue((1,128,128,128,64))
        self.features_cache.inputs["fixAtCurrent"].setValue(False)  
    
        self.labels.inputs["blockShape"].setValue((1, 32, 32, 32, 1))
        self.labels.inputs["eraser"].setValue(100)    

        ##
        ## Entry point to the pipeline: 
        ## self.images.inputs["Input0"].connect(array_like_input)
        ## shape = array_like_input.meta.shape
        ## self.labels.inputs["shape"].setValue(shape[:-1] + (1,))
        ##


        
        ##
        # training
        ##
        opMultiL = Op5ToMulti( graph )    
        opMultiL.inputs["Input0"].connect(self.labels.outputs["Output"])

        opMultiLblocks = Op5ToMulti( graph )
        opMultiLblocks.inputs["Input0"].connect(self.labels.outputs["nonzeroBlocks"])
        train = OpTrainRandomForestBlocked( graph )
        train.inputs['Labels'].connect(opMultiL.outputs["Outputs"])
        train.inputs['Images'].connect(self.features_cache.outputs["Output"])
        train.inputs["nonzeroLabelBlocks"].connect(opMultiLblocks.outputs["Outputs"])
        train.inputs['fixClassifier'].setValue(False)                

        self.classifier_cache = OpArrayCache( graph )
        self.classifier_cache.inputs["Input"].connect(train.outputs['Classifier'])


        ##
        # prediction
        ##
        self.predict=OpPredictRandomForest( graph )
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.features.outputs["Output"])

        pCache = OpSlicedBlockedArrayCache( graph )
        pCache.inputs["fixAtCurrent"].setValue(False)
        pCache.inputs["innerBlockShape"].setValue(((1,256,256,1,2),(1,256,1,256,2),(1,1,256,256,2)))
        pCache.inputs["outerBlockShape"].setValue(((1,256,256,4,2),(1,256,4,256,2),(1,4,256,256,2)))
        pCache.inputs["Input"].connect(self.predict.outputs["PMaps"])
        self.prediction_cache = pCache

    def setInputData(self, inputProvider):
        """Set the pipeline input data, which is given as an operator in inputProvider."""
        shape = inputProvider.Output.meta.shape
        self.labels.shape.setValue(shape[:-1] + (1,))
        self.images.inputs["Input0"].connect(inputProvider.outputs["Output"])
        
        # Notify the GUI that our input data changed
        self.inputDataChangedSignal.emit(inputProvider)
    
class PixelClassificationSerializer(object):
    """ Encapsulate the serialization scheme for pixel classification workflow parameters and datasets."""
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def serializeToHdf5(self, hdf5Group):
        pass
    
    def deserializeFromHdf5(self, hdf5Group):
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5Group["ilastikVersion"].value

        # TODO: Fix this when the version number scheme is more thought out
        if ilastikVersion != 0.6:
            # This class is for 0.6 projects only.
            # v0.5 projects are handled in a different serializer (below).
            return

    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk. """
        return True

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass

class Ilastik05ImportDeserializer(object):
    """Special (de)serializer for importing ilastik 0.5 projects.
       For now, this class is import-only.  Only the deserialize function is implemented.
       If the project is not an ilastik0.5 project, this serializer does nothing."""
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def serializeToHdf5(self, hdf5Group):
        """Not implemented. (See above.)"""
        pass
    
    def deserializeFromHdf5(self, hdf5File):
        """If (and only if) the given hdf5Group is the root-level group of an 
           ilastik 0.5 project, then the project is imported.  The pipeline is updated 
           with the saved parameters and datasets."""
        # The group we were given is the root (file).
        # Check the version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # The pixel classification workflow supports importing projects in the old 0.5 format
        if ilastikVersion == 0.5:
            print "Deserializing ilastik 0.5 project..."
            self.importProjectAttributes(hdf5File) # (e.g. description, labeler, etc.)
            self.importFeatureSelections(hdf5File)
            self.importClassifier(hdf5File)
            self.importDataSets(hdf5File)
            self.importLabelSets(hdf5File)
    
    def importProjectAttributes(self, hdf5File):
        description = hdf5File["Project"]["Description"].value
        labeler = hdf5File["Project"]["Labeler"].value
        name = hdf5File["Project"]["Name"].value
        # TODO: Actually store these values and show them in the GUI somewhere . . .
        
    def importFeatureSelections(self, hdf5File):
        """Import the feature selections from the v0.5 project file"""
        # Create a feature selection matrix of the correct shape (all false by default)
        # TODO: The shape shouldn't be hard-coded.
        pipeLineSelectedFeatureMatrix = numpy.array(numpy.zeros((6,7)), dtype=bool)

        try:
            # In ilastik 0.5, features were grouped into user-friendly selections.  We have to split these 
            #  selections apart again into the actual features that must be computed.
            userFriendlyFeatureMatrix = hdf5File['Project']['FeatureSelection']['UserSelection'].value
        except KeyError:
            # If the project file doesn't specify feature selections,
            #  we'll just use the default (blank) selections as initialized above
            pass
        else:            
            assert( userFriendlyFeatureMatrix.shape == (4, 7) )
            # Here's how features map to the old "feature groups"
            # (Note: Nothing maps to the orientation group.)
            # TODO: It is terrible that these indexes are hard-coded.
            featureToGroup = { 0 : 0,  # Gaussian Smoothing -> Color
                               1 : 1,  # Laplacian of Gaussian -> Edge
                               2 : 3,  # Structure Tensor Eigenvalues -> Texture
                               3 : 3,  # Eigenvalues of Hessian of Gaussian -> Texture
                               4 : 1,  # Gradient Magnitude of Gaussian -> Edge
                               5 : 1 } # Difference of Gaussians -> Edge

            # For each feature, determine which group's settings to take
            for featureIndex, featureGroupIndex in featureToGroup.items():
                # Copy the whole row of selections from the feature group
                pipeLineSelectedFeatureMatrix[featureIndex] = userFriendlyFeatureMatrix[featureGroupIndex]
        
        # Finally, update the pipeline with the feature selections
        self.pipeline.features.inputs['Matrix'].setValue(pipeLineSelectedFeatureMatrix)
        
    def importClassifier(self, hdf5File):
        """Import the random forest classifier (if any) from the v0.5 project file."""
        # ilastik 0.5 can SAVE the RF, but it can't load it back (vigra doesn't provide a function for that).
        # For now, we simply emulate that behavior.
        # (Technically, v0.5 would retrieve the user's "number of trees" setting, 
        #  but this applet doesn't expose that setting to the user anyway.)
        pass
        
    def importDataSets(self, hdf5File):
        # _openHdf5Data
        pass
    
    def importLabelSets(self, hdf5File):
        pass
    
    def isDirty(self):
        """Always returns False because we don't support saving to ilastik0.5 projects"""
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        pass

class PixelClassificationApplet( Applet ):
    def __init__( self, pipeline = None, graph = None ):
        # (No need to call the base class constructor here.)
        # Applet.__init__( self, "Pixel Classification" )

        self.name = "Pixel Classification"
        self.graph = graph if graph else Graph()
        self.pipeline = pipeline if pipeline else PixelClassificationPipeline( self.graph )

        self._centralWidget = PixelClassificationGui( self.pipeline, self.graph )

        # To save some typing, the menu bar is defined in the .ui file 
        #  along with the rest of the central widget.
        # However, we must expose it here as an applet property since we 
        #  want it to show up properly in the shell
        self._menuWidget = self._centralWidget.menuBar
        
        # For now, the central widget owns the applet bar gui
        self._controlWidget = self._centralWidget.getAppletBarUi()
        
        self._serializableItems = [
                                    PixelClassificationSerializer(self.pipeline), # Default serializer for new projects
                                    Ilastik05ImportDeserializer(self.pipeline)    # Legacy (v0.5) importer
                                  ]

if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    pca = PixelClassificationApplet()
    pca.centralWidget.show()
    pca.controlWidget.show()
    app.exec_()
