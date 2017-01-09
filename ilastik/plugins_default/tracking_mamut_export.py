import os.path
import random
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
from mamutexport.mamutxmlbuilder import MamutXmlBuilder
from mamutexport.bigdataviewervolumeexporter import BigDataViewerVolumeExporter

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

def setFeatures(builder, rawimage, labelimage_filename, is_3D, axes_order_label):
    ''' set features in the xml '''
    with h5py.File(labelimage_filename, 'r') as h5raw:
        labelimage = h5raw['/segmentation/labels'].value
        labelimage = checkAxes(labelimage, is_3D, axes_order_label, False)
        #if changed
        #labelimage = np.swapaxes(labelimage, 0, 1)

        rawimage = np.squeeze(rawimage)
        # print 'setFeatures', rawimage.shape, labelimage.shape

        if is_3D == 0 and labelimage.ndim == 3:
            labelimage = np.squeeze(labelimage)

        features = vigra.analysis.extractRegionFeatures(np.float32(rawimage), np.uint32(labelimage))

        for key in features:
            feature_string = key
            feature_string = convertKeyName(feature_string)
            if len(feature_string) > 15:
                shortname = getShortname(feature_string).replace('_', '')
            else:
                shortname = feature_string.replace('_', '')

            isInt = isinstance(features[key], int)

            if (np.array(features[key])).ndim == 2:
                if key != 'Histogram':
                    #print key, np.array(features[key]).shape
                    for column in xrange((np.array(features[key])).shape[1]):
                        builder.addFeatureName(feature_string + '_' + str(column), feature_string, shortname + '_' + str(column), isInt)

            else:
                #print "ELSE", key, np.array(features[key]).shape
                builder.addFeatureName(feature_string, feature_string, shortname, isInt)

class TrackingMamutExportFormatPlugin(TrackingExportFormatPlugin):
    """MaMuT export"""

    exportsToFile = True

    def export(self, filename, hypothesesGraph, objectFeaturesSlot, labelImageSlot):
        """Export the tracking solution stored in the hypotheses graph to two XML files so that 
        a) the raw data can be displayed in Fiji's BigDataViewer, and b) that the tracks can be visualized in MaMuT. 

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param objectFeaturesSlot: lazyflow.graph.InputSlot, connected to the RegionFeaturesAll output 
               of ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction
        
        :returns: True on success, False otherwise
        """
        bigDataViewerFile = filename + '_bdv.xml'
        builder = MamutXmlBuilder()
        graph = hypothesesGraph._graph

        features = objectFeaturesSlot([]).wait() # this isa dict of structure: frame: category: featureNames

        for node in graph.nodes_iter():
            frame, label = node

            if graph.node[node]['value'] > 0:
                t = graph.node[node]['traxel']

                radius = 2*features[frame]['Standard Object Features']['RegionRadii'][label, 0]
                
                featureDict = {}
                for category in features[frame].keys():
                    for key in features[frame][category].keys():
                        if key != 'Histogram':
                            if label != 0: # ignoring background
                                if (np.array(features[frame][category][key])).ndim == 0:
                                    featureDict[convertKeyName(key)] = features[frame][category][key]
                                if (np.array(features[frame][category][key])).ndim == 1:
                                    featureDict[convertKeyName(key)] = features[frame][category][key][label]
                                if (np.array(features[frame][category][key])).ndim == 2:
                                    for j in xrange((np.array(features[frame][category][key])).shape[1]):
                                        try:
                                            exists = features[frame][category][key][label, 0]
                                        except IndexError:
                                            if 'SquaredDistances' in key:
                                                featureDict[convertKeyName(key) + '_{}'.format(str(j))] = 9999.
                                            else:
                                                featureDict[convertKeyName(key) + '_{}'.format(str(j))] = 0.
                                            continue
                                        featureDict[convertKeyName(key) + '_{}'.format(str(j))] = features[frame][category][key][label, j]

                # TODO: builder.addSpot(frame, graph.node[node]['id'], t.X(), t.Y(), t.Z(), radius, featureDict)
                # instead of the next lines
                xpos = features[frame]['Standard Object Features']['RegionCenter'][label, 0]
                ypos = features[frame]['Standard Object Features']['RegionCenter'][label, 1]
                try:
                    zpos = features[frame]['Standard Object Features']['RegionCenter']
                except keyError:
                    zpos = 0.0
                builder.addSpot(frame, graph.node[node]['id'], xpos, ypos, zpos, radius, featureDict)


        for edge in graph.edges_iter():
            if graph.edge[edge[0]][edge[1]]['value'] > 0:
                builder.addLink(graph.node[edge[0]]['trackId'], graph.node[edge[0]]['id'], graph.node[edge[1]]['id'])

        for node in graph.nodes_iter():
            if'divisionValue' in graph.node[node].keys() and graph.node[node]['divisionValue'] > 0:
                parentId = graph.node[node]['children'][0][0]
                childrenIds = [ graph.node[node]['children'][0][1] ] + [ graph.node[node]['children'][1][1] ]
                builder.addSplit(graph.node[node]['id'], parentId, childrenIds)

        builder.setBigDataViewerImagePath(os.path.dirname(bigDataViewerFile), os.path.basename(bigDataViewerFile))
        builder.writeToFile(filename + '_mamut.xml')

        return True
