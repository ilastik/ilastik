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
from ilastik.applets.base.standardApplet import StandardApplet

from .opObjectClassification import OpObjectClassification
from .objectClassificationSerializer import ObjectClassificationSerializer


class ObjectClassificationApplet(StandardApplet):
    """An applet for labeling and classifying objects."""
    def __init__(self,
                 name="Object Classification",
                 workflow=None,
                 projectFileGroupName="ObjectClassification",
                 selectedFeatures=dict()):
        self._topLevelOperator = OpObjectClassification(parent=workflow)
        self.connected_to_knime = False
        self._selectedFeatures = selectedFeatures

        super(ObjectClassificationApplet, self).__init__(name=name, workflow=workflow)

        self._serializableItems = [
            ObjectClassificationSerializer(projectFileGroupName,
                                           self.topLevelOperator)]

    def getMultiLaneGui(self):
        """
        Override from base class. The label that is initially selected needs to be selected after volumina knows
        the current layer stack. Which is only the case when the gui objects LayerViewerGui.updateAllLayers run at
        least once after object init.
        """
        from .objectClassificationGui import ObjectClassificationGui  # Prevent imports of QT classes in headless mode
        multi_lane_gui = super(ObjectClassificationApplet, self).getMultiLaneGui()
        guis = multi_lane_gui.getGuis()
        if len(guis) > 0 and isinstance(guis[0], ObjectClassificationGui) and not guis[0].isInitialized:
            guis[0].selectLabel(0)
            guis[0].isInitialized = True
        return multi_lane_gui

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        from .objectClassificationGui import ObjectClassificationGui  # Prevent imports of QT classes in headless mode
        return ObjectClassificationGui
