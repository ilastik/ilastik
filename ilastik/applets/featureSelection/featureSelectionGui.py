from PyQt4.QtGui import *
from PyQt4 import uic

from ilastik.widgets.featureTableWidget import FeatureEntry
from ilastik.widgets.featureDlg import FeatureDlg

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

#    # Default order
#    FeatureIds = [ 'GaussianSmoothing',
#                   'LaplacianOfGaussian',
#                   'GaussianGradientMagnitude',
#                   'DifferenceOfGaussians',
#                   'StructureTensorEigenvalues',
#                   'HessianOfGaussianEigenvalues' ]

    # Map feature groups to lists of feature IDs
    FeatureGroups = [ ( "Color/Intensity",   [ "GaussianSmoothing" ] ),
                      ( "Edge",    [ "LaplacianOfGaussian", "GaussianGradientMagnitude", "DifferenceOfGaussians" ] ),
                      ( "Texture", [ "StructureTensorEigenvalues", "HessianOfGaussianEigenvalues" ] ) ]

    # Map feature IDs to feature names
    FeatureNames = { 'GaussianSmoothing' : 'Gaussian Smoothing',
                     'LaplacianOfGaussian' : "Laplacian of Gaussian",
                     'GaussianGradientMagnitude' : "Gaussian Gradient Magnitude",
                     'DifferenceOfGaussians' : "Difference of Gaussians",
                     'StructureTensorEigenvalues' : "Structure Tensor EigenValues",
                     'HessianOfGaussianEigenvalues' : "Hessian of Gaussian Eigenvalues" }

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawer(self):
        return self.drawer

    @classmethod
    def appletDrawerName(cls):
        return 'Feature Selection'

    def viewerControlWidget(self):
        return self._viewerControlWidget

    def reset(self):
        super(FeatureSelectionGui, self).reset()
        self.drawer.caption.setText( "(No features selected)" )

        # Why is this necessary?
        # Clearing the layerstack doesn't seem to call the rowsRemoved signal?
        self._viewerControlWidget.featureListWidget.clear()

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    @traceLogged(traceLogger)
    def __init__(self, mainOperator):
        """
        """
        self.mainOperator = mainOperator
        super(FeatureSelectionGui, self).__init__(mainOperator)

        self.mainOperator.SelectionMatrix.notifyDirty( bind(self.onFeaturesSelectionsChanged) )

        # Init feature dialog
        self.initFeatureDlg()

    def getFeatureIdOrder(self):
        featureIrdOrder = []
        for group, featureIds in self.FeatureGroups:
            featureIrdOrder += featureIds
        return featureIrdOrder

    def initFeatureOrder(self):
        self.mainOperator.Scales.setValue( self.ScalesList )
        self.mainOperator.FeatureIds.setValue( self.getFeatureIdOrder() )
            
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
        
        layerListWidget = self._viewerControlWidget.featureListWidget

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
            for i in reversed(range(start, end+1)):
                layerListWidget.takeItem(i)
        self.layerstack.rowsRemoved.connect( handleRemovedLayers )
        
        def handleSelectionChanged(row):
            # Only one layer is visible at a time
            for i, layer in enumerate(self.layerstack):
                layer.visible = (i == row)
        layerListWidget.currentRowChanged.connect( handleSelectionChanged )
    
    @traceLogged(traceLogger)
    def setupLayers(self):
        layers = []
        
        opFeatureSelection = self.mainOperator

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
        self.initFeatureOrder()

        self.featureDlg = FeatureDlg()
        self.featureDlg.setWindowTitle("Features")
        
        # Map from groups of feature IDs to groups of feature NAMEs
        groupedNames = []
        for group, featureIds in self.FeatureGroups:
            featureEntries = []
            for featureId in featureIds:
                featureName = self.FeatureNames[featureId]
                featureEntries.append( FeatureEntry(featureName) )
            groupedNames.append( (group, featureEntries) )
        self.featureDlg.createFeatureTable( groupedNames, self.ScalesList )
        self.featureDlg.setImageToPreView(None)

        # Init with no features
        rows = len(self.mainOperator.FeatureIds.value)
        cols = len(self.mainOperator.Scales.value)
        defaultFeatures = numpy.zeros((rows,cols), dtype=bool)
        self.featureDlg.selectedFeatureBoolMatrix = defaultFeatures

        self.featureDlg.accepted.connect(self.onNewFeaturesFromFeatureDlg)

    def onFeatureButtonClicked(self):
        # Refresh the feature matrix in case it has changed since the last time we were opened
        # (e.g. if the user loaded a project from disk)
        if self.mainOperator.SelectionMatrix.ready() and self.mainOperator.FeatureIds.ready():
            # Re-order the feature matrix using the loaded feature ids
            matrix = self.mainOperator.SelectionMatrix.value
            featureOrdering = self.mainOperator.FeatureIds.value
            
            reorderedMatrix = numpy.zeros(matrix.shape, dtype=bool)
            newrow = 0
            for group, featureIds in self.FeatureGroups:
                for featureId in featureIds:
                    oldrow = featureOrdering.index(featureId)
                    reorderedMatrix[newrow] = matrix[oldrow]
                    newrow += 1
                
            self.featureDlg.selectedFeatureBoolMatrix = reorderedMatrix
        
        # Now open the feature selection dialog
        self.featureDlg.exec_()

    def onNewFeaturesFromFeatureDlg(self):
        opFeatureSelection = self.mainOperator
        if opFeatureSelection is not None:
            # Re-initialize the scales and features
            self.initFeatureOrder()

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
            self.initFeatureOrder()
            matrix = self.mainOperator.SelectionMatrix.value
            self.drawer.caption.setText( "(Selected %d features)" % numpy.sum(matrix) )































