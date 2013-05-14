import logging
logger = logging.getLogger(__name__)

try:
    from chaingraph.chaingraphTrackingWorkflow import ChaingraphTrackingWorkflow 
except ImportError as e:
    logger.warn( "Failed to import chaingraph tracking workflow; check dependencies: " + str(e) )

try:    
    from manual.manualTrackingWorkflow import ManualTrackingWorkflow
except ImportError as e:
    logger.warn( "Failed to import manual tracking workflow; check dependencies: " + str(e) )
    
try:    
    from conservation.conservationTrackingWorkflow import ConservationTrackingWorkflow
except ImportError as e:
    logger.warn( "Failed to import conservation tracking workflow; check dependencies: " + str(e) )
    
