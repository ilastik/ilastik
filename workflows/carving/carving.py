import os

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet
from ilastik.applets.labeling.labelingApplet import LabelingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui

from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

from cylemon import segmentation
print segmentation.__file__

import vigra

from ilastik.applets.carving.opSeededWatershed import OpSegmentor

class OpVolumeExtractor(Operator):
    name = "OpVolumeExtractor"
    category = "dimension reduction"
    
    Input = InputSlot()
    Output = OutputSlot()
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        
        inputShape = self.Input.meta.shape
        outputShape = inputShape[1:4]
        self.Output.meta.shape = outputShape
        self.Output.meta.axistags = vigra.defaultAxistags('xyz')
    
    def execute(self, slot, roi, result):
        start = (0,) + tuple(roi.start) + (0,)
        stop = (1,) + tuple(roi.stop) + (1,)
        print roi
        print start, stop
        result[...] = self.Input(start, stop).wait()[0,...,0]
        return result            

class CarvingGui(LabelingGui):
    def __init__(self, labelingSlots, observedSlots, drawerUiPath=None, rawInputSlot=None,
                 carvingApplet=None):
        # We provide our own UI file (which adds an extra control for interactive mode)
        print __file__
        directory = os.path.split(__file__)[0]
        labelingDrawerUiPath = os.path.join(directory, 'labelingDrawer.ui')

        super(CarvingGui, self).__init__(labelingSlots, observedSlots, labelingDrawerUiPath, rawInputSlot)
        self._carvingApplet = carvingApplet

        def testit():
            self._carvingApplet.carvingOperator.update.setValue(True)
        self.labelingDrawerUi.segment.clicked.connect(testit)

    def setupLayers(self, currentImageIndex):
        layers = super(CarvingGui, self).setupLayers(currentImageIndex)

        if self._carvingApplet.carvingOperator.segmentation[currentImageIndex].ready():
            layer = self.createStandardLayerFromSlot( self._carvingApplet.carvingOperator.segmentation[currentImageIndex] )
            layer.name = "Segmentation"
            layer.visible = True
            layer.opacity = 1.0
            layers.insert(1, layer)

        return layers

class CarvingApplet(LabelingApplet):
    def __init__(self, graph, projectFileGroupName):
        super(CarvingApplet, self).__init__(graph, projectFileGroupName)

#        op3d = OperatorWrapper( OpVolumeExtractor(graph=self.topLevelOperator.graph), promotedSlotNames=['Input'] )
#        op3d.Input.connect(self.topLevelOperator.InputImages)
#
#        self.carvingOperator = OperatorWrapper( OpSegmentor(graph) )
#        self.carvingOperator.image.connect(op3d.Output)

        self.carvingOperator = OperatorWrapper( OpSegmentor(graph), promotedSlotNames=['image', 'writeSeeds', 'initial_segmentor'] )
        self.carvingOperator.image.connect(self.topLevelOperator.InputImages)

    @property
    def gui(self):
        if self._gui is None:

            labelingSlots = LabelingGui.LabelingSlots()
            labelingSlots.labelInput = self.topLevelOperator.LabelInputs
            labelingSlots.labelOutput = self.topLevelOperator.LabelImages
            labelingSlots.labelEraserValue = self.topLevelOperator.LabelEraserValue
            labelingSlots.labelDelete = self.topLevelOperator.LabelDelete
            labelingSlots.maxLabelValue = self.topLevelOperator.MaxLabelValue
            labelingSlots.labelsAllowed = self.topLevelOperator.LabelsAllowedFlags

            self.carvingOperator.writeSeeds.connect(labelingSlots.labelOutput)
            self.carvingOperator.deleteSeed.connect(labelingSlots.labelDelete)
            self.carvingOperator.eraser.connect(labelingSlots.labelEraserValue)
            
            self._gui = CarvingGui( labelingSlots, [self.carvingOperator.segmentation], rawInputSlot=self.topLevelOperator.InputImages, carvingApplet=self )
        return self._gui

class CarvingWorkflow(Workflow):
    
    def __init__(self):
        super(CarvingWorkflow, self).__init__()
        self._applets = []

        # Create a graph to be shared by all operators
        graph = Graph()
        self._graph = graph

        labeling = True
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(graph)

        self.viewerApplet.topLevelOperator.RawInput.connect( self.dataSelectionApplet.topLevelOperator.Image )
       
        if labeling:
            self.labelingApplet = CarvingApplet(graph, "xxx")
            self.labelingApplet.topLevelOperator.InputImages.connect( self.dataSelectionApplet.topLevelOperator.Image )
            self.labelingApplet.topLevelOperator.LabelsAllowedFlags.connect( self.dataSelectionApplet.topLevelOperator.AllowLabels )
            self.labelingApplet.gui.minLabelNumber = 2
            self.labelingApplet.gui.maxLabelNumber = 2

        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator
        
        ## Connect operators ##
        
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.viewerApplet)
        if labeling:
            self._applets.append(self.labelingApplet)

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

def debug_tk(shell, workflow):
    """
    (Function for debug and testing.)
    """
    # Open a project
    shell.openProjectFile("carving_40nm.ilp")

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(3)

def debug_with_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    #info.filePath = '/magnetic/gigacube.h5'
    info.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
        
    # Save the project
    shell.onSaveProjectActionTriggered()

if __name__ == "__main__":

    import lazyflow
    import numpy
    graph = lazyflow.graph.Graph()
    
    data = numpy.random.random( (1,11,12,13,1) )
    op = OpVolumeExtractor(graph=graph)
    op.Input.setValue(data)
    out = op.Output[0:11, 0:12, 0:13].wait()
    assert out.shape == (11,12,13)
    assert (out[...] == data[0,...,0]).all()
    
    from ilastik.shell.gui.startShellGui import startShellGui
    import socket
    
    # Start the GUI
    
    #startShellGui( CarvingWorkflow )

    # Start the GUI with a debug project    
    if socket.gethostname() == "carsten":
        #Thorben debugging stuff
        startShellGui( CarvingWorkflow, debug_tk )    
    else:
        startShellGui( CarvingWorkflow, debug_with_new )    
