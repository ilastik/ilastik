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
#          http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet
from .opNNclass import OpNNTrainingClassification
from .nnClassSerializer import NNTrainingClassificationSerializer
from .tiktorchController import (
    TiktorchUnetController,
    TiktorchUnetOperatorModel,
)


class NNTrainingClassApplet(StandardApplet):
    def __init__(self, workflow, projectFileGroupName, connectionFactory):
        self._topLevelOperator = OpNNTrainingClassification(parent=workflow, connectionFactory=connectionFactory)

        def on_classifier_changed(slot, roi):
            if (
                self._topLevelOperator.classifier_cache.Output.ready()
                and self._topLevelOperator.classifier_cache.fixAtCurrent.value is True
                and self._topLevelOperator.classifier_cache.Output.value is None
            ):
                # When the classifier is deleted (e.g. because the number of features has changed,
                #  then notify the workflow. (Export applet should be disabled.)
                self.appletStateUpdateRequested()

        self._topLevelOperator.classifier_cache.Output.notifyDirty(on_classifier_changed)

        applet_name = "NN Training"

        super().__init__(applet_name, workflow=workflow)

        self._serializableItems = [NNTrainingClassificationSerializer(self.topLevelOperator, projectFileGroupName)]
        self._gui = None
        self.predictionSerializer = self._serializableItems[0]
        # FIXME: For now, we can directly connect the progress signal from the classifier training operator
        # directly to the applet's overall progress signal, because it's the only thing we report progress for at the moment.
        # If we start reporting progress for multiple tasks that might occur simulatneously,
        # we'll need to aggregate the progress updates.
        # self._topLevelOperator.opTrain.progressSignal.subscribe(self.progressSignal)
        self.tiktorchOpModel = TiktorchUnetOperatorModel(self.topLevelOperator)
        self.tiktorchController = TiktorchUnetController(self.tiktorchOpModel, connectionFactory)

    @property
    def dataSerializers(self):
        """
        A list of dataSerializer objects for loading/saving any project data the applet is responsible for
        """
        return self._serializableItems

    @property
    def singleLaneGuiClass(self):
        """
        This applet uses a single lane gui and shares variables through the broadcasting slots
        """
        from .nnTrainingClassGui import NNTrainingClassGui

        return NNTrainingClassGui

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def cleanUp(self):
        return self._topLevelOperator.cleanUp()
