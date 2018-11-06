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
from __future__ import division
from builtins import range
import sys
import copy
import argparse
import itertools
import logging
logger = logging.getLogger(__name__)

import numpy

from ilastik.config import cfg as ilastik_config
from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.domainAdaptation import DomainAdaptationApplet
from ilastik.applets.pixelClassification import PixelClassificationApplet, PixelClassificationDataExportApplet
from ilastik.applets.batchProcessing import BatchProcessingApplet

from lazyflow.graph import Graph
from lazyflow.roi import TinyVector, fullSlicing

class DomainAdaptationWorkflow(Workflow):
    workflowName = "Domain Adaptation"
    workflowDescription = "Domain adaptation with neural networks"
    defaultAppletIndex = 0

    DATA_ROLE_RAW_TARGET = 0
    DATA_ROLE_RAW_SOURCE = 1
    DATA_ROLE_GROUND_TRUTH_SOURCE = 2
    ROLE_NAMES = ['Raw Data (Target Domain)', 'Raw Data (Source Domain)', 'Ground Truth Data (Source Domain)']
    EXPORT_NAMES = ['Probabilities']

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        graph = Graph()
        super(DomainAdaptationWorkflow, self).__init__(shell, workflow_cmdline_args, project_creation_args,
                                                       graph=graph, *args, **kwargs)
        self._applets = []
        self._workflow_cmdline_args = workflow_cmdline_args

        # Parse workflow-specific command-line args.
        parser = argparse.ArgumentParser()

        # Parse the creation args: These were saved to the project file when this project was first created.
        parsed_creation_args, unused_args = parser.parse_known_args(project_creation_args)

        # Applets
        self.dataSelectionApplet = self.createDataSelectionApplet()
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        opDataSelection.DatasetRoles.setValue(DomainAdaptationWorkflow.ROLE_NAMES)

        self.daApplet = self.createDomainAdaptationApplet()
        opDomainAdaptation = self.daApplet.topLevelOperator

        self.dataExportApplet = DataExportApplet(self, "Data Export")
        opDataExport = self.dataExportApplet.topLevelOperator
        opDataExport.WorkingDirectory.connect(opDataSelection.WorkingDirectory)
        opDataExport.SelectionNames.setValue(self.EXPORT_NAMES)

        # Expose applets in a list (for the shell to use)
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.daApplet)
        self._applets.append(self.dataExportApplet)

        # Parse command-line arguments
        # Command-line args are applied in on ProjectLoaded(), below.
        if workflow_cmdline_args:
            self._batch_input_args, unused_args = self.dataSelectionApplet.parse_known_cmdline_args(unused_args, ROLE_NAMES)
        else:
            unused_args = None
            self._batch_input_args = None

        if unused_args:
            logger.warning("Unused command-line args: {}".format(unused_args))

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def createDomainAdaptationApplet(self):
        return DomainAdaptationApplet(self, "DomainAdaptation")

    def createDataSelectionApplet(self):
        """
        Can be overridden by subclasses, if they want to use
        special parameters to initialize the DataSelectionApplet.
        """
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        c_at_end = ['yxc', 'xyc']
        for perm in itertools.permutations('tzyx', 3):
            c_at_end.append(''.join(perm) + 'c')
        for perm in itertools.permutations('tzyx', 4):
            c_at_end.append(''.join(perm) + 'c')

        return DataSelectionApplet(workflow=self,
                                   title="Input Data",
                                   projectFileGroupName="Input Data",
                                   supportIlastik05Import=True,
                                   instructionText=data_instructions,
                                   forceAxisOrder=c_at_end)

    def prepareForNewLane(self, laneIndex):
        opDomainAdaptation = self.daApplet.topLevelOperator
        if opDomainAdaptation.classifier_cache.Output.ready() and opDomainAdaptation.classifier_cache._dirty:
            self.stored_classifier = opDomainAdaptation.classifier_cache.Output.value
        else:
            self.stored_classifier = None

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opDomainAdaptation = self.daApplet.topLevelOperator.getLane(laneIndex)

        # Input Image -> Classification Operator
        opDomainAdaptation.InputImages.connect(opData.Image)

    def handleNewLanesAdded(self):
        if self.stored_classifier:
            self.daApplet.topLevelOperator.classifier_cache.forceValue(self.stored_classifier)
            self.stored_classifier = None

    def onProjectLoaded(self, projectManager):
        pass

    def handleAppletStateUpdateRequested(self):
        opDataSelection = self.dataSelectionApplet.topLevelOperator
        input_ready = len(opDataSelection.ImageGroup) > 0

        opDomainAdaptation = self.daApplet.topLevelOperator

        invalid_classifier = opDomainAdaptation.classifier_cache.fixAtCurrent.value and \
                             opDomainAdaptation.classifier_cache.Output.ready() and \
                             opDomainAdaptation.classifier_cache.Output.value is None

        prediction_ready = not invalid_classifier

        live_update_active = not opDomainAdaptation.FreezePredictions.value

        self._shell.setAppletEnabled(self.dataSelectionApplet, not live_update_active)
        self._shell.setAppletEnabled(self.daApplet, input_ready)

        busy = False
        busy |= self.dataSelectionApplet.busy
        self._shell.enableProjectChanges(not busy)
