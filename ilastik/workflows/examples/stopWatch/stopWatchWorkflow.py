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

from lazyflow.graph import Graph, Operator, OutputSlot
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.stopWatch import StopWatchApplet

class OpName( Operator ):
    Output = OutputSlot(level=1)


class StopWatchWorkflow(Workflow):
    def __init__(self, shell, headless, workflow_cmdline_args, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(StopWatchWorkflow, self).__init__(shell, headless, graph=graph, *args, **kwargs)
        #self.name = OperatorWrapper(OpName( graph=graph)
        #self.name.Output[0].setValue("void")

        self._applets = []

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(self, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.stopWatchApplet = StopWatchApplet(self, "Stop Watch", "Stop Watch")

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.stopWatchApplet )

    def connectLane(self, laneIndex):
        pass
        ##opThresholdMasking.InputImage.connect( opDataSelection.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):

        #return self.name.Output
        return self.dataSelectionApplet.topLevelOperator.ImageName
