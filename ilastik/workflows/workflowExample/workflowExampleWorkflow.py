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
#           http://ilastik.org/license.html
###############################################################################
import numpy as np

from ilastik.workflow import Workflow
from lazyflow.graph import Graph

#add applets
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

#example applet TODO 
from ilastik.applets.appletExample import AppletExampleApplet



class WorkflowExampleWorkflow(Workflow): #TODO 
    workflowName = "Workflow Example"
    workflowDescription = "A short example to get an impression of how a workflow works"
    defaultAppletIndex = 0 # show DataSelection by default

    DATA_ROLE_RAW = 0
    DATA_ROLE_PROBABILITIES = 1
    ROLE_NAMES = ['Raw Data', 'Probabilities']
    EXPORT_NAMES = ['workflowExample']

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_workflow, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()

        #call the __init__ of its upperclass, here Workflow
        super(WorkflowExampleWorkflow, self).__init__( shell, headless, workflow_cmdline_args, project_creation_workflow, graph=graph, *args, **kwargs) #TODO


        #################################################################
        # Create the added applets
        #################################################################
        self._applets = []

        # -- DataSelection applet
        #
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data")

        # Dataset inputs
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( self.ROLE_NAMES )


        # -- appletExample TODO
        #
        # first Parameter after self is the Name of the Applet, that will be displayed
        self.appletExampleApplet = AppletExampleApplet(self, "Workflow Example", "Example Applet Gui Name")

        # -- DataExport applet
        #
        self.dataExportApplet = DataExportApplet(self, "Data Export")

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )

        # -- BatchProcessing applet
        #
        self.batchProcessingApplet = BatchProcessingApplet(self,
                                                           "Batch Processing",
                                                           self.dataSelectionApplet,
                                                           self.dataExportApplet)

        # -- Expose applets to shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.appletExampleApplet) #TODO
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)

        # -- Parse command-line arguments
        #    (Command-line args are applied in onProjectLoaded(), below.)
        if workflow_cmdline_args:
            self._data_export_args, unused_args = \
                    self.dataExportApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = \
                    self.dataSelectionApplet.parse_known_cmdline_args( unused_args, role_names )
        else:
            unused_args = None
            self._batch_input_args = None
            self._data_export_args = None

        if unused_args:
            logger.warn("Unused command-line args: {}".format( unused_args ))

    def connectLane(self, laneIndex):
        """
        Override from base class.
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opAppletExample = self.appletExampleApplet.topLevelOperator.getLane(laneIndex) #TODO
        opDataExport    = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Apllet Example inputs #TODO
        opAppletExample.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] ) #TODO
        opAppletExample.Input.connect( opDataSelection.ImageGroup[self.DATA_ROLE_PROBABILITIES] ) #TODO

        # DataExport inputs
        opDataExport.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opDataSelection.DatasetGroup[self.DATA_ROLE_RAW] )        
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opAppletExample.Superpixels ) #TODO
        for slot in opDataExport.Inputs:
            assert slot.partner is not None
        
    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow inputs and output settings.
        """
        # Configure the data export operator.
        if self._data_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._data_export_args )

        if self._headless and self._batch_input_args and self._data_export_args:
            logger.info("Beginning Batch Processing")
            self.batchProcessingApplet.run_export_from_parsed_args(self._batch_input_args)
            logger.info("Completed Batch Processing")


    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.appletStateUpdateRequested`
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataExport    = self.dataExportApplet.topLevelOperator
        opAppletExample = self.appletExampleApplet.topLevelOperator #TODO

        # If no data, nothing else is ready.
        input_ready = len(opDataSelection.ImageGroup) > 0 and not self.dataSelectionApplet.busy

        # The user isn't allowed to touch anything while batch processing is running.
        batch_processing_busy = self.batchProcessingApplet.busy

        self._shell.setAppletEnabled( self.dataSelectionApplet,   not batch_processing_busy )
        self._shell.setAppletEnabled( self.dataExportApplet,      not batch_processing_busy \
                and input_ready and opAppletExample.Superpixels.ready()) #TODO

        # Lastly, check for certain "busy" conditions, during which we
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )


    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName


