from carvingWorkflow import CarvingWorkflow

import ilastik.config
if ilastik.config.cfg.getboolean('ilastik', 'debug'):
    try:
        from carvingFromPixelPredictionsWorkflow import CarvingFromPixelPredictionsWorkflow
    except:
        pass
    
    try:
        from splitBodyCarvingWorkflow import SplitBodyCarvingWorkflow
    except:
        pass
