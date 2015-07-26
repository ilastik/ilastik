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
import sys
import logging
logger = logging.getLogger(__name__)

from lazyflow.roi import TinyVector
from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet

class DataConversionWorkflow(Workflow):
    """
    Simple workflow for converting data between formats.  Has only two applets: Data Selection and Data Export.
    
    Also supports a command-line interface for headless mode.
    
    For example:
    
    .. code-block:: bash

        python ilastik.py --headless --new_project=NewTemporaryProject.ilp --workflow=DataConversionWorkflow --output_format="png sequence" ~/input1.h5 ~/input2.h5
    
    Or if you have an existing project with input files already selected and configured:

    .. code-block:: bash

        python ilastik.py --headless --project=MyProject.ilp --output_format=jpeg
    
    .. note:: Beware of issues related to absolute vs. relative paths.  Relative links are stored relative to the project file.
              To avoid this issue entirely, either 
                 (1) use only absolute filepaths
              or (2) cd into your project file's directory before launching ilastik.
    
    """
    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):

        
        # Create a graph to be shared by all operators
        graph = Graph()
        super(DataConversionWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)
        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       supportIlastik05Import=True, 
                                                       batchDataGui=False,
                                                       force5d=False)

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        role_names = ["Input Data"]
        opDataSelection.DatasetRoles.setValue( role_names )

        self.dataExportApplet = DataExportApplet(self, "Data Export")

        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect( opDataSelection.WorkingDirectory )
        opDataExport.SelectionNames.setValue( ["Input"] )        

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.dataExportApplet )

        # Parse command-line arguments
        # Command-line args are applied in onProjectLoaded(), below.
        self._workflow_cmdline_args = workflow_cmdline_args
        self._data_input_args = None
        self._data_export_args = None
        if workflow_cmdline_args:
            self._data_export_args, unused_args = self.dataExportApplet.parse_known_cmdline_args( unused_args )
            self._data_input_args, unused_args = self.dataSelectionApplet.parse_known_cmdline_args( workflow_cmdline_args, role_names )
            if unused_args:
                logger.warn("Unused command-line args: {}".format( unused_args ))

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        If the user provided command-line arguments, use them to configure 
        the workflow inputs and output settings.
        """
        # Configure the batch data selection operator.
        if self._data_input_args and self._data_input_args.input_files:
            self.dataSelectionApplet.configure_operator_with_parsed_args( self._data_input_args )
        
        # Configure the data export operator.
        if self._data_export_args:
            self.dataExportApplet.configure_operator_with_parsed_args( self._data_export_args )

        if self._headless and self._data_input_args and self._data_export_args:
            # Now run the export and report progress....
            opDataExport = self.dataExportApplet.topLevelOperator
            for i, opExportDataLaneView in enumerate(opDataExport):
                logger.info( "Exporting file #{} to {}".format(i, opExportDataLaneView.ExportPath.value) )
    
                sys.stdout.write( "Result #{}/{} Progress: ".format( i, len( opDataExport ) ) )
                def print_progress( progress ):
                    sys.stdout.write( "{} ".format( progress ) )
    
                # If the operator provides a progress signal, use it.
                slotProgressSignal = opExportDataLaneView.progressSignal
                slotProgressSignal.subscribe( print_progress )
                opExportDataLaneView.run_export()
                
                # Finished.
                sys.stdout.write("\n")

    def connectLane(self, laneIndex):
        opDataSelectionView = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opDataExportView = self.dataExportApplet.topLevelOperator.getLane(laneIndex)

        opDataExportView.RawDatasetInfo.connect( opDataSelectionView.DatasetGroup[0] )        
        opDataExportView.Inputs.resize( 1 )
        opDataExportView.Inputs[0].connect( opDataSelectionView.ImageGroup[0] )

        # There is no special "raw" display layer in this workflow.
        #opDataExportView.RawData.connect( opDataSelectionView.ImageGroup[0] )

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
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0

        opDataExport = self.dataExportApplet.topLevelOperator
        export_data_ready = input_ready and \
                            len(opDataExport.Inputs[0]) > 0 and \
                            opDataExport.Inputs[0][0].ready() and \
                            (TinyVector(opDataExport.Inputs[0][0].meta.shape) > 0).all()

        self._shell.setAppletEnabled(self.dataExportApplet, export_data_ready)
        
        # Lastly, check for certain "busy" conditions, during which we 
        #  should prevent the shell from closing the project.
        busy = False
        busy |= self.dataSelectionApplet.busy
        busy |= self.dataExportApplet.busy
        self._shell.enableProjectChanges( not busy )