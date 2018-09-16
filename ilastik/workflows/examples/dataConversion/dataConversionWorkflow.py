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
import logging
logger = logging.getLogger(__name__)

from lazyflow.roi import TinyVector
from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

RAW_DATA_ROLE_INDEX = 0


class DataConversionWorkflow(Workflow):
    """
    Simple workflow for converting data between formats.
    Has only two 'interactive' applets (Data Selection and Data Export), plus the BatchProcessing applet.    

    Supports headless mode. For example:
    
    .. code-block::

        python ilastik.py --headless 
                          --new_project=NewTemporaryProject.ilp
                          --workflow=DataConversionWorkflow
                          --output_format="png sequence"
                          ~/input1.h5
                          ~/input2.h5

    .. note:: Beware of issues related to absolute vs. relative paths.
              Relative links are stored relative to the project file.

              To avoid this issue entirely, either 
                 (1) use only absolute filepaths
              or (2) cd into your project file's directory before launching ilastik.
    
    """
    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):

        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(DataConversionWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self._applets = []

        # Instantiate DataSelection applet
        self.dataSelectionApplet = DataSelectionApplet(
            self,
            "Input Data",
            "Input Data",
            supportIlastik05Import=True,
            forceAxisOrder=None)

        # Configure global DataSelection settings
        role_names = ["Input Data"]
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( role_names )

        # Instantiate DataExport applet
        self.dataExportApplet = DataExportApplet(self, "Data Export")

        # Configure global DataExport settings
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( ["Input"] )        

        # No special data pre/post processing necessary in this workflow, 
        #   but this is where we'd hook it up if we needed it.
        #
        #self.dataExportApplet.prepare_for_entire_export = self.prepare_for_entire_export
        #self.dataExportApplet.prepare_lane_for_export = self.prepare_lane_for_export
        #self.dataExportApplet.post_process_lane_export = self.post_process_lane_export
        #self.dataExportApplet.post_process_entire_export = self.post_process_entire_export

        # Instantiate BatchProcessing applet
        self.batchProcessingApplet = BatchProcessingApplet(self, 
                                                           "Batch Processing", 
                                                           self.dataSelectionApplet, 
                                                           self.dataExportApplet)

        # Expose our applets in a list (for the shell to use)
        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.dataExportApplet )
        self._applets.append(self.batchProcessingApplet)

        # Parse command-line arguments
        # Command-line args are applied in onProjectLoaded(), below.
        if workflow_cmdline_args:
            self._data_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( workflow_cmdline_args )
            self._batch_input_args, unused_args = self.dataSelectionApplet.parse_known_cmdline_args( unused_args, role_names )
        else:
            unused_args = None
            self._batch_input_args = None
            self._data_export_args = None

        if unused_args:
            logger.warning("Unused command-line args: {}".format( unused_args ))

    @property
    def applets(self):
        """
        Overridden from Workflow base class.
        """
        return self._applets

    @property
    def imageNameListSlot(self):
        """
        Overridden from Workflow base class.
        """
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def prepareForNewLane(self, laneIndex):
        """
        Overridden from Workflow base class.
        Called immediately before connectLane()
        """
        # No preparation necessary.
        pass

    def connectLane(self, laneIndex):
        """
        Overridden from Workflow base class.
        """
        # Get a *view* of each top-level operator, specific to the current lane.
        opDataSelectionView = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opDataExportView = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        # Now connect the operators together for this lane.
        # Most workflows would have more to do here, but this workflow is super simple:
        # We just connect input to export
        opDataExportView.RawDatasetInfo.connect( opDataSelectionView.DatasetGroup[RAW_DATA_ROLE_INDEX] )        
        opDataExportView.Inputs.resize( 1 )
        opDataExportView.Inputs[RAW_DATA_ROLE_INDEX].connect( opDataSelectionView.ImageGroup[RAW_DATA_ROLE_INDEX] )

        # There is no special "raw" display layer in this workflow.
        #opDataExportView.RawData.connect( opDataSelectionView.ImageGroup[0] )

    def handleNewLanesAdded(self):
        """
        Overridden from Workflow base class.
        Called immediately AFTER connectLane() and the dataset is loaded into the workflow.
        """
        # No special handling required.
        pass

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
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
        """
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0

        opDataExport = self.dataExportApplet.topLevelOperator
        export_data_ready = input_ready and \
                            len(opDataExport.Inputs[0]) > 0 and \
                            opDataExport.Inputs[0][0].ready() and \
                            (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        self._shell.setAppletEnabled(self.dataSelectionApplet, not self.batchProcessingApplet.busy)
        self._shell.setAppletEnabled(self.dataExportApplet, export_data_ready and not self.batchProcessingApplet.busy)
        self._shell.setAppletEnabled(self.batchProcessingApplet, export_data_ready)
        
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        busy |= self.batchProcessingApplet.busy
        self._shell.enableProjectChanges( not busy )
