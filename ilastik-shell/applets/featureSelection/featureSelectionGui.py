from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import ArraySource, LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource

import labelListModel
from labelListModel import LabelListModel

from lazyflow.operators import OpSingleChannelSelector

from opFeatureSelection import OpFeatureSelection

from igms.featureTableWidget import FeatureEntry
from igms.featureDlg import FeatureDlg

from functools import partial
import os
import utility # This is the ilastik shell utility module
import numpy

class FeatureSelectionGui(QMainWindow):
    """
    Manages all GUI elements in the data selection applet.
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

    def __init__(self, topLevelOperator):
        super(FeatureSelectionGui, self).__init__()

        # Constants
        FeatureSelectionGui.DefaultColorTable = self.createDefault16ColorColorTable()

        self.mainOperator = topLevelOperator
        self.menuBar = QMenuBar()
        
        self.drawer = None
        self.initAppletDrawerUic()
        self.initCentralUic()
        self.initViewerControlUi()
        self.initFeatureDlg()
        
        self.editor = None
        self.layerstack = LayerStackModel()
        self.initEditor()
        
        self.imageIndex = 0
        
    def initAppletDrawerUic(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/featureSelectionDrawer.ui")
        self.drawer.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)

        # Subscribe to feature selection changes directly from the graph.
        self.mainOperator.SelectionMatrix.notifyConnect( self.onFeaturesSelectionsChanged )
        
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
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self.viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
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

    def setImageIndex(self, imageIndex):
        self.imageIndex = imageIndex
        if self.mainOperator.configured():
            self.handleFeaturesChanged()

    def onFeatureButtonClicked(self):
        # Refresh the feature matrix in case it has changed since the last time we were opened
        # (e.g. if the user loaded a project from disk)
        if self.mainOperator.SelectionMatrix.configured():
            self.featureDlg.selectedFeatureBoolMatrix = self.mainOperator.SelectionMatrix.value
        
        # Now open the feature selection dialog
        self.featureDlg.show()
    
    def onNewFeaturesFromFeatureDlg(self):
        # Re-initialize the scales and features
        self.mainOperator.Scales.setValue( self.ScalesList )
        self.mainOperator.FeatureIds.setValue(self.FeatureIds)

        # Give the new features to the pipeline 
        featureMatrix = numpy.asarray(self.featureDlg.selectedFeatureBoolMatrix)
        self.mainOperator.SelectionMatrix.setValue( featureMatrix )
    
    def onFeaturesSelectionsChanged(self, slot):
        """
        Handles changes to our top-level operator's matrix of feature selections.
        """
        # Update the drawer caption
        self.drawer.caption.setText( "(Selected %d features)" % numpy.sum(self.mainOperator.SelectionMatrix.value) )

    def initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """
        self.editor = VolumeEditor(self.layerstack)

        self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        self.editor.setInteractionMode( 'navigation' )
        self.volumeEditorWidget.init(self.editor)
        
        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        model.canMoveSelectedUp.connect(self.viewerControlWidget.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self.viewerControlWidget.DownButton.setEnabled)
        model.canDeleteSelected.connect(self.viewerControlWidget.DeleteButton.setEnabled)     

        # Connect our layer movement buttons to the appropriate layerstack actions
        self.viewerControlWidget.layerWidget.init(model)
        self.viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
        self.viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
        self.viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)
        
        # No brushing model necessary (we're using the editor as a viewer only)
        #self.pipeline.labels.inputs["eraser"].setValue(self.editor.brushingModel.erasingNumber)

        self.mainOperator.notifyConfigured( self.handleFeaturesChanged )
        
        def handleInputResize(slot, oldsize, newsize):
            if newsize == 0:
                numRows = len(self.layerstack)
                self.layerstack.removeRows(0, numRows)
        self.mainOperator.InputImage.notifyResize(handleInputResize)

    def setIconToViewMenu(self):
        """
        In the "Only for Current View" menu item of the View menu, 
        show the user which axis is the current one by changing the menu item icon.
        """
        self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))

    def handleFeaturesChanged(self):
        # Start by removing all layers
        # TODO: We can do better than this.  We should try to determine if some feature layers can be kept.
        numRows = len(self.layerstack)
        self.layerstack.removeRows(0, numRows)

        # Update the editor data shape
        shape = self.mainOperator.InputImage[self.imageIndex].shape
        self.editor.dataShape = shape
        
        # First add a black layer on the bottom of the image
        # TODO: Optimize: Replace this ArraySource with a special operator that always returns zero
        singleChannelShape = shape[:-1] + (1,)
        blackSource = ArraySource( numpy.zeros(singleChannelShape, dtype=numpy.float32) )
        blackLayer = GrayscaleLayer(blackSource)
        blackLayer.name = "Black background"
        self.layerstack.insert(0, blackLayer)

        # Now add a layer for each feature
        # TODO: This assumes the channel is the last axis 
        numFeatureChannels = self.mainOperator.CachedOutputImage[self.imageIndex].meta.shape[-1]
        for featureChannelIndex in reversed(range(0, numFeatureChannels)):
            if featureChannelIndex < len(self.DefaultColorTable):
                # Choose the next color from our default color table
                color = self.DefaultColorTable[featureChannelIndex]
            else:
                # Choose a random color
                color = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
            
            label = labelListModel.Label( str(featureChannelIndex), color )
            self.addFeatureLayer(featureChannelIndex, label)

    def addFeatureLayer(self, featureChannelIndex, ref_label):
        """
        Display a feature in the layer editor.
        """
        # Create an operator to select the channel (feature) we're interested in
        selector=OpSingleChannelSelector(self.mainOperator.graph)
        selector.Input.connect(self.mainOperator.CachedOutputImage[self.imageIndex])
        selector.Index.setValue(featureChannelIndex)
        
        # Determine the name for this feature
        channelAxis = self.mainOperator.InputImage[self.imageIndex].meta.axistags.channelIndex
        numOriginalChannels = self.mainOperator.InputImage[self.imageIndex].meta.shape[channelAxis]
        originalChannel = featureChannelIndex % numOriginalChannels
        featureNameIndex = featureChannelIndex / numOriginalChannels
        channelNames = ['R', 'G', 'B']
        # FIXME: It shouldn't be necessary to dig down into the operator to access these names.
        #        Perhaps the operator should provide them as an output?
        featureName = self.mainOperator.FeatureNames[self.imageIndex].value[ featureNameIndex ]
        if numOriginalChannels > 1:
            featureName += " (" + channelNames[originalChannel] + ")"
        
        featureSource = LazyflowSource(selector.Output)
        featureSource.setObjectName(featureName)
        featureLayer = AlphaModulatedLayer(featureSource, tintColor=ref_label.color, normalize = None )
        featureLayer.name = featureSource.objectName()

        # By default, only the first feature is visible
        featureLayer.opacity = 1.0
        featureLayer.visible = (featureChannelIndex == 0)
        featureLayer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )
        self.layerstack.insert(0, featureLayer )

    def createDefault16ColorColorTable(self):
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
        # All the controls in our GUI
        controlList = [ self.menuBar,
                        self.volumeEditorWidget,
                        self.viewerControlWidget.UpButton,
                        self.viewerControlWidget.DownButton,
                        self.viewerControlWidget.DeleteButton ]

        # Enable/disable all of them
        for control in controlList:
            control.setEnabled(enabled)































