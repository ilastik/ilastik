###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2021, the ilastik developers
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
import logging

from ilastik.config import runtime_cfg
from ilastik.applets.serverConfiguration.types import ServerConfig, Device
from ._nnWorkflowBase import _NNWorkflowBase
from ._localLauncher import LocalServerLauncher
from ilastik.applets.pixelClassificationEnhancer import PixelClassificationEnhancerApplet
from lazyflow.operators import tiktorch
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.serverConfiguration import ServerConfigApplet


logger = logging.getLogger(__name__)


class RemoteEnhancerWorkflow(_NNWorkflowBase):
    """
    This class provides workflow for a local tiktorch executable.
    It can be specified via "--tiktorch_executable" command line parameter.
    Furthermore, the ilastik app will try to find a tiktorch version
    (usually the case when bundled for distribution) if the parameter is not
    supplied. If it cannot be found, workflow is not available.
    """

    auto_register = True
    workflowName = "Pixel Classification Enhancer (Remote)"
    workflowDescription = "Allows to apply bioimage.io models on your data using bundled tiktorch"

    def __init__(self, shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs):
        tiktorch_exe_path = runtime_cfg.tiktorch_executable
        if not tiktorch_exe_path:
            raise RuntimeError("No tiktorch-executable specified")

        self._launcher = LocalServerLauncher(tiktorch_exe_path)
        super().__init__(shell, headless, workflow_cmdline_args, project_creation_args, *args, **kwargs)

    def _createFeatureSelectionApplet(self):
        return FeatureSelectionApplet(self, "Feature Selection", "FeatureSelections")

    def _createInputAndConfigApplets(self):
        connFactory = tiktorch.TiktorchConnectionFactory()
        self.serverConfigApplet = ServerConfigApplet(self, connectionFactory=connFactory)
        self._applets.append(self.serverConfigApplet)
        super()._createInputAndConfigApplets()

    def _createClassifierApplet(self):
        self.featureSelectionApplet = self._createFeatureSelectionApplet()
        self.applets.append(self.featureSelectionApplet)
        pce_appplet = PixelClassificationEnhancerApplet(
            self, "PixelClassificationEnhancer", connectionFactory=self.serverConfigApplet.connectionFactory
        )
        self.nnClassificationApplet = pce_appplet
        self._applets.append(self.nnClassificationApplet)

    def connectLane(self, laneIndex):
        """
        connects the operators for different lanes, each lane has a laneIndex starting at 0
        """
        opData = self.dataSelectionApplet.topLevelOperator.getLane(laneIndex)
        opNNclassify = self.nnClassificationApplet.topLevelOperator.getLane(laneIndex)
        opDataExport = self.dataExportApplet.topLevelOperator.getLane(laneIndex)
        opFeatures = self.featureSelectionApplet.topLevelOperator.getLane(laneIndex)

        opFeatures.InputImage.connect(opData.Image)
        # Feature Images -> Classification Op (for training, prediction)
        opNNclassify.FeatureImages.connect(opFeatures.OutputImage)
        opNNclassify.CachedFeatureImages.connect(opFeatures.CachedOutputImage)
        # Input Image ->  Classification Op (for display)
        opNNclassify.InputImages.connect(opData.Image)
        opNNclassify.OverlayImages.connect(opData.ImageGroup[self.DATA_ROLE_OVERLAY])
        # Data Export connections
        opDataExport.RawData.connect(opData.ImageGroup[self.DATA_ROLE_RAW])
        opDataExport.RawDatasetInfo.connect(opData.DatasetGroup[self.DATA_ROLE_RAW])
        opDataExport.Inputs.resize(len(self.EXPORT_NAMES))
        opDataExport.Inputs[0].connect(opNNclassify.PredictionProbabilities)
        opDataExport.Inputs[1].connect(opNNclassify.LabelImages)

        opServerConfig = self.serverConfigApplet.topLevelOperator.getLane(laneIndex)
        # TODO (k-dominik): this is probably a bug (also in the remote workflow)
        opNNclassify.ServerConfig.connect(opServerConfig.ServerConfig)

    def cleanUp(self):
        super().cleanUp()
