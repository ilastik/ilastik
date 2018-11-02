from builtins import range
import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
import vigra

from functools import partial
from lazyflow.request import Request, RequestPool

from skimage import measure

CONV_WINDOW_SIZE=20

class TrackingContoursBodyPartsPlugin(TrackingExportFormatPlugin):
    """Export contour with head location"""

    exportsToFile = True

    def checkFilesExist(self, filename):
        ''' Check whether the files we want to export are already present '''
        return os.path.exists(filename + '.contours')

    def export(self, filename, hypothesesGraph, pluginExportContext):
        """
        Export the contours, head index, and corresponding IDs for all objects on the video.
        
        Each .contours file consists of a line for each object in the video.
        All the values are space separated: the first number is the time (frame number), followed
        by the ID, the head index, the number of xy pairs in the contour, and an array of xy pairs. 

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
            labelImageSlot (required here), rawImageSlot (required here)
            as well as objectFeaturesSlot, additionalPluginArgumentsSlot

        :returns: True on success, False otherwise
        """
        
        headIndsDict = {}
        contoursDict = {}

        labelImageSlot = pluginExportContext.labelImageSlot
        rawImageSlot = pluginExportContext.rawImageSlot

        cIndex = labelImageSlot.meta.axistags.index('c')
        tIndex = labelImageSlot.meta.axistags.index('t')
        tMax = labelImageSlot.meta.shape[tIndex] 
       
        # Method to compute contours for single frame (called in parallel by a request parallel)
        def compute_contours_for_frame(tIndex, t, labelImageSlot, hypothesesGraph, contoursDict): 
            roi = [slice(None) for i in range(len(labelImageSlot.meta.shape))]
            roi[tIndex] = slice(t, t+1)
            roi = tuple(roi)

            rawFrame = rawImageSlot[roi].wait()

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
                
                    # Doing a very stupid slow convolution to sum the head probabilities for each xy point on the contour.
                    headProbs = []
                    for coord in contours[0]:
                        prob = 0
                        for  i in range(-CONV_WINDOW_SIZE,CONV_WINDOW_SIZE+1):
                            for j in range(-CONV_WINDOW_SIZE,CONV_WINDOW_SIZE+1):
                                if coord[0]+i >= 0 and coord[0]+i < rawFrame.shape[1] and coord[1]+j >= 0 and coord[1]+j < rawFrame.shape[2]:    
                                    prob += rawFrame[0,coord[0]+i, coord[1]+j, 0, 2]
                        headProbs.append(prob)
                        
                    headInd = np.argmax(headProbs)
                    
                    # Save contours and head index to dicts
                    lineageId = hypothesesGraph._graph.node[nodeId]['lineageId']
                    
                    if t in contoursDict:
                        contoursDict[t][lineageId] = contours[0]
                    else:
                        contoursDict[t] = {lineageId:contours[0]}                        
                    
                    if t in headIndsDict:
                        headIndsDict[t][lineageId] = headInd
                    else:
                        headIndsDict[t] = {lineageId:headInd} 
    
            
        # Compute the contours in parallel
        pool = RequestPool()
        
        for t in range(tMax):
            pool.add( Request( partial(compute_contours_for_frame, tIndex, t, labelImageSlot, hypothesesGraph, contoursDict) ) )
         
        pool.wait()  
        
        # Save contours and head index in .contours file 
        outlineFile = open(filename + '.contours', 'w')
        
        for t in sorted(contoursDict):
            for id in contoursDict[t]:
                contour = contoursDict[t][id]
                
                # Frame number, id, head index, contour length, contour xy pairs
                contourString = str(t)+' '+str(id)+' '+str(headIndsDict[t][id])+' '+str(len(contour))+' '
                contourString += ' '.join(str(contour[i, 1])+' '+str(contour[i, 0]) for i in range(len(contour)))                
                contourString += '\n'
                
                outlineFile.write(contourString)
              
        outlineFile.close()

        return True
