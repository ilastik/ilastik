from __future__ import absolute_import
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
from ilastik.applets.labeling.labelingApplet import LabelingApplet

from ilastik.utility import OpMultiLaneWrapper
from .opCarving import OpCarving
from .carvingSerializer import CarvingSerializer

class CarvingApplet(LabelingApplet):
    
    workflowName = "Carving"
    workflowDescription = "this is obviously self-explanatory"
    
    def __init__(self, workflow, projectFileGroupName,  hintOverlayFile=None, pmapOverlayFile=None):
        if hintOverlayFile is not None:
            assert isinstance(hintOverlayFile, str)

        if not hasattr(self, '_topLevelOperator'):
            op_kwargs = { 'hintOverlayFile' : hintOverlayFile,
                          'pmapOverlayFile' : pmapOverlayFile }
            self._topLevelOperator = OpMultiLaneWrapper( OpCarving,
                                                         parent=workflow,
                                                         operator_kwargs=op_kwargs )

        super(CarvingApplet, self).__init__(workflow, projectFileGroupName)
        self._projectFileGroupName = projectFileGroupName
        self._serializers = [CarvingSerializer(self.topLevelOperator, self._projectFileGroupName)]

    def getMultiLaneGui(self):
        """
        Override from base class. The label that is initially selected needs to be selected after volumina knows
        the current layer stack. Which is only the case when the gui objects LayerViewerGui.updateAllLayers run at
        least once after object init.
        """
        from .carvingGui import CarvingGui  # Prevent imports of QT classes in headless mode
        multi_lane_gui = super(LabelingApplet, self).getMultiLaneGui()
        guis = multi_lane_gui.getGuis()
        if len(guis) > 0 and isinstance(guis[0], CarvingGui) and not guis[0].isInitialized:
            guis[0].selectLabel(0)
            guis[0].isInitialized = True
        return multi_lane_gui

    @property
    def dataSerializers(self):
        return self._serializers
    
    @property
    def topLevelOperator(self):
        """
        Override from base class.
        """
        return self._topLevelOperator
    
    @property
    def singleLaneGuiClass(self):
        from .carvingGui import CarvingGui  # Prevent imports of QT classes in headless mode
        return CarvingGui
