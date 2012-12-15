from lazyflow.graph import Graph, OperatorWrapper

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.objectExtraction import ObjectExtractionApplet

from lazyflow.operators.obsolete.valueProviders import OpAttributeSelector
from ilastik.applets.tracking.conservation.conservationTrackingApplet import ConservationTrackingApplet
from ilastik.applets.objectExtractionMultiClass.objectExtractionMultiClassApplet import ObjectExtractionMultiClassApplet

class ConservationTrackingWorkflow( Workflow ):
    def __init__( self ):
        # Create a graph to be shared by all operators
        graph = Graph()
        
        super(ConservationTrackingWorkflow, self).__init__(graph=graph)
        self._applets = []
        self._imageNameListSlot = None
    
        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Segmentation", "Input Segmentation", batchDataGui=False)

        self.objectExtractionApplet = ObjectExtractionMultiClassApplet( self )
        self.trackingApplet = ConservationTrackingApplet( self )

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator
        opObjExtraction = self.objectExtractionApplet.topLevelOperator
        opTracking = self.trackingApplet.topLevelOperator
        
        ## Connect operators ##
        opObjExtraction.Images.connect( opData.Image )

        opTracking.LabelImage.connect( opObjExtraction.LabelImage )
        opTracking.ObjectFeatures.connect( opObjExtraction.RegionFeatures )
        opTracking.ClassMapping.connect( opObjExtraction.ClassMapping )
        opTracking.RegionLocalCenters.connect( opObjExtraction.RegionLocalCenters )

        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.trackingApplet)

        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector, parent=self )
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )

        self._imageNameListSlot = opSelectFilename.Result

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot
    
