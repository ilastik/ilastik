import logging
logger = logging.getLogger(__name__)

try:
    from conservationTrackingWorkflow import ConservationTrackingWorkflowFromPrediction, ConservationTrackingWorkflowFromBinary
except ImportError as e:
    logger.warn( "Failed to import automatic tracking workflow (conservation tracking). For this workflow, see the installation"\
             "instructions on our website ilastik.org; check dependencies: " + str(e) )
