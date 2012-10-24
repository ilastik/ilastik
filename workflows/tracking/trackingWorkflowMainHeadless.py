import ilastik.utility.monkey_patches # Must be the first import

from trackingWorkflow import TrackingWorkflow
from trackingWorkflowNN import TrackingWorkflowNN
import logging
import traceback
import argparse
import os
from ilastik.shell.headless.startShellHeadless import startShellHeadless
from lazyflow.rtype import SubRegion
import sys


#method = 'chaingraph'
method = 'nearest_neighbor'

logger = logging.getLogger(__name__)

def main(argv):
    parser = getArgParser()
    parsed_args = parser.parse_args(argv[1:])

#    ilastik.utility.monkey_patches.init_with_args(parsed_args)

    try:
        runWorkflow(parsed_args)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return 1
    
    return 0

def getArgParser():
    parser = argparse.ArgumentParser(description="Pixel Classification Prediction Workflow")
    parser.add_argument('--project', help='An .ilp file with input image', required=True)        
#    parser.add_argument('--sys_tmp_dir', help='Override the default directory for temporary file storage.')    
    return parser

def runWorkflow(parsed_args):
    args = parsed_args
    
    # Make sure project file exists.
    if not os.path.exists(args.project):
        raise RuntimeError("Project file '" + args.project + "' does not exist.")
    
    # Instantiate 'shell'
    if method is 'nearest_neighbor':
        print 'starting headless shell for nearest neighbor method...'
        shell, workflow = startShellHeadless( TrackingWorkflowNN )
    elif method is 'chaingraph':
        print 'starting headless shell for chaingraph method...'
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
    
    
    # FIXME: quick and dirty solution (copied the buttonPressed methods from trackingGui)
    curOp = workflow.objectExtractionApplet.topLevelOperator.innerOperators[0]
    _onLabelImageButtonPressed(curOp)
    _onExtractObjectsButtonPressed(curOp)
    _onMergeSegmentationsButtonPressed(curOp)
    
    # Save the project (which will request all predictions)
    shell.projectManager.saveProject()
    
#    workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = False
    
def _onLabelImageButtonPressed( curOp ):
        m = curOp.LabelImage.meta
        maxt = m.shape[0] - 1 # the last time frame will be dropped
        reqs = []
        curOp._opObjectExtractionBg._opLabelImage._fixed = False
        curOp._opObjectExtractionDiv._opLabelImage._fixed = False

        for t in range(maxt):            
            reqs.append(curOp._opObjectExtractionBg._opLabelImage.LabelImage([t]))
            reqs[-1].submit()

            reqs.append(curOp._opObjectExtractionDiv._opLabelImage.LabelImage([t]))
            reqs[-1].submit()
            logger.info('submitted requests for t = ' + str(t))
        
        logger.info('all requests submitted.')
        
        for i, req in enumerate(reqs):
            logger.info('wait for ' + str(i))
            req.wait()
        roi = SubRegion(curOp.LabelImage, start=5*(0,), stop=m.shape)        
        
        try:         
            curOp.LabelImage.setDirty(roi)
        except:
            print "TODO: set LabelImage dirty to update the result for the current view"        
        logger.info('Label Segmentation: done.')


def _onExtractObjectsButtonPressed( curOp ):
        maxt = curOp.LabelImage.meta.shape[0] - 1 # the last time frame will be dropped        
        reqs = []
        curOp._opObjectExtractionBg._opRegFeats.fixed = False
        curOp._opObjectExtractionDiv._opRegFeats.fixed = False
        for t in range(maxt):
            reqs.append(curOp._opObjectExtractionBg.RegionFeatures([t]))
            reqs[-1].submit()
            reqs.append(curOp._opObjectExtractionDiv.RegionFeatures([t]))
            reqs[-1].submit()
        for i, req in enumerate(reqs):
            req.wait()
        curOp._opObjectExtractionBg._opRegFeats.fixed = True 
        curOp._opObjectExtractionDiv._opRegFeats.fixed = True        
        curOp._opObjectExtractionBg.ObjectCenterImage.setDirty( SubRegion(curOp._opObjectExtractionBg.ObjectCenterImage))
        curOp._opObjectExtractionDiv.ObjectCenterImage.setDirty( SubRegion(curOp._opObjectExtractionDiv.ObjectCenterImage))        
        logger.info('Object Extraction: done.')
        
def _onMergeSegmentationsButtonPressed(curOp):
        m = curOp.LabelImage.meta
        maxt = m.shape[0] -1 # the last time frame will be dropped        

        reqs = []
        for t in range(maxt):
            reqs.append(curOp._opClassExtraction.ClassMapping([t]))
            reqs[-1].submit()
        for i, req in enumerate(reqs):
            req.wait()        
        logger.info('Merge Segmentation: done.')



if __name__ == "__main__":
    sys.exit( main(sys.argv) )
    