import logging
logger = logging.getLogger(__name__)

import pixelClassification
import vigraWatershed
import objectClassification
import blockwiseObjectClassification
import carving
#import synapseDetection

try:
    import autocontextClassification
except:
    logger.warn( "Failed to import autocontextClassification workflow.  Check context dependencies." )

try:
    import carving
except:
    logger.warn( "Failed to import carving workflow.  Check cylemon dependency." )
