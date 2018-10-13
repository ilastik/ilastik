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
from .opPixelClassification import OpPixelClassification
from .pixelClassificationSerializer import PixelClassificationSerializer, Ilastik05ImportDeserializer

class PixelClassificationApplet( StandardApplet ):
    """
    Implements the pixel classification "applet", which allows the ilastik shell to use it.
    """
    def __init__( self, workflow, projectFileGroupName ):
        self._topLevelOperator = OpPixelClassification( parent=workflow )
        
        def on_classifier_changed(slot, roi):
            if self._topLevelOperator.classifier_cache.Output.ready() and \
               self._topLevelOperator.classifier_cache.fixAtCurrent.value is True and \
               self._topLevelOperator.classifier_cache.Output.value is None:
                # When the classifier is deleted (e.g. because the number of features has changed,
                #  then notify the workflow. (Export applet should be disabled.)
                self.appletStateUpdateRequested()
        self._topLevelOperator.classifier_cache.Output.notifyDirty( on_classifier_changed )

        super(PixelClassificationApplet, self).__init__( "Training" )

        # We provide two independent serializing objects:
        #  one for the current scheme and one for importing old projects.
        self._serializableItems = [PixelClassificationSerializer(self._topLevelOperator, projectFileGroupName), # Default serializer for new projects
                                   Ilastik05ImportDeserializer(self._topLevelOperator)]   # Legacy (v0.5) importer


        self._gui = None
        
        # GUI needs access to the serializer to enable/disable prediction storage
        self.predictionSerializer = self._serializableItems[0]

        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        #  directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        #  we'll need to aggregate the progress updates.
        self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal)

    def getMultiLaneGui(self):
        """
        Override from base class. The label that is initially selected needs to be selected after volumina knows
        the current layer stack. Which is only the case when the gui objects LayerViewerGui.updateAllLayers run at
        least once after object init.
        """
        from .pixelClassificationGui import PixelClassificationGui  # Prevent imports of QT classes in headless mode
        multi_lane_gui = super(PixelClassificationApplet, self).getMultiLaneGui()
        guis = multi_lane_gui.getGuis()
        if len(guis) > 0 and isinstance(guis[0], PixelClassificationGui) and not guis[0].isInitialized:
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
        from .pixelClassificationGui import PixelClassificationGui  # prevent imports of QT classes in headless mode
        return PixelClassificationGui
