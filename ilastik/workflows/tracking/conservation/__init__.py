from __future__ import absolute_import

import logging

logger = logging.getLogger(__name__)

try:
    from .animalConservationTrackingWorkflow import (
        AnimalConservationTrackingWorkflowFromBinary,
        AnimalConservationTrackingWorkflowFromPrediction,
    )
    from .conservationTrackingWorkflow import (
        ConservationTrackingWorkflowFromBinary,
        ConservationTrackingWorkflowFromPrediction,
    )
except ImportError as e:
    logger.warning("Failed to automatic tracking workflow; check dependencies: " + str(e))
