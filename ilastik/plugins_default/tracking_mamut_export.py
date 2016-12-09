import os.path
from ilastik.plugins import TrackingExportFormatPlugin
from ilastik.plugins_default.mamutxmlbuilder import MamutXmlBuilder
from ilastik.plugins_default.bigdataviewervolumeexporter import BigDataViewerVolumeExporter

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
        for node in graph.nodes_iter():
            if graph.node[node]['value'] > 0:
                t = graph.node[node]['traxel']
                builder.addSpot(node[0], graph.node[node]['id'], t.X(), t.Y(), t.Z(), t.Features)

        for edge in graph.edges_iter():
            if graph.edge[edge[0]][edge[1]]['value'] > 0:
                builder.addLink(graph.node[edge[0]]['track_id'], graph.node[edge[0]]['id'], graph.node[edge[1]]['id'])

        for node in graph.nodes_iter():
            if graph.node[node]['divisionValue'] > 0:
                builder.addSplit(graph.node[node]['id'], children)

        builder.setBigDataViewerImagePath(os.path.dirname(bigDataViewerFile), os.path.basename(bigDataViewerFile))
        builder.writeToFile(filename + '_mamut.xml')
