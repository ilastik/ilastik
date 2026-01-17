###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
import logging

logger = logging.getLogger(__name__)

import ilastik.config

from .newAutocontext.newAutocontextWorkflow import AutocontextTwoStage
from .pixelClassification import PixelClassificationWorkflow

if ilastik.config.cfg.getboolean("ilastik", "debug"):
    from .newAutocontext.newAutocontextWorkflow import AutocontextFourStage, AutocontextThreeStage


try:
    from .objectClassification.objectClassificationWorkflow import (
        ObjectClassificationWorkflowBinary,
        ObjectClassificationWorkflowPixel,
        ObjectClassificationWorkflowPrediction,
    )
except ImportError as e:
    logger.warning("Failed to import object workflow; check dependencies: " + str(e))

try:
    from .tracking.manual.manualTrackingWorkflow import ManualTrackingWorkflow
except (ImportError, AttributeError) as e:
    logger.warning("Failed to import tracking workflow; check pgmlink dependency: " + str(e))

try:
    from .tracking.conservation.animalConservationTrackingWorkflow import (
        AnimalConservationTrackingWorkflowFromBinary,
        AnimalConservationTrackingWorkflowFromPrediction,
    )
    from .tracking.conservation.conservationTrackingWorkflow import (
        ConservationTrackingWorkflowFromBinary,
        ConservationTrackingWorkflowFromPrediction,
    )
except ImportError as e:
    logger.warning(
        "Failed to import automatic tracking workflow (conservation tracking). For this workflow, see the installation"
        "instructions on our website ilastik.org; check dependencies: " + str(e)
    )

try:
    from .tracking.structured.structuredTrackingWorkflow import (
        StructuredTrackingWorkflowFromBinary,
        StructuredTrackingWorkflowFromPrediction,
    )
except ImportError as e:
    logger.warning(
        "Failed to import structured learning tracking workflow. For this workflow, see the installation"
        "instructions on our website ilastik.org; check dependencies: " + str(e)
    )
try:
    from .carving.carvingWorkflow import CarvingWorkflow
except ImportError as e:
    logger.warning("Failed to import carving workflow; check vigra dependency: " + str(e))

try:
    from .edgeTrainingWithMulticut import EdgeTrainingWithMulticutWorkflow
except ImportError as e:
    logger.warning("Failed to import 'Edge Training With Multicut' workflow; check dependencies: " + str(e))

try:
    from .counting import CountingWorkflow
except ImportError as e:
    logger.warning("Failed to import counting workflow; check dependencies: " + str(e))

from .examples.dataConversion.dataConversionWorkflow import DataConversionWorkflow

# network classification, check whether required modules are available:
try:
    if ilastik.config.runtime_cfg.tiktorch_executable:
        from .neuralNetwork import LocalWorkflow
        from .trainableDomainAdaptation import (
            LocalTrainableDomainAdaptationWorkflow,
            LocalTrainableDomainAdaptationWorkflowLegacy,
        )

        logger.debug(ilastik.config.runtime_cfg)

except ImportError as e:
    logger.warning("Failed to import NeuralNet workflow; check dependencies: " + str(e), exc_info=1)

# Examples
if ilastik.config.cfg.getboolean("ilastik", "debug"):
    from . import wsdt
    from .examples import connectedComponents, deviationFromMean, labeling, layerViewer, thresholdMasking
