from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import LazyflowSource, GrayscaleLayer

from lazyflow.operators import OpSingleChannelSelector

from igms.featureTableWidget import FeatureEntry
from igms.featureDlg import FeatureDlg

import os
import numpy
from utility import bind

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from lazyflow.tracer import Tracer
from applets.layerViewer import LayerViewerGui

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
    FeatureNames = [ "G-smooth",
                     "L-of-G",
                     "ST EVs",
                     "H-of-G EVs",
                     "G. Grad Mag",
                     "Diff of G." ]

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def appletDrawers(self):
        return [ ("Feature Selection", self.drawer ) ]

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        with Tracer(traceLogger):
            super(FeatureSelectionGui, self).__init__([ mainOperator.FeatureLayers ])
            self.mainOperator = mainOperator

            self.drawer = None
            self.initAppletDrawerUic()
            self.initFeatureDlg()
            self.mainOperator.SelectionMatrix.notifyConnect( bind(self.onFeaturesSelectionsChanged) )
    
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
    
    def setupLayers(self, currentImageIndex):
        with Tracer(traceLogger):
            layers = []

            outputSlot = self.mainOperator.FeatureLayers[currentImageIndex]
            if outputSlot.ready():
                # Now add a layer for each feature
                numFeatureChannels = len(outputSlot)
                for featureChannelIndex in range(0, numFeatureChannels):
                    layer = self.getFeatureLayer(currentImageIndex, featureChannelIndex)
                    layers.append( layer )                
            return layers

    def getFeatureLayer(self, currentImageIndex, featureChannelIndex):
        """
        Display a feature in the layer editor.
        """
        with Tracer(traceLogger):
            # Determine the name for this feature
            channelAxis = self.mainOperator.InputImage[currentImageIndex].meta.axistags.channelIndex
            numOriginalChannels = self.mainOperator.InputImage[currentImageIndex].meta.shape[channelAxis]
            originalChannel = featureChannelIndex % numOriginalChannels
            featureNameIndex = featureChannelIndex / numOriginalChannels
            channelNames = ['R', 'G', 'B']
            featureNames = self.mainOperator.FeatureNames[currentImageIndex].value
            featureName = featureNames[ featureNameIndex ]
            if numOriginalChannels > 1:
                featureName += " (" + channelNames[originalChannel] + ")"

            # Create a grayscale layer for it.            
            featureLayer = self.createStandardLayerFromSlot( self.mainOperator.FeatureLayers[currentImageIndex][featureChannelIndex] )    
            # By default, only the first feature is visible
            featureLayer.visible = (featureChannelIndex == 0)
            featureLayer.opacity = 1.0
            featureLayer.name = featureName
            featureLayer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )

            return featureLayer

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































