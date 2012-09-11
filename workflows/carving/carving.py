from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet
from ilastik.applets.labeling.labelingApplet import PixelClassificationApplet as LabelingApplet

from lazyflow.graph import Graph, Operator, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

class CarvingWorkflow(Workflow):
    
    def __init__(self):
        super(CarvingWorkflow, self).__init__()
        self._applets = []

        # Create a graph to be shared by all operators
        graph = Graph()
        self._graph = graph

        ######################
        # Interactive workflow
        ######################
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(graph)
        #self.viewerApplet = LabelingApplet(graph, "xxx")

        self.viewerApplet.topLevelOperator.RawInput.connect( self.dataSelectionApplet.topLevelOperator.Image )

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator
        
        ## Connect operators ##
        
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.viewerApplet)

        # The shell needs a slot from which he can read the list of image names to switch between.
        # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
        opSelectFilename = OperatorWrapper( OpAttributeSelector(graph=graph) )
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )

        self._imageNameListSlot = opSelectFilename.Result

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self._imageNameListSlot
    
    @property
    def graph( self ):
        '''the lazyflow graph shared by the applets'''
        return self._graph

def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    # Open a project
    #shell.openProjectFile("test.ilp")

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(2)

if __name__ == "__main__":
    from ilastik.shell.gui.startShellGui import startShellGui
    
    # Start the GUI
    
    startShellGui( CarvingWorkflow )

    # Start the GUI with a debug project    
    #startShellGui( CarvingWorkflow, debug_with_existing )    
