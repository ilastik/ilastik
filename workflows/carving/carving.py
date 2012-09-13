#!/usr/bin/env python

import os, numpy

from PyQt4.QtGui import QShortcut, QKeySequence
from PyQt4.QtGui import QColor

from ilastik.workflow import Workflow

from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet
from ilastik.applets.labeling.labelingApplet import LabelingApplet
from ilastik.applets.labeling.labelingGui import LabelingGui

from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot
from lazyflow.operators import OpAttributeSelector

from volumina.pixelpipeline.datasources import RelabelingArraySource, LazyflowSource
from volumina.layer import ColortableLayer
from volumina import adaptors

from cylemon.segmentation import MSTSegmentor

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

class OpCarving(Operator):
    name = "Carving"
    category = "interactive segmentation"
    
    # I n p u t s #
    
    #filename of the pre-processed carving graph file 
    CarvingGraphFile = InputSlot()
    
    #raw data on which carving works
    RawData      = InputSlot() 
    
    #write the seeds that the users draw into this slot 
    WriteSeeds   = InputSlot() 
    
    #trigger an update by writing into this slot
    Trigger      = InputSlot(value = numpy.zeros((1,), dtype=numpy.uint8))
   
    #number between 0.0 and 1.0 
    #bias of the background
    #FIXME: correct name?
    BackgroundPriority = InputSlot()
    
    #a number between 0 and 256
    #below the number, no background bias will be applied to the edge weights
    NoBiasBelow        = InputSlot()
    
    # O u t p u t s #
    
    Segmentation = OutputSlot()
    Supervoxels  = OutputSlot()
    
    def __init__(self, graph, carvinGraphFilename):
        super(OpCarving, self).__init__(graph)
        print "[Carving id=%d] CONSTRUCTOR" % id(self) 
        
        #
        # FIXME: this operator has state
        #
        self._mst = MSTSegmentor.loadH5(carvingGraphFilename,  "graph")
    
    def setupOutputs(self):
        self.Segmentation.meta.assignFrom(self.RawData.meta)
        self.Supervoxels.meta.assignFrom(self.RawData.meta)
        
        self.Trigger.meta.shape = (1,)
        self.Trigger.meta.dtype = numpy.uint8
    
    def execute(self, slot, roi, result):
        if self._mst is None:
            return
        sl = roi.toSlice()
        if slot == self.Segmentation:
            result[0,:,:,:,0] = self._mst.segmentation[sl[1:4]]
        elif slot == self.Supervoxels:
            result[0,:,:,:,0] = self._mst.regionVol[sl[1:4]]
        else:
            raise RuntimeError("unknown slot")
        return result    
    
    def setInSlot(self, slot, key, value):
        assert slot == self.WriteSeeds
        assert self._mst is not None
        
        #FIXME: Somehow, the labelingGui sends a value of 100 for the eraser,
        #       but the cython part of carving expects 255.
        #       Fix it here so that erasing of labels works.
        value = numpy.where(value == 100, 255, value[:])
        
        self._mst.seeds[key] = value
        
    def notifyDirty(self, slot, key):
        if slot == self.Trigger or slot == self.BackgroundPriority or slot == self.NoBiasBelow: 
            if self._mst is None:
                return 
            if not self.BackgroundPriority.ready():
                return
            if not self.NoBiasBelow.ready():
                return
            
            bgPrio = self.BackgroundPriority.value
            noBiasBelow = self.NoBiasBelow.value
            print "compute new carving results with bg priority = %f, no bias below %d" % (bgPrio, noBiasBelow)
           
            labelCount = 2
            
            params = dict()
            params["prios"] = [1.0, bgPrio, 1.0] 
            params["uncertainty"] = "none" 
            params["noBiasBelow"] = noBiasBelow 
            
            unaries =  numpy.zeros((self._mst.numNodes,labelCount+1)).astype(numpy.float32)
            #assert numpy.sum(self._mst.seeds > 2) == 0, "seeds > 2 at %r" % numpy.where(self._mst.seeds > 2)
            self._mst.run(unaries, **params)
            
            self.Segmentation.setDirty(slice(None))
        elif slot == self.CarvingGraphFile:
            fname = self.CarvingGraphFile.value
            print "[Carving id=%d] loading graph file %s" % (id(self), fname) 
            self._mst = MSTSegmentor.loadH5(fname,  "graph")
            
            self.Segmentation.setDirty(slice(None))
        else:
            super(OpCarving, self).notifyDirty(slot, key) 
    
#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

