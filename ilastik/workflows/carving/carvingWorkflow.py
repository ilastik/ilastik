###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
#lazyflow
from lazyflow.graph import Graph
from lazyflow.operators.opReorderAxes import OpReorderAxes

#ilastik
from ilastik.workflow import Workflow
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet

#this workflow: carving
from carvingApplet import CarvingApplet
from preprocessingApplet import PreprocessingApplet

#===----------------------------------------------------------------------------------------------------------------===

class CarvingWorkflow(Workflow):
    
    workflowName = "Carving"
    defaultAppletIndex = 1 # show DataSelection by default
    
    @property
    def applets(self):
        return self._applets
    
    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, hintoverlayFile=None, pmapoverlayFile=None, *args, **kwargs):
        if hintoverlayFile is not None:
            assert isinstance(hintoverlayFile, str), "hintoverlayFile should be a string, not '%s'" % type(hintoverlayFile)
        if pmapoverlayFile is not None:
            assert isinstance(pmapoverlayFile, str), "pmapoverlayFile should be a string, not '%s'" % type(pmapoverlayFile)

        graph = Graph()
        
        super(CarvingWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        
        ## Create applets 
        self.projectMetadataApplet = ProjectMetadataApplet()
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        supportIlastik05Import=True,
                                                        batchDataGui=False,
                                                        instructionText=data_instructions,
                                                        max_lanes=1 )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ['Raw Data'] )
        
        
        
        self.preprocessingApplet = PreprocessingApplet(workflow=self,
                                           title = "Preprocessing",
                                           projectFileGroupName="preprocessing")
        
        self.carvingApplet = CarvingApplet(workflow=self,
                                           projectFileGroupName="carving",
                                           hintOverlayFile=hintoverlayFile,
                                           pmapOverlayFile=pmapoverlayFile)
        
        #self.carvingApplet.topLevelOperator.MST.connect(self.preprocessingApplet.topLevelOperator.PreprocessedData)
        
        # Expose to shell
        self._applets = []
        self._applets.append(self.projectMetadataApplet)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.preprocessingApplet)
        self._applets.append(self.carvingApplet)
        
    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
        opCarvingLane = self.carvingApplet.topLevelOperator.getLane(laneIndex)
        
        opCarvingLane.connectToPreprocessingApplet(self.preprocessingApplet)
        op5 = OpReorderAxes(parent=self)
        op5.AxisOrder.setValue("txyzc")
        op5.Input.connect(opData.Image)

        ## Connect operators
        opPreprocessing.InputData.connect(op5.Output)
        #opCarvingTopLevel.RawData.connect(op5.output)
        opCarvingLane.InputData.connect(op5.Output)
        opCarvingLane.FilteredInputData.connect(opPreprocessing.FilteredImage)
        opCarvingLane.MST.connect(opPreprocessing.PreprocessedData)
        opCarvingLane.UncertaintyType.setValue("none")
        
        # Special input-input connection: WriteSeeds metadata must mirror the input data
        opCarvingLane.WriteSeeds.connect( opCarvingLane.InputData )
        
        self.preprocessingApplet.enableDownstream(False)

    def handleAppletStateUpdateRequested(self):
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0

        # If preprocessing isn't configured yet, don't allow carving
        preprocessed_data_ready = input_ready and self.preprocessingApplet._enabledDS
        
        # Enable each applet as appropriate
        self._shell.setAppletEnabled(self.preprocessingApplet, input_ready)
        self._shell.setAppletEnabled(self.carvingApplet, preprocessed_data_ready)
        