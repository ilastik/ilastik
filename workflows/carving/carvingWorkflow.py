from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.valueProviders import OpAttributeSelector

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet

from carvingApplet import CarvingApplet

class CarvingWorkflow(Workflow):

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, carvingGraphFile=None, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        if carvingGraphFile is not None:
            assert isinstance(carvingGraphFile, str), "carvingGraphFile should be a string, not '%s'" % type(carvingGraphFile)
        if hintoverlayFile is not None:
            assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
        if pmapoverlayFile is not None:
            assert isinstance(pmapoverlayFile, str), "pmapoverlayFile should be a string, not '%s'" % type(pmapoverlayFile)

        graph = Graph()
        
        super(CarvingWorkflow, self).__init__(graph=graph, *args, **kwargs)
        

        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)

        self.carvingApplet = CarvingApplet(workflow=self,
                                           projectFileGroupName="carving",
                                           carvingGraphFile = carvingGraphFile,
                                           hintOverlayFile=hintoverlayFile,
                                           pmapOverlayFile=pmapoverlayFile)
        # Expose to shell
        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.carvingApplet)

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opCarvingTopLevel = self.carvingApplet.topLevelOperator.getLane(laneIndex)
        
        ## Connect operators ##
        opCarvingTopLevel.RawData.connect( opData.Image )
        opCarvingTopLevel.opCarving.opLabeling.LabelsAllowedFlag.connect( opData.AllowLabels )

    def setCarvingGraphFile(self, fname):
        self.carvingApplet.topLevelOperator.opCarving.CarvingGraphFile.setValue(fname)
