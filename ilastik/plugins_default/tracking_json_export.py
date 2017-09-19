import os.path
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin

import logging
logger = logging.getLogger(__name__)

try:
    from hytra.core.jsongraph import writeToFormattedJSON
except ImportError:
    logger.warn("Could not load hytra. JSON export plugin not loaded.")
else:

    class TrackingJSONExportFormatPlugin(TrackingExportFormatPlugin):
        """JSON export"""

        exportsToFile = True

        def checkFilesExist(self, filename):
            ''' Check whether the files we want to export are already present '''
            return os.path.exists(filename + '_graph.json') or os.path.exists(filename + '_result.json')

        def export(self, filename, hypothesesGraph, objectFeaturesSlot, labelImageSlot, rawImageSlot):
            """
            Export the tracking model and result

            :param filename: string of the FILE where to save the result (will be appended with _graph.json and _result.json)
            :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
            :param objectFeaturesSlot: lazyflow.graph.InputSlot, connected to the RegionFeaturesAll output
                   of ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction

            :returns: True on success, False otherwise
            """
            hypothesesGraph.insertEnergies()
            trackingGraph = hypothesesGraph.toTrackingGraph()

            writeToFormattedJSON(filename + '_graph.json',  trackingGraph.model)
            writeToFormattedJSON(filename + '_result.json', hypothesesGraph.getSolutionDictionary())

            return True
