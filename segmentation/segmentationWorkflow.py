#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os, sys, numpy, copy

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL
from PyQt4.QtGui import QColor, QMainWindow, QApplication, QFileDialog, \
                        QMessageBox, qApp, QItemSelectionModel, QIcon, QTransform
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

import vigra
import random
import colorsys
from segmentation_lazyflow import PixelClassificationLazyflow

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

        self._colorTable16 = self._createDefault16ColorColorTable()
        
        self.g = Graph()
        self.workflow = None
        
        self.featureDlg=None

        self.currentLabel = 1

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
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        uic.loadUi(p+"/classificationWorkflow.ui", self) 
        #connect the window and graph creation to the opening of the file
        self.actionOpenFile.triggered.connect(self.openFile)
        self.actionOpenStack.triggered.connect(self.openImageStack)
        self.actionQuit.triggered.connect(qApp.quit)
        
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
        
        self.btnUncertainBG.clicked.connect(self.goUncertainBG)
        self.btnUncertainFG.clicked.connect(self.goUncertainFG)

        self.checkInteractive.setEnabled(False)
        self.checkInteractive.toggled.connect(self.toggleInteractive)   

        self.btnSegment.clicked.connect(self.doSegment)

        self.interactionComboBox.currentIndexChanged.connect(self.changeInteractionMode)
        self.interactionComboBox.setEnabled(False)

        self.lastSegmentorIndex = 0
        self.lastSegmentorOptions = {}
        self.parameters.setPlainText("{\n \"prioBG\" : 0.97,\n \"moving_average\" : 0 \n}")

        self.comboSegmentor.currentIndexChanged.connect(self.changeSegmentor)

        self._initFeatureDlg()

    def goUncertainFG(self):
      pos = self.workflow.seg.maxUncertainFG()
      if (pos != 0).any():
        pos = [pos[0],pos[1],pos[2]]
        self.editor.posModel.slicingPos = pos
      print "MOST UNCERTAIN FG", pos

    def goUncertainBG(self):
      pos = self.workflow.seg.maxUncertainBG()
      if (pos != 0).any():
        pos = [pos[0],pos[1],pos[2]]
        self.editor.posModel.slicingPos = pos
      print "MOST UNCERTAIN BG", pos

    def changeSegmentor(self,index):
        self.lastSegmentorOptions[self.lastSegmentorIndex] =  str(self.parameters.toPlainText())  
        if index == 0:
          self.workflow.seg.algorithm.setValue("prioMST")
        elif index == 1:
          self.workflow.seg.algorithm.setValue("prioMSTperturb")
        if not self.lastSegmentorOptions.has_key(index):
          self.lastSegmentorOptions[index] = "{\n \"prioBG\" : 0.97,\n \"moving_average\" : 0 \n}"
        self.parameters.setPlainText(self.lastSegmentorOptions[index])
        self.lastSegmentorIndex = index

    def doSegment(self):
        parameters = str(self.parameters.toPlainText())
        self.workflow.seg.parameters.setValue(parameters)

        old = self.workflow.seg.update.value
        if not old:
          self.workflow.seg.update.setValue(True)
        self.workflow.seg.segmentation[0,0,:,:,0].allocate().wait()
        if not old:
          self.workflow.seg.update.setValue(old)

        print "SEGMENTED"
        if self.segLayer is None:
          self.segsrc = LazyflowSource(self.workflow.seg.segmentation)
          self.segsrc.setObjectName("segmentation")
          
          transparent = QColor(0,0,0,0)
          self.segLayer = ColortableLayer(self.segsrc, colorTable = self.labellayer.colorTable )
          self.segLayer.name = "Segmentation"
          self.segLayer.ref_object = None
          self.segLayer.opacity = 0.45
          self.layerstack.append(self.segLayer)    
        if self.uncertLayer is None:
          self.uncertsrc = LazyflowSource(self.workflow.seg.uncertainty)
          self.uncertsrc.setObjectName("uncertainty")
          
          transparent = QColor(0,0,0,0)
          self.uncertLayer = GrayscaleLayer(self.uncertsrc, normalize = [0,255])
          self.uncertLayer.name = "Uncertainty"
          self.uncertLayer.opacity = 0.95
          self.uncertLayer.visible = False
          self.uncertLayer.ref_object = None
          self.layerstack.append(self.uncertLayer)    
        
        self.editor.scheduleSlicesRedraw() 

    def toggleInteractive(self, checked):
        print "toggling interactive mode to '%r'" % checked
        
        #Check if the number of labels in the layer stack is equals to the number of Painted labels
        if checked==True:
          self.workflow.seg.update.setValue(True)
          self.doSegment()
        else:
            self.workflow.seg.update.setValue(False)
            #self.g.stopGraph()
            #self.g.resumeGraph()
                
        self.AddLabelButton.setEnabled(not checked)
        
        self.labelListModel.allowRemove(not checked)
        
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
        self.currentLabel =  row + 1

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
        
        #TODO: remove leabel from segmentor
        self.workflow.seg.deleteSeed[0] = self.currentLabel
        self.labellayer.colorTable.pop(self.currentLabel)
        if self.segLayer:
          self.seglLayer.colorTable = colorTable = self.labellayer.colorTable 
        self.editor.scheduleSlicesRedraw()
            
    def startClassification(self):
        nclasses = self.labelListModel.rowCount()
        self.checkInteractive.setEnabled(True)
                                    
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
        self.workflow = PixelClassificationLazyflow( self.g )
        self.workflow.seg.fileName.setValue(fileNames[0])
        self.workflow.seg.eraser.setValue(100)
        self.workflow.seg.algorithm.setValue("prioMST")
        self.workflow.seg.parameters.setValue("{}")
        self.haveData.emit()
       
    def initGraph(self):
        
        self.initLabels()
        self.startClassification()
        self.dataReadyToView.emit()
        
    def initLabels(self):
        #Add the layer to draw the labels, but don't add any labels
        self.labelsrc = LazyflowSinkSource(self.workflow.seg, self.workflow.seg.seeds, self.workflow.seg.writeSeeds)
        self.labelsrc.setObjectName("seeds")
        self.segLayer = None
        self.uncertLayer = None
        transparent = QColor(0,0,0,0)
        self.labellayer = ColortableLayer(self.labelsrc, colorTable = [transparent.rgba()] )
        self.labellayer.name = "Seeds"
        self.labellayer.ref_object = None
        self.layerstack.append(self.labellayer)    
    
    def initEditor(self):
        shape=self.workflow.seg.raw.meta.shape
        print "OKJASDLKJALKSJL", shape
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
        
        layersrc = LazyflowSource(self.workflow.seg.raw, priority = 100)
        layersrc.setObjectName("raw data" )
        layer1 = GrayscaleLayer(layersrc, normalize = [0,255])
        layer1.name = "Input data"
        layer1.ref_object = None
        self.layerstack.append(layer1)
 

        layersrc = LazyflowSource(self.workflow.seg.regions, priority = 100)
        layersrc.setObjectName("region data" )
        self.regionLayer = ColortableLayer(layersrc, colorTable = self._randomColors() )
        self.regionLayer.name = "Regions"
        self.regionLayer.ref_object = None
        self.layerstack.append(self.regionLayer)          

        #finally, setup the editor to have the correct shape
        #doing this last ensures that all connections are setup already
        self.editor.dataShape = shape
 
    def _randomColors(self, M=256):
        """Generates a pleasing color table with M entries."""

        colors = []
        for i in range(M):
            if i == 0:
                colors.append(QColor(0, 0, 0, 0).rgba())
            else:
                h, s, v = random.random(), random.random(), 1.0
                color = numpy.asarray(colorsys.hsv_to_rgb(h, s, v)) * 255
                qColor = QColor(*color)
                colors.append(qColor.rgba())
        return colors
   
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
        
        
        

