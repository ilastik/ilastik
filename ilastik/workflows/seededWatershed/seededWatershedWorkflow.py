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
import copy
import argparse
import collections
import logging
logger = logging.getLogger(__name__)

import numpy

from lazyflow.graph import Graph
from ilastik.workflow import Workflow
from lazyflow.utility.jsonConfig import JsonConfigParser
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.applets.seededWatershed import SeededWatershedApplet

ROLE_RAW = 0
ROLE_PROBABILITIES = 1
ROLE_INPUT_SEGMENTATION = 2

ParameterFileSchema = \
{
    "_schema_name" : "seeded watershed paramters",
    "_schema_version" : 0.1,
    
    # Input data
    "raw_data_info" : JsonConfigParser( DatasetInfo.DatasetInfoSchema ),
    "pixel_probabilities_info" : JsonConfigParser( DatasetInfo.DatasetInfoSchema ),
    "undersegmentation_info" : JsonConfigParser( DatasetInfo.DatasetInfoSchema ),
    
    "available_body_ids" : numpy.array,
    
    "focus_coordinates" : dict # e.g. {"x" : 100, "y" : 200, "z" : 300}
}


class SeededWatershedWorkflow(Workflow):
    def __init__( self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(SeededWatershedWorkflow, self).__init__( shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs )
        self._applets = []

        # Create applets
        self.dataSelectionApplet = DataSelectionApplet(self, 
                                                       "Input Data", 
                                                       "Input Data", 
                                                       supportIlastik05Import=True, 
                                                       batchDataGui=False,
                                                       force5d=True)
        self.seededWatershedApplet = SeededWatershedApplet(self, "Seeded Watershed")

        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue( ["Raw Data", "Probabilities", "Input Segmentation"] )

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.seededWatershedApplet )

        # Command-line args
        self._workflow_parameters = None
        if workflow_cmdline_args:
            arg_parser = argparse.ArgumentParser(description="Specify parameters for the seeded segmentation workflow")
            arg_parser.add_argument('--parameter-file', required=False)
            parsed_args, unused_args = arg_parser.parse_known_args(workflow_cmdline_args)
            if unused_args:
                logger.warn("Unused command-line args: {}".format( unused_args ))

            if parsed_args.parameter_file is None:
                logger.warn("Missing cmd-line arg: --parameter-file")
            else:
                logger.debug("Parsing split tool parameters: {}".format( parsed_args.parameter_file ))
                json_parser = JsonConfigParser( ParameterFileSchema )
                try:
                    self._workflow_parameters = json_parser.parseConfigFile( parsed_args.parameter_file )
                except ValueError as ex:
                    logger.error("Could not parse JSON config file:\n" + str(ex))


    def connectLane(self, laneIndex):
        opDataSelection = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opSeededWatershed = self.seededWatershedApplet.topLevelOperator.getLane(laneIndex)
        
        # Connect top-level operators
        opSeededWatershed.InputImage.connect( opDataSelection.ImageGroup[ROLE_RAW] )
        opSeededWatershed.Probabilities.connect( opDataSelection.ImageGroup[ROLE_PROBABILITIES] )
        opSeededWatershed.UndersegmentedLabels.connect( opDataSelection.ImageGroup[ROLE_INPUT_SEGMENTATION] )
        opSeededWatershed.LabelsAllowedFlag.setValue(True)
        opSeededWatershed.FreezeCache.setValue(True)
        opSeededWatershed.AvailableLabelIds.setValue( [999999999,999999998,999999997,999999996,999999995] )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def onProjectLoaded(self, projectManager):
        """
        Overridden from Workflow base class.  Called by the Project Manager.
        
        - Use the parameter json file provided on the command line to populate the project's input data settings.
        - Save the project.
        """
        if self._workflow_parameters is None:
            return
        
        workflow_params = self._workflow_parameters
        
        # -- Data Selection
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        
        # If there is already data in this project, don't touch it.
        if len(opDataSelection.DatasetGroup) > 0:
            logger.warn("Not changing project data, because your project appears to have data already.")
        else:
            opDataSelection.DatasetGroup.resize(1)
            for role, dataset_info_namespace in [ ( ROLE_RAW,                workflow_params.raw_data_info ),
                                                  ( ROLE_PROBABILITIES,      workflow_params.pixel_probabilities_info ),
                                                  ( ROLE_INPUT_SEGMENTATION, workflow_params.undersegmentation_info ) ]:
                self.dataSelectionApplet.configureRoleFromJson( lane=0,
                                                                role=role,
                                                                dataset_info_namespace=dataset_info_namespace )
            logger.info("Saving project...")
            projectManager.saveProject()
        
        # -- Seeded Watershed
        opSeededWatershed = self.seededWatershedApplet.topLevelOperator.getLane(0)
        
        if workflow_params.focus_coordinates:
            focus_coordinates = copy.copy(workflow_params.focus_coordinates)

            # Focus coordinates are provided in DVID coordinate space
            # Offset the focus coordinates for the subvolume in our viewer
            if workflow_params.raw_data_info.subvolume_roi:
                volume_axistags = opDataSelection.getLane(0).ImageGroup[ROLE_RAW].meta.original_axistags
                axis_keys = [tag.key for tag in volume_axistags]
                offset = workflow_params.raw_data_info.subvolume_roi[0]
                tagged_offset = collections.OrderedDict( zip( axis_keys, offset ) )
                for k in focus_coordinates.keys():
                    focus_coordinates[k] -= tagged_offset[k]

                subvolume_stop = workflow_params.raw_data_info.subvolume_roi[1]
                tagged_stop = collections.OrderedDict( zip( axis_keys, subvolume_stop ) )
                
                for k in focus_coordinates.keys():
                    if ( focus_coordinates[k] < 0 or
                         focus_coordinates[k] >= tagged_stop[k] ):
                        msg = "The focus coordinate in your parameter file appears to be out-of-range for the subvolume you want to view:\n"
                        msg += "focus_coordinates = {}\n".format( workflow_params.focus_coordinates )
                        msg += "subvolume start = {}\n".format( dict(tagged_offset) )
                        msg += "subvolume stop = {}\n".format( dict(tagged_stop) )
                        raise Exception(msg)
                
            opSeededWatershed.FocusCoordinates.setValue( focus_coordinates )
        
        if workflow_params.available_body_ids is not None:
            opSeededWatershed.AvailableLabelIds.setValue( workflow_params.available_body_ids )

        # Create some label classes
        opSeededWatershed.LabelNames.setValue( ['Label 1', 'Label 2'] )
        opSeededWatershed.LabelColors.setValue( [(255,0,0), (0,255,0)] )

        projectManager.saveProject()

        # Open the seeded watershed applet
        # FIXME: This is called too early: the applet guis haven't been created yet!
        # self._shell.setSelectedAppletDrawer(1)

        logger.info("FINISHED")

