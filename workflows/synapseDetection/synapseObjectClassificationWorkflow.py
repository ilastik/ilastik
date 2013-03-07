from lazyflow.graph import Graph
from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet

# Glue operators
from lazyflow.operators.adaptors import Op5ifyer

class SynapseObjectClassificationWorkflow(Workflow):
    name = "Object Classification Workflow"

    def __init__( self, headless, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(self.__class__, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        ######################
        # Interactive workflow
        ######################

        ## Create applets
        self.rawDataSelectionApplet = DataSelectionApplet(self,
                                                       "Input: Raw",
                                                       "Input Raw",
                                                       batchDataGui=False,
                                                       force5d=False)
        
        self.predictionSelectionApplet = DataSelectionApplet(self,
                                                       "Input: Prediction Maps",
                                                       "Input Prediction Maps",
                                                       batchDataGui=False,
                                                       force5d=False)

        self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self, "Threshold & Size Filter", "ThresholdTwoLevels" )

        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)

        self._applets = []
        self._applets.append(self.rawDataSelectionApplet)
        self._applets.append(self.predictionSelectionApplet)
        self._applets.append(self.thresholdTwoLevelsApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        # FIXME: The shell is very sensitive to the order in which these images are added in the GUI.
        # The slot that serves as the 'master' (this slot) for lane insertion purposes must be added last.
        # Hence, we are using the predictionSelection slot.
        # In the future, the shell and dataselection applets will be fixed to handle the multi-input-data case.
        #return self.rawDataSelectionApplet.topLevelOperator.ImageName
        return self.predictionSelectionApplet.topLevelOperator.ImageName

    def connectLane( self, laneIndex ):
        ## Access applet operators
        opRawData = self.rawDataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPredictionData = self.predictionSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # Connect Predictions -> Thresholding
        opTwoLevelThreshold.InputImage.connect( opPredictionData.Image )
        opTwoLevelThreshold.RawInput.connect( opRawData.Image ) # Used for display only

        # FIXME: For now, the object extraction and classification applets REQUIRE 5D data.
        # (But the two-level thresholding applet CAN'T HANDLE 5d data.)
        op5Raw = Op5ifyer(parent=self)
        op5Raw.input.connect( opRawData.Image )
        
        op5Predictions = Op5ifyer( parent=self )
        #op5Predictions.input.connect( opTwoLevelThreshold.Output )
        
        # Use cached output so that the BinaryImage layer is correct in the GUI.
        op5Predictions.input.connect( opTwoLevelThreshold.CachedOutput )
        
        # connect raw data -> extraction
        opObjExtraction.RawImage.connect(op5Raw.output)

        # Thresholded and filtered binary image -> extraction
        opObjExtraction.BinaryImage.connect( op5Predictions.output )

        # connect data -> classification
        opObjClassification.BinaryImages.connect(op5Predictions.output)
        opObjClassification.RawImages.connect(op5Raw.output)
        opObjClassification.LabelsAllowedFlags.connect(opPredictionData.AllowLabels)

        # connect extraction -> classification
        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
