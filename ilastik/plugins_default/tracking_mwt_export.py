from __future__ import division
from builtins import range
from past.utils import old_div
import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
import vigra

from functools import partial
from lazyflow.request import Request, RequestPool

from skimage import measure

class TrackingContourExportFormatPlugin(TrackingExportFormatPlugin):
    """MWT export"""

    exportsToFile = True

    def checkFilesExist(self, filename):
        ''' Check whether the files we want to export are already present '''
        return os.path.exists(filename + '.outline')

    def export(self, filename, hypothesesGraph, pluginExportContext):
        """
        Export the Multi-Worm-Tracker .summary and .blobs files.

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
            objectFeaturesSlot (required here),  labelImageSlot (required here)
            as well as  rawImageSlot, additionalPluginArgumentsSlot
            
        :returns: True on success, False otherwise
        """
        # Get object features
        features = pluginExportContext.objectFeaturesSlot([]).wait()
        
        contoursDict = {}
        
        summaryDict = {}

        labelImageSlot = pluginExportContext.labelImageSlot
        tIndex = labelImageSlot.meta.axistags.index('t')
        tMax = labelImageSlot.meta.shape[tIndex]
       
        # Method to compute contours for single frame (called in parallel by a request parallel)
        def compute_dicts_for_frame(tIndex, t, labelImageSlot, hypothesesGraph, contoursDict): 
            roi = [slice(None) for i in range(len(labelImageSlot.meta.shape))]
            roi[tIndex] = slice(t, t+1)
            roi = tuple(roi)

            frame = labelImageSlot[roi].wait()            
            frame = frame.squeeze()
                   
            for idx in vigra.analysis.unique(frame):
                nodeId = (t, idx)
                
                if hypothesesGraph.hasNode(nodeId) and 'lineageId' in hypothesesGraph._graph.node[nodeId]:
                    if t in summaryDict:
                        summaryDict[t]['objectsNumber'] += 1
                        summaryDict[t]['validObjectsNumber'] += 1
                        summaryDict[t]['averageDuration'] = 0.0
                        summaryDict[t]['averageSpeed'] = 0.0
                        summaryDict[t]['averageAngularSpeed'] = 0.0
                        summaryDict[t]['averageLength'] += features[t]['Standard Object Features']['RegionRadii'][idx,0]
                        summaryDict[t]['averageRelativeLength'] = summaryDict[t]['averageLength']
                        summaryDict[t]['averageWidth'] += features[t]['Standard Object Features']['RegionRadii'][idx,1]
                        summaryDict[t]['averageRelativeWidth'] = summaryDict[t]['averageWidth']         
                        summaryDict[t]['averageAspectRatio'] += old_div(features[t]['Standard Object Features']['RegionRadii'][idx,0], features[t]['Standard Object Features']['RegionRadii'][idx,1])
                        summaryDict[t]['averageRelativeAspectRatio'] = summaryDict[t]['averageAspectRatio']
                        summaryDict[t]['endWiggle'] = 0.0               
                    else:
                        summaryDict[t] = {}
                        summaryDict[t]['objectsNumber'] = 1
                        summaryDict[t]['validObjectsNumber'] = 1
                        summaryDict[t]['averageDuration'] = 0.0
                        summaryDict[t]['averageSpeed'] = 0.0
                        summaryDict[t]['averageAngularSpeed'] = 0.0
                        summaryDict[t]['averageLength'] = features[t]['Standard Object Features']['RegionRadii'][idx,0]
                        summaryDict[t]['averageRelativeLength'] = summaryDict[t]['averageLength']
                        summaryDict[t]['averageWidth'] = features[t]['Standard Object Features']['RegionRadii'][idx,1]
                        summaryDict[t]['averageRelativeWidth'] = summaryDict[t]['averageWidth']         
                        summaryDict[t]['averageAspectRatio'] = old_div(features[t]['Standard Object Features']['RegionRadii'][idx,0], features[t]['Standard Object Features']['RegionRadii'][idx,1])
                        summaryDict[t]['averageRelativeAspectRatio'] = summaryDict[t]['averageAspectRatio']
                        summaryDict[t]['endWiggle'] = 0.0                             
                    
                # Generate frame with single label idx
                frameSingleLabel = np.zeros(frame.shape).astype(np.uint8)
                frameSingleLabel[frame==idx] = 1
            
                # Find contours using skimage marching squares
                contours = measure._find_contours.find_contours(frameSingleLabel,0)
            
                # Save contours to dictionary                    
                if idx in contoursDict:
                    contoursDict[idx][t] = contours[0]
                else:
                    contoursDict[idx] = {t:contours[0]}
            
        # Compute the contours in parallel
        pool = RequestPool()
        
        for t in range(tMax):
            pool.add( Request( partial(compute_dicts_for_frame, tIndex, t, labelImageSlot, hypothesesGraph, contoursDict) ) )
         
        pool.wait()  
        
        # Generate .summary file
        summaryFile = open(filename + '.summary', 'w')
        
        for t in sorted(summaryDict):
            summaryDict[t]['averageLength'] /= summaryDict[t]['objectsNumber']
            summaryDict[t]['averageRelativeLength'] = summaryDict[t]['averageLength']
            summaryDict[t]['averageWidth'] /= summaryDict[t]['objectsNumber']
            summaryDict[t]['averageRelativeWidth'] = summaryDict[t]['averageWidth']         
            summaryDict[t]['averageAspectRatio'] /= summaryDict[t]['objectsNumber']
            summaryDict[t]['averageRelativeAspectRatio'] = summaryDict[t]['averageAspectRatio']
            
            summaryFile.write('{} {} {} {} {} {} {} {} {} {} {} {} {} {}\n'.format(t+1, \
                                                                                   t, \
                                                                                   summaryDict[t]['objectsNumber'], \
                                                                                   summaryDict[t]['validObjectsNumber'], \
                                                                                   summaryDict[t]['averageDuration'], \
                                                                                   summaryDict[t]['averageSpeed'], \
                                                                                   summaryDict[t]['averageAngularSpeed'], \
                                                                                   summaryDict[t]['averageLength'], \
                                                                                   summaryDict[t]['averageRelativeLength'], \
                                                                                   summaryDict[t]['averageWidth'], \
                                                                                   summaryDict[t]['averageRelativeWidth'], \
                                                                                   summaryDict[t]['averageAspectRatio'], \
                                                                                   summaryDict[t]['averageRelativeAspectRatio'], \
                                                                                   summaryDict[t]['endWiggle']))
            
        summaryFile.close()
                  
        # Generate contour string and save .blobs file        
        blobsFile = open(filename + '.blobs', 'w')

        for idx in sorted(contoursDict): 
            #blobsFile.write('%{}\n'.format(int(idx)))
            
            count = 0
            for t in sorted(contoursDict[idx]):
                
                nodeId = (t, idx)
                
                if hypothesesGraph.hasNode(nodeId) and 'lineageId' in hypothesesGraph._graph.node[nodeId]:
                    lineageId = hypothesesGraph._graph.node[nodeId]['lineageId']
                    
                    contour = contoursDict[idx][t]
                    
                    count += 1
                    time = t
                    xCoord = features[t]['Standard Object Features']['RegionCenter'][idx,0]
                    yCoord = features[t]['Standard Object Features']['RegionCenter'][idx,1]
                    area = features[t]['Standard Object Features']['Count'][idx,0]
                    xMajorAxis = features[t]['Standard Object Features']['RegionAxes'][idx,0]*features[t]['Standard Object Features']['RegionRadii'][idx,0]
                    yMajorAxis = features[t]['Standard Object Features']['RegionAxes'][idx,1]*features[t]['Standard Object Features']['RegionRadii'][idx,0]
                    std = np.mean([features[t]['Standard Object Features']['RegionRadii'][idx,0],features[t]['Standard Object Features']['RegionRadii'][idx,1]])
                    length = features[t]['Standard Object Features']['RegionRadii'][idx,0]
                    width = features[t]['Standard Object Features']['RegionRadii'][idx,1]
                    
                    xOffset = contour[0,0]
                    yOffset = contour[0,1]
                    
                    # Generate contour string
                    prevPoint = []
                    contourLength = 0
                    binaryString = ''
                    pointsString = ''
                    
                    for i, point in enumerate(contour):                        
                        if len(prevPoint) > 0:
                            # 4-way connected points
                            if point[0]-prevPoint[0] == -1 and point[1]-prevPoint[1] == 0:
                                binaryString += '00'
                                contourLength += 1
                            elif point[0]-prevPoint[0] == 1 and point[1]-prevPoint[1] == 0:
                                binaryString += '01'
                                contourLength += 1
                            elif point[0]-prevPoint[0] == 0 and point[1]-prevPoint[1] == -1:
                                binaryString += '10'
                                contourLength += 1
                            elif point[0]-prevPoint[0] == 0 and point[1]-prevPoint[1] == 1:
                                binaryString += '11'
                                contourLength += 1
                            # Diagonal points
                            elif point[0]-prevPoint[0] == -1 and point[1]-prevPoint[1] == -1:
                                binaryString += '00'
                                binaryString += '10'
                                contourLength += 2
                            elif point[0]-prevPoint[0] == -1 and point[1]-prevPoint[1] == 1:
                                binaryString += '00'
                                binaryString += '11'
                                contourLength += 2
                            elif point[0]-prevPoint[0] == 1 and point[1]-prevPoint[1] == -1:
                                binaryString += '01'
                                binaryString += '10'
                                contourLength += 2
                            elif point[0]-prevPoint[0] == 1 and point[1]-prevPoint[1] == 1:
                                binaryString += '01'
                                binaryString += '11'
                                contourLength += 2
                        
                        if len(binaryString) == 6:
                            pointsString += chr(int(binaryString, 2)+ord('0'))
                            binaryString = ''
                        elif len(binaryString) > 6:
                            diff = len(binaryString) - 6 
                            pointsString += chr(int(binaryString[:-diff], 2)+ord('0'))
                            binaryString = binaryString[-diff:]
                        elif i >= contour.shape[0]-1:
                            if len(binaryString) == 2:
                                binaryString += '00001'
                                pointsString += chr(int(binaryString, 2)+ord('0'))
                                binaryString = ''
                            elif len(binaryString) == 4:
                                binaryString += '00'
                                pointsString += chr(int(binaryString, 2)+ord('0'))
                                binaryString = ''
                                
                        prevPoint = point
 
                    # Create contour string and append to file
                    contourString = '{} {} {} {} {} {} {} {} {} {} %% {} {} {} '.format(count, time , xCoord, yCoord, area, xMajorAxis, yMajorAxis, std, length, width, xOffset, yOffset, contourLength+1)
                    contourString += pointsString
                    
                    if count == 1:
                        blobsFile.write('% {}\n'.format(int(idx)))
                        
                    blobsFile.write(contourString+'\n')
              
        blobsFile.close()

        return True