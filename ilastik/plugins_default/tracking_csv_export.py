import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
import vigra

class TrackingCSVExportFormatPlugin(TrackingExportFormatPlugin):
    """CSV export"""

    exportsToFile = True

    def checkOverwriteFiles(self, filename, checkOverwriteFiles):
        print filename
        if checkOverwriteFiles and os.path.exists(filename + '.csv'):
            return True
        else:
            return False

    def export(self, filename, hypothesesGraph, objectFeaturesSlot, labelImageSlot, rawImageSlot):
        """
        Export the features of all objects together with their tracking information

        :param filename: string of the FILE where to save the result (different .xml files were)
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param objectFeaturesSlot: lazyflow.graph.InputSlot, connected to the RegionFeaturesAll output
               of ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction

        :returns: True on success, False otherwise
        """
        features = objectFeaturesSlot([]).wait()  # this is a dict of structure: {frame: {category: {featureNames}}}
        graph = hypothesesGraph._graph
        headers = ['frame', 'labelimageId', 'trackId', 'lineageId', 'parentTrackId']
        excludedFeatures = ['Histogram']
        
        # check which features are present and construct table of the appropriate size
        frame, _ = graph.nodes_iter().next()
        for category in features[frame].keys():
            for feature in features[frame][category].keys():
                if feature not in excludedFeatures:
                    if (np.array(features[frame][category][feature])).ndim == 2:
                        for column in range(np.array(features[frame][category][feature]).shape[1]):
                            singleFeatureValueName = '{f}_{c}'.format(f=feature, c=column)
                            headers.append(singleFeatureValueName)
                    else:
                        headers.append(feature)

        table = np.zeros([graph.number_of_nodes(), len(headers)])

        for rowIdx, node in enumerate(graph.nodes_iter()):
            frame, label = node    
            trackId = graph.node[node]['trackId']
            lineageId = graph.node[node]['lineageId']

            table[rowIdx, 0] = frame
            table[rowIdx, 1] = label
            table[rowIdx, 2] = trackId
            table[rowIdx, 3] = lineageId
            try:
                table[rowIdx, 4] = graph.node[graph.node[node]['parent']]['trackId']
            except KeyError:
                table[rowIdx, 4] = 0
            colIdx = 5

            for category in features[frame].keys():
                for feature in features[frame][category].keys():

                    if feature not in excludedFeatures:
                        if (np.array(features[frame][category][feature])).ndim == 2:
                            for column in range(np.array(features[frame][category][feature]).shape[1]):
                                try:
                                    table[rowIdx, colIdx] = features[frame][category][feature][label, column]
                                except IndexError:
                                    if 'SquaredDistances' in feature:
                                        table[rowIdx, colIdx] = 9999
                                    else:
                                        table[rowIdx, colIdx] = 0
                                colIdx += 1
                        else:
                            table[rowIdx, colIdx] = features[frame][category][feature][label]
                            colIdx += 1

        # sort table by frame, then labelImage
        table = table[table[:,1].argsort()]
        table = table[table[:,0].argsort(kind='mergesort')]

        headerLine = ','.join(headers)
        np.savetxt(filename + '.csv', table, header=headerLine, delimiter=',', comments='')

        return True
