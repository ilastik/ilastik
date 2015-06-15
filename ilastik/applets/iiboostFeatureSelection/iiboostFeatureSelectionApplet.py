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
from ilastik.applets.featureSelection import FeatureSelectionApplet
from opIIBoostFeatureSelection import OpIIBoostFeatureSelection

class IIBoostFeatureSelectionApplet( FeatureSelectionApplet ):
    """
    This applet is a subclass of the standard feature selection applet from the pixel classification workflow,
    except it uses a variant of the top-level operator which adds channels needed for the IIBoost classifier.  
    """
    def __init__( self, workflow, guiName, projectFileGroupName, filter_implementation='Original' ):
        super(IIBoostFeatureSelectionApplet, self).__init__(workflow, guiName, projectFileGroupName, filter_implementation='Original')

    @property
    def singleLaneOperatorClass(self):
        return OpIIBoostFeatureSelection
