from builtins import range
import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
import vigra

from functools import partial
from lazyflow.request import Request, RequestPool

from skimage import measure

class TrackingContourExportFormatPlugin(TrackingExportFormatPlugin):
    """Contour export"""

    exportsToFile = True

    def checkFilesExist(self, filename):
        ''' Check whether the files we want to export are already present '''
        return os.path.exists(filename + '.outline')

    def export(self, filename, hypothesesGraph, pluginExportContext):
        """
        Export the contours and corresponding IDs for all objects on the video
        
         Each .outline file consists of a line for each frame the animal is tracked for. 
         The first number on this line is the timestamp of the frame, followed by the id, 
         and unknown number, and then the rest of numbers are the (x,y) coordinates of 
         the contour points (in what units?).

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
            labelImageSlot (required here) as well as objectFeaturesSlot, rawImageSlot, additionalPluginArgumentsSlot

        :returns: True on success, False otherwise
        """
        
        contoursDict = {}

        labelImageSlot = pluginExportContext.labelImageSlot
        tIndex = labelImageSlot.meta.axistags.index('t')
        tMax = labelImageSlot.meta.shape[tIndex] 
       
        # Method to compute contours for single frame (called in parallel by a request parallel)
        def compute_contours_for_frame(tIndex, t, labelImageSlot, hypothesesGraph, contoursDict): 
            roi = [slice(None) for i in range(len(labelImageSlot.meta.shape))]
            roi[tIndex] = slice(t, t+1)
            roi = tuple(roi)

            frame = labelImageSlot[roi].wait()            
            frame = frame.squeeze()
                   
            for idx in vigra.analysis.unique(frame):
                nodeId = (t, idx)
                
                if hypothesesGraph.hasNode(nodeId) and 'lineageId' in hypothesesGraph._graph.node[nodeId]:
                    # Generate frame with single label idx
                    frameSingleLabel = np.zeros(frame.shape).astype(np.uint8)
                    frameSingleLabel[frame==idx] = 1
                
                    # Find contours using skimage marching squares
                    contours = measure._find_contours.find_contours(frameSingleLabel,0)
                
                    # Save contours to dictionary
                    lineageId = hypothesesGraph._graph.node[nodeId]['lineageId']
                    
                    if lineageId in contoursDict:
                        contoursDict[lineageId][t] = contours[0]
                    else:
                        contoursDict[lineageId] = {t:contours[0]}
            
        # Compute the contours in parallel
        pool = RequestPool()
        
        for t in range(tMax):
            pool.add( Request( partial(compute_contours_for_frame, tIndex, t, labelImageSlot, hypothesesGraph, contoursDict) ) )
         
        pool.wait()  
        
        # Generate contour string (from sorted dicts) and save .outline file
        outlineFile = open(filename + '.outline', 'w')

        for id in sorted(contoursDict):
            for t in sorted(contoursDict[id]):
                # Generate contour string compatible with the .outline format
                contour = contoursDict[id][t]
                contourString =' '.join(str(contour[i, 1])+' '+str(contour[i, 0]) for i in range(len(contour)))
                contourString = '00000000_'+str(int(t)).zfill(6)+' '+str(int(id)).zfill(5)+' '+'0.000 '+contourString+'\n'
                 
                # Append contour to file
                outlineFile.write(contourString)
              
        outlineFile.close()

        return True
