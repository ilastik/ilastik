from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.adaptors import Op5ifyer
from volumina.api import ArraySource, LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource

from igms.labelListModel import LabelListModel, Label

from lazyflow.operators import OpSingleChannelSelector

from opFeatureSelection import OpFeatureSelection

from igms.featureTableWidget import FeatureEntry
from igms.featureDlg import FeatureDlg

from functools import partial
import os
import utility # This is the ilastik shell utility module
import numpy
from utility import bind

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from lazyflow.tracer import Tracer

class FeatureSelectionGui(QMainWindow):
    """
    Manages all GUI elements in the feature selection applet.
    This class itself is the central widget and also owns/manages the applet drawer widgets.
    """

    # Constants    
    ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
    DefaultColorTable = None

    FeatureIds = [ 'GaussianSmoothing',
                   'LaplacianOfGaussian',
                   'StructureTensorEigenvalues',
                   'HessianOfGaussianEigenvalues',
                   'GaussianGradientMagnitude',
                   'DifferenceOfGaussians' ]

    # Note: The order of these feature names must match the order of the feature Ids above
    FeatureNames = [ "G-smooth",
                     "L-of-G",
                     "ST EVs",
                     "H-of-G EVs",
                     "G. Grad Mag",
                     "Diff of G." ]

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawers(self):
        return [ ("Feature Selection", self.drawer) ]

    def menuWidget( self ):
        return self.menuBar

    def viewerControlWidget(self):
        return self._viewerControlWidget

    def setImageIndex(self, index):
        with Tracer(traceLogger):
            self.currentImageIndex = index
            if self.mainOperator.configured():
                self.updateAllLayers()
            else:
                self.layerstack.clear()

    ###########################################
    ###########################################

    def __init__(self, mainOperator):
        with Tracer(traceLogger):
            super(FeatureSelectionGui, self).__init__()
    
            # Constants
            FeatureSelectionGui.DefaultColorTable = self.createDefault16ColorColorTable()
    
            self.menuBar = QMenuBar()
            
            self.drawer = None
            self.initAppletDrawerUic()
            self.initCentralUic()
            self.initViewerControlUi()
            self.initFeatureDlg()
            
            self.editor = None
            self.currentImageIndex = -1
            self.layerstack = LayerStackModel()
            self.initEditor()
            
            self.mainOperator = mainOperator
            self.mainOperator.SelectionMatrix.notifyConnect( bind(self.onFeaturesSelectionsChanged) )
            
            def handleOutputInsertion(slot, index):
                slot[index].notifyDirty( bind(self.updateAllLayers) )
    
            self.mainOperator.CachedOutputImage.notifyInserted( bind(handleOutputInsertion) )

    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        with Tracer(traceLogger):
            localDir = os.path.split(__file__)[0]
            # (We don't pass self here because we keep the drawer ui in a separate object.)
            self.drawer = uic.loadUi(localDir+"/featureSelectionDrawer.ui")
            self.drawer.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
    
            def enableDrawerControls(enabled):
                """
                Enable or disable all of the controls in this applet's drawer widget.
                """
                # All the controls in our GUI
                controlList = [ self.drawer.SelectFeaturesButton ]
        
                # Enable/disable all of them
                for control in controlList:
                    control.setEnabled(enabled)
    
            # Expose the enable function with the name the shell expects
            self.drawer.enableControls = enableDrawerControls
    
    def initViewerControlUi(self):
        with Tracer(traceLogger):
            p = os.path.split(__file__)[0]+'/'
            if p == "/": p = "."+p
            self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        with Tracer(traceLogger):
            # Load the ui file into this class (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            uic.loadUi(localDir+"/centralWidget.ui", self)
                
            def toggleDebugPatches(show):
                self.editor.showDebugPatches = show
            def fitToScreen():
                shape = self.editor.posModel.shape
                for i, v in enumerate(self.editor.imageViews):
                    s = list(shape)
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
                hide = not self.editor.imageViews[0]._hud.isVisible()
                for i, v in enumerate(self.editor.imageViews):
                    v.setHudVisible(hide)
                    
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
                
    def initFeatureDlg(self):
        """
        Initialize the feature selection widget.
        """
        with Tracer(traceLogger):
            self.featureDlg = FeatureDlg()
            self.featureDlg.setWindowTitle("Features")
            self.featureDlg.createFeatureTable( { "Features": [ FeatureEntry(s) for s in self.FeatureNames ] },
                                                self.ScalesList)
            self.featureDlg.setImageToPreView(None)
    
            # Create a matrix of False values
            defaultFeatures = numpy.zeros((6,7), dtype=bool)
    
            # Select some default features.
            defaultFeatures[0,0] = True
            defaultFeatures[1,0] = True
            defaultFeatures[3,0] = True
            defaultFeatures[4,0] = True
            defaultFeatures[5,0] = True
    
            self.featureDlg.selectedFeatureBoolMatrix = defaultFeatures
            self.featureDlg.accepted.connect(self.onNewFeaturesFromFeatureDlg)

    def onFeatureButtonClicked(self):
        with Tracer(traceLogger):
            # Refresh the feature matrix in case it has changed since the last time we were opened
            # (e.g. if the user loaded a project from disk)
            if self.mainOperator.SelectionMatrix.configured():
                self.featureDlg.selectedFeatureBoolMatrix = self.mainOperator.SelectionMatrix.value
            
            # Now open the feature selection dialog
            self.featureDlg.show()

    def onNewFeaturesFromFeatureDlg(self):
        with Tracer(traceLogger):
            # Re-initialize the scales and features
            self.mainOperator.Scales.setValue( self.ScalesList )
            self.mainOperator.FeatureIds.setValue(self.FeatureIds)
    
            # Give the new features to the pipeline 
            featureMatrix = numpy.asarray(self.featureDlg.selectedFeatureBoolMatrix)
            self.mainOperator.SelectionMatrix.setValue( featureMatrix )
    
    def onFeaturesSelectionsChanged(self):
        """
        Handles changes to our top-level operator's matrix of feature selections.
        """
        with Tracer(traceLogger):
            # Update the drawer caption
            if not self.mainOperator.SelectionMatrix.configured():
                self.drawer.caption.setText( "(No features selected)" )
                self.layerstack.clear()
            else:
                self.drawer.caption.setText( "(Selected %d features)" % numpy.sum(self.mainOperator.SelectionMatrix.value) )

    def initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """
        with Tracer(traceLogger):
            self.editor = VolumeEditor(self.layerstack)
    
            self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
            self.editor.setInteractionMode( 'navigation' )
            self.volumeEditorWidget.init(self.editor)
            
            # The editor's layerstack is in charge of which layer movement buttons are enabled
            model = self.editor.layerStack
            model.canMoveSelectedUp.connect(self._viewerControlWidget.UpButton.setEnabled)
            model.canMoveSelectedDown.connect(self._viewerControlWidget.DownButton.setEnabled)
            model.canDeleteSelected.connect(self._viewerControlWidget.DeleteButton.setEnabled)     
    
            # Connect our layer movement buttons to the appropriate layerstack actions
            self._viewerControlWidget.layerWidget.init(model)
            self._viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
            self._viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
            self._viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)
            
            # No brushing model necessary (we're using the editor as a viewer only)
            #self.pipeline.labels.inputs["eraser"].setValue(self.editor.brushingModel.erasingNumber)
        
    def setIconToViewMenu(self):
        """
        In the "Only for Current View" menu item of the View menu, 
        show the user which axis is the current one by changing the menu item icon.
        """
        with Tracer(traceLogger):
            self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))

    def updateAllLayers(self):
        with Tracer(traceLogger):
            # Start by removing all layers
            # TODO: We can do better than this.  We should try to determine if some feature layers can be kept.
            numRows = len(self.layerstack)
            self.layerstack.removeRows(0, numRows)
    
            # Give the editor the appropriate shape (transposed via an Op5ifyer adapter).
            op5 = Op5ifyer( graph=self.mainOperator.graph )
            op5.input.connect( self.mainOperator.InputImage[self.currentImageIndex] )
            self.editor.dataShape = op5.output.meta.shape
            
            # Zoom at a 1-1 scale to avoid loading big datasets entirely...
            for view in self.editor.imageViews:
                view.doScaleTo(1)
            
            # We just needed the operator to determine the transposed shape.
            # Disconnect it so it can be deleted.
            op5.input.disconnect()
            
            # First add a black layer on the bottom of the image
            # TODO: Optimize: Replace this ArraySource with a special operator that always returns zero
    #        singleChannelShape = shape[:-1] + (1,)
    #        blackSource = ArraySource( numpy.zeros(singleChannelShape, dtype=numpy.float32) )
    #        blackLayer = GrayscaleLayer(blackSource)
    #        blackLayer.name = "Black background"
    #        self.layerstack.insert(0, blackLayer)
    
            # Now add a layer for each feature
            # TODO: This assumes the channel is the last axis 
            numFeatureChannels = self.mainOperator.CachedOutputImage[self.currentImageIndex].meta.shape[-1]
            for featureChannelIndex in range(0, numFeatureChannels):
                if featureChannelIndex < len(self.DefaultColorTable):
                    # Choose the next color from our default color table
                    color = self.DefaultColorTable[featureChannelIndex]
                else:
                    # Choose a random color
                    color = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
                
                label = Label( str(featureChannelIndex), color )
                self.addFeatureLayer(featureChannelIndex, label)

    def addFeatureLayer(self, featureChannelIndex, ref_label):
        """
        Display a feature in the layer editor.
        """
        with Tracer(traceLogger):
            # Create an operator to select the channel (feature) we're interested in
            selector=OpSingleChannelSelector(self.mainOperator.graph)
            selector.Input.connect(self.mainOperator.CachedOutputImage[self.currentImageIndex])
            selector.Index.setValue(featureChannelIndex)
            
            # Determine the name for this feature
            channelAxis = self.mainOperator.InputImage[self.currentImageIndex].meta.axistags.channelIndex
            numOriginalChannels = self.mainOperator.InputImage[self.currentImageIndex].meta.shape[channelAxis]
            originalChannel = featureChannelIndex % numOriginalChannels
            featureNameIndex = featureChannelIndex / numOriginalChannels
            channelNames = ['R', 'G', 'B']
            featureName = self.mainOperator.FeatureNames[self.currentImageIndex].value[ featureNameIndex ]
            if numOriginalChannels > 1:
                featureName += " (" + channelNames[originalChannel] + ")"
            
            featureSource = LazyflowSource(selector.Output)
            featureSource.setObjectName(featureName)
    #        featureLayer = AlphaModulatedLayer(featureSource, tintColor=ref_label.color, normalize = None )
            featureLayer = GrayscaleLayer( featureSource )
            featureLayer.name = featureSource.objectName()
    
            # By default, only the first feature is visible
            featureLayer.opacity = 1.0
            featureLayer.visible = (featureChannelIndex == 0)
            featureLayer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )
            self.layerstack.insert(len(self.layerstack), featureLayer )

    def createDefault16ColorColorTable(self):
        with Tracer(traceLogger):
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

    def enableControls(self, enabled):
        """
        Enable or disable all of the controls in this applet's central widget.
        """
        with Tracer(traceLogger):
            # All the controls in our GUI
            controlList = [ self.menuBar,
                            self.volumeEditorWidget,
                            self._viewerControlWidget.UpButton,
                            self._viewerControlWidget.DownButton,
                            self._viewerControlWidget.DeleteButton ]
    
            # Enable/disable all of them
            for control in controlList:
                control.setEnabled(enabled)































