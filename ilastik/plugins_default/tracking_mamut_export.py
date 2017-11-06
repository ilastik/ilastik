from builtins import range
import os.path
import random
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
from mamutexport.mamutxmlbuilder import MamutXmlBuilder
from mamutexport.bigdataviewervolumeexporter import BigDataViewerVolumeExporter
import vigra
import h5py

def convertKeyName(key):
    key = key.replace('<', '_')
    key = key.replace('>', '')
    key = key.replace(' ', '')
    return key

def getShortname(string):
    ''' convert name to shortname'''
    shortname = string[0:2]
    for i, l in enumerate(string):
        try:
            if l == "_":
                shortname += string[i+1]
                shortname += string[i+2]
                shortname += string[i+3]
            if shortname == 'WeReg':
                shortname += string[i+7]
                shortname += string[i+8]
                shortname += string[i+9]

        except IndexError:
            break
    return shortname.strip()

class TrackingMamutExportFormatPlugin(TrackingExportFormatPlugin):
    """MaMuT export"""

    exportsToFile = True

    def checkFilesExist(self, filename):
        ''' Check whether the files we want to export are already present '''
        return os.path.exists(filename + '_mamut.xml') or os.path.exists(filename + '_bdv.xml') or os.path.exists(filename + '_raw.h5')

    def export(self, filename, hypothesesGraph, objectFeaturesSlot, labelImageSlot, rawImageSlot):
        """Export the tracking solution stored in the hypotheses graph to two XML files so that 
        a) the raw data can be displayed in Fiji's BigDataViewer, and b) that the tracks can be visualized in MaMuT. 

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param objectFeaturesSlot: lazyflow.graph.InputSlot, connected to the RegionFeaturesAll output 
               of ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction
        
        :returns: True on success, False otherwise
        """
        bigDataViewerFile = filename + '_bdv.xml'

        rawImage = rawImageSlot([]).wait()
        rawImage = np.swapaxes(rawImage, 1, 3)
        with h5py.File(filename + '_raw.h5', 'w') as f:
            f.create_dataset('exported_data', data=rawImage)
        
        bve = BigDataViewerVolumeExporter(filename + '_raw.h5', 'exported_data', rawImage.shape[1:4])
        for t in range(rawImage.shape[0]):
            bve.addTimePoint(t)
        bve._finalizeTimepoints()
        MamutXmlBuilder.indent(bve.root)
        bve.writeToFile(filename + '_bdv.xml')

        builder = MamutXmlBuilder()
        graph = hypothesesGraph._graph

        features = objectFeaturesSlot([]).wait() # this is a dict of structure: {frame: {category: {featureNames}}}

        # first loop over all nodes to find present features
        presentTrackIds = set([])
        for node in graph.nodes_iter():
            frame, label = node
            # print(f"Node {node} has value={graph.node[node]['value']} and trackId={graph.node[node]['trackId']}")
            if graph.node[node]['value'] > 0:
                t = graph.node[node]['traxel']

                radius = 2*features[frame]['Standard Object Features']['RegionRadii'][label, 0]
                for category in list(features[frame].keys()):
                    for key in list(features[frame][category].keys()):
                        feature_string = key
                        feature_string = convertKeyName(feature_string)
                        if len(feature_string) > 15:
                            shortname = getShortname(feature_string).replace('_', '')
                        else:
                            shortname = feature_string.replace('_', '')

                        isInt = isinstance(features[frame][category][key], int)

                        if (np.asarray(features[frame][category][key])).ndim == 2:
                            if key != 'Histogram':
                                #print key, np.asarray(features[key]).shape
                                for column in range((np.asarray(features[frame][category][key])).shape[1]):
                                    builder.addFeatureName(feature_string + '_' + str(column), feature_string, shortname + '_' + str(column), isInt)
                        else:
                            #print "ELSE", key, np.asarray(features[key]).shape
                            builder.addFeatureName(feature_string, feature_string, shortname, isInt)

                builder.addFeatureName("LabelimageId", "LabelimageId", "labelid", False)
                builder.addFeatureName("Track_color", "Track_color", "trackcol", False)
                builder.addTrackFeatureName("Track_color", "Track_color", "trackcol", False)
                break

        # insert edges
        for edge in graph.edges_iter():
            if graph.edge[edge[0]][edge[1]]['value'] > 0:
                builder.addLink(graph.node[edge[0]]['trackId'], graph.node[edge[0]]['id'], graph.node[edge[1]]['id'])
                presentTrackIds.add(int(graph.node[edge[0]]['trackId']))

        # assign random colors to tracks that have at least one edge (empty tracks cause MaMuT errors)
        randomColorPerTrack = {}
        for trackId in presentTrackIds:
            randomColorPerTrack[trackId] = np.random.random()
            builder.setTrackFeatures(trackId, {'Track_color': randomColorPerTrack[trackId]})

        # second pass over the nodes passes features and tracks to the builder
        for node in graph.nodes_iter():
            frame, label = node
            if graph.node[node]['value'] > 0:
                t = graph.node[node]['traxel']
                trackId = int(graph.node[node]['trackId'])

                radius = 2*features[frame]['Standard Object Features']['RegionRadii'][label, 0]
                
                featureDict = {}
                for category in list(features[frame].keys()):
                    for key in list(features[frame][category].keys()):
                        if key != 'Histogram':
                            if label != 0: # ignoring background
                                if (np.asarray(features[frame][category][key])).ndim == 0:
                                    featureDict[convertKeyName(key)] = features[frame][category][key]
                                if (np.asarray(features[frame][category][key])).ndim == 1:
                                    featureDict[convertKeyName(key)] = features[frame][category][key][label]
                                if (np.asarray(features[frame][category][key])).ndim == 2:
                                    for j in range((np.asarray(features[frame][category][key])).shape[1]):
                                        try:
                                            _ = features[frame][category][key][label, 0]
                                        except IndexError:
                                            if 'SquaredDistances' in key:
                                                featureDict[convertKeyName(key) + '_{}'.format(str(j))] = 9999.
                                            else:
                                                featureDict[convertKeyName(key) + '_{}'.format(str(j))] = 0.
                                            continue
                                        featureDict[convertKeyName(key) + '_{}'.format(str(j))] = features[frame][category][key][label, j]

                xpos = features[frame]['Standard Object Features']['RegionCenter'][label, 0]
                ypos = features[frame]['Standard Object Features']['RegionCenter'][label, 1]
                try:
                    zpos = features[frame]['Standard Object Features']['RegionCenter'][label, 2]
                except IndexError:
                    zpos = 0.0

                if trackId in randomColorPerTrack:
                    featureDict['Track_color'] = randomColorPerTrack[trackId]
                else:
                    featureDict['Track_color'] = np.random.random()
                    
                featureDict['LabelimageId'] = label
                builder.addSpot(frame, 'track-{}'.format(trackId), graph.node[node]['id'], xpos, ypos, zpos, radius, featureDict)

        builder.setBigDataViewerImagePath(os.path.dirname(bigDataViewerFile), os.path.basename(bigDataViewerFile))
        builder.writeToFile(filename + '_mamut.xml')

        return True
