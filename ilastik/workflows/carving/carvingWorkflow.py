from __future__ import absolute_import
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
import argparse
import logging
logger = logging.getLogger(__name__)

#lazyflow
from lazyflow.graph import Graph
from lazyflow.operators.opReorderAxes import OpReorderAxes

#ilastik
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet

#this workflow: carving
from .carvingApplet import CarvingApplet
from .preprocessingApplet import PreprocessingApplet
from ilastik.workflows.carving.opPreprocessing import OpPreprocessing, OpFilter

#===----------------------------------------------------------------------------------------------------------------===

DATA_ROLES = ['Raw Data', 'Overlay']
DATA_ROLE_RAW_DATA = 0
DATA_ROLE_OVERLAY = 1

class CarvingWorkflow(Workflow):
    
    workflowName = "Carving"
    defaultAppletIndex = 0 # show DataSelection by default
    
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
        self.workflow_cmdline_args = workflow_cmdline_args
        
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right.\n\n"\
                            "Additionally, you may optionally add an 'Overlay' data volume if it helps you annotate. (It won't be used for any computation.)"
        
        ## Create applets 
        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        supportIlastik05Import=True,
                                                        batchDataGui=False,
                                                        instructionText=data_instructions,
                                                        max_lanes=1 )
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( DATA_ROLES )
        
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
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.preprocessingApplet)
        self._applets.append(self.carvingApplet)

    def connectLane(self, laneIndex):
        ## Access applet operators
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(laneIndex)
        opCarvingLane = self.carvingApplet.topLevelOperator.getLane(laneIndex)
        
        opCarvingLane.connectToPreprocessingApplet(self.preprocessingApplet)

        op5Raw = OpReorderAxes(parent=self)
        op5Raw.AxisOrder.setValue("txyzc")
        op5Raw.Input.connect( opData.ImageGroup[DATA_ROLE_RAW_DATA] )

        op5Overlay = OpReorderAxes(parent=self)
        op5Overlay.AxisOrder.setValue("txyzc")
        op5Overlay.Input.connect( opData.ImageGroup[DATA_ROLE_OVERLAY] )

        ## Connect operators
        opPreprocessing.InputData.connect(op5Raw.Output)
        opPreprocessing.OverlayData.connect(op5Overlay.Output)

        opCarvingLane.InputData.connect(op5Raw.Output)
        opCarvingLane.OverlayData.connect(op5Overlay.Output)
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

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.

        If the user provided command-line arguments, apply them to the workflow operators.
        Currently, we support command-line configuration of:
        - DataSelection
        - Preprocessing, in which case preprocessing is immediately executed
        """
        # If input data files were provided on the command line, configure the DataSelection applet now.
        # (Otherwise, we assume the project already had a dataset selected.)
        input_data_args, unused_args = DataSelectionApplet.parse_known_cmdline_args(self.workflow_cmdline_args, DATA_ROLES)
        if input_data_args.raw_data:
            self.dataSelectionApplet.configure_operator_with_parsed_args(input_data_args)

        #
        # Parse the remaining cmd-line arguments
        #
        filter_indexes = { 'bright-lines' : OpFilter.HESSIAN_BRIGHT,
                           'dark-lines'   : OpFilter.HESSIAN_DARK,
                           'step-edges'   : OpFilter.STEP_EDGES,
                           'original'     : OpFilter.RAW,
                           'inverted'     : OpFilter.RAW_INVERTED }

        parser = argparse.ArgumentParser()
        parser.add_argument('--run-preprocessing', action='store_true')
        parser.add_argument('--preprocessing-sigma', type=float, required=False)
        parser.add_argument('--preprocessing-filter', required=False, type=str.lower,
                            choices=list(filter_indexes.keys()))

        parsed_args, unused_args = parser.parse_known_args(unused_args)
        if unused_args:
            logger.warning("Did not use the following command-line arguments: {}".format(unused_args))

        # Execute pre-processing.
        if parsed_args.run_preprocessing:
            if len(self.preprocessingApplet.topLevelOperator) != 1:
                raise RuntimeError("Can't run preprocessing on a project with no images.")

            opPreprocessing = self.preprocessingApplet.topLevelOperator.getLane(0) # Carving has only one 'lane'

            # If user provided parameters, override the defaults.
            if parsed_args.preprocessing_sigma is not None:
                opPreprocessing.Sigma.setValue(parsed_args.preprocessing_sigma)

            if parsed_args.preprocessing_filter:
                filter_index = filter_indexes[parsed_args.preprocessing_filter]
                opPreprocessing.Filter.setValue(filter_index)

            logger.info("Running Preprocessing...")
            opPreprocessing.PreprocessedData[:].wait()
            logger.info("FINISHED Preprocessing...")

            logger.info("Saving project...")
            self._shell.projectManager.saveProject()
            logger.info("Done saving.")
