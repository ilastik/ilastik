import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
import vigra

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
        
        for t in range(tMax):
            s = [slice(None) for i in range(len(labelImageSlot.meta.shape))]
            s[tIndex] = slice(t, t+1)
            s = tuple(s)

            # Request in parallel
            frame = labelImageSlot[s].wait()            
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
                    contoursDict[id].append(contours[0])
                else:
                    contoursDict[id] = [contours[0]]           
        
        
        # Generate contour string and save .outline file
        outlineFile = open(filename + '.outline', 'w')

        for id, contours in contoursDict.iteritems():
            for contour in contours:
                # Generate contour string compatible with the .outline format
                contourString =' '.join(str(contour[i, 1])+' '+str(contour[i, 0]) for i in range(len(contour)))
                contourString = '20170201_000000 '+str(int(id)).zfill(5)+' '+'0.000 '+contourString+'\n'
                
                # Append contour
                outlineFile.write(contourString)
              
        outlineFile.close()

        return True
