from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.obsolete.valueProviders import OpAttributeSelector

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet

from carvingApplet import CarvingApplet

class CarvingWorkflow(Workflow):

    def __init__(self, carvingGraphFile=None, hintoverlayFile=None):
        if carvingGraphFile is not None:
            assert isinstance(carvingGraphFile, str), "carvingGraphFile should be a string, not '%s'" % type(carvingGraphFile)
        if hintoverlayFile is not None:
            assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
        #super(CarvingWorkflow, self).__init__()
        self._applets = []

        graph = Graph()
        
        super(CarvingWorkflow, self).__init__(graph=graph)
        
        self._applets = []

        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)

        self.carvingApplet = CarvingApplet(workflow=self,
                                           projectFileGroupName="carving",
                                           carvingGraphFile = carvingGraphFile,
                                           hintOverlayFile=hintoverlayFile)
        self.carvingApplet.topLevelOperator.RawData.connect( self.dataSelectionApplet.topLevelOperator.Image )
        self.carvingApplet.topLevelOperator.opLabeling.LabelsAllowedFlags.connect( self.dataSelectionApplet.topLevelOperator.AllowLabels )
        self.carvingApplet.gui.minLabelNumber = 2
        self.carvingApplet.gui.maxLabelNumber = 2

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator
        
        ## Connect operators ##
        
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.carvingApplet)

        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector, graph=graph )
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )

        self._imageNameListSlot = opSelectFilename.Result

    def setCarvingGraphFile(self, fname):
        self.carvingApplet.topLevelOperator.opCarving.CarvingGraphFile.setValue(fname)

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot