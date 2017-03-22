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

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow 
from ilastik.applets.iiboostFeatureSelection import IIBoostFeatureSelectionApplet
from ilastik.applets.iiboostPixelClassification import IIBoostPixelClassificationApplet

class IIBoostPixelClassificationWorkflow(PixelClassificationWorkflow):
    workflowName = "IIBoost Synapse Detection"
    workflowDescription = "Find synapses in EM volumes with the IIBoost classifier"
    workflowDisplayName = "IIBoost Synapse Detection"
    defaultAppletIndex = 0 # show DataSelection by default
    
    def __init__(self, *args, **kwargs):
        super( IIBoostPixelClassificationWorkflow, self ).__init__( *args, **kwargs )

    def createDataSelectionApplet(self):
        """
        Overridden from the base PixelClassificationWorkflow.
        We require a particular axis order and we also allow axis details editing.
        """
        data_instructions = "Select your input data using the 'Raw Data' tab shown on the right"
        return DataSelectionApplet( self,
                                    "Input Data",
                                    "Input Data",
                                    supportIlastik05Import=True,
                                    forceAxisOrder=['zyxc'], # This workflow requires 3D data and assumes zyxc order in feature computation and prediction.
                                    instructionText=data_instructions,
                                    show_axis_details=True ) # IIBoost supports/requires information about anisotropy.

    def createFeatureSelectionApplet(self):
        """
        Overridden from the base PixelClassificationWorkflow
        """
        return IIBoostFeatureSelectionApplet(self, "Feature Selection", "FeatureSelections", self.filter_implementation)

    def createPixelClassificationApplet(self):
        """
        Overridden from the base PixelClassificationWorkflow
        """
        return IIBoostPixelClassificationApplet( self, "PixelClassification" )
