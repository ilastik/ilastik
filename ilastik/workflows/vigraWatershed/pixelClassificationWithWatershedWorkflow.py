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

from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

class PixelClassificationWithWatershedWorkflow(PixelClassificationWorkflow):

    workflowName = "Pixel Classification (with Watershed Preview)"
    
    def __init__( self, shell, headless, workflow_cmdline_args, *args, **kwargs ):
        super(PixelClassificationWithWatershedWorkflow, self).__init__( shell, headless, workflow_cmdline_args, appendBatchOperators=False, *args, **kwargs )

        # Create applets
        self.watershedApplet = VigraWatershedViewerApplet(self, "Watershed", "Watershed")
        
        # Expose for shell
        self._applets.append(self.watershedApplet)

    def connectLane(self, laneIndex):
        super( PixelClassificationWithWatershedWorkflow, self ).connectLane( laneIndex )

        # Get the right lane from each operator
        opPixelClassification = self.pcApplet.topLevelOperator.getLane(laneIndex)
        opWatershedViewer = self.watershedApplet.topLevelOperator.getLane(laneIndex)

        # Connect them up
        opWatershedViewer.InputImage.connect( opPixelClassification.CachedPredictionProbabilities )
        opWatershedViewer.RawImage.connect( opPixelClassification.InputImages )
