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

    def export(self, filename, hypothesesGraph, objectFeaturesSlot, labelImageSlot, rawImageSlot):
        """
        Export the contours and corresponding IDs for all objects on the video

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param objectFeaturesSlot: lazyflow.graph.InputSlot, connected to the RegionFeaturesAll output
               of ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction

        :returns: True on success, False otherwise
        """
        
        contoursDict = {}
        
        tIndex = labelImageSlot.meta.axistags.index('t')
        tMax = labelImageSlot.meta.shape[tIndex] 
       
        # Method to compute contours for single frame (called in parallel by a request parallel)
        def compute_contours_for_frame(tIndex, t, labelImageSlot, contoursDict): 
            roi = [slice(None) for i in range(len(labelImageSlot.meta.shape))]
            roi[tIndex] = slice(t, t+1)
            roi = tuple(roi)

            # Request in parallel
            frame = labelImageSlot[roi].wait()            
            frame = frame.squeeze()#frame[0,:,:,0,0]
                   
            for label in vigra.analysis.unique(frame):
                # Generate frame with single label
                frameSingleLabel = np.zeros(frame.shape).astype(np.uint8)
                frameSingleLabel[frame==label] = 1
            
                # Find contours using skimage marching squares
                contours = measure._find_contours.find_contours(frameSingleLabel,0)
                
                # Save contours to dictionary
                id = label
                if id in contoursDict:
                    #if t in contoursDict[id]:
                        #contoursDict[id][t].append(contours[0])
                    contoursDict[id][t] = contours[0]
#                     else:
#                         contoursDict[id] = {t:contours[0]}
                else:
                    #contoursDict[id] = [contours[0]]
                    contoursDict[id] = {t:contours[0]}
            
        # Compute the contours in parallel
        pool = RequestPool()
        
        for t in range(tMax):
            pool.add( Request( partial(compute_contours_for_frame, tIndex, t, labelImageSlot, contoursDict) ) )
         
        pool.wait()  
        
        # Generate contour string (from sorted dicts) and save .outline file
        outlineFile = open(filename + '.outline', 'w')

        for id in sorted(contoursDict):
            for t in sorted(contoursDict[id]):
                # Generate contour string compatible with the .outline format
                contour = contoursDict[id][t]
                contourString =' '.join(str(contour[i, 1])+' '+str(contour[i, 0]) for i in range(len(contour)))
                contourString = '20170201_000000 '+str(int(id)).zfill(5)+' '+'0.000 '+contourString+'\n'
                 
                # Append contour to file
                outlineFile.write(contourString)
              
        outlineFile.close()

        return True
