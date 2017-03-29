import os.path
import random
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
from mamutexport.mamutxmlbuilder import MamutXmlBuilder
from mamutexport.bigdataviewervolumeexporter import BigDataViewerVolumeExporter
import vigra

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
        vigra.writeHDF5(rawImage, filename + '_raw.h5', 'exported_data')

        bve = BigDataViewerVolumeExporter(filename + '_raw.h5', 'exported_data', rawImage.shape[1:4])
        for t in range(rawImage.shape[0]):
            bve.addTimePoint(t)
        bve._finalizeTimepoints()
        MamutXmlBuilder.indent(bve.root)
        bve.writeToFile(filename + '_bdv.xml')

        builder = MamutXmlBuilder()
        graph = hypothesesGraph._graph

        features = objectFeaturesSlot([]).wait() # this is a dict of structure: {frame: {category: {featureNames}}}
        firstPass = True

        for node in graph.nodes_iter():
            frame, label = node
            if graph.node[node]['value'] > 0:
                t = graph.node[node]['traxel']

                radius = 2*features[frame]['Standard Object Features']['RegionRadii'][label, 0]
                
                featureDict = {}
                for category in features[frame].keys():
                    for key in features[frame][category].keys():

                        if firstPass:
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
                                    for column in xrange((np.asarray(features[frame][category][key])).shape[1]):
                                        builder.addFeatureName(feature_string + '_' + str(column), feature_string, shortname + '_' + str(column), isInt)
                            else:
                                #print "ELSE", key, np.asarray(features[key]).shape
                                builder.addFeatureName(feature_string, feature_string, shortname, isInt)

                        if key != 'Histogram':
                            if label != 0: # ignoring background
                                if (np.asarray(features[frame][category][key])).ndim == 0:
                                    featureDict[convertKeyName(key)] = features[frame][category][key]
                                if (np.asarray(features[frame][category][key])).ndim == 1:
                                    featureDict[convertKeyName(key)] = features[frame][category][key][label]
                                if (np.asarray(features[frame][category][key])).ndim == 2:
                                    for j in xrange((np.asarray(features[frame][category][key])).shape[1]):
                                        try:
                                            exists = features[frame][category][key][label, 0]
                                        except IndexError:
                                            if 'SquaredDistances' in key:
                                                featureDict[convertKeyName(key) + '_{}'.format(str(j))] = 9999.
                                            else:
                                                featureDict[convertKeyName(key) + '_{}'.format(str(j))] = 0.
                                            continue
                                        featureDict[convertKeyName(key) + '_{}'.format(str(j))] = features[frame][category][key][label, j]
                firstPass = False

                # TODO: builder.addSpot(frame, graph.node[node]['id'], t.X(), t.Y(), t.Z(), radius, featureDict)
                # instead of the next lines
                xpos = features[frame]['Standard Object Features']['RegionCenter'][label, 0]
                ypos = features[frame]['Standard Object Features']['RegionCenter'][label, 1]
                try:
                    zpos = features[frame]['Standard Object Features']['RegionCenter'][label, 2]
                except IndexError:
                    zpos = 0.0

                builder.addSpot(frame, 'track-{}'.format(graph.node[node]['trackId']), graph.node[node]['id'], xpos, ypos, zpos, radius, featureDict)

        for edge in graph.edges_iter():
            if graph.edge[edge[0]][edge[1]]['value'] > 0:
                builder.addLink(graph.node[edge[0]]['lineageId'], graph.node[edge[0]]['id'], graph.node[edge[1]]['id'])

        builder.setBigDataViewerImagePath(os.path.dirname(bigDataViewerFile), os.path.basename(bigDataViewerFile))
        builder.writeToFile(filename + '_mamut.xml')

        return True
