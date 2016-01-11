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
from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.multicut import MulticutApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph

class MulticutWorkflow(Workflow):
    workflowName = "Multicut"
    workflowDescription = "A bare-bones workflow for testing the multicut applet"
    defaultAppletIndex = 1 # show DataSelection by default

    DATA_ROLE_RAW = 0
    DATA_ROLE_PROBABILITIES = 1
    DATA_ROLE_SUPERPIXELS = 2
    ROLE_NAMES = ['Raw Data', 'Probabilities', 'Superpixels']
    EXPORT_NAMES = ['Multicut Segmentation']

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_workflow, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()

        super(MulticutWorkflow, self).__init__( shell, headless, workflow_cmdline_args, project_creation_workflow, graph=graph, *args, **kwargs)
        self._applets = []

        # -- DataSelection applet
        #
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data")

        # Dataset inputs
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( self.ROLE_NAMES )

        # -- Multicut applet
        #
        self.multicutApplet = MulticutApplet(self, "Multicut Segmentation", "Multicut Segmentation")

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
        self._applets.append(self.multicutApplet)
        self._applets.append(self.dataExportApplet)
        self._applets.append(self.batchProcessingApplet)


    def connectLane(self, laneIndex):
        """
        Override from base class.
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opMulticut = self.multicutApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # multicut inputs
        opMulticut.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opMulticut.Probabilities.connect( opDataSelection.ImageGroup[self.DATA_ROLE_PROBABILITIES] )
        opMulticut.Superpixels.connect( opDataSelection.ImageGroup[self.DATA_ROLE_SUPERPIXELS] )

        # DataExport inputs
        opDataExport.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opDataSelection.DatasetGroup[self.DATA_ROLE_RAW] )        
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opMulticut.Output )
        for slot in opDataExport.Inputs:
            assert slot.partner is not None
        
