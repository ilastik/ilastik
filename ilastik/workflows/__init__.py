import logging
logger = logging.getLogger(__name__)

import pixelClassification

#import vigraWatershed
try:
    import objectClassification
except ImportError as e:
    logger.warn("Failed to import object workflow; check dependencies: " + str(e))

try:
    import carving 
except ImportError as e:
    logger.warn( "Failed to import carving workflow; check cylemon dependency: " + str(e) )

try:
    import tracking
except ImportError as e:
    logger.warn( "Failed to import tracking workflow; check pgmlink dependency: " + str(e) )
    
try:
    import counting
except ImportError as e:
    logger.warn("Failed to import counting workflow; check dependencies: " + str(e))


# Examples
import ilastik.config



if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    import examples.layerViewer
    import examples.thresholdMasking
