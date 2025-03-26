from builtins import range
import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin
import vigra


class TrackingCSVExportFormatPlugin(TrackingExportFormatPlugin):
    """CSV export"""

    exportsToFile = True

    def checkFilesExist(self, filename):
        """Check whether the files we want to export are already present"""
        return os.path.exists(filename + ".csv")

    def export(self, filename, hypothesesGraph, pluginExportContext):
        """
        Export the features of all objects together with their tracking information into a table

        :param filename: string of the FILE where to save the resulting CSV file
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param pluginExportContext: instance of ilastik.plugins.PluginExportContext containing:
            objectFeaturesSlot (required here) as well as labelImageSlot, rawImageSlot, additionalPluginArgumentsSlot

        :returns: True on success, False otherwise
        """

    def importFromCSV(self, filename):
        """
        Import tracking data from a CSV file.
        :param filename: string of the FILE to read the CSV data from
        :returns: A dictionary containing the imported data
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"The file '{filename}' does not exist.")

        # Read the CSV file
        data = np.genfromtxt(filename, delimiter=",", names=True, dtype=None, encoding="utf-8")

        # Convert the structured array into a dictionary for easier processing
        importedData = {col: data[col] for col in data.dtype.names}

        return importedData

        features = pluginExportContext.objectFeaturesSlot(
            []
        ).wait()  # this is a dict of structure: {frame: {category: {featureNames}}}
        graph = hypothesesGraph._graph
        headers = ["frame", "labelimageId", "trackId", "lineageId", "parentTrackId", "mergerLabelId"]
        formats = ["%d"] * len(headers)
        excludedFeatures = ["Histogram"]

        def appendFormat(featureName):
            if (
                "Number_of" in featureName
                or "Center_of" in featureName
                or "Bounding_Box" in featureName
                or featureName == "Size_in_pixels"
            ):
                formats.append("%d")
            else:
                formats.append("%f")

        # check which features are present and construct table of the appropriate size
        # need to awkwardly grab one node in the for loop since networkx 2.0
        for node in graph.nodes():
            frame = node[0]
            break

        # the feature categories can contain 'Default features' and 'Standard Object Features',
        # which actually reference the same features. Hence we block all of the one group from the other to prevent duplicates.
        categories = list(features[frame].keys())
        blockedFeatures = dict([(c, []) for c in categories])
        defaultFeatStr = "Default features"
        standardObjFeatStr = "Standard Object Features"

        if defaultFeatStr in categories and standardObjFeatStr in categories:
            for feature in list(features[frame][defaultFeatStr].keys()):
                blockedFeatures[standardObjFeatStr].append(feature)

        for category in categories:
            for feature in sorted(list(features[frame][category].keys())):
                if feature not in excludedFeatures and feature not in blockedFeatures[category]:
                    featureName = self._getFeatureNameTranslation(category, feature).replace(" ", "_")
                    ndim = (np.asarray(features[frame][category][feature])).ndim
                    if ndim == 2:
                        for column in range(np.asarray(features[frame][category][feature]).shape[1]):
                            singleFeatureValueName = "{f}_{c}".format(f=featureName, c=column)
                            headers.append(singleFeatureValueName)
                            appendFormat(singleFeatureValueName)
                    elif ndim == 1:
                        headers.append(featureName)
                        appendFormat(featureName)
                    elif ndim == 0:
                        pass  # ignoring "global" features
                    else:
                        raise ValueError(
                            f"Found feature matrix {feature} that has a dimensionality of > 2, cannot handle that yet"
                        )

        table = np.zeros([graph.number_of_nodes(), len(headers)])

        for rowIdx, node in enumerate(graph.nodes()):
            frame, label = node
            trackId = graph.nodes[node]["trackId"]
            lineageId = graph.nodes[node]["lineageId"]

            if trackId is None:
                trackId = -1
            if lineageId is None:
                lineageId = -1

            table[rowIdx, 0] = frame
            table[rowIdx, 1] = label
            table[rowIdx, 2] = trackId
            table[rowIdx, 3] = lineageId

            # insert parent of a division
            try:
                table[rowIdx, 4] = graph.nodes[graph.nodes[node]["parent"]]["trackId"]
            except KeyError:
                table[rowIdx, 4] = 0

            # insert merger
            try:
                if isinstance(graph.nodes[node]["mergerValue"], int):
                    table[rowIdx, 5] = graph.nodes[node]["mergerValue"]
                else:
                    table[rowIdx, 5] = 0
            except KeyError:
                table[rowIdx, 5] = 0
            colIdx = 6

            for category in categories:
                for feature in sorted(list(features[frame][category].keys())):

                    if feature not in excludedFeatures and feature not in blockedFeatures[category]:
                        ndim = (np.asarray(features[frame][category][feature])).ndim
                        if ndim == 2:
                            for column in range(np.asarray(features[frame][category][feature]).shape[1]):
                                try:
                                    table[rowIdx, colIdx] = features[frame][category][feature][label, column]
                                except IndexError:
                                    if "SquaredDistances" in feature:
                                        table[rowIdx, colIdx] = 9999
                                    else:
                                        table[rowIdx, colIdx] = 0
                                colIdx += 1
                        elif ndim == 1:
                            table[rowIdx, colIdx] = features[frame][category][feature][label]
                            colIdx += 1
                        elif ndim == 0:
                            pass  # ignoring "global" features
                        else:
                            raise ValueError(
                                f"Found feature matrix {feature} that has a dimensionality of > 2, cannot handle that yet"
                            )

        # sort table by frame, then labelImage
        table = table[np.lexsort(table[:, :2].transpose()[::-1])]

        headerLine = ",".join(headers)
        np.savetxt(filename + ".csv", table, header=headerLine, delimiter=",", comments="", fmt=formats)

        return True
