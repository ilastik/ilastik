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
import logging
logger = logging.getLogger(__name__)

WORKFLOW_CLASSES = []

import ilastik.config

from .pixelClassification import PixelClassificationWorkflow
WORKFLOW_CLASSES += [PixelClassificationWorkflow]

from .newAutocontext.newAutocontextWorkflow import AutocontextTwoStage
WORKFLOW_CLASSES += [AutocontextTwoStage]
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    from .newAutocontext.newAutocontextWorkflow import AutocontextThreeStage, AutocontextFourStage
    WORKFLOW_CLASSES += [AutocontextThreeStage, AutocontextFourStage]


try:
    from .objectClassification.objectClassificationWorkflow import ObjectClassificationWorkflowPixel, ObjectClassificationWorkflowPrediction, ObjectClassificationWorkflowBinary
    WORKFLOW_CLASSES += [ObjectClassificationWorkflowPixel, ObjectClassificationWorkflowPrediction, ObjectClassificationWorkflowBinary]
except ImportError as e:
    logger.warning("Failed to import object workflow; check dependencies: " + str(e))

try:
    from .tracking.manual.manualTrackingWorkflow import ManualTrackingWorkflow
    WORKFLOW_CLASSES += [ManualTrackingWorkflow]
except (ImportError, AttributeError) as e:
    logger.warning( "Failed to import tracking workflow; check pgmlink dependency: " + str(e) )

try:
    from .tracking.conservation.conservationTrackingWorkflow import ConservationTrackingWorkflowFromBinary, ConservationTrackingWorkflowFromPrediction
    from .tracking.conservation.animalConservationTrackingWorkflow import AnimalConservationTrackingWorkflowFromBinary, AnimalConservationTrackingWorkflowFromPrediction
    WORKFLOW_CLASSES += [ ConservationTrackingWorkflowFromBinary, ConservationTrackingWorkflowFromPrediction,
                          AnimalConservationTrackingWorkflowFromBinary, AnimalConservationTrackingWorkflowFromPrediction ]
except ImportError as e:
    logger.warning( "Failed to import automatic tracking workflow (conservation tracking). For this workflow, see the installation"\
                 "instructions on our website ilastik.org; check dependencies: " + str(e) )

try:
    from .tracking.structured.structuredTrackingWorkflow import StructuredTrackingWorkflowFromBinary, StructuredTrackingWorkflowFromPrediction
    WORKFLOW_CLASSES += [StructuredTrackingWorkflowFromBinary, StructuredTrackingWorkflowFromPrediction]    
except ImportError as e:
    logger.warning( "Failed to import structured learning tracking workflow. For this workflow, see the installation"\
             "instructions on our website ilastik.org; check dependencies: " + str(e) )
try:
    from .carving.carvingWorkflow import CarvingWorkflow
    WORKFLOW_CLASSES += [CarvingWorkflow]    
except ImportError as e:
    logger.warning( "Failed to import carving workflow; check vigra dependency: " + str(e) )

# try:
#     import multicut
# except ImportError as e:
#     logger.warning("Failed to import multicut workflow; check dependencies: " + str(e))

try:
    from .edgeTrainingWithMulticut import EdgeTrainingWithMulticutWorkflow
    WORKFLOW_CLASSES += [EdgeTrainingWithMulticutWorkflow]
except ImportError as e:
    logger.warning("Failed to import 'Edge Training With Multicut' workflow; check dependencies: " + str(e))

try:
    from .counting import CountingWorkflow
    WORKFLOW_CLASSES += [CountingWorkflow]
except ImportError as e:
    logger.warning("Failed to import counting workflow; check dependencies: " + str(e))

from .examples.dataConversion.dataConversionWorkflow import DataConversionWorkflow
WORKFLOW_CLASSES += [DataConversionWorkflow]

# network classification, check whether required modules are available:
can_nn = True
try:
    import torch
    import inferno
    import tiktorch
except ImportError as e:
    can_nn = False
    logger.debug(f"NNClassificationWorkflow: could not import required modules: {e}")

if can_nn:
    if ilastik.config.cfg.getboolean('ilastik', 'hbp', fallback=False):
        from .nnClassification import NNClassificationWorkflow
        WORKFLOW_CLASSES += [NNClassificationWorkflow]


# Examples
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    from . import wsdt
    from .examples import layerViewer
    from .examples import thresholdMasking
    from .examples import deviationFromMean
    from .examples import labeling
    from .examples import connectedComponents
