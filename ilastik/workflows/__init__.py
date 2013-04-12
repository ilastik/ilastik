import logging
logger = logging.getLogger(__name__)

import pixelClassification
import vigraWatershed
try:
    import objectClassification
    import blockwiseObjectClassification
    #import synapseDetection
except ImportError as e:
    logger.warn("Failed to import object workflow; check dependencies: " + str(e))

try:
    import autocontextClassification
except ImportError as e:
    logger.warn( "Failed to import autocontextClassification workflow; check context dependencies: " + str(e) )

try:
    import carving 
except ImportError as e:
    logger.warn( "Failed to import carving workflow; check cylemon dependency: " + str(e) )

try:
    import tracking
except ImportError as e:
    logger.warn( "Failed to import tracking workflow; check pgmlink dependency: " + str(e) )

