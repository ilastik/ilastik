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
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from ilastik.applets.vigraWatershedViewer import VigraWatershedViewerApplet

class PixelClassificationWithWatershedWorkflow(PixelClassificationWorkflow):

    workflowName = "Pixel Classification (with Watershed Preview)"
    workflowDisplayName = "Pixel Classification (with Watershed Preview)"
    
    
    def __init__( self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs ):
        super(PixelClassificationWithWatershedWorkflow, self).__init__( shell, headless, workflow_cmdline_args, project_creation_args, appendBatchOperators=False, supports_anisotropic_data=False, *args, **kwargs )

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
