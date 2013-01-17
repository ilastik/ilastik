import logging
logger = logging.getLogger(__name__)

import pixelClassification
import vigraWatershed

try:
    import autocontextClassification
except:
    logger.warn( "Failed to import autocontextClassification workflow.  Check context dependencies." )

try:
    import carving
except:
    logger.warn( "Failed to import carving workflow.  Check context dependencies." )
