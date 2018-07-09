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
from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.thresholdMasking import ThresholdMaskingApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class ThresholdMaskingWorkflow(Workflow):

    DATA_ROLE_RAW = 0
    ROLE_NAMES = ['Raw Data']
    EXPORT_NAMES = ['Thresholded Output', 'Inverted Thresholded Output']

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(ThresholdMaskingWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.thresholdMaskingApplet = ThresholdMaskingApplet(self, "Thresholding", "Thresholding Stage 1")
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( self.ROLE_NAMES )

        # Instantiate DataExport applet
        self.dataExportApplet = DataExportApplet(self, "Data Export")

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( self.EXPORT_NAMES )


        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.thresholdMaskingApplet )
        self._applets.append( self.dataExportApplet )

    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)        
        opThresholdMasking = self.thresholdMaskingApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators
        opThresholdMasking.InputImage.connect( opDataSelection.Image )

        # Data Export connections
        opDataExport.RawData.connect( opDataSelection.ImageGroup[self.DATA_ROLE_RAW] )
        opDataExport.RawDatasetInfo.connect( opDataSelection.DatasetGroup[self.DATA_ROLE_RAW] )
        opDataExport.Inputs.resize( len(self.EXPORT_NAMES) )
        opDataExport.Inputs[0].connect( opThresholdMasking.Output )
        opDataExport.Inputs[1].connect( opThresholdMasking.InvertedOutput )

        # following assertion was copied from pixelClassificationWorkflow
        for slot in opDataExport.Inputs:
            assert slot.upstream_slot is not None

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
