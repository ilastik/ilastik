import os.path
import textwrap
import numpy as np
from ilastik.plugins import TrackingExportFormatPlugin

import logging

from ilastik.plugins.types import PluginInfo

logger = logging.getLogger(__name__)

try:
    from hytra.core.jsongraph import writeToFormattedJSON
except ImportError:
    logger.warning("Could not load hytra. JSON export plugin not loaded.")
else:

    class TrackingJSONExportFormatPlugin(TrackingExportFormatPlugin):
        """JSON export"""

        plugin_info = PluginInfo(
            name="JSON",
            author="Carsten Haubold",
            version="0.1",
            website="ilastik.org",
            description=textwrap.dedent(
                """
                JSON export for use of some tracking analysis tools developed by the ilastik tracking guys.
                <br><br>
                <b>Usage:</b> Select the folder in which two files will be exported:
                <ul>
                    <li> The tracking <b>hypotheses graph</b> will have the suffix and extension <i> _graph.json </i>.</li>
                    <li> The tracking <b>result</b> with suffix and extension <i> _result.json </i>. </li>
                </ul>
                <br><br>
                Both contain <i>segmentationHypotheses</i> (or <i>detections</i>), <i>linkingHypotheses</i>, and possibly <i>divisions</i>.
                Each detection is assigned a globally unique <i>id</i>, and in the graph there is a <i>traxelToUniqueId</i>
                mapping from timestep and object ID inside ilastik to those unique ids.
                The graph also contains the costs of different configurations of every detection, division, and link.
                The result assigns a state to each of them.
                """
            ),
        )
        exportsToFile = True

        def checkFilesExist(self, filename):
            """Check whether the files we want to export are already present"""
            return os.path.exists(filename + "_graph.json") or os.path.exists(filename + "_result.json")

        def export(self, filename, hypothesesGraph, pluginExportContext):
            """
            Export the tracking model and result

            :param filename: string of the FILE where to save the result (will be appended with _graph.json and _result.json)
            :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
            :param pluginExportContext: additional contextual info (here to adhere to the interface)

            :returns: True on success, False otherwise
            """

            # The nodes inserted into the graph after merger resolving
            # do not have detectionProbabilities set. We first find one node that was no merger,
            # check how many entries are needed, and then insert 0.0 as detection probabilities there everywhere.

            numStates = -1
            for n in hypothesesGraph.nodeIterator():
                t = hypothesesGraph._graph.nodes[n]["traxel"]
                if "detProb" in t.Features:
                    numStates = len(t.Features["detProb"])
                    break

            assert numStates > 0, "Cannot export hypotheses graph without features (e.g. only resolved mergers) to JSON"

            dummyVector = np.zeros(numStates)
            for n in hypothesesGraph.nodeIterator():
                t = hypothesesGraph._graph.nodes[n]["traxel"]
                if "detProb" not in t.Features:
                    logger.debug(f"replacing detProb of node with ID={hypothesesGraph._graph.nodes[n]['id']}")
                    t.Features["detProb"] = dummyVector

            # now we can insert the energies into the graph
            hypothesesGraph.insertEnergies()
            trackingGraph = hypothesesGraph.toTrackingGraph()

            writeToFormattedJSON(filename + "_graph.json", trackingGraph.model)
            writeToFormattedJSON(filename + "_result.json", hypothesesGraph.getSolutionDictionary())

            return True
