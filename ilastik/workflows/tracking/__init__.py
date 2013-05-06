import logging
logger = logging.getLogger(__name__)

try:
    from chaingraph.chaingraphTrackingWorkflow import ChaingraphTrackingWorkflow 
except ImportError as e:
    logger.warn( "Failed to import ChaingraphTrackingWorkflow; check pgmlink dependency: " + str(e) )
    
