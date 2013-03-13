from PyQt4.QtGui import *
from PyQt4 import uic

from ilastik.widgets.featureTableWidget import FeatureEntry
from ilastik.widgets.featureDlg import FeatureDlg

import os
import numpy
import h5py
from ilastik.utility import bind
from lazyflow.operators import OpSubRegion

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from lazyflow.utility import Tracer, traceLogged
from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.config import cfg as ilastik_config

class FeatureSelectionGui(LayerViewerGui):
    """
    """
    
    # Constants    
    ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
    DefaultColorTable = None

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
    def __init__(self, topLevelOperatorView):
        """
        """
        self.topLevelOperatorView = topLevelOperatorView
        super(FeatureSelectionGui, self).__init__(topLevelOperatorView, crosshair=False)

        self.topLevelOperatorView.SelectionMatrix.notifyDirty( bind(self.onFeaturesSelectionsChanged) )
        self.topLevelOperatorView.FeatureListFilename.notifyDirty( bind(self.onFeaturesSelectionsChanged) )
        self.onFeaturesSelectionsChanged()

        # Init feature dialog
        self.initFeatureDlg()

    def getFeatureIdOrder(self):
        featureIrdOrder = []
        for group, featureIds in self.FeatureGroups:
            featureIrdOrder += featureIds
        return featureIrdOrder

    def initFeatureOrder(self):
        self.topLevelOperatorView.Scales.setValue( self.ScalesList )
        self.topLevelOperatorView.FeatureIds.setValue( self.getFeatureIdOrder() )
            
    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/featureSelectionDrawer.ui")
        self.drawer.SelectFeaturesButton.clicked.connect(self.onFeatureButtonClicked)
        self.drawer.UsePrecomputedFeaturesButton.clicked.connect(self.onUsePrecomputedFeaturesButtonClicked)
        dbg = ilastik_config.getboolean("ilastik", "debug") 
        if not dbg:
            self.drawer.UsePrecomputedFeaturesButton.setHidden(True)

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
        
        opFeatureSelection = self.topLevelOperatorView

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

            opSubRegion = OpSubRegion(graph=self.topLevelOperatorView.graph)
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
        rows = len(self.topLevelOperatorView.FeatureIds.value)
        cols = len(self.topLevelOperatorView.Scales.value)
        defaultFeatures = numpy.zeros((rows,cols), dtype=bool)
        self.featureDlg.selectedFeatureBoolMatrix = defaultFeatures

        self.featureDlg.accepted.connect(self.onNewFeaturesFromFeatureDlg)

    def onUsePrecomputedFeaturesButtonClicked(self):
        filename = QFileDialog.getOpenFileName(self, 'Open Feature List', '.')
        
        #sanity checks on the given file
        if not filename:
            return
        if not os.path.exists(filename):
            QMessageBox.critical(self, "Open Feature List", "File '%s' does not exist" % filename)
            return
        f = open(filename, 'r')
        with f:
            for line in f:
                line = line.strip()
                if len(line) == 0:
                    continue
                if not os.path.exists(line):
                    QMessageBox.critical(self, "Open Feature List", "File '%s', referenced in '%s', does not exist" % (line, filename))
                    return
                try:
                    h = h5py.File(line, 'r')
                    with h:
                        assert len(h["data"].shape) == 3
                except:
                    QMessageBox.critical(self, "Open Feature List", "File '%s', referenced in '%s', could not be opened as an HDF5 file or does not contain a 3D dataset called 'data'" % (line, filename))
                    return

        self.topLevelOperatorView.FeatureListFilename.setValue(filename)
        self.topLevelOperatorView._setupOutputs()
        self.onFeaturesSelectionsChanged()

    def onFeatureButtonClicked(self):
        self.topLevelOperatorView.FeatureListFilename.setValue("")
        
        # Refresh the feature matrix in case it has changed since the last time we were opened
        # (e.g. if the user loaded a project from disk)
        if self.topLevelOperatorView.SelectionMatrix.ready() and self.topLevelOperatorView.FeatureIds.ready():
            # Re-order the feature matrix using the loaded feature ids
            matrix = self.topLevelOperatorView.SelectionMatrix.value
            featureOrdering = self.topLevelOperatorView.FeatureIds.value
            
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
        opFeatureSelection = self.topLevelOperatorView
        if opFeatureSelection is not None:
            # Re-initialize the scales and features
            self.initFeatureOrder()

            # Give the new features to the pipeline (if there are any)
            featureMatrix = numpy.asarray(self.featureDlg.selectedFeatureBoolMatrix)
            if featureMatrix.any():
                opFeatureSelection.SelectionMatrix.setValue( featureMatrix )
                self.topLevelOperatorView._setupOutputs()
            else:
                # Not valid to give a matrix with no features selected.
                # Disconnect.
                opFeatureSelection.SelectionMatrix.disconnect()
    
    def onFeaturesSelectionsChanged(self):
        """
        Handles changes to our top-level operator's matrix of feature selections.
        """
        # Update the drawer caption
        
        fff = ( self.topLevelOperatorView.FeatureListFilename.ready() and \
                len(self.topLevelOperatorView.FeatureListFilename.value) != 0)
        
        if not self.topLevelOperatorView.SelectionMatrix.ready() and not fff: 
            self.drawer.caption.setText( "(No features selected)" )
            self.layerstack.clear()
        elif fff:
            self.drawer.caption.setText( "(features from files)" )
        else:
            self.initFeatureOrder()
            matrix = self.topLevelOperatorView.SelectionMatrix.value
            self.drawer.caption.setText( "(Selected %d features)" % numpy.sum(matrix) )
