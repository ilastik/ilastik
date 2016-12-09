from ilastik.plugins import TrackingExportFormatPlugin

class TrackingH5EventExportFormatPlugin(TrackingExportFormatPlugin):
    """H5 Sequence export"""

    exportsToFile = True

    def export(self, filename, hypothesesGraph, objectFeaturesSlot, labelImageSlot):
        """Export the tracking solution stored in the hypotheses graph as a sequence of H5 files,
        one per frame, containing the label image of that frame and which objects were part
        of a move or a division.

        :param filename: string of the FOLDER where to save the result
        :param hypothesesGraph: hytra.core.hypothesesgraph.HypothesesGraph filled with a solution
        :param objectFeaturesSlot: lazyflow.graph.InputSlot, connected to the RegionFeaturesAll output 
               of ilastik.applets.trackingFeatureExtraction.opTrackingFeatureExtraction.OpTrackingFeatureExtraction
        
        :returns: True on success, False otherwise
        """
        return False