from lazyflow.graph import Graph
from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.thresholdTwoLevels import ThresholdTwoLevelsApplet
from ilastik.applets.objectExtraction import ObjectExtractionApplet
from ilastik.applets.objectClassification import ObjectClassificationApplet

from ilastik.applets.fillMissingSlices import FillMissingSlicesApplet
from ilastik.applets.fillMissingSlices.opFillMissingSlices import OpFillMissingSlicesNoCache

# Glue operators
from lazyflow.operators.adaptors import Op5ifyer

class SynapseObjectClassificationWorkflow(Workflow):
    name = "Object Classification Workflow"

    def __init__( self, headless, *args, **kwargs ):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(SynapseObjectClassificationWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        ######################
        # Interactive workflow
        ######################

        ## Create applets
        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Input Data",
                                                       "Input Data",
                                                       batchDataGui=False,
                                                       force5d=True)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data', 'Prediction Maps'] )

        self.thresholdTwoLevelsApplet = ThresholdTwoLevelsApplet( self, "Threshold & Size Filter", "ThresholdTwoLevels" )

        self.fillMissingSlicesApplet = FillMissingSlicesApplet(self, "Fill Missing Slices", "Fill Missing Slices")

        self.objectExtractionApplet = ObjectExtractionApplet(workflow=self)
        self.objectClassificationApplet = ObjectClassificationApplet(workflow=self)

        self._applets = []
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.thresholdTwoLevelsApplet)
        self._applets.append(self.fillMissingSlicesApplet)
        self._applets.append(self.objectExtractionApplet)
        self._applets.append(self.objectClassificationApplet)

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane( self, laneIndex ):
        ## Access applet operators
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTwoLevelThreshold = self.thresholdTwoLevelsApplet.topLevelOperator.getLane(laneIndex)
        opFillMissingSlices = self.fillMissingSlicesApplet.topLevelOperator.getLane(laneIndex)
        opObjExtraction = self.objectExtractionApplet.topLevelOperator.getLane(laneIndex)
        opObjClassification = self.objectClassificationApplet.topLevelOperator.getLane(laneIndex)

        # Connect Raw data -> Fill missing slices
        opFillMissingSlices.Input.connect(opDataSelection.ImageGroup[0])
        op5Raw = Op5ifyer(parent=self)
        op5Raw.input.connect(opFillMissingSlices.Output)
        
        op5Predictions = Op5ifyer( parent=self )
        op5Predictions.input.connect( opDataSelection.ImageGroup[1] )

        # Connect Predictions -> Thresholding
        opTwoLevelThreshold.InputImage.connect( op5Predictions.output )
        opTwoLevelThreshold.RawInput.connect( opDataSelection.ImageGroup[0]) # Used for display only

        
        op5Binary = Op5ifyer( parent=self )
        
        # Use cached output so that the BinaryImage layer is correct in the GUI.
        op5Binary.input.connect( opTwoLevelThreshold.CachedOutput )
        
        # connect raw data -> extraction
        opObjExtraction.RawImage.connect(op5Raw.output)

        # Thresholded and filtered binary image -> extraction
        opObjExtraction.BinaryImage.connect( op5Binary.output )

        # connect data -> classification
        opObjClassification.BinaryImages.connect(op5Predictions.output)
        opObjClassification.RawImages.connect(op5Raw.output)
        opObjClassification.LabelsAllowedFlags.connect(opDataSelection.AllowLabels)

        # connect extraction -> classification
        opObjClassification.SegmentationImages.connect(opObjExtraction.LabelImage)
        opObjClassification.ObjectFeatures.connect(opObjExtraction.RegionFeatures)
        