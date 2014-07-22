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
from lazyflow.roi import TinyVector

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer import LayerViewerApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

import logging
logger = logging.getLogger(__name__)

class LayerViewerWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(LayerViewerWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       supportIlastik05Import=True, 
                                                       batchDataGui=False,
                                                       force5d=True)
        self.viewerApplet = LayerViewerApplet(self)
        self.dataExportApplet = DataExportApplet(self, "Data Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.SelectionNames.setValue( ['Raw Data', 'Other Data'] )

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ["Raw Data", "Other Data"] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.viewerApplet )
        self._applets.append( self.dataExportApplet )

        self._workflow_cmdline_args = workflow_cmdline_args

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        """
        logger.info( "LayerViewerWorkflow Project was opened with the following args: " )
        logger.info( self._workflow_cmdline_args )

    def connectLane(self, laneIndex):
        opDataSelectionView = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opLayerViewerView = self.viewerApplet.topLevelOperator.getLane(laneIndex)
        opDataExportView = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Connect top-level operators                                                                                                                 
        opLayerViewerView.RawInput.connect( opDataSelectionView.ImageGroup[0] )
        opLayerViewerView.OtherInput.connect( opDataSelectionView.ImageGroup[1] )

        opDataExportView.RawData.connect( opDataSelectionView.ImageGroup[0] )
        opDataExportView.RawDatasetInfo.connect( opDataSelectionView.DatasetGroup[0] )        
        opDataExportView.WorkingDirectory.connect( opDataSelectionView.WorkingDirectory )

        opDataExportView.Inputs.resize(2)
        opDataExportView.Inputs[0].connect( opDataSelectionView.ImageGroup[0] )
        opDataExportView.Inputs[1].connect( opDataSelectionView.ImageGroup[1] )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def handleAppletStateUpdateRequested(self):
        """
        Overridden from Workflow base class
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
        """
        # If no data, nothing else is ready.
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0

        opDataExport = self.dataExportApplet.topLevelOperator
        export_data_ready = input_ready and \
                            len(opDataExport.Inputs) > 0 and \
                            opDataExport.Inputs[0][0].ready() and \
                            (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        self._shell.setAppletEnabled(self.viewerApplet, input_ready)
        self._shell.setAppletEnabled(self.dataExportApplet, export_data_ready)
        
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )

