import logging
logger = logging.getLogger(__name__)

try:
    from .conservationTrackingWorkflow import ConservationTrackingWorkflowFromPrediction, ConservationTrackingWorkflowFromBinary
    from .animalConservationTrackingWorkflow import AnimalConservationTrackingWorkflowFromPrediction, AnimalConservationTrackingWorkflowFromBinary
except ImportError as e:
    logger.warn( "Failed to automatic tracking workflow; check dependencies: " + str(e) )
