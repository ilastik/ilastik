from lazyflow.graph import Graph, Operator, OperatorWrapper

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
#from ilastik.applets.pixelClassification import \
#    PixelClassificationApplet, PixelClassificationBatchResultsApplet
#from ilastik.applets.objectExtraction import ObjectExtractionApplet
#from ilastik.applets.objectClassification import ObjectClassificationApplet
#from ilastik.applets.objectViewer import ObjectViewerApplet
from ilastik.applets.counting3d import Counting3dApplet 

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OpAttributeSelector, OpSegmentation, Op5ifyer


class CountingWorkflow(Workflow):
    name = "Counting Workflow"

    def __init__(self, headless, *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs: del kwargs['graph']
        super(CountingWorkflow, self).__init__(headless=headless, graph=graph, *args, **kwargs)

        ######################
        # Interactive workflow
        ######################

        self.projectMetadataApplet = ProjectMetadataApplet()

        self.dataSelectionApplet = DataSelectionApplet(self,
                                                       "Data Selection",
                                                       "DataSelection",
                                                       batchDataGui=False,
                                                       force5d=False
                                                      )

        self.featureSelectionApplet = FeatureSelectionApplet(self,
                                                             "Feature Selection",
                                                             "FeatureSelections")

        #self.pcApplet = PixelClassificationApplet(self, "PixelClassification")
        self.counting3dApplet = Counting3dApplet(workflow=self)

        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.featureSelectionApplet)
        self._applets.append(self.counting3dApplet)


    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opTrainingFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)
        opCounting3d = self.counting3dApplet.topLevelOperator.getLane(laneIndex)

        #### connect input image
        opTrainingFeatures.InputImage.connect(opData.Image)

        opCounting3d.InputImages.connect(opData.Image)
        opCounting3d.FeatureImages.connect(opTrainingFeatures.OutputImage)
        opCounting3d.LabelsAllowedFlags.connect(opData.AllowLabels)
        opCounting3d.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
        #opCounting3d.UserLabels.connect(opClassify.LabelImages)
        #opCounting3d.ForegroundLabels.connect(opObjExtraction.LabelImage)
