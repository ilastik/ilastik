# to ensure that plugin system is available
import logging
logger = logging.getLogger(__name__)
from ilastik.plugins import pluginManager
try:
    from countingWorkflow import *
except ImportError as e:
    logger.warn( "Failed to import counting workflow; check dependencies: " + str(e) )
    
