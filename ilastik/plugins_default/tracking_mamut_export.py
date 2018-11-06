import os.path

import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
from mamutexport.mamutxmlbuilder import MamutXmlBuilder


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

    def export(self, filename, hypothesesGraph, pluginExportContext):
        """Export the tracking solution stored in the hypotheses graph to MaMuT XML file.
        Creates an _mamut.xml file that contains the tracks for visualization and proof-reading in MaMuT.

        :param filename: string of the FILE where to save the result (*_mamut.xml file)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
            objectFeaturesSlot (required here), additionalPluginArgumentsSlot (required here)
            as well as rawImageSlot, labelImageSlot

        :returns: True on success, False otherwise
        """

        builder = MamutXmlBuilder()
        graph = hypothesesGraph._graph

        features = pluginExportContext.objectFeaturesSlot([]).wait() # this is a dict of structure: {frame: {category: {featureNames}}}

        # first loop over all nodes to find present features
        presentTrackIds = set([])
        for node in graph.nodes_iter():
            frame, label = node
            # print(f"Node {node} has value={graph.node[node]['value']} and trackId={graph.node[node]['trackId']}")
            if graph.node[node]['value'] > 0:
                for category in list(features[frame].keys()):
                    for key in list(features[frame][category].keys()):
                        feature_string = convertKeyName(key)
                        if len(feature_string) > 15:
                            shortname = getShortname(feature_string).replace('_', '')
                        else:
                            shortname = feature_string.replace('_', '')

                        isInt = isinstance(features[frame][category][key], int)

                        if (np.asarray(features[frame][category][key])).ndim == 2:
                            if key != 'Histogram':
                                for column in range((np.asarray(features[frame][category][key])).shape[1]):
                                    builder.addFeatureName(feature_string + '_' + str(column), feature_string, shortname + '_' + str(column), isInt)
                        else:
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
                                feature_string = convertKeyName(key)
                                ndim = (np.asarray(features[frame][category][key])).ndim
                                if ndim == 0:
                                    featureDict[feature_string] = features[frame][category][key]
                                elif ndim == 1:
                                    featureDict[feature_string] = features[frame][category][key][label]
                                elif ndim == 2:
                                    for j in range((np.asarray(features[frame][category][key])).shape[1]):
                                        try:
                                            _ = features[frame][category][key][label, 0]
                                        except IndexError:
                                            if 'SquaredDistances' in key:
                                                featureDict[feature_string + '_{}'.format(str(j))] = 9999.
                                            else:
                                                featureDict[feature_string + '_{}'.format(str(j))] = 0.
                                            continue
                                        featureDict[feature_string + '_{}'.format(str(j))] = features[frame][category][key][label, j]
                                else:
                                    raise ValueError(f"Found feature matrix {feature_string} that has a dimensionality of > 2, cannot handle that yet")

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

        additional_plugin_args = pluginExportContext.additionalPluginArgumentsSlot.value
        assert 'bdvFilepath' in additional_plugin_args, "'bdvFilepath' must be present in 'additionalPluginArgumentsSlot'"
        bigDataViewerFile = additional_plugin_args['bdvFilepath']
        builder.setBigDataViewerImagePath(os.path.dirname(bigDataViewerFile), os.path.basename(bigDataViewerFile))
        builder.writeToFile(filename + '_mamut.xml')

        return True
