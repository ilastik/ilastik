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
import os
import warnings
import argparse

from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet

from lazyflow.graph import Graph, OperatorWrapper

from connectedComponentsApplet import ConnectedComponentsApplet

import logging
logger = logging.getLogger(__name__)


class ConnectedComponentsWorkflow(Workflow):
    workflowName = "Connected Components Testing"
    defaultAppletIndex = 0 # show DataSelection by default

    def __init__(self, shell, headless,
                 workflow_cmdline_args,
                 project_creation_args,
                 *args, **kwargs):
        graph = kwargs['graph'] if 'graph' in kwargs else Graph()
        if 'graph' in kwargs:
            del kwargs['graph']
        super(ConnectedComponentsWorkflow, self).__init__(shell, headless, workflow_cmdline_args, project_creation_args, graph=graph, *args, **kwargs)

        self._applets = []
        self.setupInputs()

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def connectLane(self, laneIndex):
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)

        opCC = self.CCApplet.topLevelOperator.getLane(laneIndex)
        opCC.Input.connect(opData.ImageGroup[0])

    def _inputReady(self, nRoles):
        slot = self.dataSelectionApplet.topLevelOperator.ImageGroup
        if len(slot) > 0:
            input_ready = True
            for sub in slot:
                input_ready = input_ready and \
                    all([sub[i].ready() for i in range(nRoles)])
        else:
            input_ready = False

        return input_ready

    def setupInputs(self):
        data_instructions = 'Use the "Segmentation" tab to load your volume.'

        self.dataSelectionApplet = DataSelectionApplet( self,
                                                        "Input Data",
                                                        "Input Data",
                                                        batchDataGui=False,
                                                        force5d=True,
                                                        instructionText=data_instructions )

        opData = self.dataSelectionApplet.topLevelOperator
        opData.DatasetRoles.setValue(['Segmentation'])
        self._applets.append(self.dataSelectionApplet)

        self.CCApplet = ConnectedComponentsApplet(self, "Connected Components")
        self._applets.append(self.CCApplet)

    def handleAppletStateUpdateRequested(self):
        input_ready = self._inputReady(1)

        self._shell.setAppletEnabled(self.CCApplet, input_ready)


if __name__ == "__main__":
    from sys import argv
    w = ConnectedComponentsWorkflow(True, argv)
