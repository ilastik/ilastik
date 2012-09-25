from PyQt4.QtGui import *
from PyQt4 import uic

from igms.featureTableWidget import FeatureEntry
from igms.featureDlg import FeatureDlg

import os
import numpy
from ilastik.utility import bind
from lazyflow.operators import OpSubRegion

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from lazyflow.tracer import traceLogged
from ilastik.applets.layerViewer import LayerViewerGui

class FeatureSelectionGui(LayerViewerGui):
    """
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
    FeatureNames = [ "Gaussian Smoothing",
                     "Laplacian of Gaussian",
                     "Structure Tensor Eigenvalues",
                     "Hessian of Gaussian Eigenvalues",
                     "Gaussian Gradient Magnitude",
                     "Difference of Gaussians" ]

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawers(self):
        return [ ("Feature Selection", self.drawer ) ]

    def viewerControlWidget(self):
        return self._viewerControlWidget

    def reset(self):
        super(FeatureSelectionGui, self).reset()
        self.drawer.caption.setText( "(No features selected)" )

        # Why is this necessary?
        # Clearing the layerstack doesn't seem to call the rowsRemoved signal?
        self._viewerControlWidget.listWidget.clear()

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    @traceLogged(traceLogger)
    def __init__(self, mainOperator):
        """
        """
        super(FeatureSelectionGui, self).__init__(mainOperator)
        self.mainOperator = mainOperator

        self.initFeatureDlg()
        self.mainOperator.SelectionMatrix.notifyDirty( bind(self.onFeaturesSelectionsChanged) )
    
    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/featureSelectionDrawer.ui")
        self.drawer.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
    

    @traceLogged(traceLogger)
    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        
        TODO: Right now we manage adding/removing entries to a plain listview 
              widget by monitoring the layerstack for changes.
              Ideally, we should implement a custom widget that does this for us, 
              which would be initialized with the layer list model (like volumina.layerwidget)
        """
        self._viewerControlWidget = uic.loadUi(os.path.split(__file__)[0] + "/viewerControls.ui")
        
        layerListWidget = self._viewerControlWidget.listWidget

        # Need to handle data changes because the layerstack model hasn't 
        # updated his data yet by the time he calls the rowsInserted signal
        def handleLayerStackDataChanged(startIndex, stopIndex):
            row = startIndex.row()
            layerListWidget.item(row).setText(self.layerstack[row].name)
        self.layerstack.dataChanged.connect(handleLayerStackDataChanged)
        
        def handleInsertedLayers(parent, start, end):
            for i in range(start, end+1):
                layerListWidget.insertItem(i, self.layerstack[i].name)
        self.layerstack.rowsInserted.connect( handleInsertedLayers )

        def handleRemovedLayers(parent, start, end):
            for i in range(start, end+1):
                layerListWidget.takeItem(i)
        self.layerstack.rowsRemoved.connect( handleRemovedLayers )
        
        def handleSelectionChanged(row):
            # Only one layer is visible at a time
            for i, layer in enumerate(self.layerstack):
                layer.visible = (i == row)
        layerListWidget.currentRowChanged.connect( handleSelectionChanged )
    
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        layers = []
        
        opFeatureSelection = self.operatorForCurrentImage()

        inputSlot = opFeatureSelection.InputImage
        featureMultiSlot = opFeatureSelection.FeatureLayers
        if inputSlot.ready() and featureMultiSlot.ready():
            for featureIndex, featureSlot in enumerate(featureMultiSlot):
                assert featureSlot.ready()
                layers += self.getFeatureLayers(inputSlot, featureSlot)
            
            layers[0].visible = True
        return layers

    @traceLogged(traceLogger)
    def getFeatureLayers(self, inputSlot, featureSlot):
        """
        Generate a list of layers for the feature image produced by the given slot.
        """
        layers = []
        
        channelAxis = inputSlot.meta.axistags.channelIndex
        assert channelAxis == featureSlot.meta.axistags.channelIndex
        numInputChannels = inputSlot.meta.shape[channelAxis]
        numFeatureChannels = featureSlot.meta.shape[channelAxis]

        # Determine how many channels this feature has (up to 3)
        featureChannelsPerInputChannel = numFeatureChannels / numInputChannels
        assert 0 < featureChannelsPerInputChannel <= 3, "The feature selection Gui does not yet support features with more than three channels per input channel." 

        for inputChannel in range(numInputChannels):
            # Determine the name for this feature
            featureName = featureSlot.meta.description
            assert featureName is not None
            if 2 <= numInputChannels <= 3:
                channelNames = ['R', 'G', 'B']
                featureName += " (" + channelNames[inputChannel] + ")"
            if numInputChannels > 3:
                featureName += " (Ch. {})".format(inputChannel)

            opSubRegion = OpSubRegion(graph=self.mainOperator.graph)
            opSubRegion.Input.connect( featureSlot )
            start = [0] * len(featureSlot.meta.shape)
            start[channelAxis] = inputChannel * featureChannelsPerInputChannel
            stop = list(featureSlot.meta.shape)
            stop[channelAxis] = (inputChannel+1) * featureChannelsPerInputChannel
            opSubRegion.Start.setValue( tuple(start) )
            opSubRegion.Stop.setValue( tuple(stop) )
            
            featureLayer = self.createStandardLayerFromSlot( opSubRegion.Output )
            featureLayer.visible = False
            featureLayer.opacity = 1.0
            featureLayer.name = featureName
            
            layers.append(featureLayer)

        return layers

    @traceLogged(traceLogger)
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

    def onFeatureButtonClicked(self):
        # Refresh the feature matrix in case it has changed since the last time we were opened
        # (e.g. if the user loaded a project from disk)
        if self.mainOperator.SelectionMatrix.ready():
            self.featureDlg.selectedFeatureBoolMatrix = self.mainOperator.SelectionMatrix.value
        
        # Now open the feature selection dialog
        self.featureDlg.show()

    def onNewFeaturesFromFeatureDlg(self):
        opFeatureSelection = self.operatorForCurrentImage()
        if opFeatureSelection is not None:
            # Re-initialize the scales and features
            opFeatureSelection.Scales.setValue( self.ScalesList )
            opFeatureSelection.FeatureIds.setValue(self.FeatureIds)

            # Give the new features to the pipeline (if there are any)
            featureMatrix = numpy.asarray(self.featureDlg.selectedFeatureBoolMatrix)
            if featureMatrix.any():
                opFeatureSelection.SelectionMatrix.setValue( featureMatrix )
            else:
                # Not valid to give a matrix with no features selected.
                # Disconnect.
                opFeatureSelection.SelectionMatrix.disconnect()
    
    def onFeaturesSelectionsChanged(self):
        """
        Handles changes to our top-level operator's matrix of feature selections.
        """
        # Update the drawer caption
        if not self.mainOperator.SelectionMatrix.ready():
            self.drawer.caption.setText( "(No features selected)" )
            self.layerstack.clear()
        else:
            self.drawer.caption.setText( "(Selected %d features)" % numpy.sum(self.mainOperator.SelectionMatrix.value) )































