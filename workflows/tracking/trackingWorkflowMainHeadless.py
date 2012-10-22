import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.gui.startShellGui import startShellGui
from trackingWorkflow import TrackingWorkflow
from trackingWorkflowNN import TrackingWorkflowNN
import logging
import traceback
import argparse
import os
from ilastik.shell.headless.startShellHeadless import startShellHeadless

debug_testing = False
#method = 'chaingraph'
method = 'nearest_neighbor'


logger = logging.getLogger(__name__)

def main(argv):
    parser = getArgParser()
    parsed_args = parser.parse_args(argv[1:])

    ilastik.utility.monkey_patches.init_with_args(parsed_args)

    try:
        runWorkflow(parsed_args)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return 1
    
    return 0

def getArgParser():
    parser = argparse.ArgumentParser(description="Pixel Classification Prediction Workflow")
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=True)        
#    parser.add_argument('--sys_tmp_dir', help='Override the default directory for temporary file storage.')    
    return parser

def runWorkflow(parsed_args):
    args = parsed_args
    
    # Make sure project file exists.
    if not os.path.exists(args.project):
        raise RuntimeError("Project file '" + args.project + "' does not exist.")
    
    # Instantiate 'shell'
    if method is 'nearest_neighbor':
        shell, workflow = startShellHeadless( TrackingWorkflowNN )
    elif method is 'chaingraph':
        shell, workflow = startShellHeadless( TrackingWorkflow )
    else:
        logger.error("tracking method does not exist")
    
    # Load project (auto-import it if necessary)
    logger.info("Opening project: '" + args.project + "'")
    shell.openProjectPath(args.project)

    # object extraction for project input dataset 
    doObjectExtraction(shell, workflow)
    
    result = True
    
    logger.info("Closing project...")
    shell.projectManager.closeCurrentProject()
    
    assert result    
    
    logger.info("FINISHED.")
    
    
    
def doObjectExtraction(shell, workflow):
#    """
#    Compute predictions for all project inputs (not batch inputs), and save them to the project file.
#    """
#    # Set up progress display handling (just logging for now)        
#    currentProgress = [None]
#    def handleProgress(percentComplete):
#        if currentProgress[0] != percentComplete:
#            currentProgress[0] = percentComplete
#            logger.info("Object Extraction: {}% complete.".format(percentComplete))
#    workflow.pcApplet.progressSignal.connect( handleProgress )
    
#    # Enable prediction saving
#    workflow.objectExtractionApplet.topLevelOperator.FreezePredictions.setValue(False)
#    workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = True
    
    
    ##### "press all buttons"

    # Save the project (which will request all predictions)
    shell.projectManager.saveProject()
    
#    workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = False
    
