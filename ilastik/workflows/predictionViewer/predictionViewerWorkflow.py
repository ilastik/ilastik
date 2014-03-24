# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ilastik.workflow import Workflow

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.predictionViewer import PredictionViewerApplet

from lazyflow.graph import Graph

class PredictionViewerWorkflow(Workflow):

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName

    def __init__(self, shell, headless, workflow_cmdline_args, appendBatchOperators=True, *args, **kwargs):
        # Create a graph to be shared by all operators
        graph = Graph()
        super(PredictionViewerWorkflow, self ).__init__( shell, headless, graph=graph, *args, **kwargs )
        self._applets = []

        # Applets for training (interactive) workflow 
        self.dataSelectionApplet = DataSelectionApplet(self, "Viewed Predictions", "Viewed Predictions", supportIlastik05Import=False, batchDataGui=False)
        self.viewerApplet = PredictionViewerApplet(self)

        # Expose for shell
        self._applets.append(self.dataSelectionApplet)
        self._applets.append(self.viewerApplet)

    def connectLane(self, laneIndex):
        # Get a handle to each operator lane
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opViewer = self.viewerApplet.topLevelOperator.getLane(laneIndex)

        opViewer.PredictionProbabilities.connect( opData.Image )