class CarvingGui(LabelingGui):
    def __init__(self, labelingSlots, observedSlots, drawerUiPath=None, rawInputSlot=None,
                 carvingApplet=None):
        # We provide our own UI file (which adds an extra control for interactive mode)
        print __file__
        directory = os.path.split(__file__)[0]
        carvingDrawerUiPath = os.path.join(directory, 'carvingDrawer.ui')

        super(CarvingGui, self).__init__(labelingSlots, observedSlots, carvingDrawerUiPath, rawInputSlot)
        self._carvingApplet = carvingApplet
        
        #set up keyboard shortcuts
        c = QShortcut(QKeySequence("Ctrl+S"), self, member=self.labelingDrawerUi.segment.click, ambiguousMember=self.labelingDrawerUi.segment.click)

        def onSegmentButton():
            print "segment button clicked"
            self._carvingApplet.opCarving.Trigger[0].setDirty(slice(None))
        self.labelingDrawerUi.segment.clicked.connect(onSegmentButton)
        
        def onBackgroundPrioritySpin(value):
            print "background priority changed to %f" % value
            self._carvingApplet.opCarving.BackgroundPriority.setValue(value)
        self.labelingDrawerUi.backgroundPrioritySpin.valueChanged.connect(onBackgroundPrioritySpin)
        
        def onNoBiasBelowSpin(value):
            print "background priority changed to %f" % value
            self._carvingApplet.opCarving.NoBiasBelow.setValue(value)
        self.labelingDrawerUi.noBiasBelowSpin.valueChanged.connect(onNoBiasBelowSpin)
        
    def getNextLabelName(self):
        l = len(self._labelControlUi.labelListModel)
        if l == 0:
            return "Background"
        else:
            return "Object"
        
    def appletDrawers(self):
        return [ ("Carving", self._labelControlUi) ]

    def setupLayers( self, currentImageIndex ):
        layers = []
        
        # Labels
        labellayer, labelsrc = self.createLabelLayer(currentImageIndex)
        if labellayer is not None:
            layers.append(labellayer)
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)
       
        #segmentation 
        #seg = self._carvingApplet._segmentation5D[currentImageIndex]
        seg = self._carvingApplet.opCarving.Segmentation[currentImageIndex]
        if seg.ready(): 
            #source = RelabelingArraySource(seg)
            #source.setRelabeling(numpy.arange(256, dtype=numpy.uint8))
            colortable = [QColor(0,0,0,0).rgba(), QColor(0,0,0,0).rgba(), QColor(0,255,0).rgba()]
            for i in range(256-len(colortable)):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            layer = ColortableLayer(LazyflowSource(seg), colortable)
            #layer = ColortableLayer(source, colortable)
            layer.name = "segmentation"
            layer.visible = True
            layer.opacity = 0.3
            layers.append(layer)
            
        #supervoxel
        sv = self._carvingApplet.opCarving.Supervoxels[currentImageIndex]
        if sv.ready():
            for i in range(256):
                r,g,b = numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)
                colortable.append(QColor(r,g,b).rgba())
            layer = ColortableLayer(LazyflowSource(sv), colortable)
            #layer = ColortableLayer(source, colortable)
            layer.name = "supervoxels"
            layer.visible = False
            layer.opacity = 1.0
            layers.append(layer)
        
        #raw data
        img = self._carvingApplet._inputImage[currentImageIndex]
        if img.ready():
            layer = self.createStandardLayerFromSlot( img )
            layer.name = "raw"
            layer.visible = True
            layer.opacity = 1.0
            #layers.insert(1, layer)
            layers.append(layer)
        
        return layers

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

class CarvingApplet(LabelingApplet):
    def __init__(self, graph, projectFileGroupName, raw, carvingGraphFile):
        super(CarvingApplet, self).__init__(graph, projectFileGroupName)

        self._raw = raw
       
        #
        # raw data
        # 
        o = OperatorWrapper( adaptors.Op5ifyer(graph) )
        o.order.setValue('txyzc')
        o.input.connect(self._raw)
        self._inputImage = o.output

        self.opCarving = OperatorWrapper( OpCarving(graph, carvingGraphFilename) )
        self.opCarving.RawData.connect(self._inputImage)
        self.opCarving.BackgroundPriority.setValue(0.95)
        self.opCarving.NoBiasBelow.setValue(64)
        #self.opCarving.CarvingGraphFile.setValue(carvingGraphFile)

        o = OperatorWrapper( adaptors.Op5ifyer(graph) )
        o.order.setValue('txyzc')
        o.input.connect(self.opCarving.Segmentation)
        self._segmentation5D = o.output
        assert self._segmentation5D is not None

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

            self.opCarving.WriteSeeds.connect(labelingSlots.labelInput)
            
            self._gui = CarvingGui( labelingSlots, [self._segmentation5D, self._inputImage], rawInputSlot=self._raw, carvingApplet=self )
        return self._gui

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

class CarvingWorkflow(Workflow):
    
    def __init__(self, carvingGraphFile):
        super(CarvingWorkflow, self).__init__()
        self._applets = []

        graph = Graph()
        self._graph = graph

        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(graph)

        self.carvingApplet = CarvingApplet(graph, "xxx", self.dataSelectionApplet.topLevelOperator.Image, carvingGraphFile)
        self.carvingApplet.topLevelOperator.InputImages.connect( self.dataSelectionApplet.topLevelOperator.Image )
        self.carvingApplet.topLevelOperator.LabelsAllowedFlags.connect( self.dataSelectionApplet.topLevelOperator.AllowLabels )
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
        opSelectFilename = OperatorWrapper( OpAttributeSelector(graph=graph) )
        opSelectFilename.InputObject.connect( opData.Dataset )
        opSelectFilename.AttributeName.setValue( 'filePath' )

        self._imageNameListSlot = opSelectFilename.Result

    def setCarvingGraphFile(self, fname):
        self.carvingApplet.opCarving.CarvingGraphFile.setValue(fname)

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

if __name__ == "__main__":
    import lazyflow
    import numpy
    from ilastik.shell.gui.startShellGui import startShellGui
    import socket
    
    graph = lazyflow.graph.Graph()
    
    from optparse import OptionParser
    usage = "%prog [options] <carving graph filename> <project filename to be created>"
    parser = OptionParser(usage)

    (options, args) = parser.parse_args()
    
    if len(args) == 2:
        carvingGraphFilename = args[0]
        projectFilename = args[1]
        def loadProject(shell, workflow):
            shell.createAndLoadNewProject(projectFilename)
            workflow.setCarvingGraphFile(carvingGraphFilename)
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = carvingGraphFilename + "/graph/raw"
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.Dataset.resize(1)
            opDataSelection.Dataset[0].setValue(info)
            shell.setSelectedAppletDrawer(2)
        startShellGui( CarvingWorkflow, loadProject, windowTitle="Carving %s" % carvingGraphFilename,
                       workflowKwargs={'carvingGraphFile': carvingGraphFilename} )
    else:
        parser.error("incorrect number of arguments")
