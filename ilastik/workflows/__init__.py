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

import pixelClassification
WORKFLOW_CLASSES += [pixelClassification.PixelClassificationWorkflow]

import newAutocontext.newAutocontextWorkflow
WORKFLOW_CLASSES += [newAutocontext.newAutocontextWorkflow.AutocontextTwoStage]
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    WORKFLOW_CLASSES += [newAutocontext.newAutocontextWorkflow.AutocontextThreeStage,
                         newAutocontext.newAutocontextWorkflow.AutocontextFourStage]

try:
    import iiboostPixelClassification
    WORKFLOW_CLASSES += [iiboostPixelClassification.IIBoostPixelClassificationWorkflow]
except ImportError as e:
    logger.warn( "Failed to import the IIBoost Synapse detection workflow.  Check IIBoost dependency." )


try:
    import objectClassification
    WORKFLOW_CLASSES += [objectClassification.objectClassificationWorkflow.ObjectClassificationWorkflowPixel,
                         objectClassification.objectClassificationWorkflow.ObjectClassificationWorkflowPrediction,
                         objectClassification.objectClassificationWorkflow.ObjectClassificationWorkflowBinary]
except ImportError as e:
    logger.warn("Failed to import object workflow; check dependencies: " + str(e))

try:
    import tracking.manual
    WORKFLOW_CLASSES += [tracking.manual.manualTrackingWorkflow.ManualTrackingWorkflow]
except ImportError as e:
    logger.warn( "Failed to import tracking workflow; check pgmlink dependency: " + str(e) )

try:
    import tracking.conservation
    WORKFLOW_CLASSES += [tracking.conservation.conservationTrackingWorkflow.ConservationTrackingWorkflowFromBinary,
                         tracking.conservation.conservationTrackingWorkflow.ConservationTrackingWorkflowFromPrediction,
                         tracking.conservation.animalConservationTrackingWorkflow.AnimalConservationTrackingWorkflowFromBinary,
                         tracking.conservation.animalConservationTrackingWorkflow.AnimalConservationTrackingWorkflowFromPrediction]
except ImportError as e:
    logger.warn( "Failed to import automatic tracking workflow (conservation tracking). For this workflow, see the installation"\
                 "instructions on our website ilastik.org; check dependencies: " + str(e) )

try:
    import tracking.structured
    WORKFLOW_CLASSES += [tracking.structured.structuredTrackingWorkflow.StructuredTrackingWorkflowFromBinary,
                         tracking.structured.structuredTrackingWorkflow.StructuredTrackingWorkflowFromPrediction]    
except ImportError as e:
    logger.warn( "Failed to import structured learning tracking workflow. For this workflow, see the installation"\
             "instructions on our website ilastik.org; check dependencies: " + str(e) )
try:
    import carving
    WORKFLOW_CLASSES += [carving.carvingWorkflow.CarvingWorkflow]    
except ImportError as e:
    logger.warn( "Failed to import carving workflow; check vigra dependency: " + str(e) )

# try:
#     import multicut
# except ImportError as e:
#     logger.warn("Failed to import multicut workflow; check dependencies: " + str(e))

try:
    import edgeTrainingWithMulticut
    WORKFLOW_CLASSES += [edgeTrainingWithMulticut.EdgeTrainingWithMulticutWorkflow]
except ImportError as e:
    logger.warn("Failed to import 'Edge Training With Multicut' workflow; check dependencies: " + str(e))

try:
    import counting
    WORKFLOW_CLASSES += [counting.countingWorkflow.CountingWorkflow]
except ImportError as e:
    logger.warn("Failed to import counting workflow; check dependencies: " + str(e))

import examples.dataConversion
WORKFLOW_CLASSES += [examples.dataConversion.dataConversionWorkflow.DataConversionWorkflow]

# Examples
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    import vigraWatershed
    import wsdt
    import examples.layerViewer
    import examples.thresholdMasking
    import examples.deviationFromMean
    import examples.labeling
    import examples.connectedComponents
